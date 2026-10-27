# 결과 진단·비교·프레임 오버레이

[프로젝트 홈](../README.md) · [진행 현황](PROJECT_STATUS.md) · [세부 규약](BENCHMARK_DETAIL_SPEC.md)

**2026-10-27 · 0.4.0: 정답 없는 기록 진단과 후처리 표시 구현. 실제 침대 성능 평가와 구분합니다.**

## 구현한 기능

| 명령 | 입력과 출력 | 해석 |
|---|---|---|
| `evaluate` | 기존 run → 새 `evaluations/<evaluation_id>/aggregate_metrics.json`, `report.md`, 완결/해시 manifest | 후보 출력률, 처리 성공률, 오프라인 전체 경로 FPS, 단계별 p50/p95와 표본/누락 수 |
| `compare` | 요청한 모든 run 경로 → 새 출력 폴더의 `comparison.json`, `report.md`, 완결/해시 manifest | 누락·손상·실패 실행도 행에 남김. 같은 조건 그룹·scope·대상 연결 방식인지 표시. 순위·우열 결론 없음 |
| `render` | run + 같은 원본 영상 → 새 폴더의 프레임별 SVG, `frames.json`, `index.html`, 완결/해시 manifest | 원본 RGB를 무손실 PNG로 포함하고 공통 17점·연결선과 상태/PTS를 표시. 브라우저에서 수동 프레임 선택 |

모든 명령은 모델을 재호출하지 않습니다. 원본 run의 결과 파일은 수정하지 않으며 기존 출력 폴더는 덮어쓰지 않습니다. 평가는 매번 새 ID를 사용합니다. 추론 설정에 GT나 외부 센서 입력을 추가하지 않았습니다.

## 실행 예

아래 `<run_id>`는 demo가 출력한 run_directory의 ID입니다. 자신의 영상 대신 생성 영상으로 기능을 점검할 수 있습니다.

```sh
python -m pip install -e .
python -m bed_pose demo --output data/demo_01
python -m bed_pose evaluate --run data/demo_01/runs/<run_id>
python -m bed_pose render --run data/demo_01/runs/<run_id> --video data/demo_01/synthetic_input.mkv --output data/overlay_01
python -m bed_pose compare --runs data/demo_01/runs/<run_id> --output data/comparison_01
```

`render` 출력의 `index.html`을 브라우저로 열어 프레임을 선택합니다. 이는 실시간 모니터나 동영상 파일이 아닙니다. VFR·누락 PTS를 임의의 고정 FPS로 바꾸지 않기 위해 첫 구현은 프레임 이미지와 원본 PTS/time base/duration 목록으로 제공합니다. 모델의 내부 전처리 영상 대신 실제 분석 입력의 정규 RGB 프레임 위에 그립니다.

실패 실행의 기록이 완결되어 있을 때 부분 진단은 다음과 같이 명시합니다.

```sh
python -m bed_pose evaluate --run data/demo_01/runs/<run_id> --scope diagnostic_partial
```

## 계산 규칙과 한계

- 후보 출력률은 `후보 수>0인 프레임/원래 입력 프레임 전체 수`, 처리 성공률은 `ok/원래 전체 수`입니다. 정상 0명은 처리 성공이며, 실패·미처리를 분모에서 빼지 않습니다. **사람 검출 정확도나 침대 자세 정확도가 아닙니다.**
- full은 성공·기록 완결·무결성이 확인된 실행에만 계산합니다. 실패/취소 실행을 full로 요청하면 모든 성능 지표가 `unavailable/INCOMPLETE_RUN`입니다. 실행 상태·오류·프레임 수는 계속 보고합니다.
- diagnostic_partial은 기록이 완결된 실패 실행에서도 전체 입력 분모로 출력률을 계산합니다. 시간은 실제 측정된 표본만 사용하며 프레임 ID 목록·표본 수·측정 누락 수를 남깁니다. FPS는 미계산합니다.
- 전체 FPS의 T는 기존 manifest의 `pipeline_started_ns`부터 `data_finished_ns`까지입니다. 첫 호출, 디코딩·기록·정리·최종 데이터 fsync를 포함하고 초기화·warm-up·최종 manifest 교체·후처리를 제외합니다. 실시간 카메라 지연이 아닙니다.
- 단계별 시간은 프레임 처리 상태 ok/failed로 분리합니다. 그룹의 실패가 해당 단계의 SDK 실패를 뜻하는 것은 아닙니다. 첫 측정 프레임/값도 별도로 보존합니다. p50/p95는 `(n-1)*p` 위치의 선형 보간입니다. 빈 표본은 0으로 만들지 않습니다.
- 원본 결과/참조/파일 해시 외에 입력 스냅샷·프레임 해시, 요청/해석 설정의 비경로 필드, 어댑터·매핑 profile 해시를 확인합니다. 읽는 중 변경도 검사합니다. 손상된 기록의 지표는 모두 `invalid/INPUT_INTEGRITY_ERROR`이며 CLI 종료 코드는 4입니다.
- 프레임 간 시계 순서와 전체 실행 시간 경계도 확인합니다. 이상이 있으면 시간 지표는 `invalid/CLOCK_INVALID`입니다. 유효한 프레임 수 기반 출력률은 별도로 유지합니다. `integrity`는 기록 정합성, `evaluation_status`는 지표 평가의 invalid 여부를 나타냅니다.
- 정답·인물 연결 입력은 이번 버전에서 받지 않습니다. PCK·정지 떨림은 `NO_VERIFIED_GT`, 대상 관절 출력률은 `NO_TARGET_ASSOCIATION`으로 미계산합니다. 자세/이벤트 정확도는 제공하지 않습니다. GT 주석 형식·주석 지침·대상 연결·scale/alpha 및 정답 기반 평가 구현은 후속 작업입니다.
- 비교 그룹에는 동일 입력 manifest, scope, 연결 방식, 합성/모델 종류, 실행 모드, warm-up, 실행 환경, 추론 코드 source hash, 평가 정책 hash가 반영됩니다. 다른 그룹은 같은 조건의 비교로 취급하지 않습니다. 모델별 설정·자산·장치·SDK 정보는 각 행의 JSON에 보존합니다. 같은 그룹이어도 주석·독립 반복·장비 부하 등을 확인하지 않고 품질이나 속도 우열을 확정하지 않습니다.
- 비교 요청의 누락/손상 경로는 삭제하지 않으며 진단 행과 종료 코드 4로 남깁니다. 존재하지 않는 run을 평가하면서 해당 run 폴더를 새로 만들지 않습니다.

## 표시 규칙

합성 실행에는 `SYNTHETIC - NOT AI INFERENCE`, 모델 경로에는 `MODEL PREDICTIONS - NOT VERIFIED GT`를 표시합니다. 전체 run 상태, 프레임 처리 상태, 후보 수, 원본 PTS, 실패 코드와 대상 미지정 상태를 따로 보여 줍니다.

유한하고 화면 안에 있는 예측 관절만 그립니다. 누락·화면 밖 관절을 보간하거나 테두리에 강제로 옮기지 않고, 양끝 관절이 모두 표시 가능할 때만 선을 그립니다. confidence 임계값이나 해부학적 합격 판정은 추가하지 않았습니다. 후보 색/ID는 프레임 안의 표시이며 동일 인물 추적을 의미하지 않습니다.

영상 SHA-256과 프레임별 PTS·픽셀·회전을 재검증합니다. 렌더링이 중단되면 manifest는 `complete:false`로 남으며, 완성된 출력으로 취급하면 안 됩니다. 생성물의 이미지와 식별 정보는 원본 영상과 같은 접근/보관 범위로 관리합니다. 원본 영상·실험별 결과·오버레이는 공개 GitHub 업로드 대상이 아닙니다.

현재 후처리는 결과 프레임·쓰기 시각·필요한 관절을 메모리에서 읽습니다. 대규모/장시간 영상에서의 메모리 사용, 동영상 인코딩·자동 재생, 실시간 표시, GT 기반 평가, 연속 누락·떨림 분석, 외부 센서 비교는 이번 완료 범위에 포함하지 않습니다. 파생 보고 파일의 전원 장애 내구성을 보장하지 않습니다.

## 개발 검증

생성한 비인체 6프레임 VFR 영상과 합성/오류 주입 기록으로 확인했습니다. 수작업 기대값에는 출력률 0.5, 실패 후 전체 분모 6 유지, `[10,20,30,40]ms`의 p50=25/p95=38.5, 정상 0명·실패·미처리의 표시 구분, SVG 속 PNG를 복호화했을 때 원본 RGB와 픽셀 일치를 포함합니다. 기존 SDK 경계 검사와 함께 전체 테스트를 실행합니다. 실제 모델·침대 정확도를 검증한 작업이 아닙니다.

전체 51개 검사가 통과했고, 0.4.0 wheel을 별도 디렉터리에 설치해 저장소 밖에서 demo/evaluate/render, 오류 주입의 부분 진단, 누락 실행을 포함한 compare의 종료 코드 4, 기존 inspect를 실행했습니다. 별도 CairoSVG 개발 도구로 생성 SVG를 PNG로 렌더링해 합성 표시·시각·관절 표시도 확인했습니다. CairoSVG는 제품 의존성에 추가하지 않았습니다. 이 환경의 headless Chromium은 제한 시간 안에 스크린샷을 생성하지 못했으므로 HTML 프레임 선택의 실제 브라우저 동작은 미확인입니다. SVG 구조·내장 PNG 복호화·카탈로그와 링크 생성은 검사했습니다. Windows 및 실제 모델/침대 영상 검증은 별도로 남아 있습니다.
