# 논문 문서 안내와 공통 평가 기준

**정리일:** 2026-10-25 (한국 시간)

기존 25편과 새로 본문을 검토한 기술 논문 4편을 합쳐 **총 29편**을 두 상세 문서로 분리했습니다. 기존 P01–P25 번호를 유지하고 P26–P29를 추가했습니다.

| 문서 | 편수 | 범위 |
|---|---:|---|
| [침대 위 자세 구분을 위한 논문](BED_POSTURE_PAPERS.md) | 17 | 침대 자세·이탈·가림·데이터·리뷰 |
| [스켈레톤 인식 기술](SKELETON_TECHNOLOGY_PAPERS.md) | 12 | 관절 추출·프레임워크 6편 + 후속 분석·리뷰 6편 |

**2026-10-25 재검토:** 29편 모두의 서지·분류를 점검하고, 그중 **26편의 원문 또는 공개 저자판에서 방법·자료·평가 조건·결과를 다시 대조**했습니다. **P11·P12·P19는 본문 미확보로 세부 검증 보류**입니다. 수치 불일치가 있는 논문도 본문 대조 26편에 포함되므로, 이 숫자는 ‘26편의 성능이 검증됐다’는 뜻이 아닙니다. [논문별 근거·정정·미검증 사항](LITERATURE_AUDIT.md)을 함께 확인합니다.

**정정:** P05의 Full 102·Lite 312 FPS 표기는 각주를 붙여 읽은 오류로, Full 10·Lite 31 FPS로 수정했습니다. [BlazePose Table 1](https://arxiv.org/html/2006.10204v1).

## 기존 논문 링크 안내

기존 문서의 개별 논문 링크를 계속 사용할 수 있도록 아래 앵커를 유지합니다.

<a id="p01"></a>
- [P01. Simultaneously-Collected Multimodal Lying Pose Dataset: Towards In-Bed Human Pose Monitoring under Adverse Vision Conditions](BED_POSTURE_PAPERS.md#p01)

<a id="p02"></a>
- [P02. Posture Monitoring for Health Care of Bedridden Elderly Patients Using 3D Human Skeleton Analysis via Machine Learning Approach](BED_POSTURE_PAPERS.md#p02)

<a id="p03"></a>
- [P03. BedEye: A Bed Exit and Bedside Fall Warning System Based on Skeleton Recognition Technology for Elderly Patients](BED_POSTURE_PAPERS.md#p03)

<a id="p04"></a>
- [P04. RGB-Only in-Bed Pose Estimation Under Occlusion via Image Reconstruction](BED_POSTURE_PAPERS.md#p04)

<a id="p05"></a>
- [P05. BlazePose: On-device Real-time Body Pose tracking](SKELETON_TECHNOLOGY_PAPERS.md#p05)

<a id="p06"></a>
- [P06. RTMPose: Real-Time Multi-Person Pose Estimation based on MMPose](SKELETON_TECHNOLOGY_PAPERS.md#p06)

<a id="p07"></a>
- [P07. Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition](SKELETON_TECHNOLOGY_PAPERS.md#p07)

<a id="p08"></a>
- [P08. Two-Stream Adaptive Graph Convolutional Networks for Skeleton-Based Action Recognition](SKELETON_TECHNOLOGY_PAPERS.md#p08)

<a id="p09"></a>
- [P09. Revisiting Skeleton-based Action Recognition](SKELETON_TECHNOLOGY_PAPERS.md#p09)

<a id="p10"></a>
- [P10. An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling](SKELETON_TECHNOLOGY_PAPERS.md#p10)

<a id="p11"></a>
- [P11. Bed Exit Action Detection Based on Patient Posture with Long Short-Term Memory](BED_POSTURE_PAPERS.md#p11)

<a id="p12"></a>
- [P12. Bed-Exit Prediction Applying Neural Network Combining Bed Position Detection and Patient Posture Estimation](BED_POSTURE_PAPERS.md#p12)

<a id="p13"></a>
- [P13. BlanketGen2-Fit3D: Synthetic Blanket Augmentation Towards Improving Real-World In-Bed Blanket Occluded Human Pose Estimation](BED_POSTURE_PAPERS.md#p13)

<a id="p14"></a>
- [P14. BlanketSet – A Clinical Real-World In-Bed Action Recognition and Qualitative Semi-Synchronised Motion Capture Dataset](BED_POSTURE_PAPERS.md#p14)

<a id="p15"></a>
- [P15. In-Bed Pose Estimation: A Review](BED_POSTURE_PAPERS.md#p15)

<a id="p16"></a>
- [P16. Deep learning methods for single camera based clinical in-bed movement action recognition](BED_POSTURE_PAPERS.md#p16)

<a id="p17"></a>
- [P17. SaccpaNet: A Separable Atrous Convolution-Based Cascade Pyramid Attention Network to Estimate Body Landmarks Using Cross-Modal Knowledge Transfer for Under-Blanket Sleep Posture Classification](BED_POSTURE_PAPERS.md#p17)

<a id="p18"></a>
- [P18. Advances in Skeleton-Based Fall Detection in RGB Videos: From Handcrafted to Deep Learning Approaches](SKELETON_TECHNOLOGY_PAPERS.md#p18)

<a id="p19"></a>
- [P19. Skeleton-Based Sleep Posture Recognition with BP Neural Network](BED_POSTURE_PAPERS.md#p19)

<a id="p20"></a>
- [P20. A New Hybrid Algorithm for Vision-Based Sleep Posture Analysis Integrating CNN, LSTM and MediaPipe](BED_POSTURE_PAPERS.md#p20)

<a id="p21"></a>
- [P21. Towards automated joint detection in sleep studies: bridging clinical insight and artificial intelligence](BED_POSTURE_PAPERS.md#p21)

<a id="p22"></a>
- [P22. A Vision-Based System for In-Sleep Upper-Body and Head Pose Classification](BED_POSTURE_PAPERS.md#p22)

<a id="p23"></a>
- [P23. Classification of In-Bed Sleeping Position using U-Net and MobileNetV3](BED_POSTURE_PAPERS.md#p23)

<a id="p24"></a>
- [P24. Deep State-Space Model for Noise Tolerant Skeleton-Based Action Recognition](SKELETON_TECHNOLOGY_PAPERS.md#p24)

<a id="p25"></a>
- [P25. Fall-from-Bed Risk Prediction Using Physics-Based Bed Simulation](BED_POSTURE_PAPERS.md#p25)

<a id="p26"></a>
- [P26. BlazePose GHUM Holistic: Real-time 3D Human Landmarks and Pose Estimation](SKELETON_TECHNOLOGY_PAPERS.md#p26)

<a id="p27"></a>
- [P27. Realtime Multi-Person 2D Pose Estimation using Part Affinity Fields](SKELETON_TECHNOLOGY_PAPERS.md#p27)

<a id="p28"></a>
- [P28. Deep High-Resolution Representation Learning for Human Pose Estimation](SKELETON_TECHNOLOGY_PAPERS.md#p28)

<a id="p29"></a>
- [P29. MediaPipe: A Framework for Building Perception Pipelines](SKELETON_TECHNOLOGY_PAPERS.md#p29)

<a id="technology-comparison"></a>
## 사용 기술 비교표

두 상세 문서의 사용 기술 비교와 개별 항목을 참조합니다. 범용 모델과 침대 특화 연구는 중복 수록하지 않고 연결합니다.

## 수치·내용 대조 기록

| 확인 항목 | 대조 방법 | 결과와 처리 |
|---|---|---|
| P02 지표·표 | §4.3.1, PDF Tables 4–5 | precision 식을 accuracy로 표기; Table 5의 3D 행 합계·요약 수치에도 불일치 |
| P03 BedEye | §IV-B 정답 건수/전체 건수 계산 | 3943/4000=98.575%; 함께 적힌 97.4%와 불일치. 병원 평가 97.72%와 구분 |
| P04 재구성 | 공개 승인본 초록·Table 8·결론 | 35/37%, 21/13% 표기 차이; 최종판 대조 전 단일 개선율 확정 보류 |
| P25 실제 자료 평가 | §4.6, Tables 6–7, PDF p.12 | 기존 누락 정정: 실제 영상 100개의 수작업 관절 평가가 있음. AUROC 0.8175±0.0188 |
| P20 주간 성능 | PDF 원본 Fig.4 대각선 합 / 전체 표본과 Tables I·III 대조 | 41/42=97.62%, Table I로는 약 38/42=90.48%, Table III 96.4%; 보고값의 일관성 미확인 |
| P20 야간 성능 | Fig.5와 Tables II·III 대조 | 전체 39/42=92.86%; 우측 recall 100%와 표의 88.9%는 불일치 |
| P21 성능·집계 단위 | 초록, Tables 2·3·5·6 | 초록/표 성능 차이; Table 3의 recordings 합계는 본문 구간 수 198과 같으므로 89회 기록과 구분 |
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

[Ultralytics Pose 공식 문서](https://docs.ultralytics.com/tasks/pose/)는 YOLO Pose 구현 후보를 확인하기 위한 자료이며 전체 **29편의 학술 논문에 포함하지 않습니다**. 라이브러리 버전·모델 크기·가중치·라이선스와 실행 장치 지원은 실제 비교 실험을 시작할 때 다시 확인합니다. 특정 라이브러리의 설치나 모델 선정은 아직 완료하지 않았습니다.

## 연계 문서

- [현재 진행 현황](PROJECT_STATUS.md)
- [시스템 구조](ARCHITECTURE.md)
- [측정 절차](MEASUREMENT_PROTOCOL.md)
- [데이터와 검증 기준](DATA_AND_VALIDATION.md)
- [결정·미정·보류 사항](DECISIONS.md)
- [개발 로드맵](../ROADMAP.md)

**후속 갱신 원칙:** 새로운 논문을 추가할 때 입력 장비·정답 종류·데이터 분할·접근 가능 여부·확인한 원문 범위를 함께 기록합니다. 논문의 결과, 우리가 추론한 활용점, 실제 재현 결과를 서로 분리합니다.
