# 논문 안내와 색인

[프로젝트 홈](../README.md) · [진행 현황](PROJECT_STATUS.md) · [기술 후보 비교](TECHNOLOGY_CANDIDATES.md)

**기준일: 2026-10-26 · 총 37편 · 공개 본문/저자판 대조 33편 · 초록·서지만 확인 4편**

논문 상세는 두 문서에서 관리합니다. 각 항목은 서지·원문 링크, 확인한 범위, 방법·자료·평가 결과, 한계와 프로젝트 활용 제안 순서로 구성합니다.

| 상세 문서 | 범위 | 확인 상태 |
|---|---|---|
| [침대 위 자세 구분을 위한 논문](BED_POSTURE_PAPERS.md) | 24편: 자세·이탈·가림·데이터·리뷰 | 본문 20편(판본 제한 포함), 초록·서지 중심 4편 |
| [스켈레톤 인식 기술](SKELETON_TECHNOLOGY_PAPERS.md) | 13편: 관절 추출·프레임워크 7편, 후속 분석·리뷰 6편 | 본문 13편 |

‘본문 확인’은 관련 절·표에 적힌 방법과 결과를 대조했다는 뜻입니다. 모든 최종 출판본의 전체 검증, 코드 실행, 원자료 검사, 성능 재현을 뜻하지 않습니다. 수치가 일치하지 않는 논문도 본문 확인 33편에 포함됩니다. P35는 2020 공개판을 확인했으나 2022 ACM 최종판 본문은 미확보입니다. 새로 추가한 8편은 P30–P37이며, 서지상 완전 중복 3편은 추가하지 않았습니다.

## 목적별 읽는 순서

| 알고 싶은 내용 | 읽을 자료 |
|---|---|
| 먼저 구현·비교할 후보 | [기술 후보 비교](TECHNOLOGY_CANDIDATES.md) → [관절 추출 논문](SKELETON_TECHNOLOGY_PAPERS.md#p05) |
| 침대 자세·이탈 판단 | [P02](BED_POSTURE_PAPERS.md#p02) → [P03 BedEye](BED_POSTURE_PAPERS.md#p03) → [P25](BED_POSTURE_PAPERS.md#p25) |
| 데이터와 가림 조건 | [P01 SLP](BED_POSTURE_PAPERS.md#p01) → [P14 BlanketSet](BED_POSTURE_PAPERS.md#p14) → [P21 HypnoPose](BED_POSTURE_PAPERS.md#p21) → [P34 회전 동작](BED_POSTURE_PAPERS.md#p34) |
| 관절 이후의 시간 분석 | [P10 TCN](SKELETON_TECHNOLOGY_PAPERS.md#p10) → [P07 ST-GCN](SKELETON_TECHNOLOGY_PAPERS.md#p07) → [P09 PoseC3D](SKELETON_TECHNOLOGY_PAPERS.md#p09) |
| 자체 실험 설계 | [측정 절차](MEASUREMENT_PROTOCOL.md) · [데이터·검증 기준](DATA_AND_VALIDATION.md) |

## 결과를 읽는 기준

| 구분 | 확인할 내용 |
|---|---|
| 입력·정답 | RGB/IR/LWIR/깊이/압력, 추정 3D/실측 깊이, 수작업/모델 생성/합성 라벨 |
| 과제·지표 | 관절 PCK·AP, 자세 분류, 이탈 이벤트, 사전 위험 예측을 각각 해석 |
| 시험 조건 | 참가자·세션 분리, 정답 사람 영역 제공 여부, 제외된 실패·결측 구간 |
| 시간·속도 | 과거만 쓰는 실시간 처리인지, 미래 프레임 사용 여부, 모델 단독/전체 지연 |
| 적용 가능성 | 실제 침대·이불·환자 조건, 코드·가중치·데이터 이용 가능 범위 |

논문별로 다른 데이터·분할·장비의 점수를 단일 성능 순위로 합치지 않습니다. 논문의 보고 결과, 프로젝트 적용 제안, 실제 자체 실험 결과를 구분합니다.

**현재 제한:** [P11](BED_POSTURE_PAPERS.md#p11)·[P12](BED_POSTURE_PAPERS.md#p12)·[P19](BED_POSTURE_PAPERS.md#p19)·[P34](BED_POSTURE_PAPERS.md#p34)는 **본문 미확보**입니다. 신규 P30·P31·P33·P36은 이번에 공개 본문 또는 저자 게재 승인본의 방법·자료·결과표를 대조했고, 기존 P32·P37도 다시 확인했습니다. [P35](BED_POSTURE_PAPERS.md#p35)는 **2020 arXiv 공개판의 본문·성능표를 확인**했지만 2022 ACM 최종판은 초록·서지만 확인했습니다. P35 공개 원고는 '가정환경 102명'과 '학습 85명 + 평가 22명'의 수치 불일치가 있으므로 임의 수정하지 않습니다. P31 저자 원고에도 시간·AUC 설명의 주의점이 있습니다. 기존 [P02](BED_POSTURE_PAPERS.md#p02)·[P03](BED_POSTURE_PAPERS.md#p03)·[P04](BED_POSTURE_PAPERS.md#p04)·[P20](BED_POSTURE_PAPERS.md#p20)·[P21](BED_POSTURE_PAPERS.md#p21)·[P23](BED_POSTURE_PAPERS.md#p23)의 제한도 각 항목에 유지했습니다. 논문의 성능 재현이나 데이터셋 자체 검증은 수행하지 않았습니다.

<a id="technology-comparison"></a>
## 전체 색인

ID는 기존 링크와 연결되도록 유지합니다. 표의 짧은 이름을 누르면 전체 제목과 세부 설명으로 이동합니다.

### 침대 위 자세 구분 · 24편

| ID | 논문 | 역할 |
|---|---|---|
| <a id="p01"></a>P01 | [SLP](BED_POSTURE_PAPERS.md#p01) | 다중 입력 데이터·관절 벤치마크 |
| <a id="p02"></a>P02 | [RGB-D 상체 관절 + XGBoost](BED_POSTURE_PAPERS.md#p02) | 3자세 분류·지원자/환자 비교 |
| <a id="p03"></a>P03 | [BedEye](BED_POSTURE_PAPERS.md#p03) | 좌표 규칙과 LSTM·침대 이탈 |
| <a id="p04"></a>P04 | [RGB 복원 + 관절 추정](BED_POSTURE_PAPERS.md#p04) | MAE/AOT-GAN·가림 대응 |
| <a id="p11"></a>P11 | [LSTM 침대 이탈 검출](BED_POSTURE_PAPERS.md#p11) | 자세·상대 위치의 시간 분석 |
| <a id="p12"></a>P12 | [침대 위치 + 자세 추정](BED_POSTURE_PAPERS.md#p12) | 이탈 관련 상태 예측 |
| <a id="p13"></a>P13 | [BlanketGen2-Fit3D](BED_POSTURE_PAPERS.md#p13) | 합성 이불·ViTPose-B 학습 |
| <a id="p14"></a>P14 | [BlanketSet](BED_POSTURE_PAPERS.md#p14) | RGB/IR/깊이 데이터·HybrIK 평가 |
| <a id="p15"></a>P15 | [침대 자세 추정 리뷰](BED_POSTURE_PAPERS.md#p15) | 입력·모델·데이터 정리 |
| <a id="p16"></a>P16 | [임상 침대 동작 리뷰](BED_POSTURE_PAPERS.md#p16) | 3D MoCap·행동 인식·전이 학습 |
| <a id="p17"></a>P17 | [SaccpaNet](BED_POSTURE_PAPERS.md#p17) | 깊이 관절 추정 + 자세 분류 |
| <a id="p19"></a>P19 | [스켈레톤 + BP 신경망](BED_POSTURE_PAPERS.md#p19) | 관절 특징 기반 수면 자세 |
| <a id="p20"></a>P20 | [MediaPipe + CNN + LSTM](BED_POSTURE_PAPERS.md#p20) | IR 영상의 4자세 분류 |
| <a id="p21"></a>P21 | [HypnoPose](BED_POSTURE_PAPERS.md#p21) | HigherHRNet + CBAM·상체 9관절 |
| <a id="p22"></a>P22 | [상체·머리 자세 분류](BED_POSTURE_PAPERS.md#p22) | SleePose-FRCNN-Net |
| <a id="p23"></a>P23 | [U-Net + MobileNetV3](BED_POSTURE_PAPERS.md#p23) | 사람 분할 후 3자세 영상 분류 |
| <a id="p25"></a>P25 | [물리 시뮬레이션 기반 낙상 위험](BED_POSTURE_PAPERS.md#p25) | 13관절 → MLP·합성/실제 평가 |
| <a id="p30"></a>P30 | [단일 IR 카메라 전이학습](BED_POSTURE_PAPERS.md#p30) | 밤샘 4자세·빈 침대 판별 |
| <a id="p31"></a>P31 | [RGB·열화상 앙상블](BED_POSTURE_PAPERS.md#p31) | 이불 조건 5자세 분류 |
| <a id="p32"></a>P32 | [IRS·CPM·HOG](BED_POSTURE_PAPERS.md#p32) | 마네킹 관절·방향 보정 |
| <a id="p33"></a>P33 | [Bodies at Rest](BED_POSTURE_PAPERS.md#p33) | 압력→3D·합성 PressurePose |
| <a id="p34"></a>P34 | [전신 회전 동작 기반 가림 대응](BED_POSTURE_PAPERS.md#p34) | 이불 아래 방향 변화·3자세 |
| <a id="p35"></a>P35 | [다중 센서 자세·형상 융합](BED_POSTURE_PAPERS.md#p35) | IR·깊이·압력·RGB / 판본 주의 |
| <a id="p36"></a>P36 | [IR 이불 가림 증강](BED_POSTURE_PAPERS.md#p36) | 통계적 증강·전이학습·반지도 학습 |

### 스켈레톤 인식 기술 · 13편

| ID | 논문 | 역할 |
|---|---|---|
| <a id="p05"></a>P05 | [BlazePose](SKELETON_TECHNOLOGY_PAPERS.md#p05) | 33개 2D 랜드마크 |
| <a id="p06"></a>P06 | [RTMPose](SKELETON_TECHNOLOGY_PAPERS.md#p06) | CSPNeXt·SimCC·GAU |
| <a id="p26"></a>P26 | [BlazePose GHUM Holistic](SKELETON_TECHNOLOGY_PAPERS.md#p26) | 몸·손 3D 추정·GHUM Lifter |
| <a id="p27"></a>P27 | [OpenPose / PAF](SKELETON_TECHNOLOGY_PAPERS.md#p27) | 관절 히트맵·신체 연결 |
| <a id="p37"></a>P37 | [OpenPose 2021 확장](SKELETON_TECHNOLOGY_PAPERS.md#p37) | PAF-only 반복 정교화·발 관절 |
| <a id="p28"></a>P28 | [HRNet](SKELETON_TECHNOLOGY_PAPERS.md#p28) | 병렬 해상도·반복 융합 |
| <a id="p29"></a>P29 | [MediaPipe 프레임워크](SKELETON_TECHNOLOGY_PAPERS.md#p29) | Packet·Stream·Calculator·Graph |
| <a id="p07"></a>P07 | [ST-GCN](SKELETON_TECHNOLOGY_PAPERS.md#p07) | 관절의 공간·시간 그래프 |
| <a id="p08"></a>P08 | [2s-AGCN](SKELETON_TECHNOLOGY_PAPERS.md#p08) | 관절·뼈 두 흐름·적응형 그래프 |
| <a id="p09"></a>P09 | [PoseC3D](SKELETON_TECHNOLOGY_PAPERS.md#p09) | 관절 히트맵 시계열·3D CNN |
| <a id="p10"></a>P10 | [TCN 비교 연구](SKELETON_TECHNOLOGY_PAPERS.md#p10) | 인과적·팽창 1D 합성곱 |
| <a id="p18"></a>P18 | [스켈레톤 낙상 탐지 리뷰](SKELETON_TECHNOLOGY_PAPERS.md#p18) | 추정기·전처리·시간 모델·평가 |
| <a id="p24"></a>P24 | [Deep State-Space Model](SKELETON_TECHNOLOGY_PAPERS.md#p24) | DSSM + 양방향 LSTM |

## 추가 자료와 갱신

공식 API·라이브러리 문서와 후보 가이드의 추가 연구 S11·S12는 [기술 후보 비교의 출처](TECHNOLOGY_CANDIDATES.md#sources)에 모았습니다. 이 자료들은 위 P01–P29 목록에 포함하지 않습니다.

새 논문을 추가할 때는 확인한 판본·본문 범위, 입력 장비, 정답 출처, 자료 분할, 결과의 제한을 함께 기록합니다. 설치·모델 채택·성능 재현 여부는 [진행 현황](PROJECT_STATUS.md)에서 관리합니다.
