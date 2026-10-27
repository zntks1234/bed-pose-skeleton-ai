# 최소 실시간 측정기 · live-0.1-draft

[프로젝트 홈](../README.md) · [진행 현황](PROJECT_STATUS.md) · [측정 절차](MEASUREMENT_PROTOCOL.md)

**2026-10-27 · 구현 범위: 카메라 RGB → 기존 관절 어댑터 → 화면·수동 침대 사각 영역 → 자유 측정 기록.** 모델 최종 선정·학습·자세/점유/이탈/복귀 판정·센서 동기화는 완료하지 않았습니다.

## 실행

Windows의 프로젝트 폴더 PowerShell에서 실행합니다. Python 3.12 가상환경과 이미 받은 로컬 모델을 사용합니다.

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".[live]"
& .\.venv\Scripts\python.exe -m bed_pose live --model checkpoints/pose_landmarker_full.task --camera 0
```

카메라 번호는 장치에 따라 0, 1 등으로 다를 수 있습니다. OpenCV의 기본 backend를 사용하고 실제 backend·버전·드라이버가 보고한 FPS를 기록합니다. 카메라 연결 실패 시 합성 화면으로 자동 전환하지 않습니다. 데스크톱 화면과 Tk를 포함한 Python이 필요합니다. Windows 공식 Python의 Tk가 없는 사용자 지정 설치라면 Tk 구성요소를 추가해야 합니다.

장치 없이 조작을 확인할 때는 **명시적으로 합성 모드**를 선택합니다. 실시간 창의 입력·모델 동작을 같은 제어 흐름으로 점검하지만 실제 인체 추론이 아닙니다.

```powershell
& .\.venv\Scripts\python.exe -m bed_pose live --demo
```

새 프레임을 받으면 영상이 나타납니다. 영상 안에서 침대를 감싸는 두 모서리를 드래그합니다. 영역은 영상 좌표의 사각형이며 침대 의미를 자동 검증한 정답이나 원근 보정된 실제 경계가 아닙니다. ‘측정 시작’은 첫 영상과 영역이 준비된 뒤 활성화됩니다. 측정 종료 후 카메라 미리보기는 계속되며 다시 시작하면 다른 폴더에 저장합니다.

- **침대 영역 수정:** 측정 중에도 다시 드래그할 수 있습니다. 적용 시각·요청 시각·버전과 적용될 첫 stream_frame_id를 기록합니다.
- **영역 지우기:** 관절 분석·이미 시작한 기록은 계속하며 관련 프레임은 null 영역의 새 버전을 참조합니다. 지운 뒤 다음 측정을 시작하려면 다시 지정합니다.
- **측정 종료:** 데이터 flush/fsync·해시/기록 검사를 완료한 뒤 종료를 표시합니다. 매우 짧게 시작/종료해 기록 프레임이 0개인 경우도 있으며, 이는 인식 성능 표본이 아닙니다.
- **창 닫기:** 작업 중인 프레임을 마치고 카메라·모델·기록을 정리합니다. backend가 read/추론에서 멈추면 종료가 지연될 수 있으며 강제 종료는 미완료 기록으로 남을 수 있습니다. 자동 재연결은 없으며 새 실행으로 다시 시작합니다.
- **영상 크기 변경:** 현재 스트림을 실패로 종료합니다. 이전 침대 영역을 다른 기하에 자동으로 재사용하지 않습니다. 동일 크기에서 카메라가 움직였는지는 자동 감지하지 않으므로 사용자 재확인이 필요합니다.

현재 앱은 연속 프레임 모드와 명시적 CPU를 사용합니다. 실행 장비의 최종 선정이 아닙니다. 첫 MediaPipe 설정은 기존 기본값·최대 후보 1개를 사용하며, p0를 실제 측정 대상이라고 자동 지정하지 않습니다. 안정적인 인물 ID·대상 선택/복구는 미구현입니다. 후보 0명, 실행 오류, 미구현 자세 판정은 서로 다릅니다. 모델 점수에 임의의 품질 수용 임계값을 추가하지 않았습니다.

## 화면과 스레드

`live_gui.py`는 표준 Tk 창·입력 조작과 화면 그리기, `live_engine.py`는 단일 작업 스레드의 수신·추론·측정 상태, `live_sources.py`는 카메라/합성 입력, `live_recording.py`는 별도의 실시간 기록 계약을 담당합니다. 기존 MediaPipe/Fake 어댑터·공통 17점 매핑을 재사용합니다. Tk 객체는 UI 스레드에서만 조작합니다.

수신·추론은 순차 실행하며 완료된 결과를 화면용 크기 1 큐로 전달합니다. UI가 느리면 **화면에 표시하지 않은 처리 결과**만 교체하고, 측정 중 처리 결과는 그 전에 기록합니다. 화면 교체 수는 카메라 노출 프레임 손실 수가 아닙니다. 장치/드라이버에서 놓친 프레임 수와 내부 버퍼 지연은 현재 알 수 없으며 null로 기록합니다. 실시간 처리율·지연 목표 달성을 검증한 것은 아닙니다.

미리보기 동안도 SDK 내부 추적이 작동하고, 측정 시작 때 그 이력을 유지합니다. manifest에 tracking_scope=camera_stream과 preview_tracking_history_retained=true를 기록합니다. SDK 재생성은 스트림 시작 때 수행합니다. 이 경로를 영상 benchmark의 독립 초기화·warm-up 조건과 섞어 비교하지 않습니다.

오류 후 창에는 이전 관절 출력을 현재 결과처럼 유지하지 않습니다. 기록이 실패하면 정상 종료로 표시하지 않습니다. 자세/점유/이벤트는 **미구현**으로 표시하며 후보 미출력을 침대 이탈로 변환하지 않습니다.

## 기록 구조와 시간 의미

기본 저장 위치는 `recordings/live/<measurement_id>/`이며 `--output-root`로 변경할 수 있습니다. 영상과 이미지는 저장하지 않습니다. 선택적 원본 영상 녹화는 최종 목표로 유지하지만 이번 최소 구현에서는 미지원입니다. 녹화가 꺼진 상태의 분석·결과 기록을 먼저 연결했습니다.

```text
manifest.json
live_frames.jsonl
control_events.jsonl
```

저장 영상 benchmark와 다른 **live-0.1-draft** 계약입니다. 고정된 영상 PTS·전체 프레임 수가 없으므로 benchmark의 FrameResult나 not_processed 행을 만들어 끼워 넣지 않습니다. 두 가지 파일과 manifest의 최종 검사는 다음 명령을 사용합니다.

```powershell
& .\.venv\Scripts\python.exe -m bed_pose live-inspect --run "recordings/live/<measurement_id>"
```

`live-inspect`는 파일 해시·기록/이벤트 수·식별자·시각 순서·영역 버전·설정/profile 해시·미구현 출력 상태를 확인합니다. succeeded/failed 실행 모두 ledger_complete=true일 수 있습니다. 이것은 **남긴 측정 기록의 완결성**이며 전체 카메라 노출을 빠짐없이 받았다는 보장이 아닙니다. 관절의 실제 위치 정확도·침대 영역의 의미·자세 성능을 검사하는 명령도 아닙니다. 기존 inspect/evaluate/render는 이 live 형식을 받지 않습니다.

| 항목 | 의미 |
|---|---|
| measurement_id / frame_id | 한 측정 폴더와 그 안의 0부터 시작하는 순서 |
| stream_id / stream_frame_id | 한 앱의 카메라 스트림과 미리보기를 포함한 수신 순서 |
| read_started_ns / received_ns | 같은 perf_counter_ns 기준점 이후 경과 ns. received는 CameraSource.read가 RGB 변환까지 마치고 반환한 시각 |
| camera_exposure_ns | 확인할 수 없어 null. 수신 시각을 실제 노출 시각으로 대체하지 않음 |
| received_utc_ns | 수신 후 시스템 UTC 시계 time_ns 표본. 다른 센서와 동기화됐다고 가정하지 않음 |
| model_timestamp_ms | received_ns를 ms로 내림한 실제 SDK 입력. 중복 시각을 몰래 +1ms로 바꾸지 않고 실패 기록 |
| inference_started/finished_ns / mapping_finished_ns | 같은 단조시계 도메인의 실제 측정 경계 |
| record_started_ns | JSON 직렬화/쓰기 시작 전 시각. 해당 행 안에서 쓰기 완료 시각을 가정하지 않음 |
| control_events.time_ns / request | 제어가 적용된 시각과 버튼 요청의 단조/UTC 시각. 직접 API로 제어한 경우 request=null |
| initial_bed_selection / selection | 최초/변경 영역을 지정한 미리보기 프레임, 적용 시각·UTC·요청 메타데이터. 미리보기 프레임은 기록 시작 전이면 JSONL에 없을 수 있음 |
| bed_region_revision | manifest 초기 영역과 control_events의 변경 이력 참조. 변경은 다음 수신 프레임부터 적용 |
| raw_candidates / mapped_people | 원본 33점·점수 등과 공통 17점. 수치 검사와 실제 정확도를 구분 |
| target_posture / verified_gt / sensor_results | 이번에는 각각 null. 지시·정답·외부 측정을 카메라 예측으로 대체하지 않음 |
| posture_prediction / event_analysis_status / bed_occupancy_status | not_implemented. event_predictions=[]도 이벤트가 없었다는 판정이 아님 |

manifest에는 코드 source hash·환경·원본 자산 해시·옵션과 profile·초기화 방법을 남깁니다. SDK 초기화에 사용한 옵션 파일 경로는 임시 경로일 수 있으며 실제 옵션 값은 adapter_profile에 보존합니다. 별도 전원 장애/강제 종료 복구 모드는 없고 파일별 최종 fsync와 미완료 표시만 구현합니다. 디렉터리 fsync와 절대적인 내구성은 보장하지 않습니다.

## 검증 범위

가상 소스와 Fake 어댑터로 영역 지정 전 시작 거부, 영역 변경/삭제 버전, 반복 측정, 후보 0명의 정상 호출, 추론 오류, 소스 끊김, 기하 변경, 저장/정리 실패, 시각 충돌, 변조·미구현 라벨 주입 거부를 검사했습니다. OpenCV 카메라 API는 모의 객체로 RGB 변환·열기 실패 처리를 확인했습니다. UI는 임시 가상 디스플레이에서 합성 입력으로 드래그·버튼·토글·반복 시작/종료·오류 후 화면 비우기·기록 검사를 확인했습니다.

전체 개발 검사 77개가 통과했고 0.6.0 wheel 빌드와 저장소 밖 설치본의 CLI·합성 GUI도 확인했습니다.

**실제 USB/내장 카메라와 Windows Tk 창의 동작·권한·장치별 지연은 아직 검증하지 못했습니다.** 사용자 PC에서 첫 하드웨어 확인이 필요합니다. 이 검사는 모델 학습·실제 침대 자세 정확도·ToF/mmWave 비교를 대체하지 않습니다. 이후 계획 측정·선택적 녹화·자동 침대 인식·대상 관리·실제 자세/이벤트 판정을 단계적으로 추가합니다.
