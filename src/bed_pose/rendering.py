"""Postprocess verified frames into self-contained SVG overlays, preserving PTS."""
import base64
from html import escape
from pathlib import Path
import struct
import zlib
from .contracts import SourceError
from .evaluation import read_run
from .io_utils import atomic_json, file_hash
from .video import VideoSource

# COCO17 topology, for visual inspection only; no anatomical acceptance rule.
EDGES = ((0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9),
         (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13),
         (13, 15), (12, 14), (14, 16))
COLORS = ('#00ffb3', '#ffbf00', '#90b7ff', '#ff81e3')
BANNER = 88


def png_bytes(rgb):
    """Lossless RGB PNG using the standard library; no plotting dependency."""
    height, width, channels = rgb.shape
    if channels != 3 or rgb.dtype.name != 'uint8':
        raise ValueError('Expected uint8 RGB')
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    scanlines = b''.join(b'\x00' + rgb[y].tobytes() for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b''))


def frame_svg(packet, row, mapped, execution_kind, run_status):
    width, height = packet.width, packet.height
    canvas_width = max(width, 640)
    stamp = f"{row['source_pts']} x {row['time_base_num']}/{row['time_base_den']} s" if row['source_pts'] is not None else 'unavailable'
    synthetic = execution_kind == 'synthetic'
    label = 'SYNTHETIC - NOT AI INFERENCE' if synthetic else 'MODEL PREDICTIONS - NOT VERIFIED GT'
    text = [label,
            f"run={run_status} frame={row['frame_id']} status={row['processing_status']} candidates={row['candidate_count']} PTS={stamp}",
            f"target=not_configured failure={row['failure_code']} | IDs are frame-local; lines do not certify quality"]
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{height + BANNER}" viewBox="0 0 {canvas_width} {height + BANNER}">',
                f'<rect width="100%" height="100%" fill="#151515"/>',
                f'<image x="0" y="{BANNER}" width="{width}" height="{height}" href="data:image/png;base64,{base64.b64encode(png_bytes(packet.rgb)).decode()}"/>']
    for index, value in enumerate(text):
        elements.append(f'<text x="8" y="{20 + index * 24}" fill="{("#ffb0b0" if synthetic else "white")}" font-size="14" font-family="sans-serif">{escape(value)}</text>')
    for index, person in enumerate(mapped['people'] if mapped else []):
        color = COLORS[index % len(COLORS)]
        points = {j: (joint['x_px'], joint['y_px'] + BANNER)
                  for j, joint in enumerate(person['joints'])
                  if joint['availability'] == 'predicted' and
                  0 <= joint['x_px'] < width and 0 <= joint['y_px'] < height}
        for a, b in EDGES:
            if a in points and b in points:
                x1, y1 = points[a]
                x2, y2 = points[b]
                elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>')
        for j, (x, y) in points.items():
            elements.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"><title>{escape(person["candidate_id"])} joint={j}</title></circle>')
    return '\n'.join(elements) + '\n</svg>\n'


def render_overlay(video_path, run_dir, output):
    bundle = read_run(run_dir, include_keypoints=True)
    manifest, source = bundle['manifest'], bundle['source']
    video_path, output = Path(video_path).resolve(), Path(output).resolve()
    if file_hash(video_path) != source['video_sha256']:
        raise SourceError('Render video does not match the run input')
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'manifest.json', {'complete': False, 'run_id': manifest['run_id']})
    mapped = {row['frame_id']: row for row in bundle['keypoints']}
    decoder = VideoSource(source, bundle['input_frames'], video_path)
    hashes, catalog = {}, []
    try:
        decoder.open()
        for row in bundle['frames']:
            packet = decoder.read_next()
            if packet is None:
                raise SourceError('Render source ended before recorded frames')
            name = f"frame_{row['frame_id']:08d}.svg"
            (output / name).write_text(frame_svg(packet, row, mapped.get(row['frame_id']),
                                                manifest['execution_kind'], manifest['run_status']), encoding='utf-8')
            hashes[name] = file_hash(output / name)
            catalog.append({'file': name, **{k: row[k] for k in ('frame_id', 'source_pts', 'time_base_num',
                'time_base_den', 'source_duration_pts', 'timestamp_source',
                'processing_status', 'candidate_count', 'failure_code')}})
        if decoder.read_next() is not None:
            raise SourceError('Render source has unrecorded frames')
    finally:
        decoder.close()
    if file_hash(video_path) != source['video_sha256'] or file_hash(Path(run_dir) / 'manifest.json') != bundle['manifest_sha256']:
        raise SourceError('Render inputs changed during rendering')
    links = ''.join(f'<li><a target="preview" href="{r["file"]}">frame {r["frame_id"]}: {escape(r["processing_status"])}; PTS={escape(str(r["source_pts"]))}</a></li>' for r in catalog)
    html = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Pose overlays</title>'
            '<body><h1>Frame overlays</h1><p>' + escape(manifest['execution_kind']) + '; run=' + escape(manifest['run_status']) +
            '; no GT or posture/event decisions. Frame selection is manual; no synthetic playback timing.</p>'
            f'<iframe title="Selected frame" name="preview" src="{catalog[0]["file"]}" style="width:95vw;height:70vh;border:0"></iframe>'
            f'<ol>{links}</ol></body></html>')
    (output / 'index.html').write_text(html, encoding='utf-8')
    atomic_json(output / 'frames.json', catalog)
    for name in ('index.html', 'frames.json'):
        hashes[name] = file_hash(output / name)
    from .runner import _code_version
    report = {'complete': True, 'renderer_code': _code_version(), 'run_id': manifest['run_id'], 'run_status': manifest['run_status'],
              'execution_kind': manifest['execution_kind'], 'run_manifest_sha256': bundle['manifest_sha256'],
              'video_sha256': source['video_sha256'], 'input_manifest_sha256': manifest['input_manifest_sha256'],
              'frame_count': len(catalog), 'format': 'svg_with_lossless_rgb_png', 'playback': 'manual_frame_selection',
              'artifact_sha256': hashes}
    atomic_json(output / 'manifest.json', report)
    return output, report
