"""Commands for prepared input, explicit adapters and result integrity."""
import argparse
import json
from pathlib import Path
import sys
from jsonschema import ValidationError
from .contracts import IntegrityError, SourceError
from .io_utils import file_hash, load_json
from .pose.fake import FakeOptions
from .recording import verify_records
from .runner import run_benchmark, validate_run
from .video import prepare_input


def _testing_args(parser):
    parser.add_argument('--fake-fail-at', type=int, default=None,
                        help='Intentionally fail at this zero-based frame (synthetic only)')
    parser.add_argument('--fake-no-detection-at', type=int, action='append', default=[])
    parser.add_argument('--fake-people', type=int, default=1)
    parser.add_argument('--fake-missing-joint', type=int, action='append', default=[])


def _options(args):
    return FakeOptions(tuple(args.fake_no_detection_at), args.fake_fail_at,
                       args.fake_people, tuple(args.fake_missing_joint))


def _summary(path, manifest):
    return {'run_directory': str(path), 'execution_kind': manifest['execution_kind'],
            'run_status': manifest['run_status'], 'ledger_complete': manifest['ledger_complete'],
            'counts': manifest['counts'], 'errors': manifest['errors']}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prepared-video pose benchmark and synthetic pipeline checks.')
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='Decode a video and fix its frame/PTS manifest')
    prepare.add_argument('--video', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    prepare.add_argument('--run-output-root', type=Path, default=None)
    run = commands.add_parser('run', help='Run the configured adapter on prepared video frames')
    run.add_argument('--config', type=Path, required=True)
    _testing_args(run)
    demo = commands.add_parser('demo', help='Generate a nonhuman test video and run the synthetic adapter')
    demo.add_argument('--output', type=Path, required=True)
    _testing_args(demo)
    inspect = commands.add_parser('inspect', help='Verify result hashes, frame identities and record references')
    inspect.add_argument('--run', type=Path, required=True)
    configure = commands.add_parser('configure-mediapipe', help='Create a hashed MediaPipe config; does not download models')
    configure.add_argument('--config', type=Path, required=True)
    configure.add_argument('--model', type=Path, required=True)
    configure.add_argument('--output', type=Path, required=True)
    configure.add_argument('--num-poses', type=int, default=1)
    configure.add_argument('--execution-mode', choices=('independent_frames', 'ordered_sequence'), default='independent_frames')
    args = parser.parse_args(argv)
    try:
        if args.command == 'configure-mediapipe':
            from .pose.mediapipe import prepare_configuration
            path = prepare_configuration(args.config, args.model, args.output,
                        execution_mode=args.execution_mode, num_poses=args.num_poses)
            print(json.dumps({'config': str(path)}, ensure_ascii=False))
            return 0
        if args.command == 'prepare':
            path = prepare_input(args.video, args.output, args.run_output_root)
            print(json.dumps({'input_manifest': str(path), 'sha256': file_hash(path),
                              'fake_config': str(path.parent / 'run_config.fake.json')}, ensure_ascii=False))
            return 0
        if args.command == 'inspect':
            manifest = load_json(args.run / 'manifest.json')
            if not manifest['ledger_complete']:
                raise IntegrityError('Run ledger is incomplete; inspect manifest errors before using any results')
            counts = verify_records(args.run, manifest)
            if counts != manifest['counts']:
                raise IntegrityError('Persisted counters differ from the manifest')
            print(json.dumps(dict(_summary(args.run, manifest), integrity='verified'), ensure_ascii=False))
            return 0
        if args.command == 'demo':
            from .demo import create_demo_video
            args.output = args.output.resolve()
            args.output.mkdir(parents=True, exist_ok=False)
            video = create_demo_video(args.output / 'synthetic_input.mkv')
            prepared = prepare_input(video, args.output / 'input', args.output / 'runs')
            config_path = prepared.parent / 'run_config.fake.json'
        else:
            config_path = args.config
        validated = validate_run(config_path, _options(args))
        path, manifest = run_benchmark(validated)
        print(json.dumps(_summary(path, manifest), ensure_ascii=False))
        if not manifest['ledger_complete']:
            return 4
        return {'succeeded': 0, 'failed': 3, 'cancelled': 130}[manifest['run_status']]
    except IntegrityError as exc:
        print(f'Integrity error: {exc}', file=sys.stderr)
        return 4
    except (SourceError, ValueError, OSError, ValidationError, KeyError, TypeError) as exc:
        print(f'Input/configuration error: {exc}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f'Execution error ({type(exc).__name__}): {exc}', file=sys.stderr)
        return 3
