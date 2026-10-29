# 논문 안내와 색인

[문서 목차](../README.md) · [분야 목차](README.md) · [현재 상태](../PROJECT_STATUS.md)


[프로젝트 홈](../../README.md) · [진행 현황](../PROJECT_STATUS.md) · [기술 후보 비교](TECHNOLOGY_CANDIDATES.md)

**기준일: 2026-10-26 · 등재 37편 · 본문/저자판 대조 33편 · 본문 미확인 4편(사실 판단 제외)**

논문 상세는 두 문서에서 관리합니다. 각 항목은 서지·원문 링크, 확인한 범위, 방법·자료·평가 결과, 한계와 프로젝트 활용 제안 순서로 구성합니다.

| 상세 문서 | 범위 | 확인 상태 |
|---|---|---|
| [침대 위 자세 구분을 위한 논문](BED_POSTURE_PAPERS.md) | 24편: 자세·이탈·가림·데이터·리뷰 | 본문 대조 20편(판본 제한 포함), **본문 미확인 4편·판단 제외** |
| [스켈레톤 인식 기술](SKELETON_TECHNOLOGY_PAPERS.md) | 13편: 관절 추출·프레임워크 7편, 후속 분석·리뷰 6편 | 본문 13편 |

‘본문 확인’은 특정 판본에서 관련 절·표를 직접 대조했다는 뜻이며, **최종 출판본 전체 검증, 코드·원자료 재현은 의미하지 않습니다.** P35는 **2020 공개판만 본문 확인**, 2022 ACM 최종판은 **본문 미확인(최종판에 관한 사실 판단 제외)**입니다. 신규 P30–P37 총 8편을 등재했고 동일 논문 3편은 중복 등록하지 않았습니다.

## 본문 확인 여부에 따른 근거 채택 규칙

| 상태 | 허용되는 기록 | 사실 판단·비교·선정에서의 취급 |
|---|---|---|
| **본문 확인** | 확인한 **해당 판본**의 방법·실험·수치(절·표·한계 명기) | 검증한 범위에서만 근거로 사용; 자체 실험·일반화와 구분 |
| **본문 미확인** | 논문 제목, 저자, 연도, DOI 등 **서지와 원문 확보 상태** | **연구 주장·효과·데이터셋·모델 구조·성능 수치를 사실로 인정하지 않고 전부 배제** |
| **판본별 본문 미확인** | 확인한 공개판의 근거, 다른 출판판의 서지 | 미확인 판본의 구조·성능은 **배제**; 공개판 결과를 최종 출판판에 전용하지 않음 |
| **본문 수치/조건 불일치** | 상충한 값과 표·절을 함께 기록 | 원문 또는 원자료로 해소되기 전에는 관련 **논쟁 수치를 결정 근거에서 제외** |

**현재 본문 미확인:** [P11](BED_POSTURE_PAPERS.md#p11), [P12](BED_POSTURE_PAPERS.md#p12), [P19](BED_POSTURE_PAPERS.md#p19), [P34](BED_POSTURE_PAPERS.md#p34). 네 항목은 **목록에는 남지만 유효 연구 근거 33편에는 포함되지 않습니다.** 독립적인 본문 확인 전까지 요약·근거 표·개발 프롬프트가 이 4편의 초록 내용을 재사용하지 않도록 합니다.

## 목적별 읽는 순서

| 알고 싶은 내용 | 읽을 자료 |
|---|---|
| 먼저 구현·비교할 후보 | [기술 후보 비교](TECHNOLOGY_CANDIDATES.md) → [관절 추출 논문](SKELETON_TECHNOLOGY_PAPERS.md#p05) |
| 침대 자세·이탈 판단 | [P02](BED_POSTURE_PAPERS.md#p02) → [P03 BedEye](BED_POSTURE_PAPERS.md#p03) → [P25](BED_POSTURE_PAPERS.md#p25) |
| 데이터와 가림 조건 | [P01 SLP](BED_POSTURE_PAPERS.md#p01) → [P14 BlanketSet](BED_POSTURE_PAPERS.md#p14) → [P21 HypnoPose](BED_POSTURE_PAPERS.md#p21) → [P36 IR 가림 증강](BED_POSTURE_PAPERS.md#p36) |
| 관절 이후의 시간 분석 | [P10 TCN](SKELETON_TECHNOLOGY_PAPERS.md#p10) → [P07 ST-GCN](SKELETON_TECHNOLOGY_PAPERS.md#p07) → [P09 PoseC3D](SKELETON_TECHNOLOGY_PAPERS.md#p09) |
| 자체 실험 설계 | [스켈레톤 비교 실험 계획](POSE_BENCHMARK_PLAN.md) · [측정 절차](../design/MEASUREMENT_PROTOCOL.md) · [데이터·검증 기준](../design/DATA_AND_VALIDATION.md) |
| 후보의 역할과 실행 부담 | [기술 후보 비교](TECHNOLOGY_CANDIDATES.md): 적용 방법·선택 조건 · [연산·실행 부담 비교](POSE_COMPUTE_AND_RESOURCE_COMPARISON.md): 공개 처리 시간·학습·결합 부담 |

## 결과를 읽는 기준

| 구분 | 확인할 내용 |
|---|---|
| 입력·정답 | RGB/IR/LWIR/깊이/압력, 추정 3D/실측 깊이, 수작업/모델 생성/합성 라벨 |
| 과제·지표 | 관절 PCK·AP, 자세 분류, 이탈 이벤트, 사전 위험 예측을 각각 해석 |
| 시험 조건 | 참가자·세션 분리, 정답 사람 영역 제공 여부, 제외된 실패·결측 구간 |
| 시간·속도 | 과거만 쓰는 실시간 처리인지, 미래 프레임 사용 여부, 모델 단독/전체 지연 |
| 적용 가능성 | 실제 침대·이불·환자 조건, 코드·가중치·데이터 이용 가능 범위 |

논문별로 다른 데이터·분할·장비의 점수를 단일 성능 순위로 합치지 않습니다. 논문의 보고 결과, 프로젝트 적용 제안, 실제 자체 실험 결과를 구분합니다.

**현재 제한:** [P11](BED_POSTURE_PAPERS.md#p11)·[P12](BED_POSTURE_PAPERS.md#p12)·[P19](BED_POSTURE_PAPERS.md#p19)·[P34](BED_POSTURE_PAPERS.md#p34)는 **본문 미확인 · 사실 판단 제외**입니다. 신규 P30·P31·P33·P36은 이번에 공개 본문 또는 저자 게재 승인본의 방법·자료·결과표를 대조했고, 기존 P32·P37도 다시 확인했습니다. [P35](BED_POSTURE_PAPERS.md#p35)는 **2020 arXiv 공개판의 본문·성능표를 확인**했지만 2022 ACM 최종판은 **본문 미확인 · 최종판 판단 제외**입니다. P35 공개 원고는 '가정환경 102명'과 '학습 85명 + 평가 22명'의 수치 불일치가 있으므로 임의 수정하지 않습니다. P31 저자 원고에도 시간·AUC 설명의 주의점이 있습니다. 기존 [P02](BED_POSTURE_PAPERS.md#p02)·[P03](BED_POSTURE_PAPERS.md#p03)·[P04](BED_POSTURE_PAPERS.md#p04)·[P20](BED_POSTURE_PAPERS.md#p20)·[P21](BED_POSTURE_PAPERS.md#p21)·[P23](BED_POSTURE_PAPERS.md#p23)의 제한도 각 항목에 유지했습니다. 논문의 성능 재현이나 데이터셋 자체 검증은 수행하지 않았습니다.

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
| <a id="p11"></a>P11 | [LSTM 침대 이탈 검출](BED_POSTURE_PAPERS.md#p11) | **본문 미확인 · 판단 제외** |
| <a id="p12"></a>P12 | [침대 위치 + 자세 추정](BED_POSTURE_PAPERS.md#p12) | **본문 미확인 · 판단 제외** |
| <a id="p13"></a>P13 | [BlanketGen2-Fit3D](BED_POSTURE_PAPERS.md#p13) | 합성 이불·ViTPose-B 학습 |
| <a id="p14"></a>P14 | [BlanketSet](BED_POSTURE_PAPERS.md#p14) | RGB/IR/깊이 데이터·HybrIK 평가 |
| <a id="p15"></a>P15 | [침대 자세 추정 리뷰](BED_POSTURE_PAPERS.md#p15) | 입력·모델·데이터 정리 |
| <a id="p16"></a>P16 | [임상 침대 동작 리뷰](BED_POSTURE_PAPERS.md#p16) | 3D MoCap·행동 인식·전이 학습 |
| <a id="p17"></a>P17 | [SaccpaNet](BED_POSTURE_PAPERS.md#p17) | 깊이 관절 추정 + 자세 분류 |
| <a id="p19"></a>P19 | [스켈레톤 + BP 신경망](BED_POSTURE_PAPERS.md#p19) | **본문 미확인 · 판단 제외** |
| <a id="p20"></a>P20 | [MediaPipe + CNN + LSTM](BED_POSTURE_PAPERS.md#p20) | IR 영상의 4자세 분류 |
| <a id="p21"></a>P21 | [HypnoPose](BED_POSTURE_PAPERS.md#p21) | HigherHRNet + CBAM·상체 9관절 |
| <a id="p22"></a>P22 | [상체·머리 자세 분류](BED_POSTURE_PAPERS.md#p22) | SleePose-FRCNN-Net |
| <a id="p23"></a>P23 | [U-Net + MobileNetV3](BED_POSTURE_PAPERS.md#p23) | 사람 분할 후 3자세 영상 분류 |
| <a id="p25"></a>P25 | [물리 시뮬레이션 기반 낙상 위험](BED_POSTURE_PAPERS.md#p25) | 13관절 → MLP·합성/실제 평가 |
| <a id="p30"></a>P30 | [단일 IR 카메라 전이학습](BED_POSTURE_PAPERS.md#p30) | 밤샘 4자세·빈 침대 판별 |
| <a id="p31"></a>P31 | [RGB·열화상 앙상블](BED_POSTURE_PAPERS.md#p31) | 이불 조건 5자세 분류 |
| <a id="p32"></a>P32 | [IRS·CPM·HOG](BED_POSTURE_PAPERS.md#p32) | 마네킹 관절·방향 보정 |
| <a id="p33"></a>P33 | [Bodies at Rest](BED_POSTURE_PAPERS.md#p33) | 압력→3D·합성 PressurePose |
| <a id="p34"></a>P34 | [전신 회전 동작 기반 가림 대응](BED_POSTURE_PAPERS.md#p34) | **본문 미확인 · 판단 제외** |
| <a id="p35"></a>P35 | [다중 센서 자세·형상 융합](BED_POSTURE_PAPERS.md#p35) | 2020 공개판 본문 확인 / **2022 최종판 본문 미확인** |
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

공식 API·라이브러리 문서와 후보 가이드의 추가 연구 S11·S12는 [기술 후보 비교의 출처](TECHNOLOGY_CANDIDATES.md#sources)에 모았습니다. 이 자료들은 위 P01–P37 색인 37편에 포함하지 않습니다.

새 논문은 우선 서지 후보로 등록하며 **본문 확인 전까지 사실 판단과 기술·모델 선정 근거에서 제외**합니다. 원문을 확보한 경우에만 판본·절·표, 입력 장비, 정답 출처, 자료 분할, 결과의 제한을 근거와 함께 기록합니다. 설치·모델 채택·성능 재현 여부는 [진행 현황](../PROJECT_STATUS.md)에서 관리합니다.


<a id="new-papers-2026-10-29"></a>
## 2026-10-29 추가 조사 · MediaPipe·침대 영역·다중 카메라 신규 문헌 8편

사용자 요청에 따라 신규 문헌을 이 문서 아래에 모았습니다. **위 P01–P37의 2026-10-26 집계와 별도로 관리하는 추가 조사 목록**입니다. N01–N08은 이 절의 식별자이며 기존 P 번호를 변경하지 않습니다. 기존 BlazePose(P05), GHUM(P26), MediaPipe 프레임워크(P29), CNN·LSTM 수면 자세 연구(P20)는 중복 등록하지 않았습니다.

SciSpace·Consensus로 후보를 검색하고 공개 원문을 대조한 앞선 조사 결과를 기록합니다. 이번 문서 추가는 새 원문 재검증이나 자체 실험이 아닙니다. **관련 방법 본문을 확인한 공개판 4편, 본문 일부 발췌만 확인한 1편, 본문 미확인 서지 후보 3편**으로 구분합니다. 논문 성능의 재현·모델 채택·침대 환경 적합성 검증은 수행하지 않았습니다.

### 신규 목록 한눈에 보기

| ID | 논문 | 확인 상태 |
|---|---|---|
| [N01](#n01) | MediaPipe 스테레오 3D 복원 평가 · Dill 외, 2024 | 출판 본문 §2 일부 발췌 확인; 전체 방법·결과 검증 전 |
| [N02](#n02) | Learnable Triangulation · Iskakov 외, 2019 | 공개 arXiv PDF 방법·Figure 1·가중 삼각측량 식 확인 |
| [N03](#n03) | Grounding DINO · Liu 외, 2023 공개 | arXiv v4 §3 확인 |
| [N04](#n04) | SAM 2 · Ravi 외, 2024 공개 | arXiv v1 §3–4 확인 |
| [N05](#n05) | 평면 기반 카메라 보정 · Zhang | Microsoft 기술보고서 §2.2·§3 확인; 학술지 최종판 미대조 |
| [N06](#n06) | 앉은 자세의 MLP·KAN 비교 · Carneros-Prado 외, 2024 | **본문 미확인 · 서지 후보 · 사실 판단 제외** |
| [N07](#n07) | MediaPipe 자세 평가 비교 · Ferraris 외, 2025 | **본문 미확인 · 서지 후보 · 사실 판단 제외** |
| [N08](#n08) | MediaPipe 스테레오 복원의 시점 각도 평가 · Dill 외, 2024 | **본문 미확인 · 서지 후보 · 사실 판단 제외** |

<a id="n01"></a>
### N01 · MediaPipe 스테레오 3D 복원 평가

**제목:** Accuracy Evaluation of 3D Pose Reconstruction Algorithms Through Stereo Camera Information Fusion for Physical Exercises with MediaPipe Pose  
**서지:** Sebastian Dill 외, 2024, *Sensors*, 24(23), 7772.  
**링크:** [DOI: 10.3390/s24237772](https://doi.org/10.3390/s24237772) · [출판사](https://www.mdpi.com/1424-8220/24/23/7772) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11644880/)

**확인 범위:** 앞선 조사에서 검색 도구가 제공한 출판 본문 §2.1–2.4 일부 발췌를 읽었습니다. 원문 직접 열기는 접근 제한이 있었으므로 전체 방법·실험표를 검증한 논문으로 집계하지 않습니다. 성능 수치와 우수성 판단은 제외합니다.

**확인한 발췌 내용:** 두 영상에 각각 MediaPipe를 적용하고 2D 관절과 에피폴라 기하·삼각측량으로 3D를 복원하는 구성, 스쿼트 촬영 및 마커 기반 비교, 단안 3D 등과 비교하는 평가 항목을 설명합니다. 여기까지는 발췌 확인 범위이며 전체 조건의 완결성을 보증하지 않습니다.

**프로젝트 연결 제안:** 현재 양쪽 라벨 일치 방식에서 관절 관측 결합으로 확장하기 위한 우선 원문 확보 대상입니다. 전체 본문 확인 전 기술 선정 근거로 사용하지 않습니다. 스쿼트 결과를 침대 자세 정확도로 전용하지 않으며, 사전 스테레오 보정이 없다는 표현을 시간 정렬·카메라 기하·대응점 확인이 불필요하다는 뜻으로 해석하지 않습니다.

**남은 확인:** 전체 복원 절차, 좌표 스케일과 정답 정렬, 필터의 미래 프레임 사용, 결과표·오차 단위, 코드와 데이터 접근 조건.

<a id="n02"></a>
### N02 · 관절별·시점별 가중치를 이용한 삼각측량

**제목:** Learnable Triangulation of Human Pose  
**서지:** Karim Iskakov, Egor Burkov, Victor Lempitsky, Yury Malkov, ICCV 2019, pp. 7718–7727.  
**링크:** [학회 서지](https://openaccess.thecvf.com/content_ICCV_2019/html/Iskakov_Learnable_Triangulation_of_Human_Pose_ICCV_2019_paper.html) · [확인한 공개 PDF](https://arxiv.org/pdf/1905.05754)

**확인 범위:** 앞선 조사에서 제공된 9쪽 arXiv 공개 PDF의 방법 설명, Figure 1, 식 (3)–(4). URL에 버전이 고정되지 않아 v 번호는 확정하지 않았으며, ICCV 최종판 전체와 동일하다고 주장하지 않습니다. 재현 시 사용 판본을 고정해야 합니다.

**확인한 방법:** 알려진 카메라 파라미터와 여러 시점의 2D 관절을 사용합니다. 단순히 모든 관측을 동일하게 취급하는 대신 카메라·관절별 학습된 가중치를 삼각측량에 반영합니다.

**프로젝트 응용 제안:** 어깨·골반·무릎마다 잘 보이는 카메라가 다른 경우, 관절 단위 품질을 고려하는 결합 방식의 참고 자료입니다. 현재 라벨 일치 기준선과 별도로 비교해야 합니다.

**제약:** MediaPipe 전용 연구가 아닙니다. 학습된 가중치를 MediaPipe visibility로 바꾼 구현은 별도 변형이며 논문 재현으로 부를 수 없습니다. 카메라 보정·동일인 대응·시간 정렬·재투영 오차 검증이 필요합니다. 침대 환경 성능과 실시간 처리 비용은 미검증입니다.

<a id="n03"></a>
### N03 · 침대 후보 위치 검출을 위한 Grounding DINO

**제목:** Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection  
**서지:** Shilong Liu 외, 2023 최초 공개.  
**링크:** [arXiv 서지](https://arxiv.org/abs/2303.05499) · [확인한 v4 본문](https://arxiv.org/html/2303.05499v4)

**확인 범위:** arXiv v4 §3, 입력 영상·텍스트와 출력 상자·명사구의 관계. 학회 최종판 전체 검증과 구분합니다.

**확인한 방법:** 영상과 텍스트를 입력받아 대상의 상자와 대응하는 텍스트 정보를 출력하는 검출 구조입니다.

**프로젝트 응용 제안:** bed 또는 mattress를 입력해 침대 후보 상자를 구하고, 영역 분할·수동 보정으로 연결하는 실험을 제안합니다. 최초 자동 영역 설정과 재인식의 앞단 후보입니다.

**제약:** 침대 전체 상자는 매트리스 윗면 네 모서리와 다릅니다. 논문의 일반 검출 결과는 우리 침대의 검출 정확도가 아닙니다. 침대·매트리스·이불·사람이 섞이는 사례에서 원하는 영역 정의와 실제 검출 품질을 따로 확인해야 합니다.

<a id="n04"></a>
### N04 · 침대 경계 분할·보정에 응용할 SAM 2

**제목:** SAM 2: Segment Anything in Images and Videos  
**서지:** Nikhila Ravi 외, 2024 공개.  
**링크:** [arXiv 서지](https://arxiv.org/abs/2408.00714) · [확인한 v1 본문](https://arxiv.org/html/2408.00714v1)

**확인 범위:** arXiv v1 §3–4의 프롬프트 기반 영상 분할 과제와 모델 설명. 후속 판본 전체 검증과 구분합니다.

**확인한 방법:** 점·상자·마스크로 대상을 지정하거나 수정하고, 영상의 다른 프레임으로 분할 결과를 전파하는 구조를 제시합니다.

**프로젝트 응용 제안:** 침대 후보 상자 또는 사용자 클릭으로 경계를 분할하고 즉시 수동 보정하는 흐름을 검토할 수 있습니다. 세션 중 카메라가 고정되는 조건에서는 시작 시 설정과 필요 시 재인식을 먼저 비교합니다.

**제약:** 대상 분할은 매트리스 평면의 기하 복원과 다릅니다. 사람이 가린 영역까지 전체 침대가 정확히 복원된다고 가정하지 않습니다. 이불·침대 프레임·매트리스 중 무엇을 영역으로 삼는지 정하고, 분할 마스크와 기존 네 점 영역의 연결을 별도로 검증해야 합니다.

<a id="n05"></a>
### N05 · 평면과 영상의 좌표 관계·카메라 보정

**제목:** A Flexible New Technique for Camera Calibration  
**서지:** Zhengyou Zhang. 학술지 서지: *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 22(11), 1330–1334, 2000.  
**링크:** [학술지 DOI: 10.1109/34.888718](https://doi.org/10.1109/34.888718) · [확인한 Microsoft 기술보고서](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr98-71.pdf)

**확인 판본:** MSR-TR-98-71, 표지의 1998년 작성 및 2008-08-13 최종 수정 표기가 있는 22쪽 공개 PDF. §2.2의 평면 호모그래피, §3의 보정 절차를 확인했습니다. 2000년 학술지 최종판 본문은 별도 대조하지 않았습니다.

**확인한 방법:** 평면 패턴의 영상 관측을 이용해 카메라 내부 파라미터를 구하고 렌즈 왜곡을 고려하는 보정 방법입니다. 평면과 영상 사이의 호모그래피 관계를 설명합니다.

**프로젝트 응용 제안:** 현재 수동 네 점과 단위 정사각형 사이의 변환을 이해하고, 향후 다중 카메라 보정을 설계하는 기초 자료입니다.

**제약:** 자동 침대 검출 논문이 아닙니다. 네 점으로 영상 좌표를 변환한 것만으로 카메라 전체 보정이나 3D 복원이 완료되지 않습니다. 침대 평면 위에 있지 않은 머리·어깨의 영상점을 변환한 값을 실제 침대 위 위치나 높이로 해석하지 않습니다.

<a id="n06"></a>
### N06 · 앉은 자세 분류 연구 후보 — 본문 미확인

**제목:** A Comparison Between Multilayer Perceptrons and Kolmogorov-Arnold Networks for Multi-Task Classification in Sitting Posture Recognition  
**서지:** David Carneros-Prado 외, 2024, *IEEE Access*, 12, 180198–180209.  
**링크:** [DOI: 10.1109/ACCESS.2024.3510034](https://doi.org/10.1109/ACCESS.2024.3510034) · [저자 연구실 안내](https://mamilab.eu/journal_article/a-comparison-between-multilayer-perceptrons-and-kolmogorov-arnold-networks-for-multi-task-classification-in-sitting-posture-recognition/) · [연관 데이터 공개 안내](https://zenodo.org/records/14230872)

**상태:** 서지와 공개 안내만 확인했습니다. 논문 방법·실험 본문은 충분히 확보하지 못했습니다. 초록의 구조·참가자 수·분할·성능 주장은 채택하지 않으며 기술 선정 근거에서 제외합니다. 원문 확보 후 방법·실험 절과 데이터 이용 조건을 확인할 후보입니다.

<a id="n07"></a>
### N07 · MediaPipe 자세 평가 연구 후보 — 본문 미확인

**제목:** A Deep Dive Into MediaPipe Pose for Postural Assessment: A Comparative Investigation  
**서지:** Claudia Ferraris, Gianluca Amprimo, Serena Cerfoglio, Luca Vismara, Valentina Cimolin, 2025, *IEEE Access*.  
**링크:** [DOI: 10.1109/ACCESS.2025.3643126](https://doi.org/10.1109/ACCESS.2025.3643126)

**상태:** SciSpace·Consensus의 서지를 확인했으나 방법·실험 본문을 검증하지 못했습니다. 초록의 2D/3D 성능·모델 복잡도별 결과를 사실 판단이나 모델 선택에 사용하지 않습니다. 저자명 최종 표기와 출판본을 포함해 원문 대조가 필요합니다.

<a id="n08"></a>
### N08 · MediaPipe 다중 시점 각도 연구 후보 — 본문 미확인

**제목:** Evaluation of Accuracy and Angle Dependency of 3D Pose Estimation through Stereo Camera Information Fusion with MediaPipe Pose  
**서지:** Sebastian Dill, Maurice Rohr, Gökhan Güney, Christoph Hoog Antink, 2024.  
**링크:** [DOI: 10.23919/FUSION59988.2024.10706380](https://doi.org/10.23919/FUSION59988.2024.10706380)

**상태:** SciSpace의 서지 후보이며 방법·실험 본문은 미확인입니다. 최적 카메라 각도·자료 구성·성능을 판단 근거로 사용하지 않습니다. N01과 제목·DOI가 다른 연구로 구분하되, 두 연구의 방법과 자료 중복 여부는 원문 확보 후 확인해야 합니다.

### 프로젝트 적용을 검토할 순서

아래는 조사에 따른 **제안**이며 구현 승인·모델 선정·성능 실증 결과가 아닙니다.

1. N01 전체 원문을 확보하고 기존 [GHUM(P26)](SKELETON_TECHNOLOGY_PAPERS.md#p26)과 함께 단안 추정 3D와 다중 시점 복원의 좌표·평가 조건을 정리합니다.
2. N03·N04의 역할을 침대 후보 검출과 경계 분할로 나누고, 매트리스 윗면 확인·네 점 수동 보정·기존 좌표 변환으로 연결하는 소규모 비교를 설계합니다.
3. 실제 동시 촬영 자료에서 단일 시점 A/B·현재 라벨 일치·관절 결합을 비교합니다. N02의 관절별 가중치와 N05의 기하는 참고하되 가림·정렬 오차·재투영 오차·보류율도 함께 평가합니다.
4. N06–N08은 본문 확보 전까지 서지 후보로 유지합니다. 자세 시계열 연구가 필요할 때 기존 [P20](BED_POSTURE_PAPERS.md#p20)을 참고하되 수치 불일치 제한을 유지합니다.

**검증 경계:** 문헌의 공개판과 확인 절만 기록했습니다. 코드 실행, 데이터 다운로드·재현, 실제 카메라 평가, 모델·데이터 이용 허가 검토는 수행하지 않았습니다. 추가 목록은 상단의 기존 37편 검증 집계를 소급 변경하지 않습니다.
