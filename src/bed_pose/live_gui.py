"""Native Tk preview and manual bed region controls; all inference stays in a worker."""
import base64
from pathlib import Path
import queue
import tempfile
import time
from .io_utils import atomic_json, file_hash
from .live_engine import LiveEngine, LiveWorker
from .live_sources import CameraSource, SyntheticSource
from .rendering import COLORS, EDGES, png_bytes


def viewport(width, height, image_width, image_height):
    scale = min(width/image_width, height/image_height)
    return scale, (width-image_width*scale)/2, (height-image_height*scale)/2


def source_point(x, y, width, height, image_width, image_height, clamp=False):
    scale, dx, dy = viewport(width, height, image_width, image_height)
    px, py = (x-dx)/scale, (y-dy)/scale
    if clamp:
        return max(0, min(image_width, px)), max(0, min(image_height, py))
    if not 0 <= px <= image_width or not 0 <= py <= image_height:
        return None
    return px, py


class LiveWindow:
    def __init__(self, root, worker):
        import tkinter as tk
        from tkinter import ttk, font
        self.tk, self.ttk, self.root, self.worker = tk, ttk, root, worker
        families = {name.casefold(): name for name in font.families(root)}
        choices = ('Malgun Gothic','맑은 고딕','Noto Sans CJK KR','Noto Sans CJK SC','Unifont')
        self.font_family = next((families[name.casefold()] for name in choices if name.casefold() in families),
                                font.nametofont('TkDefaultFont').actual('family'))
        self.frame = self.region = self.drag_start = self.drag_end = None
        self.geometry = None
        self.drag_frame_id = None
        self.pending, self.recording, self.closed, self.closing, self.had_error = False, False, False, False, False
        self.close_started = None
        self.last_error = None
        self.record_count = 0
        self.measure_started_ns = None
        self.measure_elapsed = 0.0
        root.title('BedPose · 실시간 측정')
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f'{min(1200,max(820,screen_w-80))}x{min(850,max(600,screen_h-80))}')
        root.minsize(min(900,screen_w-60), min(640,screen_h-60))
        root.configure(background='#f3f6fa')
        style = ttk.Style(root)
        style.configure('TFrame', background='#f3f6fa')
        style.configure('TLabel', background='#f3f6fa', foreground='#172538', font=(self.font_family, 10))
        style.configure('Title.TLabel', font=(self.font_family, 18, 'bold'))
        style.configure('TButton', font=(self.font_family, 10), padding=(12, 8))
        style.configure('TCheckbutton', font=(self.font_family, 10), background='#f3f6fa')
        style.configure('TEntry', font=(self.font_family, 10))
        outer = ttk.Frame(root, padding=20)
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x', pady=(0, 12))
        ttk.Label(header, text='BedPose  실시간 측정', style='Title.TLabel').pack(side='left')
        self.kind = tk.StringVar(value='연결 중')
        ttk.Label(header, textvariable=self.kind).pack(side='right')
        self.status = tk.StringVar(value='카메라와 모델을 준비하고 있습니다.')
        ttk.Label(outer, textvariable=self.status, wraplength=1100).pack(anchor='w', pady=(0, 10))
        self.canvas = tk.Canvas(outer, background='#0c1420', highlightthickness=0, height=470)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.canvas.bind('<ButtonPress-1>', self.drag_begin)
        self.canvas.bind('<B1-Motion>', self.drag_move)
        self.canvas.bind('<ButtonRelease-1>', self.drag_finish)
        ttk.Label(outer, text='영상에서 침대의 두 모서리를 드래그해 영역을 지정하세요. 카메라는 측정 중 고정하세요.').pack(anchor='w', pady=(10, 6))
        controls = ttk.Frame(outer)
        controls.pack(fill='x')
        self.start_button = ttk.Button(controls, text='측정 시작', command=self.start)
        self.start_button.pack(side='left', padx=(0, 8))
        self.stop_button = ttk.Button(controls, text='측정 종료', command=self.stop)
        self.stop_button.pack(side='left', padx=(0, 8))
        self.clear_button = ttk.Button(controls, text='침대 영역 지우기', command=self.clear_region)
        self.clear_button.pack(side='left', padx=(0, 16))
        self.overlay = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text='관절 표시', variable=self.overlay, command=self.draw).pack(side='left')
        self.measure_status = tk.StringVar(value='기록 대기')
        ttk.Label(controls, textvariable=self.measure_status).pack(side='right')
        self.summary = tk.StringVar(value='프레임 수신 대기 · 침대 영역 미지정')
        ttk.Label(outer, textvariable=self.summary).pack(anchor='w', pady=(10, 4))
        ttk.Label(outer, text='자세 분류: 미구현  |  점유·이탈·복귀: 미구현  |  대상 추적: 미구현  |  원본 영상 저장: 꺼짐').pack(anchor='w')
        ttk.Label(outer, text='좌표 출력과 정확도는 다릅니다. 수신 시각을 기록하며 카메라 노출 시각·센서 동기화는 제공하지 않습니다.').pack(anchor='w', pady=(4, 8))
        self.path = tk.StringVar(value='측정을 시작하면 새 결과 폴더가 생성됩니다.')
        ttk.Entry(outer, textvariable=self.path, state='readonly').pack(fill='x')
        self.update_controls()
        root.bind('<Configure>', self.resize_text)
        self.outer = outer
        root.protocol('WM_DELETE_WINDOW', self.quit)
        root.after(30, self.poll)

    def resize_text(self, event):
        if event.widget == self.root:
            for child in self.outer.winfo_children():
                if isinstance(child, self.ttk.Label):
                    child.configure(wraplength=max(500, self.root.winfo_width()-40))

    def update_controls(self):
        active = not self.closed and not self.closing and not self.pending
        self.start_button.configure(state='normal' if active and self.frame is not None and self.region is not None and not self.recording else 'disabled')
        self.stop_button.configure(state='normal' if active and self.recording else 'disabled')
        self.clear_button.configure(state='normal' if active and self.frame is not None else 'disabled')

    def start(self):
        self.pending = True
        self.status.set('측정 기록을 준비하고 있습니다.')
        self.measure_status.set('시작 준비 중')
        self.update_controls()
        self.worker.submit('start')

    def stop(self):
        self.pending = True
        self.status.set('기록을 저장하고 검사하고 있습니다.')
        self.measure_status.set('기록 정리 중')
        self.update_controls()
        self.worker.submit('stop')

    def clear_region(self):
        if self.geometry:
            self.worker.submit('region', box=None, width=self.geometry[0], height=self.geometry[1], selected_frame_id=self.frame['row']['stream_frame_id'])

    def drag_begin(self, event):
        if self.frame is None or self.closed or self.closing:
            return
        self.drag_start = source_point(event.x, event.y, max(1, self.canvas.winfo_width()),
            max(1, self.canvas.winfo_height()), *self.geometry)
        self.drag_end = self.drag_start
        self.drag_frame_id = self.frame['row']['stream_frame_id']

    def drag_move(self, event):
        if self.drag_start is not None:
            self.drag_end = source_point(event.x, event.y, max(1, self.canvas.winfo_width()),
                max(1, self.canvas.winfo_height()), *self.geometry, clamp=True)
            self.draw()

    def drag_finish(self, event):
        self.drag_move(event)
        if self.drag_start is not None and self.drag_end is not None:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_end
            if x1 != x2 and y1 != y2:
                self.worker.submit('region', box=[min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)],
                                   width=self.geometry[0], height=self.geometry[1], selected_frame_id=self.drag_frame_id)
                self.status.set('침대 영역을 적용하고 있습니다.')
        self.drag_start = self.drag_end = None
        self.draw()

    def draw(self):
        if self.frame is None:
            return
        import cv2
        rgb = self.frame['rgb']
        width, height = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        scale, dx, dy = viewport(width, height, *self.geometry)
        image = cv2.resize(rgb, (max(1, round(self.geometry[0]*scale)), max(1, round(self.geometry[1]*scale))))
        self.photo = self.tk.PhotoImage(data=base64.b64encode(png_bytes(image)).decode('ascii'), format='png')
        self.canvas.delete('all')
        self.canvas.create_image(dx, dy, anchor='nw', image=self.photo)
        if self.overlay.get():
            for index, person in enumerate(self.frame['row']['mapped_people'] or []):
                points = {i:(dx+j['x_px']*scale, dy+j['y_px']*scale) for i,j in enumerate(person['joints'])
                          if j['availability']=='predicted' and 0<=j['x_px']<self.geometry[0] and 0<=j['y_px']<self.geometry[1]}
                color = COLORS[index%len(COLORS)]
                for a,b in EDGES:
                    if a in points and b in points:
                        self.canvas.create_line(*points[a], *points[b], fill=color, width=2)
                for x,y in points.values():
                    self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=color,outline='#0c1420')
        box = None
        if self.drag_start is not None and self.drag_end is not None:
            box = (*self.drag_start, *self.drag_end)
        elif self.region is not None:
            box = [self.region[k] for k in ('x1','y1','x2','y2')]
        if box is not None:
            self.canvas.create_rectangle(dx+box[0]*scale,dy+box[1]*scale,dx+box[2]*scale,dy+box[3]*scale,
                                         outline='#5da9ff',width=3,dash=(8,4))
        if self.worker.engine.execution_kind == 'synthetic':
            self.canvas.create_text(16,16,anchor='nw',text='합성 입력 · 실제 카메라/인식 아님',fill='white',font=(self.font_family,12,'bold'))

    def poll(self):
        try:
            while True:
                kind, value = self.worker.messages.get_nowait()
                if kind == 'ready':
                    self.kind.set('합성 입력 · 실제 인식 아님' if self.worker.engine.execution_kind=='synthetic' else '카메라 · 모델 출력')
                    self.status.set('영상을 확인하고 침대 영역을 드래그로 지정하세요.')
                elif kind == 'region':
                    self.region = value['region']
                    self.status.set('침대 영역을 수동 지정했습니다.' if self.region else '침대 영역 미지정 · 침대 관련 판정은 제공하지 않습니다.')
                elif kind == 'started':
                    self.recording, self.pending = True, False
                    self.record_count = 0
                    self.measure_started_ns = int(value['started_ns'])
                    self.measure_elapsed = 0.0
                    self.measure_status.set('측정 중 · 영상 저장 꺼짐')
                    self.path.set(value['directory'])
                    self.status.set('측정 중 · 관절과 시각을 기록합니다. 영상은 저장하지 않습니다.')
                elif kind == 'stopped':
                    self.recording, self.pending = False, False
                    self.path.set(value['directory'])
                    manifest = value['manifest']
                    self.record_count = manifest['recorded_frames']
                    self.measure_elapsed = (int(manifest['finished_ns'])-int(manifest['started_ns']))/1e9
                    self.measure_status.set('기록 검사 완료' if manifest['run_status']=='succeeded' else '기록 오류')
                    self.status.set(('측정 종료 · 기록 검사 완료' if manifest['run_status']=='succeeded' else '오류로 측정 종료') + f" · {manifest['recorded_frames']}프레임" + (' · '+self.last_error if manifest['run_status']=='failed' and self.last_error else ''))
                elif kind in ('error','command_rejected'):
                    self.pending = False
                    if kind == 'error':
                        self.had_error = True
                        self.last_error = value['message']
                        self.measure_status.set('오류 · 연결 종료 중')
                        self.frame = None
                        self.drag_start = self.drag_end = None
                        self.summary.set('입력/분석 중단 · 마지막 수신 결과는 현재 관측이 아닙니다.')
                        self.canvas.delete('all')
                        self.canvas.create_text(20,20,anchor='nw',text='입력/분석 중단 · 이전 결과를 현재 결과로 표시하지 않습니다.',fill='white',font=(self.font_family,12))
                    else:
                        self.measure_status.set('측정 중' if self.recording else '기록 대기')
                    self.status.set(('오류: ' if kind=='error' else '요청 확인: ') + value['message'])
                elif kind == 'closed':
                    self.closed = True
                    self.recording = self.pending = False
        except queue.Empty:
            pass
        try:
            frame = self.worker.frames.get_nowait()
            if self.had_error:
                raise queue.Empty
            self.frame = frame
            self.geometry = (self.frame['rgb'].shape[1], self.frame['rgb'].shape[0])
            row = self.frame['row']
            count = row['candidate_count']
            candidate = '후보 없음' if count==0 else f'출력 후보 {count}개'
            if self.recording:
                self.record_count = self.frame['recorded_frames']
                if self.measure_started_ns is not None and int(row['received_ns']) >= self.measure_started_ns:
                    self.measure_elapsed = (int(row['received_ns'])-self.measure_started_ns)/1e9
            self.summary.set(f"수신 프레임 {row['stream_frame_id']} · {candidate} · 최근 측정 기록 {self.record_count}개 · 측정 {self.measure_elapsed:.1f}초 · 세션 시각 +{int(row['received_ns'])/1e9:.1f}초 · 화면 교체 {self.frame['display_replaced']}개")
            try:
                self.draw()
            except Exception as exc:
                self.had_error = True
                self.last_error = str(exc)
                self.frame = None
                self.canvas.delete('all')
                self.status.set('화면 표시 오류: '+str(exc))
                self.worker.request_close()
        except queue.Empty:
            pass
        self.update_controls()
        if self.closing and self.closed:
            self.root.destroy()
            return
        if self.closing and self.close_started is not None and time.monotonic()-self.close_started > 5 and not self.closed:
            self.status.set('장치 응답을 기다리는 중입니다. 강제 종료하면 기록이 미완료 상태로 남을 수 있습니다.')
        self.root.after(30, self.poll)

    def quit(self):
        if self.closing:
            return
        self.closing = True
        self.close_started = time.monotonic()
        self.status.set('카메라와 모델을 종료하고 기록을 정리하고 있습니다.')
        self.worker.request_close()
        self.update_controls()


def launch_live(model=None, camera=0, output_root=Path('recordings/live'), demo=False):
    try:
        import tkinter as tk
    except ImportError as exc:
        raise ValueError('실시간 창에는 Python의 Tk 구성요소가 필요합니다.') from exc
    try:
        import cv2  # Reuse the OpenCV dependency supplied by the existing MediaPipe extra.
    except ImportError as exc:
        raise ValueError('실시간 기능에는 pip install -e .[live] 설치가 필요합니다.') from exc
    if not demo and (model is None or not Path(model).is_file()):
        raise ValueError('사용할 로컬 MediaPipe .task 모델을 지정하세요.')
    with tempfile.TemporaryDirectory(prefix='bed-pose-live-') as tmp:
        if demo:
            from .pose.fake import FakeAdapter
            source, adapter = SyntheticSource(), FakeAdapter()
            settings, profile, kind = {'execution_mode':'ordered_sequence'}, None, 'synthetic'
        else:
            from .pose.mediapipe import MediaPipeAdapter, DEFAULT_OPTIONS, mapping_profile
            model = Path(model).resolve()
            options = Path(tmp)/'adapter_options.json'
            atomic_json(options, DEFAULT_OPTIONS)
            settings = {'execution_mode':'ordered_sequence', 'requested_device':'cpu',
                        'assets':[{'role':'pose_landmarker_task','path':str(model),'sha256':file_hash(model)}],
                        'adapter_options_path':str(options), 'adapter_options_sha256':file_hash(options)}
            source, adapter, profile, kind = CameraSource(camera), MediaPipeAdapter(), mapping_profile(), 'model_inference'
        engine = LiveEngine(source, adapter, settings, output_root, profile=profile, execution_kind=kind)
        worker = LiveWorker(engine)
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            raise ValueError('실시간 창을 열 수 없습니다. 데스크톱 화면과 Python Tk 설치를 확인하세요.') from exc
        window = LiveWindow(root, worker)
        worker.start()
        try:
            root.mainloop()
        finally:
            worker.request_close()
            worker.join(timeout=5)
        return 3 if window.had_error else 0
