# 참고 논문 상세 정리와 프로젝트 적용 계획

**원문 대조일:** 2026-10-24 (UTC) · **기획 버전:** v0.3 · **대상:** 침대 자세·움직임을 카메라 스켈레톤으로 분석하고 ToF·mmWave 결과와 독립 비교하는 프로젝트

지금까지 검토한 참고 논문 **25편**을 모았습니다. 이번 갱신에서는 **22편의 공개 본문에서 방법·실험·결과를 확인**했고, 원문을 확보하지 못한 **P11·P12·P19 3편은 본문 검증 보류**로 남겼습니다. 각 항목에서 논문이 수행한 연구와 우리 프로젝트에 적용하려는 제안을 구분했습니다. 문헌 조사 결과이며, 이 저장소에서 모델을 구현하거나 논문 성능을 재현한 결과는 아닙니다.

## 이번 원문 검증에서 달라진 점

이 문서의 ‘검증’은 **원문과 요약의 일치 여부, 평가 조건, 표·그림의 산술 및 논문 간 교차 확인**을 뜻합니다. 모델을 다시 학습하거나 원자료로 성능을 재현한 것은 아닙니다. ‘본문 확인’도 논문에 쓰인 모든 주장이나 연구의 타당성을 보증하는 표시가 아닙니다.

| 항목 | 확인 후 반영한 내용 | 근거 |
|---|---|---|
| 누락된 구현 | P02 OpenPose·XGBoost, P04 부록의 YOLOv8-seg, P14 HybrIK, P22 ResNet-50 기반 SleePose-FRCNN-Net 추가 | 각 논문의 방법·부록 |
| 최종 모델과 비교 모델 | P03 임상 시험은 좌표 규칙, LSTM은 비교안으로 구분 | P03 §IV-B/C |
| 정답·출력 정의 | P17 OpenPose 유래 라벨과 깊이 입력 구분; P21 주석 13관절과 모델 출력 9관절 구분 | P17 Fig.1; P21 Dataset/Network training |
| 분할과 일반화 | P02 지원자→환자 성능 저하, P22 같은 사람의 수면 구간 분할, P21 사람 단위 교차 검증 명시 | 해당 실험 절·표 |
| 수치 불일치 | **P20의 표·혼동행렬이 일치하지 않아 보고 성능의 활용 보류** | P20 pp.137–138 |
| 지표 해석 | 관절 PCK/AP, 자세 분류, 이탈·낙상 위험을 분리; P23 전체 정확도 산술 확인 | 아래 상세 설명·검증 기록 |
| 확인하지 못한 원문 | P11·P12·P19는 모델명·분할·지표 정의를 추정하지 않음 | 공개 초록·서지까지만 확인 |

**확인한 버전:** 출판사 원문 또는 저자 공개 PDF를 사용했습니다. P04·P18은 게재 승인 저자본, P16은 2023년 프리프린트, P13은 arXiv v1, P14는 arXiv v3, P15는 arXiv v1 기준입니다. 프리프린트 본문을 읽은 경우 최종 출판본까지 대조했다고 표시하지 않았습니다. 각 논문의 **확인 범위**에 절·표·부록과 접근 링크를 적었습니다.

## 읽는 기준

- **확인 범위:** 초록·서지 확인과 본문 방법·실험 확인을 구분합니다. 본문에 명시되지 않은 참가자 분리·설정은 ‘확인되지 않음’으로 표시했습니다. 이는 반드시 분리를 하지 않았다는 뜻이 아닙니다.
- **출처:** 학술지/학회, DOI, 저자 공개 원문을 우선 연결했습니다. SciSpace·Consensus는 검색·서지 확인을 보조했습니다. 프리프린트와 정식 게재 연도가 다른 경우 함께 표시했습니다.
- **입력 차이:** RGB, 근적외선/IR, 열영상(LWIR), 깊이, 압력은 서로 다른 입력입니다. MediaPipe 등에서 추정한 z 좌표는 깊이 센서 실측값과 같지 않습니다.
- **평가 차이:** 관절 위치 정확도, 자세 분류, 이탈 이벤트, 낙상 위험 예측은 별개입니다. 서로 다른 데이터와 분할에서 나온 정확도 숫자로 모델의 우열을 정하지 않습니다.
- **적용 제안:** 아래 우선순위와 활용점은 프로젝트 관점의 판단입니다. 논문의 결론이나 확정된 개발 사양으로 해석하지 않습니다.

## 빠른 탐색

| ID | 논문/연구 | 주요 입력·문제 | 우선 읽을 이유 |
|---|---|---|---|
| [P01](#p01) | SLP | RGB·LWIR·깊이·압력 / 누운 관절 | 침대 자세 데이터와 가림 평가 |
| [P02](#p02) | 3D Skeleton Posture Monitoring | RGB-D / 소수 관절 자세 분류 | 일부 관절만 보이는 조건 |
| [P03](#p03) | BedEye | 영상 스켈레톤 / 이탈·낙상 경고 | 침대 관계와 동작 흐름 |
| [P04](#p04) | RGB-Only + Image Reconstruction | RGB / 가림 관절 | 가림 대응 확장 |
| [P05](#p05) | BlazePose | RGB / 모바일 관절 추정 | MediaPipe 계열의 기초 |
| [P06](#p06) | RTMPose | RGB / 관절 추정 | 속도·정확도 비교 후보 |
| [P07](#p07) | ST-GCN | 스켈레톤 시계열 / 행동 | 그래프 기반 행동 인식 기초 |
| [P08](#p08) | 2s-AGCN | 관절·뼈 시계열 / 행동 | 적응형 그래프 확장 |
| [P09](#p09) | PoseC3D | 관절 히트맵 시계열 / 행동 | 좌표 그래프 외 대안 |
| [P10](#p10) | TCN empirical study | 일반 시계열 / 순차 모델 | LSTM 비교 기준 |
| [P11](#p11) | Bed Exit Action Detection + LSTM | 단안 자세·상대 위치 / 이탈 | 시간 모델의 직접 관련 연구 |
| [P12](#p12) | Bed-Exit Prediction + Bed Position | 침대 위치·자세 / 가장자리 | 위치 특징의 필요성 |
| [P13](#p13) | BlanketGen2-Fit3D | 합성 이불 RGB / 가림 관절 | 학습 데이터 증강 |
| [P14](#p14) | BlanketSet | RGB-IR-D 영상 / 침대 동작 | 반복 동작 수집 설계 |
| [P15](#p15) | In-Bed Pose Estimation: A Review | 문헌 검토 | 데이터·평가 전체 지도 |
| [P16](#p16) | Single-camera clinical movement review | 단일 카메라 / 임상 동작 | 시간·가림·도메인 차이 |
| [P17](#p17) | SaccpaNet | 깊이 / 이불 아래 자세 | 다른 입력 방식의 비교 참고 |
| [P18](#p18) | Skeleton-Based Fall Detection review | RGB 스켈레톤 / 낙상 | 특징·시간 모델과 오경보 |
| [P19](#p19) | Skeleton + BP Neural Network | 관절 특징 / 수면 자세 | 단순 분류 기준선 |
| [P20](#p20) | CNN + LSTM + MediaPipe | IR 카메라·관절 시계열 / 수면 자세 | 유사 처리 구조와 실험 한계 |
| [P21](#p21) | HypnoPose | 근적외선 수면 영상 / 관절 | 실제 환경에서의 검출 한계 |
| [P22](#p22) | Upper-Body and Head Pose | RGB/IR 영상 / 상체·머리 | 머리와 몸통 방향 분리 |
| [P23](#p23) | U-Net + MobileNetV3 | 카메라 영상 / 수면 자세 | 스켈레톤 없는 비교 기준 |
| [P24](#p24) | Noise-Tolerant Deep State-Space Model | 잡음·결측 스켈레톤 / 행동 | 누락·시간 처리 |
| [P25](#p25) | Physics-Based Bed Simulation | 합성 2D 관절 / 낙상 위험 | 침대 좌표 특징의 확장 |

### 프로젝트에서의 권장 읽기 순서

1. **실험 설계:** P01·P16·P21. 관절 정답·사람 단위 분할·임상 도메인 차이를 먼저 확인합니다. P15는 문헌 지도, P11·P12는 원문 확보가 필요한 후속 자료입니다.
2. **초기 구현 비교:** P05·P06 → P02 → P10. 관절 추정·단순 분류·시간 모델을 나누어 비교합니다. P20은 구조만 참고하고 불일치한 성능 수치는 선정 근거에서 제외합니다.
3. **실제 환경 한계:** P21·P22·P14. 관절이 안 보이는 조건과 정답 수집 방법을 확인합니다.
4. **후속 확장:** P13·P04·P17, 이후 P07·P08·P09·P24. 가림·복잡한 시간 모델은 기준선과 비교합니다.
5. **별도 위험 예측:** P25. 낙상 위험 점수는 현재 이탈·복귀 비교 MVP와 다른 연구 과제로 둡니다.

<a id="technology-comparison"></a>
## 논문별 사용 기술 비교

**관절 추출 기술**은 영상에서 어깨·골반·무릎 등의 위치를 얻고, **자세·행동 분석 기술**은 그 좌표나 영상 특징으로 자세와 시간 변화를 판단합니다. 예를 들어 P20의 MediaPipe는 관절 추출, CNN은 공간 특징 추출, LSTM은 시간 분석을 담당합니다. MediaPipe를 선택해도 뒤에 연결할 분류 모델은 별도로 선택할 수 있습니다.

아래 표는 각 상세 항목에 연결된 원문과 확인 범위를 기준으로 정리했습니다. 화살표는 처리 흐름, 슬래시는 비교 후보를 뜻합니다. 데이터셋·리뷰 논문에는 단일 구현 모델이 없는 경우가 있으며, **추가 확인 필요**는 현재 확인한 자료만으로 정확한 모델명을 확정하지 않았다는 뜻입니다. 패키지 버전·가중치·세부 설정까지 모두 확인했다는 의미는 아닙니다.

| 논문 | 관절 추출·전처리·주요 기술 | 자세 분류·시간 분석 또는 연구 역할 | 구분·확인할 점 |
|---|---|---|---|
| [P01 SLP](#p01) | RGB·LWIR·깊이·압력 수집; HRNet·PyraNet 등 평가 | 다중 입력 데이터셋·관절 벤치마크 | 주요 비교는 LWIR·깊이·압력; RGB 성능과 구분 |
| [P02 3D Skeleton Posture Monitoring](#p02) | D435 RGB-D → OpenPose → 코·목·양어깨 + 깊이 | 12개 특징 → XGBoost 3자세 분류 | 지원자 평가와 실제 환자 시험을 분리 |
| [P03 BedEye](#p03) | 경량 OpenPose 계열 | 좌표 규칙 또는 LSTM; 임상에는 좌표 규칙 | 비교 모델과 최종 적용 모델을 구분 |
| [P04 RGB-Only + Reconstruction](#p04) | MAE / AOT-GAN → OpenPose / ViTPose / HRNet | 부록: YOLOv8-seg로 이불 마스크 생성 | YOLO Pose 사용 사례가 아님 |
| [P05 BlazePose](#p05) | 얼굴 기반 검출 → BlazePose 추적 | 33개 2D 랜드마크 | 2020 논문과 현재 MediaPipe 3D를 구분 |
| [P06 RTMPose](#p06) | RTMDet-nano → CSPNeXt·SimCC·GAU | RTMPose 관절 좌표 분류 | 검출 포함 경로의 속도 별도 |
| [P07 ST-GCN](#p07) | OpenPose 18관절 / Kinect 25관절 | ST-GCN 행동 분류 | 영상 추정 2D와 센서 3D 입력 구분 |
| [P08 2s-AGCN](#p08) | OpenPose / Kinect → 관절·뼈 두 흐름 | 2s-AGCN 행동 분류 | 전처리·학습 설정도 성능에 영향 |
| [P09 PoseC3D](#p09) | Faster R-CNN → HRNet → 관절 히트맵 | SlowOnly 3D CNN 행동 분류 | FineGYM 정답 인물 박스 조건 주의 |
| [P10 TCN 연구](#p10) | 인과적·팽창 1D 합성곱·잔차 연결 | TCN 일반 시계열 모델링 | 침대 전용 평가 아님 |
| [P11 Bed Exit Action Detection](#p11) | 단안 자세·상대 위치; 추정기 미확인 | LSTM 이탈 검출 | 본문 검증 보류 |
| [P12 Bed-Exit Prediction](#p12) | 침대 위치·환자 자세; 추정기 미확인 | 신경망 이탈 관련 상태 예측 | 본문 검증 보류 |
| [P13 BlanketGen2-Fit3D](#p13) | 물리 기반 이불 합성 → ViTPose-B 미세 조정 | 가림 관절 추정 | 평가에 정답 박스 사용; 공개 v1 기준 |
| [P14 BlanketSet](#p14) | Azure Kinect RGB·IR·깊이; HybrIK 비교 | 데이터셋·인체 mesh 정성 평가 | 29명 응답자 평점은 관절 정확도가 아님 |
| [P15 In-Bed Pose Estimation Review](#p15) | 입력·데이터·관절 모델 문헌 검토 | 리뷰 | SLP 설명은 데이터 원 논문 우선 |
| [P16 Clinical In-Bed Movement Review](#p16) | 3D MoCap·행동 분류·단계별 전이 학습 검토 | 임상 동작 리뷰 | 2023 저자 프리프린트 기준 |
| [P17 SaccpaNet](#p17) | OpenPose 라벨 전이 → 깊이 입력 JCE | SaccpaNet JCE + SPC | 라벨이 독립 수작업 정답은 아님 |
| [P18 Skeleton-Based Fall Detection Review](#p18) | OpenPose·MediaPipe 등과 전처리·시간 모델 검토 | 낙상 탐지 리뷰 | 특정 단일 구현이 아님 |
| [P19 Skeleton + BP Neural Network](#p19) | 관절 특징; 추정기 미확인 | BP 신경망 자세 분류 | 본문 검증 보류 |
| [P20 CNN + LSTM + MediaPipe](#p20) | IR 영상 → MediaPipe → 1D CNN | LSTM 4자세 분류 | 표·혼동행렬 수치 불일치 |
| [P21 HypnoPose](#p21) | HigherHRNet + CBAM | 9개 상체 관절 추정 | AlphaPose·ViTPose는 비교 모델 |
| [P22 Upper-Body and Head Pose](#p22) | RGB/IR → ResNet-50·RPN·RoI | SleePose-FRCNN-Net 머리·상체 검출/분류 | 전신 스켈레톤이 필수 출력은 아님 |
| [P23 U-Net + MobileNetV3](#p23) | U-Net 사람 분할 → MobileNetV3 | 3자세 영상 분류 | 281/300=93.67% 산술 확인 |
| [P24 Deep State-Space Model](#p24) | Kinect 스켈레톤 → DSSM | BiLSTM 행동 분류 | 무작위 프레임 결측과 실제 가림 구분 |
| [P25 Physics-Based Bed Simulation](#p25) | MuJoCo → 13개 2D 관절 | MLP 위험 회귀; RF·CNN·GCN·LSTM 비교 | 실제 영상 관절 추정 실험 아님 |

**MediaPipe 관련 논문:** P20은 MediaPipe를 직접 사용하지만 보고 성능에 불일치가 있습니다. P05는 2D BlazePose의 기반 연구입니다. YOLO Pose는 현재 프로젝트의 비교 후보이며, 실제 사용한 것으로 확인하지 않은 논문에 임의로 배정하지 않습니다.

## 논문별 상세 설명


<a id="p01"></a>
### P01. Simultaneously-Collected Multimodal Lying Pose Dataset: Towards In-Bed Human Pose Monitoring under Adverse Vision Conditions

**저자·출처:** Shuangjun Liu 외. arXiv, 2020. 정식 게재 제목은 *Simultaneously-Collected Multimodal Lying Pose Dataset: Enabling In-Bed Human Pose Monitoring*, IEEE TPAMI 45(1), 1106–1118, 2023(온라인 2022).  
**링크:** [프리프린트](https://arxiv.org/abs/2008.08735) · [DOI: 10.1109/TPAMI.2022.3155712](https://doi.org/10.1109/TPAMI.2022.3155712) · [저자 데이터·코드 안내](https://github.com/ostadabbas/SLP-Dataset-and-Code)  
**확인 범위:** 본문 확인 — 공개 PDF §4.1·§4.4, 데이터 구성과 단일 입력 벤치마크 표. 정식 게재본과 초기 프리프린트의 제목을 구분합니다.

- **문제·처리 흐름:** 누운 자세를 RGB·LWIR·깊이·압력으로 동시 수집한 데이터셋입니다. 데이터 공개만 하는 연구가 아니라 HRNet-W32, SimpleBaseline(ResNet-50), ChainedPredictions, PoseAttention, PyraNet, StackedHourglass의 관절 추정 실험도 수행합니다.
- **데이터·정답:** 가정 환경 102명과 모의 병원 환경 7명, 총 109명입니다. 모집 대상은 대학생으로, 109명의 입원 환자 자료가 아닙니다. 각 사람에게 3종 기본 자세 × 15개 변형 × 3종 가림 조건을 수집해 입력 종류별 14,715개 표본과 14개 관절 정보를 제공합니다.
- **학습·시험:** 가정 환경 첫 90명을 학습, 나머지 12명을 시험에 사용하고 모의 병원 7명에서 환경 변화도 평가합니다. 모델은 100 epochs 학습합니다. 주요 단일 입력 벤치마크는 어두움·가림 때문에 **RGB를 제외하고 LWIR·깊이·압력**을 비교합니다.
- **결과·검증:** PyraNet의 PCKh@0.5는 LWIR 94.2%, 압력 90.7%, 깊이 96.6%로 보고됩니다. 이는 머리 크기로 정규화한 **관절 위치 지표**이며 RGB 자세 분류 정확도가 아닙니다. 기존 설명에 빠졌던 벤치마크 모델·입력과 참가자 성격을 보완했습니다.
- **한계·활용 제안:** 정적 자세 및 가림 평가에 활용합니다. 이탈·복귀 연속 이벤트의 정답 자료나 고령 환자 일반화 검증으로 해석하지 않습니다.


<a id="p02"></a>
### P02. Posture Monitoring for Health Care of Bedridden Elderly Patients Using 3D Human Skeleton Analysis via Machine Learning Approach

**저자·출처:** Jui-Chiu Chiang 외. *Applied Sciences*, 12(6), 3087, 2022.  
**링크:** [출판사 원문 / DOI: 10.3390/app12063087](https://www.mdpi.com/2076-3417/12/6/3087)  
**확인 범위:** 본문 확인 — §3.1–3.3, §4.1–4.3, Tables 3–5 및 7–9.

- **기술·처리 흐름:** Intel RealSense D435의 RGB에서 **OpenPose**로 18개 관절을 검출한 뒤 코·목·양쪽 어깨 4개를 선택합니다. 대응 깊이를 33×33 영역의 trilateral filter로 보정하고, 2D 좌표+깊이 또는 카메라 3D 좌표로 만든 12개 특징을 **XGBoost**에 입력합니다. 코를 원점으로 이동한 특징도 비교합니다. 출력은 바로 누움·좌측·우측 3종입니다.
- **장비·자료:** 높이 174 cm, 수직 방향에서 약 10° 기울인 RGB-D 카메라를 사용합니다. 지원자 20명(남 15·여 5)의 표본 3,154개와 실제 와상 고령 환자 2명(남 1,525개·여 1,056개)의 자료를 구분합니다.
- **분할:** Setting 1은 지원자 19명 학습·1명 시험을 반복하는 사람 단위 평가입니다. Setting 2는 지원자로 학습하고 두 환자로 시험합니다. Settings 3–5는 같은 환자 자료 일부가 학습에도 들어가므로 새로운 환자에 대한 성능과 구별해야 합니다.
- **결과·검증:** 같은 2D+depth 표현에서 지원자 평가의 보고값 96.32%가 환자 남 46.55%·여 78.31%로 낮아집니다(Tables 4–5). 따라서 초록의 ‘95% 이상’을 임상 일반화 성능으로 쓰면 안 됩니다. §4.3.1은 accuracy를 TP/(TP+FP)로 정의하는데 이는 통상 precision 식입니다. 수치는 저자의 보고값으로 인용하며 지표 명칭의 혼동을 함께 기록합니다.
- **한계·활용 제안:** 일부 상체 관절만 사용하는 기준선 설계에 유용합니다. 깊이 센서가 필요하고 실제 환자는 2명뿐입니다. MediaPipe의 추정 z로 동일 결과를 얻는다고 가정하지 않습니다.


<a id="p03"></a>
### P03. BedEye: A Bed Exit and Bedside Fall Warning System Based on Skeleton Recognition Technology for Elderly Patients

**저자·출처:** Liang-Bi Chen 외. *IEEE Access*, 13, 60403–60423, 2025.  
**링크:** [IEEE 원문](https://ieeexplore.ieee.org/document/10949079/) · [DOI: 10.1109/ACCESS.2025.3558004](https://doi.org/10.1109/ACCESS.2025.3558004)  
**확인 범위:** 본문 확인 — [저자 공개 원문](https://www.researchgate.net/publication/390513208_BedEye_A_Bed_Exit_and_Bedside_Fall_Warning_System_Based_on_Skeleton_Recognition_Technology_for_Elderly_Patients), §III의 자세 판단·LSTM 구성, §IV-B/C, Tables 6–14.

- **기술·흐름:** Jetson Xavier NX에서 경량 OpenPose 계열로 관절을 추출합니다. **관절 좌표의 기하 규칙**과 **LSTM 시계열 분류**는 비교하는 두 대안입니다. 임상 시험에는 좌표 기반 규칙을 선택했으며, LSTM이 최종 임상 모델이라는 설명은 부정확합니다.
- **시간 모델:** 어깨·골반·무릎의 중심 좌표 3쌍을 특징으로, 약 15.4 FPS의 5초·77프레임 창을 LSTM에 입력합니다. 누움·몸 일으킴·가장자리 앉음·이탈을 구분합니다.
- **실험:** 주간·야간 시험 자료와 병원 시험을 분리합니다. 병원 시험에는 간호사 26명, 고령 지원자 11명, 입원 환자 11명이 참여합니다. 지정된 연속 동작 150회와 분해 동작 594회를 수행했습니다.
- **결과·검증:** §IV-C의 병원 평가 보고값은 97.72%입니다. 주간·야간 자세 인식 값 및 초록의 97.4%와 동일한 시험으로 합치지 않습니다. 장기간 자연 발생 낙상 감소를 입증한 임상시험으로 해석할 수도 없습니다.
- **활용 제안:** 침대 상대 위치와 상태 전이 규칙의 직접 참고 자료입니다. 우리 데이터에서 경고 지연·환자별 성능·시간당 오경보를 별도로 측정해야 합니다.


<a id="p04"></a>
### P04. RGB-Only in-Bed Pose Estimation Under Occlusion via Image Reconstruction

**저자·출처:** Sewon Kim, Hyebin Kim, Seohyun Lee, Taeyong Lee. *IEEE Access*, 14, 128244–128261, 2026.  
**링크:** [DOI: 10.1109/ACCESS.2026.3723433](https://doi.org/10.1109/ACCESS.2026.3723433) · [저자 소속기관의 초록·서지](https://pure.ewha.ac.kr/en/publications/rgb-only-in-bed-pose-estimation-under-occlusion-via-image-reconst/)  
**확인 범위:** 본문 확인 — [저자 게재 승인본](https://www.researchgate.net/publication/412247821_RGB-only_In-bed_Pose_Estimation_under_Occlusion_via_Image_Reconstruction), §II–III·결과·§XI Appendix. 최종 편집본과 차이가 있을 수 있습니다.

- **기술·흐름:** 가림 영역을 **MAE(ViT-Large)** 또는 **AOT-GAN**으로 복원한 뒤 OpenPose·ViTPose·HRNet을 각각 적용합니다. 부록의 실제 이불 실험은 **YOLOv8-seg**로 마스크를 생성하며, 학습 라벨은 SAM/SAM2 보조 후 사람이 확인합니다. YOLO Pose를 사용했다는 뜻은 아닙니다.
- **학습:** SLP의 비가림 RGB에 인공 마스크를 씌워 복원을 학습합니다. 사람 단위로 87명·3,915장 학습 / 22명·990장 검증을 나눕니다. MAE 입력은 224×224, 200 epochs, batch 32, AdamW입니다.
- **외부 자료:** EWHA_BED는 55명의 비가림 595장·부분 가림 595장으로 구성됩니다. 개인정보 때문에 비공개입니다. 합성 마스크 실험과 부록의 실제 이불 검출 실험을 구분해야 합니다.
- **결과·검증:** MAE와 ViTPose 조합의 개선을 보고하지만 AOT-GAN 조합은 외부 자료에서 악화되기도 합니다. 복원 영상의 자연스러움만으로 관절 정확도를 판단할 수 없습니다.
- **활용 제안:** 자동 이불 마스크 생성까지 포함한 후속 가림 실험 후보입니다. 복원한 신체를 실제 관측 정답으로 저장하거나, 정적 이미지 결과를 연속 이탈 탐지 성능으로 바꾸어 해석하지 않습니다.


<a id="p05"></a>
### P05. BlazePose: On-device Real-time Body Pose tracking

**저자·출처:** Valentin Bazarevsky 외. arXiv:2006.10204, 2020, 프리프린트.  
**링크:** [논문](https://arxiv.org/abs/2006.10204)  
**확인 범위:** 본문 확인 — arXiv:2006.10204의 §2.2–2.5, §3, Table 1, 결론.

- **기술·흐름:** 얼굴 검출을 인체 위치의 단서로 삼는 검출기와, 인물 영역에서 33개 랜드마크를 추적하는 네트워크로 구성합니다. 추적이 실패하면 검출기를 다시 실행합니다. 학습 때 히트맵·오프셋과 좌표 회귀를 함께 쓰지만 추론 때 히트맵 분기를 제거해 비용을 줄입니다.
- **자료·평가:** 일반 자세 약 60,000장과 운동 자세 약 25,000장으로 학습합니다. AR 1,000장·요가 1,000장 평가에서는 출력 33개 전체가 아니라 COCO와 공통인 17개 관절을 사용합니다. 몸통 크기로 정규화한 PCK@0.2를 계산합니다.
- **결과:** Full 모델은 AR 84.1%, Yoga 84.5%를 보고합니다. 속도 표의 Full 102 FPS·Lite 312 FPS는 Pixel 2 단일 코어 조건입니다. OpenPose 행은 다른 장치이므로 단순한 동일 장치 속도 비교로 읽으면 안 됩니다.
- **검증·보완:** **2020년 이 논문은 2D 자세 추정 연구**이며 결론에서 3D 확장을 향후 방향으로 제시합니다. 현재 MediaPipe의 3D 출력이나 GHUM 모델을 이 논문의 실험 결과로 소급하지 않습니다.
- **한계·활용 제안:** 머리가 보인다는 검출 가정은 이불·옆누움에서 실패할 수 있습니다. 현재 배포 모델의 이름·버전을 고정하고 침대 영상에서 검출 실패율을 따로 측정합니다.


<a id="p06"></a>
### P06. RTMPose: Real-Time Multi-Person Pose Estimation based on MMPose

**저자·출처:** Tao Jiang 외. arXiv:2303.07399, 2023, 프리프린트.  
**링크:** [논문](https://arxiv.org/abs/2303.07399)  
**확인 범위:** 본문 확인 — §3, §4.4, Tables 11–12.

- **기술·흐름:** CSPNeXt 특징 추출기, SimCC 방식의 x/y 1차원 좌표 분류, GAU attention을 사용합니다. top-down 방식이므로 사람 영역을 먼저 얻어야 합니다. 논문의 전체 경로는 RTMDet-nano 검출기와 RTMPose를 연결합니다.
- **시험 조건:** 관절 모델 입력 256×192와 검출기 입력 320×320을 구분합니다. CPU는 i7-11700 단일 스레드 ONNX Runtime, GPU는 GTX 1660 Ti의 TensorRT FP16 조건입니다. batch 1 추론 시간을 보고합니다.
- **결과·검증:** RTMPose-m 관절 모델만의 지연은 CPU 11.060 ms·GPU 2.288 ms입니다(Table 11). 검출까지 포함한 경로는 CPU 26.613 ms·GPU 4.312 ms·Snapdragon 865 32.122 ms입니다(Table 12). 관절 모델만의 속도를 전체 카메라 시스템의 FPS로 쓰지 않습니다. 두 표의 AP도 평가 경로가 달라 동일 조건 수치처럼 합치지 않습니다.
- **한계·활용 제안:** COCO 등 일반 자세 벤치마크이며 침대 이불 조건 검증이 아닙니다. MediaPipe와 비교할 때는 인물 검출·전처리·좌표 변환까지 포함한 지연과 동일 관절 정의를 사용합니다.


<a id="p07"></a>
### P07. Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition

**저자·출처:** Sijie Yan, Yuanjun Xiong, Dahua Lin. AAAI, 2018.  
**링크:** [저자 공개 원문](https://arxiv.org/abs/1801.07455)  
**확인 범위:** 본문 확인 — 모델 구조, 실험 설정, Tables 2–3.

- **기술·흐름:** 관절을 노드, 뼈 연결을 공간 간선, 같은 관절의 인접 프레임 연결을 시간 간선으로 구성합니다. 9개 ST-GCN 층(출력 채널 64·128·256 각 3층), 시간 커널 9, 학습 가능한 간선 가중치, 전역 pooling과 softmax로 행동을 분류합니다.
- **입력·자료:** Kinetics는 **OpenPose의 18개 2D 관절(x, y, confidence)**을 사용합니다. NTU RGB+D는 **Kinect의 25개 3D 관절**을 사용합니다. 같은 ST-GCN이라도 입력의 측정 방식과 차원이 다릅니다.
- **평가·결과:** NTU 60개 행동에서 사람을 나누는 cross-subject 81.5%, 시점을 나누는 cross-view 88.3%를 보고합니다. Kinetics 400개 행동의 top-1은 30.7%입니다. 이들은 관절 검출 정확도가 아니라 주어진 행동 클래스의 분류 정확도입니다.
- **검증·한계:** 앞단의 관절 획득 기술을 기존 표에 추가했습니다. 일반 행동 자료 성능이며, 누운 자세·이탈 예측·장시간 오경보 평가가 아닙니다.
- **활용 제안:** 좌표 시계열의 구조적 관계를 쓰는 후속 기준선입니다. 먼저 적은 데이터에서 규칙·MLP·TCN과 비교하고 실제 가림에 의한 연속 결측을 별도로 시험합니다.


<a id="p08"></a>
### P08. Two-Stream Adaptive Graph Convolutional Networks for Skeleton-Based Action Recognition

**저자·출처:** Lei Shi, Yifan Zhang, Jian Cheng, Hanqing Lu. CVPR, 2019.  
**링크:** [저자 공개 원문](https://arxiv.org/abs/1805.07694)  
**확인 범위:** 본문 확인 — §5.1–5.3, Tables 1–4.

- **기술·흐름:** 관절 좌표와 뼈의 방향·길이 벡터를 서로 다른 흐름으로 처리한 뒤 결과를 결합합니다. 고정 인체 연결뿐 아니라 학습 가능한 공통 그래프와 입력 표본별 관계를 사용합니다.
- **자료·학습:** NTU의 Kinect 25관절과 Kinetics의 OpenPose 18관절을 사용합니다. NTU는 최대 300프레임 길이, Kinetics는 150프레임을 사용합니다. NTU 설정은 batch 64, Nesterov SGD, 50 epochs이며 학습률을 30·40 epoch에 낮춥니다.
- **결과:** NTU cross-subject 88.5%, cross-view 95.1%, Kinetics top-1 36.1%를 보고합니다.
- **검증·해석:** 제거 실험에서 ST-GCN 기준선도 전처리·학습 설정을 바꾸면 NTU cross-view 88.3%에서 92.7%로 개선됩니다. 논문 간 전체 차이를 모두 적응형 그래프의 효과라고 설명하지 않습니다. 모델 구조뿐 아니라 학습 조건도 비교해야 합니다.
- **한계·활용 제안:** 가려진 관절 좌표를 실제로 복원했다는 증거는 아닙니다. 작은 침대 데이터에서는 두 흐름의 추가 복잡도와 과적합을 확인하고, 같은 전처리·분할로 한 흐름 및 고정 그래프와 비교합니다.


<a id="p09"></a>
### P09. Revisiting Skeleton-based Action Recognition

**저자·출처:** Haodong Duan 외. CVPR, 2022(프리프린트 2021). 모델명 PoseC3D.  
**링크:** [논문](https://arxiv.org/abs/2104.13586)  
**확인 범위:** 본문 확인 — §3·§4, Appendix D/Table 13. 코드에서 널리 쓰는 PoseC3D 명칭과 본문의 PoseConv3D 표현을 함께 확인했습니다.

- **기술·흐름:** 기본 영상 경로는 **Faster R-CNN(ResNet-50) 인물 검출 → HRNet 관절 추정 → Gaussian 관절 히트맵 시계열 → SlowOnly 3D CNN**입니다. 여기서 3D는 시간·영상 높이·너비이며 실측 3차원 관절을 의미하지 않습니다.
- **실험:** FineGYM, NTU, Kinetics 등을 사용하고, 관절 품질·해상도·샘플링·검출 박스의 영향을 비교합니다. FineGYM 주요 실험은 운동선수의 **정답 박스**를 사용합니다. 부록에서는 검출·추적 박스 조건도 따로 비교합니다.
- **결과·검증:** 검출기와 관절 추정기가 포함된 실제 운용 경로와 정답 박스를 준 조건을 분리해야 합니다. 1-clip과 여러 clip 평균, 앙상블 결과도 서로 다른 평가 설정입니다. 임의의 사지 관절 누락에 대한 강건성 시험을 지속적인 이불 가림의 해결 증거로 읽지 않습니다.
- **한계·활용 제안:** 좌표 GCN의 대안이지만 인물·관절 추정과 히트맵 생성의 총비용이 있습니다. 동일한 입력 관절로 GCN·TCN과 비교해야 표현 방식의 효과를 분리할 수 있습니다.


<a id="p10"></a>
### P10. An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling

**저자·출처:** Shaojie Bai, J. Zico Kolter, Vladlen Koltun. arXiv:1803.01271, 2018, 프리프린트.  
**링크:** [논문](https://arxiv.org/abs/1803.01271)  
**확인 범위:** 본문 확인 — §3–5, Table 1, Appendix A.

- **기술·흐름:** 미래 값을 보지 않는 인과적 1D 합성곱, 팽창 합성곱, 잔차 연결, weight normalization과 dropout으로 TCN을 구성합니다. 팽창률·커널·층수로 과거를 보는 범위가 결정됩니다.
- **실험 설계:** adding/copy-memory, 순차 MNIST, 음악 모델링, 언어 모델링 등 여러 과제에서 LSTM·GRU·RNN과 비교합니다. 가능한 한 파라미터 규모를 맞추지만 과제별 하이퍼파라미터와 기억 길이는 다릅니다.
- **결과·검증:** 순차 MNIST 99.0%, permuted MNIST 97.2% 등은 해당 과제의 성능입니다. 침대 자세나 이탈 탐지 성능이 아니며, 모든 특화 모델보다 항상 우수하다는 결론도 아닙니다.
- **한계·활용 제안:** LSTM만 선택하지 않고 TCN을 비교할 근거로 사용합니다. 우리 시험에서는 동일 관절·같은 시간 창·같은 참가자 분할로 평가하고, 모델의 과거 수용 범위와 실제 경고 지연을 함께 기록합니다.


<a id="p11"></a>
### P11. Bed Exit Action Detection Based on Patient Posture with Long Short-Term Memory

**저자·출처:** Madoka Inoue, Ryo Taguchi. IEEE EMBC, 2020, 4390–4393.  
**링크:** [DOI: 10.1109/EMBC44109.2020.9175619](https://doi.org/10.1109/EMBC44109.2020.9175619) · [PubMed 초록](https://pubmed.ncbi.nlm.nih.gov/33018968/)  
**확인 범위:** **본문 검증 보류** — DOI·PubMed 초록 및 저자 소속기관 서지까지 확인했습니다. IEEE PDF에 접근하지 못했고 공개 저자 원문도 확보하지 못했습니다.

- **확인된 기술:** 단안 영상의 자세·상대 위치 정보를 LSTM에 연결해 침대 이탈 동작을 검출한다는 연구입니다. 초록에는 검출 99.2%와 false detection 5.7%가 보고됩니다.
- **검증하지 못한 내용:** 앞단 관절 추정기의 정확한 모델, 참가자 수, 학습·시험 사람 분리, 시간 창, 경고 시점, false detection의 분모와 집계 단위입니다. 이를 OpenPose·MediaPipe 또는 시간당 오경보로 임의 해석하지 않습니다.
- **판정:** 위 두 수치는 **초록의 저자 보고값이며 본문 검증된 성능이 아닙니다**. 수치 비교·모델 선정의 근거로 사용을 보류합니다.
- **활용 제안:** 자세와 침대 상대 위치의 시간 변화를 함께 쓰는 아이디어만 참고합니다. 원문 확보 후 Methods의 특징 추출, Experimental setup의 분할, Results의 혼동행렬·이벤트 정의를 확인해야 합니다.


<a id="p12"></a>
### P12. Bed-Exit Prediction Applying Neural Network Combining Bed Position Detection and Patient Posture Estimation

**저자·출처:** Madoka Inoue, Ryo Taguchi, Taizo Umezaki. IEEE EMBC, 2019.  
**링크:** [DOI: 10.1109/EMBC.2019.8857233](https://doi.org/10.1109/EMBC.2019.8857233) · [PubMed 초록](https://pubmed.ncbi.nlm.nih.gov/31946570/)  
**확인 범위:** **본문 검증 보류** — DOI·PubMed 초록 확인. 출판사 전체 원문이나 공개 저자 사본은 확보하지 못했습니다.

- **확인된 기술:** 침대 위치 검출과 환자 자세 추정을 결합한 신경망으로 침대 이탈 관련 상태를 예측합니다. 신체 자세만 보는 방식에 침대와의 상대 위치를 추가한다는 점이 핵심입니다.
- **검증하지 못한 내용:** 침대 검출기·관절 추정기 이름, 신경망 층 구조, 참가자 구성, 실제 환자/모의 동작 비율, 독립 시험 여부, 가장자리 상태와 최종 이탈의 정답 기준입니다.
- **판정:** ‘침대 위치+자세+신경망’ 수준까지만 기술을 확정합니다. 다른 논문이 인용한 구현이나 모델명을 이 논문의 직접 사용 기술로 옮기지 않습니다. 임상 유효성 또는 이탈 전 경고 시간을 확정할 근거도 부족합니다.
- **활용 제안:** 몸 중심 정규화와 침대 중심 정규화를 분리해야 한다는 설계 참고 자료로 둡니다. 원문 확보 후 좌표계·라벨·시간 분할부터 검증합니다.


<a id="p13"></a>
### P13. BlanketGen2-Fit3D: Synthetic Blanket Augmentation Towards Improving Real-World In-Bed Blanket Occluded Human Pose Estimation

**저자·출처:** Tamás Karácsony, João Carmona, João Paulo Silva Cunha. arXiv:2501.12318, 2025. 2026년 *Computer Vision and Image Understanding* 출판 기록도 있으나, 아래 방법 설명은 공개 프리프린트 기준입니다.  
**링크:** [프리프린트](https://arxiv.org/abs/2501.12318) · [본문 v1](https://arxiv.org/html/2501.12318v1) · [출판 기록](https://www.sciencedirect.com/science/article/pii/S1077314226003425)  
**확인 범위:** 본문 확인 — arXiv:2501.12318v1, 데이터 생성·§III-D·Table II. 2026년 최종 출판본의 모든 변경 사항을 검증한 것은 아닙니다.

- **기술·흐름:** Fit3D의 인체 표현과 물리 기반 이불 합성으로 BlanketGen2-Fit3D를 만듭니다. 합성 프레임 1,217,312개를 이용해 **ViTPose-B(약 86M 파라미터, 256×192 입력, MMPose)**를 미세 조정합니다. 합성기는 영상 추론 단계의 필수 모듈이 아니라 학습 데이터 생성 도구입니다.
- **분할·학습:** Fit3D의 S3·4·5·7·8·9를 학습, S10을 시험, S11을 검증에 사용합니다. backbone을 고정하고 head를 학습한 뒤 전체를 미세 조정하는 조건을 비교합니다. 평가에는 관절 정답에서 만든 인물 박스와 30픽셀 여유 영역을 사용합니다.
- **외부 평가:** SLP의 가림 9,810장·비가림 4,905장을 별도 평가에 사용합니다. 합성 자료의 개선과 실제 이불 자료로 옮겨 갔을 때의 개선을 구분합니다.
- **결과·검증:** Table II의 FT-Mixed는 합성 시험에서 PCK 0.977을 보고하고, 실제 자료의 개선은 약 **0.023 PCK, 즉 2.3%p** 수준입니다. 2.3% 상대 개선이나 모든 관절의 동일 개선으로 바꾸지 않습니다. 골반 관절 정의의 데이터 간 차이도 결과에 영향을 줍니다.
- **한계·활용 제안:** 실제 검출기가 만든 박스와 우리 카메라에서도 효과가 유지되는지 확인해야 합니다. 합성 이불 사전학습 후보로 두고 실제 자료만 학습한 기준선과 동일 조건으로 비교합니다.


<a id="p14"></a>
### P14. BlanketSet – A Clinical Real-World In-Bed Action Recognition and Qualitative Semi-Synchronised Motion Capture Dataset

**저자·출처:** João Carmona, Tamás Karácsony, João Paulo Silva Cunha. IEEE ENBENG, 2023, 116–119(프리프린트 2022).  
**링크:** [DOI: 10.1109/ENBENG58165.2023.10175335](https://doi.org/10.1109/ENBENG58165.2023.10175335) · [논문](https://arxiv.org/abs/2210.03600) · [공식 데이터 안내](https://rdm.inesctec.pt/dataset/nis-2022-004)  
**확인 범위:** 본문 확인 — arXiv:2210.03600v3, 수집 절차 및 §III-E의 정성 평가.

- **자료·장비:** Azure Kinect로 RGB·IR·깊이를 수집합니다. 14명, 405개 영상, 303,965프레임과 8개 동작 시퀀스를 다룹니다. 이불 유무 등에 따라 동작을 반복하는 semi-synchronised 방식으로, 서로 다른 촬영의 모든 순간이 정확히 일치하는 것은 아닙니다.
- **사용 기술:** 데이터셋만 소개하는 데 그치지 않고, **HybrIK**의 사전학습 모델과 BlanketGen으로 미세 조정한 모델의 인체 mesh 결과도 비교합니다. 기존 기술 표에 이 평가 모델을 추가했습니다.
- **평가·검증:** 정량적인 관절 좌표 정답 대신 29명의 응답자가 결과를 0–10점으로 평가하는 정성 비교를 사용합니다. 시각적 평가 점수나 통계적 차이를 관절 정확도(PCK/MPJPE)로 바꾸어 해석할 수 없습니다.
- **한계·활용 제안:** 이불 조건을 바꾼 반복 촬영과 동작 수집 설계에 유용합니다. 대응 영상이 있다는 사실만으로 가려진 프레임의 완전한 좌표 정답이나 이탈 이벤트 라벨이 제공된다고 가정하지 않습니다. 실제 자료 이용은 공식 데이터 안내의 접근 조건을 따라야 합니다.


<a id="p15"></a>
### P15. In-Bed Pose Estimation: A Review

**저자·출처:** Ziya Ata Yazıcı, Sara Colantonio, Hazım Kemal Ekenel. HCCS'24 / PerCom 워크숍, 2024(arXiv 수록본).  
**링크:** [논문](https://arxiv.org/abs/2402.00700) · [본문](https://arxiv.org/html/2402.00700v1)  
**확인 범위:** 본문 확인 — arXiv:2402.00700v1, §II–IV 및 Tables I–II. 데이터 관련 내용은 P01·P14 원문과 교차 확인했습니다.

- **연구 범위:** RGB·열영상·깊이·압력 등 침대 자세 입력, 공개 데이터, 단일/복합 입력 모델을 정리한 리뷰입니다. 하나의 새 관절 추정기를 제안하거나 여러 모델을 같은 조건으로 재학습한 벤치마크가 아닙니다.
- **기술 내용:** CNN, 전통 특징, autoencoder, 도메인 적응, 합성 데이터, 영상 복원 및 attention 기반 입력 융합 등을 다룹니다. PCK와 MPJPE 같은 관절 지표와 데이터별 차이를 파악하는 데 적합합니다.
- **교차 검증:** Table I의 SLP에 대한 ‘3D pose/video’ 표기는 SLP 원문의 정적 자료·2D 관절 주석 설명과 맞지 않습니다. 이 문서의 SLP 설명은 데이터 원 논문을 우선했습니다. RGB·IR·LWIR도 리뷰 표기만으로 합치지 않습니다.
- **한계·활용 제안:** 연구 지도를 얻는 출발점으로 사용하되 참가자 수, 입력 종류, 정답 차원, 점수는 각 원 논문에서 다시 확인합니다. 서로 다른 연구의 수치를 하나의 성능 순위로 만들지 않습니다.


<a id="p16"></a>
### P16. Deep learning methods for single camera based clinical in-bed movement action recognition

**저자·출처:** Tamás Karácsony, László Attila Jeni, Fernando De la Torre, João Paulo Silva Cunha. *Image and Vision Computing*, 143, 104928, 2024.  
**링크:** [DOI: 10.1016/j.imavis.2024.104928](https://doi.org/10.1016/j.imavis.2024.104928) · [출판사](https://www.sciencedirect.com/science/article/pii/S0262885624000313) · [저자 공개 PDF](https://humansensing.cs.cmu.edu/sites/default/files/Kara%CC%81csony%20et.%20al.%20_revision.pdf)  
**확인 범위:** 본문 확인 — [2023년 저자 프리프린트](https://www.researchgate.net/publication/372799787_Deep_Learning_Methods_for_Single_Camera_Based_Clinical_In-bed_Movement_Action_Recognition)의 임상 과제·전이 학습 논의 및 Table III. 2024년 최종판 전체를 대조한 것은 아닙니다.

- **연구 범위:** 간질 모니터링 등 침대 위 임상 동작을 중심으로 단일 카메라 3D motion capture와 행동 인식을 검토합니다. 새로운 모델의 단일 정확도를 제시하는 실험 논문이 아닙니다.
- **세부 제안:** 일반 이미지 학습 → 자세·인체 표현 학습 → 영상 움직임 추출 → 일반 행동 학습 → 임상 행동 미세 조정처럼 단계별 전이 학습을 설명합니다(Table III). **관절/움직임 추출과 임상 행동 분류를 분리**하는 구성을 논의합니다.
- **근거·한계:** 카메라 시점, 이불·의료진 가림, 야간 IR, 저해상도, 드문 임상 라벨을 별도 문제로 다룹니다. 두 단계 방식은 모듈 교체가 쉽지만 앞단 관절 오류가 뒷단 분류에 전파된다는 단점도 명시합니다.
- **검증·활용 제안:** 환자별로 학습·검증·시험을 분리하라는 본문 권고를 자체 실험에 반영합니다. 이 리뷰를 특정 모델의 임상 성공 증거로 사용하지 않습니다.


<a id="p17"></a>
### P17. SaccpaNet: A Separable Atrous Convolution-Based Cascade Pyramid Attention Network to Estimate Body Landmarks Using Cross-Modal Knowledge Transfer for Under-Blanket Sleep Posture Classification

**저자·출처:** Andy Yiu-Chau Tam 외. *IEEE Journal of Biomedical and Health Informatics*, 온라인 공개 2024, 정식 호 30(2), 1593–1604, 2026.  
**링크:** [DOI: 10.1109/JBHI.2024.3432195](https://doi.org/10.1109/JBHI.2024.3432195) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/39042546/)  
**확인 범위:** 본문 확인 — [PolyU 공개 논문 PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/115296/1/Tam_SaccpaNet_Separable_Atrous.pdf), pp.1593–1604, §III–VI, Fig.1 및 Table III.

- **기술·흐름:** 깊이 영상에서 관절을 추정하는 JCE와, 깊이·추정 관절을 이용하는 자세 분류기 SPC를 연결합니다. JCE는 SegNeXt 계열 encoder, dilation 1·2·5·7의 separable atrous convolution과 cascade pyramid attention, Hamburger decoder, soft-argmax를 사용합니다. SPC는 residual CNN 구조이며 ResNet-152+SVM 등과 비교합니다.
- **정답의 출처:** RGB의 **OpenPose 18관절 좌표를 대응 깊이 영상에 옮겨 학습·평가 라벨로 사용**합니다. COCO-WholeBody 사전학습과 cross-modal transfer가 포함됩니다. 시험 시 입력이 깊이 영상이라는 점과 학습 라벨이 RGB 추정기에서 왔다는 점을 구분해야 합니다.
- **자료·분할:** RealSense D435i로 건강한 참가자 150명, 7자세 × 비가림/3종 이불의 4조건, 총 4,200쌍을 수집합니다. 비율은 학습 64%·시험 20%·검증 16%입니다. 확인한 분할 설명만으로 **참가자 독립 분할을 확정할 수 없습니다**.
- **결과·검증:** JCE의 PCK@0.1은 0.6518이며 박스 대각선으로 정규화합니다. OpenPose 유래 라벨과의 일치도라는 한계가 있습니다. 7클래스와 두 엎드림 변형을 합친 6클래스 F1은 서로 다른 과제입니다. 본문의 클래스 평균·가중 평균·이불 조건별 수치를 섞어 하나의 개선폭으로 계산하지 않습니다.
- **활용 제안:** 깊이 방식과 RGB 방식의 차이를 이해하는 비교 자료입니다. 원문이 사용한 pseudo-label을 독립적인 수작업 관절 정답과 동일시하지 않습니다.


<a id="p18"></a>
### P18. Advances in Skeleton-Based Fall Detection in RGB Videos: From Handcrafted to Deep Learning Approaches

**저자·출처:** Van-Ha Hoang, Jong Weon Lee, Md. Jalil Piran, Chun-Su Park. *IEEE Access*, 11, 92322–92352, 2023.  
**링크:** [DOI: 10.1109/ACCESS.2023.3307138](https://doi.org/10.1109/ACCESS.2023.3307138) · [공식 기관 초록](https://pure.skku.edu/en/publications/advances-in-skeleton-based-fall-detection-in-rgb-videos-from-hand/) · [저자 비교표 저장소](https://github.com/hahv/Advances-in-Skeleton-Based-Fall-Detection-in-RGB-Videos)  
**확인 범위:** 본문 확인 — [저자 게재 승인본](https://www.researchgate.net/publication/373286744_Advances_in_Skeleton-Based_Fall_Detection_in_RGB_Videos_from_Handcrafted_to_Deep_Learning_Approaches), §IV의 관절 추출·전처리·분류·평가 지표 및 비교표. 최종 편집 전 버전입니다.

- **기술 지도:** OpenPose·AlphaPose·MoveNet·MediaPipe 등의 관절 추출과, 규칙·MLP·CNN·LSTM/GRU·GCN 계열의 낙상 분류를 분리해 정리합니다. 이 모델들을 모두 연결한 하나의 저자 구현이 아닙니다.
- **구체 내용:** 불필요한 사람·관절 제거, 결측 보간, 몸 중심·영상 크기 정규화, 시간 창 길이·stride, 창의 라벨 부여, 데이터 분할을 비교합니다. 따라서 모델 이름만 같아도 전처리와 평가 단위가 다를 수 있습니다.
- **검증·해석:** 본문의 MediaPipe/AlphaPose 기능 설명은 2023년 당시 상태입니다. 현재 라이브러리 기능으로 그대로 인용하지 않습니다. 비교표의 서로 다른 데이터·분할 성능도 직접 순위로 바꾸지 않습니다.
- **활용 제안:** 자체 실험에 관절 획득·결측 처리·시간 창·사람 단위 분할을 함께 기록하고, 낙상 분류 정확도 외에 장시간 오경보를 평가합니다. 이 리뷰의 낙상 탐지를 침대 이탈 예측과 같은 과제로 취급하지 않습니다.


<a id="p19"></a>
### P19. Skeleton-Based Sleep Posture Recognition with BP Neural Network

**저자·출처:** Haozhou Lyu, Jinglan Tian. IEEE CCET, 2020, 99–104.  
**링크:** [DOI: 10.1109/CCET50901.2020.9213125](https://doi.org/10.1109/CCET50901.2020.9213125) · [IEEE](https://ieeexplore.ieee.org/document/9213125/)  
**확인 범위:** **본문 검증 보류** — IEEE/DOI 서지와 공개 초록 수준. IEEE PDF는 접근되지 않았고 공개 저자 사본을 확보하지 못했습니다.

- **확인된 기술:** 스켈레톤 특징을 BP(backpropagation) 신경망으로 분류하는 수면 자세 연구입니다. BP는 학습 방식이며 관절을 검출하는 제품·라이브러리 이름이 아닙니다.
- **검증하지 못한 내용:** 관절 추정기(OpenPose/MediaPipe 등), 정확한 특징식, 은닉층·활성화 함수, 데이터 규모, 참가자 분리, 이불·조명별 성능입니다.
- **판정:** 제목과 관련 논문만으로 앞단 모델을 추정하지 않습니다. 구체 구조 및 성능의 재현 근거로 사용하는 것은 보류합니다.
- **활용 제안:** 단순 특징+작은 신경망 기준선의 조사 대상으로 유지합니다. 본문 확보 후 특징 정의와 분할을 확인해야 비교 실험에 정확히 포함할 수 있습니다.


<a id="p20"></a>
### P20. A New Hybrid Algorithm for Vision-Based Sleep Posture Analysis Integrating CNN, LSTM and MediaPipe

**저자·출처:** Apichaya Nimkoompai, Puwadol Sirikongtham. *International Journal of Advanced Computer Science and Applications*, 16(10), 2025.  
**링크:** [공식 논문 페이지](https://thesai.org/Publications/ViewPaper?Code=IJACSA&Issue=10&SerialNo=13&Volume=16) · [DOI: 10.14569/IJACSA.2025.0161013](https://doi.org/10.14569/IJACSA.2025.0161013) · [PDF](https://thesai.org/Downloads/Volume16No10/Paper_13-A_New_Hybrid_Algorithm_for_Vision_Based_Sleep_Posture_Analysis.pdf)  
**확인 범위:** 본문 확인 — §III의 자료·모델·분할, Tables I–III, Figs.4–5. 수치 충돌은 추출 텍스트뿐 아니라 **PDF 원본 pp.137–138의 표·그림을 시각적으로 대조**했습니다.

- **기술·흐름:** **MediaPipe 33개 관절(x,y,z) → TimeDistributed 1D CNN(kernel 3, ReLU, MaxPool, Flatten) → LSTM(hidden 32) → 4자세 softmax**입니다. CNN은 관절 특징, LSTM은 시간 변화를 처리합니다. MediaPipe의 z는 IR 카메라에서 측정한 실제 깊이가 아닙니다.
- **장비·자료:** 침대 위 약 2 m의 고정 IR 카메라, 19–21세 참가자 20명(남 12·여 8), 주간 140개·야간 140개 영상입니다. 조명별로 학습 70·검증 28·시험 42개, 즉 50/20/30으로 나눕니다. 참가자 독립 분할은 확인되지 않습니다. 100 epochs와 early stopping을 설명하지만 시퀀스 길이 등 재현에 필요한 설정이 충분하지 않습니다.
- **보고 결과:** Table III는 주간 96.4%, 야간 92.8%를 제시합니다.
- **검증 결과 — 불일치:** Fig.4의 주간 혼동행렬 대각선은 12+11+9+9=41, 전체는 42이므로 **41/42=97.62%**입니다. Table I의 클래스별 recall·support로 계산하면 11+11+8+8=38/42, **90.48%**가 됩니다. 같은 주간 결과로 제시된 Table III의 96.4%와 일치하지 않으며, 이를 연결하는 반복 실험 평균 등의 설명도 확인하지 못했습니다.
- **야간 확인:** Fig.5는 39/42=92.86%로 Table III의 92.8%에 가깝지만, 우측 자세 recall은 그림상 9/9=100%이고 Table II는 88.9%입니다. 반올림만으로 모든 차이를 설명할 수 없습니다.
- **판정·활용 제안:** 처리 구조는 참고할 수 있으나 **보고 성능의 일관성은 검증되지 않았습니다**. 원자료나 저자의 설명 없이 정확도를 확정하거나 모델 선정의 우위 근거로 사용하지 않습니다. 다른 연구와의 성능 비교표도 동일 시험집합 비교로 해석하지 않습니다.


<a id="p21"></a>
### P21. Towards automated joint detection in sleep studies: bridging clinical insight and artificial intelligence

**저자·출처:** Alexis Dorier 외. *Sleep*, 49(7), zsag108, 2026. HypnoPose 연구.  
**링크:** [DOI: 10.1093/sleep/zsag108](https://doi.org/10.1093/sleep/zsag108) · [출판사 원문](https://academic.oup.com/sleep/article/49/7/zsag108/8659223) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/42007581/)  
**확인 범위:** 본문 확인 — 출판사 원문의 Dataset/Network training/Evaluation, Tables 3·5·6. 표의 단일 분할 결과와 교차 검증을 구분했습니다.

- **기술·흐름:** **HigherHRNet에 CBAM attention**을 여러 위치에 넣어 비교합니다. COCO에서 상체 관절로 사전학습한 뒤 수면 영상으로 미세 조정합니다. AlphaPose·ViTPose는 비교 모델입니다.
- **자료·관절:** 74명, 89회 기록, 198개 움직임 구간, 4,419개 주석 프레임입니다. 자료의 수작업 관절 주석은 13개지만 **모델 출력은 머리·양쪽 어깨/팔꿈치/손목/골반의 9개 상체 관절**입니다. ‘13개를 출력하는 모델’로 쓰지 않습니다.
- **분할·학습:** 주 실험은 사람을 분리한 59명 학습·15명 검증입니다. 긴 영상의 과대표집을 줄이도록 사람별 프레임 수를 조정합니다. 선택한 Stage 4 모델은 별도로 **참가자 단위 5-fold 교차 검증**을 수행합니다. 사전학습·미세 조정은 각각 50 epochs입니다. 표본 추출 후 시간적 연속성이 유지되지 않아 프레임 단위 자세 추정 자료입니다.
- **결과·검증:** Table 5의 Stage 4는 mAP 0.090, AP@0.5 0.335입니다. Table 6의 5-fold 결과는 mAP **0.120±0.031**, AP@0.5 **0.350±0.032**입니다. 초록의 0.088/0.326과 본문 표 값에는 차이가 있으므로 이 문서는 표 번호와 평가 설정을 붙여 인용합니다.
- **한계·활용 제안:** 이 값은 OKS 기반 관절 위치 AP이며 자세 분류 정확도가 아닙니다. 실제 수면 환경에서 엄격한 관절 위치 추정이 여전히 어렵다는 근거입니다. 검출 실패·가림·카메라 시점별 성능과 판정 불가 구간을 함께 보고합니다.


<a id="p22"></a>
### P22. A Vision-Based System for In-Sleep Upper-Body and Head Pose Classification

**저자·출처:** Yan-Ying Li, Shoue-Jen Wang, Yi-Ping Hung. *Sensors*, 22(5), 2014, 2022.  
**링크:** [DOI: 10.3390/s22052014](https://doi.org/10.3390/s22052014) · [출판사](https://www.mdpi.com/1424-8220/22/5/2014) · [공개 원문](https://pmc.ncbi.nlm.nih.gov/articles/PMC8914692/)  
**확인 범위:** 본문 확인 — §3.1–3.2의 SleePose-FRCNN-Net, §4.1–4.3.2의 SLP·iSP·실제 수면 평가.

- **기술·흐름:** **SleePose-FRCNN-Net**은 ImageNet 사전학습 ResNet-50 backbone, RPN, RoI 특징, 머리·상체의 검출/분류 head를 쓰는 Faster R-CNN 계열 멀티태스크 모델입니다. 전신 관절을 먼저 얻는 MediaPipe 방식이 아닙니다.
- **자료·분할:** SLP는 90명 학습·12명 검증·모의 병원 7명 시험을 사용합니다. 자체 iSP 통제 촬영은 36명(남 29·여 7), 여러 자세 변형과 3종 덮개 조건입니다. 25명·15,000장 학습 / 11명·6,600장 시험으로 분리합니다.
- **실제 수면 평가:** 별도의 성인 4명 야간 자료에서 평균 91.67%를 보고합니다. 그러나 같은 사람의 서로 다른 수면 구간을 80/20으로 나눈 조건이므로 새로운 사람에 대한 91.67%로 해석하지 않습니다.
- **속도·검증:** RTX 2070에서 영상 한 장 처리 약 0.7초를 보고합니다. 수집 영상의 20 FPS를 추론 속도 20 FPS로 옮기면 안 됩니다. 머리 방향과 상체 방향의 결과 역시 구분해야 합니다.
- **한계·활용 제안:** 하체 가림 때 상체·머리 영상 특징을 쓰는 보조 기준선입니다. 머리를 돌린 상태를 몸 전체의 옆누움 또는 침대 이탈로 곧바로 바꾸지 않습니다.


<a id="p23"></a>
### P23. Classification of In-Bed Sleeping Position using U-Net and MobileNetV3

**저자·출처:** Jomlowe Andres D. Gaco, Cyrel O. Manlises. ICISPC 2025, *Advances in Transdisciplinary Engineering: Imaging, Signal Processing and Communications*, 174–184, 2025.  
**링크:** [출판사 원문 / DOI: 10.3233/ATDE251143](https://journals.sagepub.com/doi/full/10.3233/ATDE251143)  
**확인 범위:** 본문 확인 — 출판사 §2.4–2.6, Tables 1–3. 혼동행렬 합계와 지표를 직접 재계산했습니다.

- **기술·흐름:** Raspberry Pi 4·Camera Module 3 영상에서 **U-Net으로 사람 영역을 분할하고 MobileNetV3로 바로 누움·좌측·우측을 분류**합니다. 관절 추출 과정은 없습니다.
- **시험 조건:** 18–26세 지원자, 복잡하지 않은 배경, 이불 없는 조건입니다. 시험은 자세별 100장, 총 300장입니다. 참가자 수와 사람 단위 독립 분할은 확인한 설명만으로 확정하기 어렵습니다.
- **검증된 산술:** Table 2의 정분류는 85+99+97=281장으로 **281/300=93.67%**가 맞습니다. 행은 예측, 열은 실제 클래스이므로 바로 누움·좌측·우측 recall은 각각 **85%·99%·97%**입니다.
- **주의할 표기:** Table 3의 클래스별 ‘accuracy’ 85·90.83·88.18은 위 recall과 다릅니다. 정의가 분명하지 않으므로 이 문서는 혼동행렬에서 재계산한 recall을 별도 명칭으로 사용합니다.
- **활용 제안:** 영상 분류 기준선으로 참고합니다. 전체 정확도의 산술 일치는 이불·환자·새 참가자 일반화나 장시간 오경보까지 검증됐다는 뜻이 아닙니다.


<a id="p24"></a>
### P24. Deep State-Space Model for Noise Tolerant Skeleton-Based Action Recognition

**저자·출처:** Kazuki Kawamura, Takashi Matsubara, Kuniaki Uehara. *IEICE Transactions on Information and Systems*, E103.D(6), 1217–1225, 2020.  
**링크:** [DOI: 10.1587/transinf.2019MVP0012](https://doi.org/10.1587/transinf.2019MVP0012) · [J-STAGE](https://www.jstage.jst.go.jp/article/transinf/E103.D/6/E103.D_2019MVP0012/_article/-char/ja) · [저자 기관 PDF](https://da.lib.kobe-u.ac.jp/da/kernel/90007346/90007346.pdf)  
**확인 범위:** 본문 확인 — §4의 NTU 실험, Tables 1–2, §4.5 및 Figs.7–8.

- **기술·흐름:** **Deep State-Space Model(DSSM)**로 스켈레톤의 시간적 잠재 상태를 학습하고 **양방향 LSTM**으로 행동을 분류합니다. 관절 추출기 자체를 새로 제안하는 방식은 아닙니다.
- **자료·평가:** NTU RGB+D의 Kinect 25개 3D 관절과 60개 행동을 사용합니다. 사람 분리(cross-subject), 시점 분리(cross-view)를 평가하고, 가우시안 잡음과 무작위 프레임 제거 조건을 추가합니다.
- **결과·검증:** 정상 입력에서는 제안 모델이 67.45%·80.68%이고 비교 ST-GCN은 81.5%·88.3%입니다. 따라서 일반 정확도가 가장 높은 모델이라는 설명은 맞지 않습니다. 장점은 잡음·프레임 누락이 커질 때 상대적인 성능 저하가 작다는 점입니다.
- **한계:** 무작위로 프레임을 지운 실험은 이불 때문에 같은 관절이 오래 가려지는 현상과 다릅니다. 양방향 모델의 전체 구간 평가는 미래 정보가 없는 실시간 경고 조건과 구별해야 합니다.
- **활용 제안:** 단순 결측 마스크·시간 필터보다 실제로 이득이 있는지 비교합니다. 학습된 잠재 표현을 가려진 관절의 관측 정답으로 취급하지 않고, 오프라인과 실시간 지연을 별도로 평가합니다.


<a id="p25"></a>
### P25. Fall-from-Bed Risk Prediction Using Physics-Based Bed Simulation

**저자·출처:** Jaeyong Kim 외. *Sensors*, 26(10), 2979, 2026.  
**링크:** [출판사 / DOI: 10.3390/s26102979](https://www.mdpi.com/1424-8220/26/10/2979) · 서지·초록 대조 [1](https://consensus.app/papers/fallfrombed-risk-prediction-using-physicsbased-bed-kim-kim/2033f2b2108c5c459e76d3cfcd7b0bf2/?utm_source=chatgpt)  
**확인 범위:** 본문 확인 — §3.1–3.2, §4.2–4.3, Tables 1–3. 초록 중심 설명을 입력·라벨·학습·시험 조건까지 확장했습니다.

- **자료·라벨:** **MuJoCo 3.4.0**의 humanoid와 침대를 구성하고 초기 자세에서 3초간 제어 없는 움직임을 계산합니다. 손 접촉을 제외한 신체의 바닥 접촉으로 낙상 이벤트를 정하고, 발생까지의 시간으로 할인한 연속 위험 라벨을 만듭니다. 시뮬레이터의 13개 관절을 침대 좌표의 2D로 투영·정규화합니다. 영상에서 관절을 검출한 실험이 아닙니다.
- **모델:** 26차원 좌표를 **MLP 26→256→128→1(ReLU, dropout 0.1)**에 입력해 위험도를 회귀합니다. CNN·GCN·RandomForestRegressor도 비교합니다. LSTM 비교 모델은 **시작 5프레임**을 쓰므로 단일 정적 자세 모델들과 입력 정보량이 다릅니다.
- **학습·시험:** 기본 비교는 균형화한 합성 표본 100,000개, 학습/검증 약 9:1, 별도 자세 균형 시험 50,000개입니다. 신경망은 MSE·Adam·학습률 0.001·batch 512·최대 50 epochs, seed 41–45를 사용합니다. 임계값은 검증 자료에서 선택합니다.
- **결과·검증:** Table 3의 MLP는 AUROC **0.9755±0.0006**, F1 **0.9138±0.0015**입니다. LSTM은 AUROC 0.9750±0.0008로 비슷합니다. 동일 시뮬레이션 분포의 결과이며 실제 병동 낙상 빈도를 반영한 시험이 아닙니다.
- **한계·활용 제안:** 실제 관절 검출 오차·이불·자발적 움직임·현장 낙상을 검증하지 않았습니다. 침대 상대 위치 특징의 연구 참고로 두고, 합성 위험 점수를 실제 이탈 이벤트 정답과 분리합니다.

## 수치·내용 대조 기록

| 확인 항목 | 대조 방법 | 결과와 처리 |
|---|---|---|
| P02 지표 명칭 | §4.3.1의 식을 통상 정의와 비교 | TP/(TP+FP)는 precision; 저자의 accuracy 표기를 주의사항으로 남김 |
| P20 주간 성능 | PDF 원본 Fig.4 대각선 합 / 전체 표본과 Tables I·III 대조 | 41/42=97.62%, Table I로는 약 38/42=90.48%, Table III 96.4%; 보고값의 일관성 미확인 |
| P20 야간 성능 | Fig.5와 Tables II·III 대조 | 전체 39/42=92.86%; 우측 recall 100%와 표의 88.9%는 불일치 |
| P21 성능 표기 | 초록, Table 5 단일 분할, Table 6 교차 검증 비교 | 설정·출처를 명시해 분리 인용; 초록 수치를 본문 값과 혼합하지 않음 |
| P23 전체 정확도 | Table 2 혼동행렬 재계산 | (85+99+97)/300=93.67% 일치 |
| P15의 SLP 설명 | 리뷰 Table I와 P01 데이터 원문 비교 | 원 논문의 정적 자료·관절 정의를 우선 반영 |
| P11·P12·P19 | 출판사 PDF·공개 사본 접근 확인 | 본문 미확보; 구체 모델·분할·성능 검증 보류 |

이상 징후는 **확인한 문서 사이의 차이**입니다. 데이터 조작이나 논문 전체의 무효를 판정한 것은 아닙니다. 특히 P20은 원자료 또는 저자의 설명을 받아야 차이를 해소할 수 있습니다. 반대로 P23의 산술이 맞는다는 사실만으로 실험의 일반화까지 검증된 것은 아닙니다.

### 앞으로 재현할 때 필요한 항목

1. 공개 코드·가중치의 실제 버전, 관절 순서, 좌표계, 신뢰도·결측 처리와 전처리를 고정합니다.
2. 참가자·세션 단위 분할 목록을 보관하고 인접 프레임이 양쪽 집합에 섞이는지 확인합니다.
3. 정답 박스·모델이 생성한 라벨·수작업 라벨을 구분합니다.
4. 원 논문과 같은 지표·평균 방식·시간 창으로 재현한 값과, 우리 환경으로 옮긴 값을 별도로 보고합니다.
5. 이벤트 탐지는 프레임 정확도 외에 이벤트 recall, 시간당 오경보, 경고 지연, 판정 불가 비율을 함께 계산합니다.

## 문헌을 실제 개발로 연결하는 방법

| 개발 질문 | 참고 논문 | 다음에 할 작업 | 아직 증명되지 않은 점 |
|---|---|---|---|
| 누운 사람의 관절이 보이는가? | P01, P05, P06, P21 | 동일 저장 영상으로 검출·관절 누락·연속 실패 비교 | 실제 카메라/PC에서의 정확도와 지연 |
| 몸 자세와 침대 위치를 어떻게 분리할까? | P02, P12, P19, P25 | 신체 정규화 특징과 침대 상대 위치를 함께 저장 | 최적 관절·특징 조합 |
| 앉음과 이탈을 어떻게 구분할까? | P03, P11, P12 | 상태 전이 기준선과 시간 모델 비교 | 외부 센서와 공통 이벤트 정의 |
| 시간 모델이 꼭 필요한가? | P07–P10, P20, P24 | 규칙/단순 분류 후 LSTM·TCN 추가 이득 평가 | 데이터량 대비 복잡도·운영 비용 |
| 이불 가림을 어떻게 다룰까? | P04, P13, P14, P17, P21 | 우선 실패·판정 불가 기록; 후속 가림 실험 | RGB만으로 복원 가능한 실제 범위 |
| 관절이 없어도 자세를 분류할 수 있을까? | P22, P23 | 상체/영상 분류를 보조 기준선으로 검토 | 스켈레톤 대비 재현성·설명 가능성 |
| 데이터·평가는 어떻게 설계할까? | P01, P14–P16, P18, P21 | 참가자·세션 분리와 독립 정답 검토 | 자체 자료의 대표성과 장시간 오경보 |

### 최초 비교 실험 제안

1. 통제된 침대 영상에서 잠정 자세와 이탈·복귀, '몸을 일으켰지만 이탈하지 않음'을 함께 수집합니다.
2. 동일 원본 영상을 MediaPipe Pose·YOLO Pose·RTMPose에 입력하고 관절 매핑·신뢰도·실패·지연을 기록합니다. 후보 추가/제외는 실제 결과로 결정합니다.
3. 원본 좌표, 신체 정규화 좌표, 침대 상대 위치를 분리 저장합니다.
4. 규칙/SVM/RF/MLP 자세 기준선과 상태 전이 이벤트 기준선을 먼저 평가합니다.
5. 필요성이 확인되면 같은 분할로 LSTM/TCN을 추가하고, 그래프·히트맵 모델은 후속 비교로 둡니다.
6. 독립적으로 확인한 정답이 있는 구간의 성능과, 두 시스템 사이 일치도를 별도 보고합니다.

### 논문 수치를 비교하기 전에 확인할 항목

- 실제 입력이 RGB인지 IR·열영상·깊이인지, 측정 3D인지 모델 추정 3D인지.
- 시험에 새로운 참가자/세션이 들어가는지, 같은 영상의 인접 프레임이 학습과 시험에 섞이지 않았는지.
- 실제 검출기로 인물 박스를 얻었는지, 정답 박스를 제공했는지.
- 결측 프레임·어려운 구간을 제외했는지, 제외 비율과 판정 불가 비율이 보고됐는지.
- 실시간 평가인지 전체 영상의 미래 프레임을 사용한 평가인지.
- 자세 정확도인지 관절 위치 정확도인지, 이벤트 단위 지표인지.
- 데이터/코드/가중치를 실제로 사용할 수 있는지와 이용 조건.

## 구현 문서와 구분할 참고 자료

[Ultralytics Pose 공식 문서](https://docs.ultralytics.com/tasks/pose/)는 YOLO Pose 구현 후보를 확인하기 위한 자료이며 위 **25편의 학술 논문에 포함하지 않습니다**. 라이브러리 버전·모델 크기·가중치·라이선스와 실행 장치 지원은 실제 비교 실험을 시작할 때 다시 확인합니다. 특정 라이브러리의 설치나 모델 선정은 아직 완료하지 않았습니다.

## 연계 문서

- [현재 진행 현황](PROJECT_STATUS.md)
- [시스템 구조](ARCHITECTURE.md)
- [측정 절차](MEASUREMENT_PROTOCOL.md)
- [데이터와 검증 기준](DATA_AND_VALIDATION.md)
- [결정·미정·보류 사항](DECISIONS.md)
- [개발 로드맵](../ROADMAP.md)

**후속 갱신 원칙:** 새로운 논문을 추가할 때 입력 장비·정답 종류·데이터 분할·접근 가능 여부·확인한 원문 범위를 함께 기록합니다. 논문의 결과, 우리가 추론한 활용점, 실제 재현 결과를 서로 분리합니다.
