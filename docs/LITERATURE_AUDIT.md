# 논문 원문 재검토 기록

**검토일:** 2026-10-25 (한국 시간)  
**대상:** [침대 자세 문서](BED_POSTURE_PAPERS.md) 17편 + [스켈레톤 기술 문서](SKELETON_TECHNOLOGY_PAPERS.md) 12편 = 29편  
**검토 방식:** 저장소의 주장과 원문의 방법·자료·분할·지표·결과·한계를 대조. 필요한 표는 PDF를 렌더링하여 확인하고 혼동행렬의 합계와 비율을 재계산.

## 판정 요약

- **29편의 서지·분류를 점검했습니다.** 확인한 범위에서 존재하지 않는 논문이나 임의로 만든 제목·DOI는 발견하지 못했습니다.
- **26편은 본문의 관련 절·표까지 직접 다시 대조했습니다.** 공개 저자판·프리프린트를 사용한 경우를 아래에 명시했습니다. 모든 논문의 최종 출판본 전체를 한 줄씩 검증했다는 뜻은 아닙니다.
- **P11·P12·P19의 본문은 확보하지 못했습니다.** 초록과 서지만 확인된 상태를 유지합니다.
- **기존 정리에 실제 누락이 있었습니다.** P25의 실제 영상 추가 평가를 빠뜨린 설명을 수정했습니다. P22의 상체·머리 지표, P01의 3D 정성 평가 범위도 명확히 했습니다.
- **논문 내부의 불일치도 있습니다.** P02·P03·P04·P20·P21은 지표·수치·집계 단위에 주의가 필요합니다. P23은 전체 정확도 산술은 맞지만 클래스별 지표 명칭이 불명확합니다.

‘본문 대조’는 **원문에 그런 방법·결과가 적혀 있음을 확인**했다는 뜻입니다. 코드·가중치 실행, 원자료 검사, 통계 재분석, 연구 부정행위 판정은 수행하지 않았습니다. 원문의 숫자가 일관되지 않을 때 어느 값이 진짜인지 임의로 선택하지 않았습니다.

## 이번에 수정하거나 추가한 내용

### 1. P25: 실제 영상 평가 누락 — 기존 요약 수정

[원문 PDF](https://www.mdpi.com/1424-8220/26/10/2979/pdf)의 **§4.6, Tables 6–7, p.12**에는 FallVision의 실제 영상 100개를 선별한 추가 평가가 있습니다. 각 영상의 한 프레임에 사람이 13개 관절을 표시하고, 합성 자료로 학습한 MLP를 재학습 없이 평가합니다.

| 평가 조건 | AUROC | F1 |
|---|---:|---:|
| 합성 시험 50,000개, Table 3 | 0.9755±0.0006 | 0.9138±0.0015 |
| 실제 영상 100개의 수작업 관절, Table 7 | 0.8175±0.0188 | 0.7497±0.0265 |

기존 문서의 ‘실제 자료를 검증하지 않았다’는 취지의 설명은 부정확했습니다. **실제 자료 평가는 있지만, 자동 관절 검출부터 수행한 전체 시스템 시험이나 실제 병동의 전향적 검증은 아닙니다.**

### 2. P03 BedEye: 정답 건수와 정확도 불일치 — 원문 주의

[공개 본문](https://www.researchgate.net/publication/390513208_BedEye_A_Bed_Exit_and_Bedside_Fall_Warning_System_Based_on_Skeleton_Recognition_Technology_for_Elderly_Patients) **§IV-B**에는 4,000개 중 3,943개 정분류와 전체 정확도 97.4%가 함께 쓰였습니다.

`3943 / 4000 × 100 = 98.575%`

같은 분모의 전체 정확도라면 서로 맞지 않습니다. 97.4%를 98.575%로 확정 교체하지 않고 불일치를 기록했습니다. **§IV-C의 병원 평가 97.72%는 별도 실험**입니다. 좌표 규칙과 LSTM은 비교 대안이고, 병원 시험에 선택된 것은 좌표 규칙이라는 기존 정리는 본문과 일치합니다.

### 3. P02: 지표 정의뿐 아니라 일부 혼동행렬도 주의

[원문 PDF](https://www.mdpi.com/2076-3417/12/6/3087/pdf) **§4.3.1**의 accuracy 식 `TP/(TP+FP)`는 통상 precision 정의입니다. 또한 **Table 5, p.9**의 남성 환자 3D 행 중 supine은 `7.90+78.00+41.10=127.00%`입니다. 여성 환자의 2D+depth와 3D 블록은 표시된 행 값이 같은데 요약 accuracy는 78.31%와 73.39%로 다릅니다.

PDF 이미지로 확인한 표기 문제이며 어느 셀이 오타인지 추정해 고치지 않았습니다. 기존 문서가 인용한 **코 중심 2D+depth의 96.32% / 46.55% / 78.31%**는 Tables 4–5에 실제로 있으나, 저자의 보고값으로 한정합니다.

### 4. P20: 표·혼동행렬 충돌 — 기존 경고 재확인

[원문 PDF](https://thesai.org/Downloads/Volume16No10/Paper_13-A_New_Hybrid_Algorithm_for_Vision_Based_Sleep_Posture_Analysis.pdf) **pp.137–138**의 Tables I–III와 Figs.4–5를 이미지로 다시 확인했습니다.

| 근거 | 재계산·보고값 | 판단 |
|---|---|---|
| 주간 Fig.4 | (12+11+9+9)/42 = 97.62% | Table III의 96.4%와 다름 |
| 주간 Table I의 recall·표본 수 | 약 (11+11+8+8)/42 = 90.48% | Fig.4 및 Table III와 다름 |
| 야간 Fig.5 | (11+11+8+9)/42 = 92.86% | 보고 92.8%에 가깝지만 전체 정합성을 보장하지 않음 |
| 야간 우측 recall | Fig.5: 9/9=100%; Table II: 88.9% | 반올림으로 설명할 수 없는 차이 |

반복 실험 평균 등 서로 다른 수치를 연결하는 설명을 확인하지 못했습니다. **모델 우위나 확정 정확도의 근거로 사용을 보류**합니다.

### 5. P04·P21·P23: 판본·집계·지표 구분

- **P04:** [공개 게재승인본 텍스트](https://www.researchgate.net/publication/412247821_RGB-only_In-bed_Pose_Estimation_under_Occlusion_via_Image_Reconstruction)의 외부 자료 하체 MPJPE 개선은 초록 35%, Table 8·결론 37%입니다. AOT-GAN 악화도 초록 21%, 본문·결론 13%로 다릅니다. 공개 페이지에 여러 사본이 있으며 최종 편집본의 수정 여부는 확인하지 못했습니다. 단일 개선율 확정은 보류합니다.
- **P21:** [공개 본문](https://pmc.ncbi.nlm.nih.gov/articles/PMC13357495/)의 초록 0.088/0.326과 Table 5의 Stage 4 0.090/0.335는 다릅니다. Table 6의 5-fold mAP 0.120±0.031도 별도 평가입니다. Table 2는 89회 기록인데 Table 3의 ‘Number of recordings’는 합계 198로, 본문의 움직임 구간 수와 같습니다. Table 3의 단위 표기에 혼동 가능성이 있어 **기록 89회와 구간 198개를 구별**합니다.
- **P23:** [출판사 본문](https://journals.sagepub.com/doi/full/10.3233/ATDE251143)의 Table 2는 행=예측, 열=실제입니다. `(85+99+97)/300=93.67%`가 맞고 recall은 85/99/97%입니다. Table 3의 클래스별 ‘accuracy’ 85/90.83/88.18과 같은 지표로 취급하지 않습니다.

### 6. 해석·정리 보완

- **P01:** §4.6에 사전학습 3D 모델의 정성적 실험이 있습니다. 다만 SLP가 3D 관절 정답을 제공하지 않는다는 점과 정적 자세 자료라는 점은 그대로입니다.
- **P13:** Table II의 실제 가림 개선은 PCK 0.313→0.336입니다. 비가림 SLP에서는 0.810→0.798로 하락하므로 ‘실제 자료에서 항상 개선’으로 요약하면 안 됩니다.
- **P22:** §4.3.2의 91.67%는 **상체 분류**, 머리 분류는 94.37%입니다. 약 0.7초/영상 추론과 촬영 20 FPS의 구별을 유지합니다.
- **P05:** 이전 작업에서 수정한 Full 10·Lite 31 FPS가 맞는지 PDF Table 1과 각주를 다시 확인했습니다. 102·312 FPS는 각주를 숫자에 붙여 읽은 과거 요약 오류입니다.
- **분류:** 17+12편과 고유 ID 29개를 유지합니다. 스켈레톤 문서 비교표에서 빠져 있던 P26–P29 네 항목을 추가했습니다. 행동 분류·리뷰를 관절 추출기로 오인하지 않도록 구분을 유지합니다.

## 29편별 확인 범위

‘대조’는 관련 본문과 기존 요약의 일치 여부를 점검했다는 뜻입니다. ‘주의’나 ‘보류’가 있는 행은 그 제한을 우선 적용합니다. 링크는 이번에 확인한 원문 또는 서지이며, 상세 설명은 각 ID의 문서로 연결됩니다.

| ID | 논문·판본 | 직접 확인한 위치 | 결과·남은 제한 |
|---|---|---|---|
| [P01](BED_POSTURE_PAPERS.md#p01) | [SLP, arXiv v1](https://arxiv.org/pdf/2008.08735v1) | §4.1, §4.4, §4.6, 단일 입력 표 | 데이터·분할·PCKh 대조; 3D 정답 없음과 정성 실험을 구분 |
| [P02](BED_POSTURE_PAPERS.md#p02) | [Applied Sciences 2022 PDF](https://www.mdpi.com/2076-3417/12/6/3087/pdf) | §3–4, Tables 3–9; pp.8–9 시각 확인 | 방법·환자 분리 대조; 지표·표 불일치 주의 |
| [P03](BED_POSTURE_PAPERS.md#p03) | [BedEye 공개 본문](https://www.researchgate.net/publication/390513208_BedEye_A_Bed_Exit_and_Bedside_Fall_Warning_System_Based_on_Skeleton_Recognition_Technology_for_Elderly_Patients) | §III, §IV-B/C, Tables 6–14 | 좌표 규칙/LSTM·병원 평가 구분; 건수/정확도 충돌 |
| [P04](BED_POSTURE_PAPERS.md#p04) | [공개 게재승인본 텍스트](https://www.researchgate.net/publication/412247821_RGB-only_In-bed_Pose_Estimation_under_Occlusion_via_Image_Reconstruction) | 복원 학습, EWHA_BED, Table 8, Appendix | 방법 대조; 초록/본문 표기 차이·최종판 미대조 |
| [P05](SKELETON_TECHNOLOGY_PAPERS.md#p05) | [BlazePose v1](https://arxiv.org/pdf/2006.10204v1) | §2–4, Table 1·각주 시각 확인 | 2D·평가 17점·10/31 FPS 확인 |
| [P06](SKELETON_TECHNOLOGY_PAPERS.md#p06) | [RTMPose v2](https://arxiv.org/pdf/2303.07399v2) | §3, §4.3, Tables 11–12 | 모델 단독/검출 포함 지연과 장치 조건 대조 |
| [P07](SKELETON_TECHNOLOGY_PAPERS.md#p07) | [ST-GCN v2](https://arxiv.org/pdf/1801.07455v2) | Network architecture, §4, 결과표 | 9층·Kinetics 2D/NTU 3D·행동 지표 대조 |
| [P08](SKELETON_TECHNOLOGY_PAPERS.md#p08) | [2s-AGCN v3](https://arxiv.org/pdf/1805.07694v3) | §5.1–5.3, Tables 1–4 | 두 흐름·분할·성능 대조; 기준선 학습 변경 주의 |
| [P09](SKELETON_TECHNOLOGY_PAPERS.md#p09) | [PoseC3D v2](https://arxiv.org/pdf/2104.13586v2) | §3–4, Appendix D, Table 13 | 히트맵 시계열·FineGYM 정답 박스 조건 대조 |
| [P10](SKELETON_TECHNOLOGY_PAPERS.md#p10) | [TCN v2](https://arxiv.org/pdf/1803.01271v2) | §3–5, Table 1, Appendix A | 구조·MNIST 결과 대조; 침대 성능 근거 아님 |
| [P11](BED_POSTURE_PAPERS.md#p11) | [EMBC 2020 / PubMed](https://pubmed.ncbi.nlm.nih.gov/33018968/) | 서지·초록만 | **본문 보류**; 99.2/5.7%의 분모·시간 창·분할 미검증 |
| [P12](BED_POSTURE_PAPERS.md#p12) | [EMBC 2019 / PubMed](https://pubmed.ncbi.nlm.nih.gov/31946570/) | 서지·초록만 | **본문 보류**; 구체 관절/침대 검출기·실험 조건 미검증 |
| [P13](BED_POSTURE_PAPERS.md#p13) | [BlanketGen2-Fit3D v1](https://arxiv.org/pdf/2501.12318v1) | §III-D, Tables I–III | 정답 박스·사람 분할·실제/합성 결과 대조; 2026 최종판 미대조 |
| [P14](BED_POSTURE_PAPERS.md#p14) | [BlanketSet v3](https://arxiv.org/pdf/2210.03600v3) | 수집·정성 평가, Tables I–II | RGB/IR/깊이·405영상·303965프레임·29응답 대조 |
| [P15](BED_POSTURE_PAPERS.md#p15) | [In-Bed Pose Estimation Review v1](https://arxiv.org/pdf/2402.00700v1) | 기술·데이터 절, Table I | 리뷰의 SLP 3D/Video 및 BlanketSet LWIR 표기는 원 데이터 논문과 구분 |
| [P16](BED_POSTURE_PAPERS.md#p16) | [2023 저자 프리프린트](https://www.researchgate.net/publication/372799787_Deep_Learning_Methods_for_Single_Camera_Based_Clinical_In-bed_Movement_Action_Recognition) | 임상 문제, §VI-C/D, Table III | 전이 학습·오류 전파·환자 분리 권고 대조; 2024 최종판 미대조 |
| [P17](BED_POSTURE_PAPERS.md#p17) | [SaccpaNet 정식 호 PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/115296/1/Tam_SaccpaNet_Separable_Atrous.pdf) | §III–VI, Fig.1, Tables I–III | 150명·4200쌍·OpenPose 라벨 대조; 참가자 독립 분할 확정 불가 |
| [P18](SKELETON_TECHNOLOGY_PAPERS.md#p18) | [Fall Detection Review 저자 승인본](https://www.researchgate.net/publication/373286744_Advances_in_Skeleton-Based_Fall_Detection_in_RGB_Videos_from_Handcrafted_to_Deep_Learning_Approaches) | §IV, Tables 3–4 | 추정기·전처리·창/stride·라벨·평가 분리 대조; 당시 라이브러리 설명 |
| [P19](BED_POSTURE_PAPERS.md#p19) | [CCET 2020 서지·목차](https://www.proceedings.com/content/056/056128webtoc.pdf) | 저자·제목·p.99, DOI 기록 | **본문 보류**; BP 입력·추정기·독립 시험 미검증 |
| [P20](BED_POSTURE_PAPERS.md#p20) | [IJACSA 2025 PDF](https://thesai.org/Downloads/Volume16No10/Paper_13-A_New_Hybrid_Algorithm_for_Vision_Based_Sleep_Posture_Analysis.pdf) | §III, Tables I–III, Figs.4–5 시각 확인 | 처리 구조 대조; **성능 수치 충돌 미해소** |
| [P21](BED_POSTURE_PAPERS.md#p21) | [HypnoPose 공개 본문](https://pmc.ncbi.nlm.nih.gov/articles/PMC13357495/) | Methods·Results, Tables 2–6; Europe PMC XML 병행 | 9출력·59/15명·5-fold 대조; 초록/표·집계 단위 차이 |
| [P22](BED_POSTURE_PAPERS.md#p22) | [Sensors 2022 PDF](https://www.mdpi.com/1424-8220/22/5/2014/pdf) | §3, §4.1–4.5, Tables 3·10–12 | iSP 사람 분리·야간 동일인 분할·상체/머리·0.7초 구분 |
| [P23](BED_POSTURE_PAPERS.md#p23) | [U-Net/MobileNetV3 출판사 본문](https://journals.sagepub.com/doi/full/10.3233/ATDE251143) | §2.4–2.6, Tables 1–3 | 총 정확도 산술 일치; 클래스 지표·사람 독립 분할은 주의 |
| [P24](SKELETON_TECHNOLOGY_PAPERS.md#p24) | [DSSM 저자기관 PDF](https://da.lib.kobe-u.ac.jp/da/kernel/90007346/90007346.pdf) | §3–4, Tables 1–2, Figs.7–8 | BiLSTM·정상 성능·잡음/무작위 프레임 제거 조건 대조 |
| [P25](BED_POSTURE_PAPERS.md#p25) | [Sensors 2026 PDF](https://www.mdpi.com/1424-8220/26/10/2979/pdf) | §3, §4.2–4.6, Tables 1–3·6–7; p.12 시각 확인 | **실제 영상 추가 평가 누락 정정**; 자동 관절/현장 검증은 없음 |
| [P26](SKELETON_TECHNOLOGY_PAPERS.md#p26) | [GHUM Holistic v1](https://arxiv.org/pdf/2206.11678v1) | §2–4, Tables 1–4 | fitting 정답·깊이 순서·요가·별도 Lifter 평가 대조 |
| [P27](SKELETON_TECHNOLOGY_PAPERS.md#p27) | [OpenPose/PAF v2](https://arxiv.org/pdf/1611.08050v2) | §2–3, Tables 1–4, Fig.9 | PAF·75.6/61.8 지표·19명 8.8 FPS 조건 대조 |
| [P28](SKELETON_TECHNOLOGY_PAPERS.md#p28) | [HRNet v1](https://arxiv.org/pdf/1902.09212v1) | §3–4, Tables 1·6 | 74.4/76.3 AP·반복 융합·입력/사전학습 조건 대조 |
| [P29](SKELETON_TECHNOLOGY_PAPERS.md#p29) | [MediaPipe v1](https://arxiv.org/pdf/1906.08172v1) | §3–6 | 타임스탬프·실행·Tracer/Visualizer 대조; 관절 모델 성능 논문 아님 |

### 후보 비교 문서의 추가 논문 2편

29편 목록 외에 [기술 후보 가이드](TECHNOLOGY_CANDIDATES.md)가 추가로 인용한 아래 두 논문도 관련 본문을 확인했습니다. 기존 ID나 29편의 개수를 변경하지 않았습니다.

| 가이드 ID | 원문 | 확인 위치·판정 |
|---|---|---|
| S11 | [Seeing Under the Cover v3](https://arxiv.org/pdf/1907.02161v3) | §2.1–2.2, §4.1: 이불 투과가 아닌 접촉 열전달, 바로/좌/우 누움, 천장 촬영, 조건 변경 후 약 10–20초 대기 설명과 일치 |
| S12 | [Privacy-Preserving In-Bed Pose Monitoring v1](https://arxiv.org/pdf/2202.10704v1) | §2–3, §4.5, Table 6: HRNet 융합·DanaLab→SimLab 평가 확인. Visible–LWIR는 LWIR 단독과 95.1로 같아 모든 조합이 개선된 것은 아님 |

후보 가이드의 API·제품 기능 전체를 재감사한 것은 아닙니다. 위 표는 추가 인용된 논문의 방법·시험 조건에 대한 확인입니다.

## 본문 미확보 3편의 처리

P11·P12는 PubMed와 저자기관 서지, P19는 학회 목차·DOI 및 저자/제목 기록을 대조했습니다. IEEE 원문 접근과 공개 저자 사본 검색으로도 이번 검토에서 본문을 확보하지 못했습니다.

- 추정기 이름, 참여자 수, 분할, 시간 창, 경고 선행 시간 등을 추측해 채우지 않습니다.
- 초록의 성능은 **초록의 저자 보고값**이라고 표시하며 본문 검증된 비교 수치로 사용하지 않습니다.
- 원문 확보 후 Methods, Experimental setup, Results의 표·정답 정의부터 추가 확인합니다.

## 결과를 개발에 사용하는 기준

관절 위치 지표(PCK/PCKh/AP), 자세 분류, 동작 검출, 사전 위험 예측을 서로 다른 과제로 유지합니다. RGB와 IR/LWIR/깊이/압력을 구분하고, 추정 3D·수작업 관절·센서 좌표·합성 관절의 정답 출처를 명시합니다. 정답 인물 박스, 참가자 중복, 제한된 조건의 시험은 실제 자동 검출·새 환자·장시간 경고 성능으로 확대하지 않습니다.

이번 문헌 검토 결과로 특정 모델을 채택하거나 프로젝트 요구사항을 변경하지 않았습니다.
