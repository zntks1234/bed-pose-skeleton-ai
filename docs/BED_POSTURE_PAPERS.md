# 침대 위 자세 구분을 위한 논문

[논문 안내](LITERATURE_REVIEW.md) · [스켈레톤 기술 논문](SKELETON_TECHNOLOGY_PAPERS.md) · [기술 후보 비교](TECHNOLOGY_CANDIDATES.md) · [프로젝트 홈](../README.md)

**기준일: 2026-10-25 · 17편 · 관련 본문 확인 14편 · 본문 미확보 3편**

침대 자세·이탈·가림·데이터셋·리뷰를 다룹니다. 침대에 특화한 관절 추정 연구도 응용 목적에 따라 이 문서에 포함합니다.

> **확인 범위:** 원문 또는 공개 저자판의 방법·자료·분할·결과를 대조했습니다. P11·P12·P19는 서지·초록만 확인했습니다. 확인한 판본·절·표와 남은 제한은 각 항목에 표시합니다. 코드 실행이나 성능 재현은 수행하지 않았습니다.

## 빠른 안내

- **자세·이탈 설계:** [P02](#p02) 상체 특징, [P03](#p03) 침대 관계·상태 전이, [P25](#p25) 위험도와 실제 영상 평가.
- **데이터·실험 조건:** [P01](#p01) SLP, [P14](#p14) BlanketSet, [P21](#p21) 실제 수면 관절 추정.
- **가림·대안 방식:** [P04](#p04)·[P13](#p13) 복원/합성, [P17](#p17) 깊이, [P22](#p22)·[P23](#p23) 영상 직접 분류.

## 논문 한눈에 보기

상태의 ‘주의’는 본문에서 확인한 제한을 뜻합니다. ‘본문 미확보’ 3편을 제외한 항목은 관련 본문을 확인했습니다.

| 논문 | 기술·역할 | 확인 상태·핵심 제한 |
|---|---|---|
| [P01 · SLP](#p01) | 다중 입력 데이터·관절 벤치마크 | 본문 확인 |
| [P02 · RGB-D 상체 관절 + XGBoost](#p02) | 3자세 분류·지원자/환자 비교 | 지표·표 주의 |
| [P03 · BedEye](#p03) | 좌표 규칙과 LSTM·침대 이탈 | 수치 주의 |
| [P04 · RGB 복원 + 관절 추정](#p04) | MAE/AOT-GAN·가림 대응 | 판본·수치 주의 |
| [P11 · LSTM 침대 이탈 검출](#p11) | 자세·상대 위치의 시간 분석 | 본문 미확보 |
| [P12 · 침대 위치 + 자세 추정](#p12) | 이탈 관련 상태 예측 | 본문 미확보 |
| [P13 · BlanketGen2-Fit3D](#p13) | 합성 이불·ViTPose-B 학습 | 본문 확인·v1 기준 |
| [P14 · BlanketSet](#p14) | RGB/IR/깊이 데이터·HybrIK 평가 | 본문 확인 |
| [P15 · 침대 자세 추정 리뷰](#p15) | 입력·모델·데이터 정리 | 원 데이터 논문과 대조 |
| [P16 · 임상 침대 동작 리뷰](#p16) | 3D MoCap·행동 인식·전이 학습 | 본문 확인·2023 저자판 |
| [P17 · SaccpaNet](#p17) | 깊이 관절 추정 + 자세 분류 | OpenPose 유래 라벨 |
| [P19 · 스켈레톤 + BP 신경망](#p19) | 관절 특징 기반 수면 자세 | 본문 미확보 |
| [P20 · MediaPipe + CNN + LSTM](#p20) | IR 영상의 4자세 분류 | 보고 수치 불일치 |
| [P21 · HypnoPose](#p21) | HigherHRNet + CBAM·상체 9관절 | 수치·집계 단위 주의 |
| [P22 · 상체·머리 자세 분류](#p22) | SleePose-FRCNN-Net | 동일인 야간 분할 주의 |
| [P23 · U-Net + MobileNetV3](#p23) | 사람 분할 후 3자세 영상 분류 | 클래스별 지표 주의 |
| [P25 · 물리 시뮬레이션 기반 낙상 위험](#p25) | 13관절 → MLP·합성/실제 평가 | 실제 평가는 수작업 관절 |

## 논문별 상세

<a id="p01"></a>
### P01 · SLP

**Simultaneously-Collected Multimodal Lying Pose Dataset: Towards In-Bed Human Pose Monitoring under Adverse Vision Conditions**

**저자·출처:** Shuangjun Liu 외. arXiv, 2020. 정식 게재 제목은 *Simultaneously-Collected Multimodal Lying Pose Dataset: Enabling In-Bed Human Pose Monitoring*, IEEE TPAMI 45(1), 1106–1118, 2023(온라인 2022).  
**링크:** [프리프린트](https://arxiv.org/abs/2008.08735) · [DOI: 10.1109/TPAMI.2022.3155712](https://doi.org/10.1109/TPAMI.2022.3155712) · [저자 데이터·코드 안내](https://github.com/ostadabbas/SLP-Dataset-and-Code)  
**확인 범위:** 본문 확인 — [arXiv v1 PDF](https://arxiv.org/pdf/2008.08735v1) §4.1·§4.4·§4.6, 데이터 구성과 단일 입력 벤치마크 표. 정식 게재본과 초기 프리프린트의 제목을 구분합니다.

- **문제·처리 흐름:** 누운 자세를 RGB·LWIR·깊이·압력으로 동시 수집한 데이터셋입니다. 데이터 공개만 하는 연구가 아니라 HRNet-W32, SimpleBaseline(ResNet-50), ChainedPredictions, PoseAttention, PyraNet, StackedHourglass의 관절 추정 실험도 수행합니다.
- **데이터·정답:** 가정 환경 102명과 모의 병원 환경 7명, 총 109명입니다. 모집 대상은 대학생으로, 109명의 입원 환자 자료가 아닙니다. 각 사람에게 3종 기본 자세 × 15개 변형 × 3종 가림 조건을 수집해 입력 종류별 14,715개 표본과 14개 관절 정보를 제공합니다.
- **학습·시험:** 가정 환경 첫 90명을 학습, 나머지 12명을 시험에 사용하고 모의 병원 7명에서 환경 변화도 평가합니다. 모델은 100 epochs 학습합니다. 주요 단일 입력 벤치마크는 어두움·가림 때문에 **RGB를 제외하고 LWIR·깊이·압력**을 비교합니다.
- **결과·검증:** PyraNet의 PCKh@0.5는 LWIR 94.2%, 압력 90.7%, 깊이 96.6%로 보고됩니다. 이는 머리 크기로 정규화한 **관절 위치 지표**이며 RGB 자세 분류 정확도가 아닙니다.
- **3D 범위:** §4.6은 사전학습 3D 모델의 정성적 예시도 제시하지만, SLP 자체에 3D 관절 정답은 없다고 명시합니다. ‘3D 연구가 전혀 없다’와 ‘3D 정답을 제공하는 데이터셋이다’는 모두 부정확합니다.
- **한계·활용 제안:** 정적 자세 및 가림 평가에 활용합니다. 이탈·복귀 연속 이벤트의 정답 자료나 고령 환자 일반화 검증으로 해석하지 않습니다.


<a id="p02"></a>
### P02 · RGB-D 상체 관절 + XGBoost

**Posture Monitoring for Health Care of Bedridden Elderly Patients Using 3D Human Skeleton Analysis via Machine Learning Approach**

**저자·출처:** Jui-Chiu Chiang 외. *Applied Sciences*, 12(6), 3087, 2022.  
**링크:** [출판사 원문 / DOI: 10.3390/app12063087](https://www.mdpi.com/2076-3417/12/6/3087) · [PDF](https://www.mdpi.com/2076-3417/12/6/3087/pdf)  
**확인 범위:** 본문 확인 — §3.1–3.3, §4.1–4.3, Tables 3–5 및 7–9.

- **기술·처리 흐름:** Intel RealSense D435의 RGB에서 **OpenPose**로 18개 관절을 검출한 뒤 코·목·양쪽 어깨 4개를 선택합니다. 대응 깊이를 33×33 영역의 trilateral filter로 보정하고, 2D 좌표+깊이 또는 카메라 3D 좌표로 만든 12개 특징을 **XGBoost**에 입력합니다. 코를 원점으로 이동한 특징도 비교합니다. 출력은 바로 누움·좌측·우측 3종입니다.
- **장비·자료:** 높이 174 cm, 수직 방향에서 약 10° 기울인 RGB-D 카메라를 사용합니다. 지원자 20명(남 15·여 5)의 표본 3,154개와 실제 와상 고령 환자 2명(남 1,525개·여 1,056개)의 자료를 구분합니다.
- **분할:** Setting 1은 지원자 19명 학습·1명 시험을 반복하는 사람 단위 평가입니다. Setting 2는 지원자로 학습하고 두 환자로 시험합니다. Settings 3–5는 같은 환자 자료 일부가 학습에도 들어가므로 새로운 환자에 대한 성능과 구별해야 합니다.
- **보고 결과:** 코 중심으로 정규화한 2D+depth 표현에서 지원자 평가의 보고값 96.32%가 환자 남 46.55%·여 78.31%로 낮아집니다(Tables 4–5). 따라서 초록의 ‘95% 이상’을 임상 일반화 성능으로 쓰면 안 됩니다.
- **지표 주의:** §4.3.1은 accuracy를 TP/(TP+FP)로 정의하는데 이는 통상 precision 식입니다. 수치는 저자의 보고값으로 인용하며 지표 명칭의 혼동을 함께 기록합니다.
- **표 주의:** PDF Table 5(p.9)의 남성 환자 3D supine 행은 7.90+78.00+41.10=127%입니다. 여성 환자의 2D+depth·3D 블록은 표시된 행 값이 같은데 요약 수치는 78.31%·73.39%로 다릅니다. PDF 이미지에서도 확인한 불일치이며, 원자료 없이 어느 셀을 고쳐야 하는지 결정하지 않습니다.
- **한계·활용 제안:** 일부 상체 관절만 사용하는 기준선 설계에 유용합니다. 깊이 센서가 필요하고 실제 환자는 2명뿐입니다. MediaPipe의 추정 z로 동일 결과를 얻는다고 가정하지 않습니다.


<a id="p03"></a>
### P03 · BedEye

**BedEye: A Bed Exit and Bedside Fall Warning System Based on Skeleton Recognition Technology for Elderly Patients**

**저자·출처:** Liang-Bi Chen 외. *IEEE Access*, 13, 60403–60423, 2025.  
**링크:** [IEEE 원문](https://ieeexplore.ieee.org/document/10949079/) · [DOI: 10.1109/ACCESS.2025.3558004](https://doi.org/10.1109/ACCESS.2025.3558004)  
**확인 범위:** 본문 확인 — [저자 공개 원문](https://www.researchgate.net/publication/390513208_BedEye_A_Bed_Exit_and_Bedside_Fall_Warning_System_Based_on_Skeleton_Recognition_Technology_for_Elderly_Patients), §III의 자세 판단·LSTM 구성, §IV-B/C, Tables 6–14.

- **기술·흐름:** Jetson Xavier NX에서 경량 OpenPose 계열로 관절을 추출합니다. **관절 좌표의 기하 규칙**과 **LSTM 시계열 분류**는 비교하는 두 대안입니다. 임상 시험에는 좌표 기반 규칙을 선택했으며, LSTM이 최종 임상 모델이라는 설명은 부정확합니다.
- **시간 모델:** 어깨·골반·무릎의 중심 좌표 3쌍을 특징으로, 약 15.4 FPS의 5초·77프레임 창을 LSTM에 입력합니다. 누움·몸 일으킴·가장자리 앉음·이탈을 구분합니다.
- **실험:** 주간·야간 시험 자료와 병원 시험을 분리합니다. 병원 시험에는 간호사 26명, 고령 지원자 11명, 입원 환자 11명이 참여합니다. 지정된 연속 동작 150회와 분해 동작 594회를 수행했습니다.
- **결과·검증:** §IV-C의 병원 평가 보고값은 97.72%입니다. 주간·야간 자세 인식 값 및 초록의 97.4%와 동일한 시험으로 합치지 않습니다. 장기간 자연 발생 낙상 감소를 입증한 임상시험으로 해석할 수도 없습니다.
- **수치 주의:** §IV-B에는 4,000개 중 3,943개 정분류와 ‘overall accuracy 97.4%’가 함께 적혀 있습니다. 단순 비율은 **98.575%**이므로 같은 전체 정확도라면 일치하지 않습니다. 이를 97.72%의 병원 평가와도 구분하며, 원자료 없이 어느 숫자가 맞는지 결정하지 않습니다.
- **활용 제안:** 침대 상대 위치와 상태 전이 규칙의 직접 참고 자료입니다. 우리 데이터에서 경고 지연·환자별 성능·시간당 오경보를 별도로 측정해야 합니다.


<a id="p04"></a>
### P04 · RGB 복원 + 관절 추정

**RGB-Only in-Bed Pose Estimation Under Occlusion via Image Reconstruction**

**저자·출처:** Sewon Kim, Hyebin Kim, Seohyun Lee, Taeyong Lee. *IEEE Access*, 14, 128244–128261, 2026.  
**링크:** [DOI: 10.1109/ACCESS.2026.3723433](https://doi.org/10.1109/ACCESS.2026.3723433) · [저자 소속기관의 초록·서지](https://pure.ewha.ac.kr/en/publications/rgb-only-in-bed-pose-estimation-under-occlusion-via-image-reconst/)  
**확인 범위:** 본문 확인 — [저자 게재 승인본](https://www.researchgate.net/publication/412247821_RGB-only_In-bed_Pose_Estimation_under_Occlusion_via_Image_Reconstruction), §II–III·결과·§XI Appendix. 최종 편집본과 차이가 있을 수 있습니다.

- **기술·흐름:** 가림 영역을 **MAE(ViT-Large)** 또는 **AOT-GAN**으로 복원한 뒤 OpenPose·ViTPose·HRNet을 각각 적용합니다. 부록의 실제 이불 실험은 **YOLOv8-seg**로 마스크를 생성하며, 학습 라벨은 SAM/SAM2 보조 후 사람이 확인합니다. YOLO Pose를 사용했다는 뜻은 아닙니다.
- **학습:** SLP의 비가림 RGB에 인공 마스크를 씌워 복원을 학습합니다. 사람 단위로 87명·3,915장 학습 / 22명·990장 검증을 나눕니다. MAE 입력은 224×224, 200 epochs, batch 32, AdamW입니다.
- **외부 자료:** EWHA_BED는 55명의 비가림 595장·부분 가림 595장으로 구성됩니다. 개인정보 때문에 비공개입니다. 합성 마스크 실험과 부록의 실제 이불 검출 실험을 구분해야 합니다.
- **결과·검증:** MAE와 ViTPose 조합의 개선을 보고하지만 AOT-GAN 조합은 외부 자료에서 악화되기도 합니다. 복원 영상의 자연스러움만으로 관절 정확도를 판단할 수 없습니다.
- **판본·수치 주의:** 공개 게재승인본 추출 텍스트에서 외부 자료의 하체 MPJPE 개선은 초록 35%, Table 8·결론 37%로 다릅니다. AOT-GAN 악화도 초록 21%, 본문·결론 13%로 적혀 있습니다. 공개 페이지에 여러 사본이 있고 최종 편집본의 수정 여부는 미확인이라 단일 개선율을 확정하지 않습니다.
- **활용 제안:** 자동 이불 마스크 생성까지 포함한 후속 가림 실험 후보입니다. 복원한 신체를 실제 관측 정답으로 저장하거나, 정적 이미지 결과를 연속 이탈 탐지 성능으로 바꾸어 해석하지 않습니다.


<a id="p11"></a>
### P11 · LSTM 침대 이탈 검출

**Bed Exit Action Detection Based on Patient Posture with Long Short-Term Memory**

**저자·출처:** Madoka Inoue, Ryo Taguchi. IEEE EMBC, 2020, 4390–4393.  
**링크:** [DOI: 10.1109/EMBC44109.2020.9175619](https://doi.org/10.1109/EMBC44109.2020.9175619) · [PubMed 초록](https://pubmed.ncbi.nlm.nih.gov/33018968/)  
**확인 범위:** **본문 검증 보류** — DOI·PubMed 초록 및 저자 소속기관 서지까지 확인했습니다. IEEE PDF에 접근하지 못했고 공개 저자 원문도 확보하지 못했습니다.

- **확인된 기술:** 단안 영상의 자세·상대 위치 정보를 LSTM에 연결해 침대 이탈 동작을 검출한다는 연구입니다. 초록에는 검출 99.2%와 false detection 5.7%가 보고됩니다.
- **검증하지 못한 내용:** 앞단 관절 추정기의 정확한 모델, 참가자 수, 학습·시험 사람 분리, 시간 창, 경고 시점, false detection의 분모와 집계 단위입니다. 이를 OpenPose·MediaPipe 또는 시간당 오경보로 임의 해석하지 않습니다.
- **판정:** 위 두 수치는 **초록의 저자 보고값이며 본문 검증된 성능이 아닙니다**. 수치 비교·모델 선정의 근거로 사용을 보류합니다.
- **활용 제안:** 자세와 침대 상대 위치의 시간 변화를 함께 쓰는 아이디어만 참고합니다. 원문 확보 후 Methods의 특징 추출, Experimental setup의 분할, Results의 혼동행렬·이벤트 정의를 확인해야 합니다.


<a id="p12"></a>
### P12 · 침대 위치 + 자세 추정

**Bed-Exit Prediction Applying Neural Network Combining Bed Position Detection and Patient Posture Estimation**

**저자·출처:** Madoka Inoue, Ryo Taguchi, Taizo Umezaki. IEEE EMBC, 2019.  
**링크:** [DOI: 10.1109/EMBC.2019.8857233](https://doi.org/10.1109/EMBC.2019.8857233) · [PubMed 초록](https://pubmed.ncbi.nlm.nih.gov/31946570/)  
**확인 범위:** **본문 검증 보류** — DOI·PubMed 초록 확인. 출판사 전체 원문이나 공개 저자 사본은 확보하지 못했습니다.

- **확인된 기술:** 침대 위치 검출과 환자 자세 추정을 결합한 신경망으로 침대 이탈 관련 상태를 예측합니다. 신체 자세만 보는 방식에 침대와의 상대 위치를 추가한다는 점이 핵심입니다.
- **검증하지 못한 내용:** 침대 검출기·관절 추정기 이름, 신경망 층 구조, 참가자 구성, 실제 환자/모의 동작 비율, 독립 시험 여부, 가장자리 상태와 최종 이탈의 정답 기준입니다.
- **판정:** ‘침대 위치+자세+신경망’ 수준까지만 기술을 확정합니다. 다른 논문이 인용한 구현이나 모델명을 이 논문의 직접 사용 기술로 옮기지 않습니다. 임상 유효성 또는 이탈 전 경고 시간을 확정할 근거도 부족합니다.
- **활용 제안:** 몸 중심 정규화와 침대 중심 정규화를 분리해야 한다는 설계 참고 자료로 둡니다. 원문 확보 후 좌표계·라벨·시간 분할부터 검증합니다.


<a id="p13"></a>
### P13 · BlanketGen2-Fit3D

**BlanketGen2-Fit3D: Synthetic Blanket Augmentation Towards Improving Real-World In-Bed Blanket Occluded Human Pose Estimation**

**저자·출처:** Tamás Karácsony, João Carmona, João Paulo Silva Cunha. arXiv:2501.12318, 2025. 2026년 *Computer Vision and Image Understanding* 출판 기록도 있으나, 아래 방법 설명은 공개 프리프린트 기준입니다.  
**링크:** [프리프린트](https://arxiv.org/abs/2501.12318) · [본문 v1](https://arxiv.org/html/2501.12318v1) · [출판 기록](https://www.sciencedirect.com/science/article/pii/S1077314226003425)  
**확인 범위:** 본문 확인 — arXiv:2501.12318v1, 데이터 생성·§III-D·Table II. 2026년 최종 출판본의 모든 변경 사항을 검증한 것은 아닙니다.

- **기술·흐름:** Fit3D의 인체 표현과 물리 기반 이불 합성으로 BlanketGen2-Fit3D를 만듭니다. 합성 프레임 1,217,312개를 이용해 **ViTPose-B(약 86M 파라미터, 256×192 입력, MMPose)**를 미세 조정합니다. 합성기는 영상 추론 단계의 필수 모듈이 아니라 학습 데이터 생성 도구입니다.
- **분할·학습:** Fit3D의 S3·4·5·7·8·9를 학습, S10을 시험, S11을 검증에 사용합니다. backbone을 고정하고 head를 학습한 뒤 전체를 미세 조정하는 조건을 비교합니다. 평가에는 관절 정답에서 만든 인물 박스와 30픽셀 여유 영역을 사용합니다.
- **외부 평가:** SLP의 가림 9,810장·비가림 4,905장을 별도 평가에 사용합니다. 합성 자료의 개선과 실제 이불 자료로 옮겨 갔을 때의 개선을 구분합니다.
- **결과·검증:** Table II의 FT-Mixed는 합성 시험에서 PCK 0.977을 보고하고, 실제 가림 자료는 **0.313→0.336 PCK, 즉 2.3%p** 개선입니다. 비가림 SLP에서는 0.810→0.798로 낮아집니다. 2.3% 상대 개선이나 모든 관절의 동일 개선으로 바꾸지 않습니다. 골반 관절 정의의 데이터 간 차이도 결과에 영향을 줍니다.
- **한계·활용 제안:** 실제 검출기가 만든 박스와 우리 카메라에서도 효과가 유지되는지 확인해야 합니다. 합성 이불 사전학습 후보로 두고 실제 자료만 학습한 기준선과 동일 조건으로 비교합니다.


<a id="p14"></a>
### P14 · BlanketSet

**BlanketSet – A Clinical Real-World In-Bed Action Recognition and Qualitative Semi-Synchronised Motion Capture Dataset**

**저자·출처:** João Carmona, Tamás Karácsony, João Paulo Silva Cunha. IEEE ENBENG, 2023, 116–119(프리프린트 2022).  
**링크:** [DOI: 10.1109/ENBENG58165.2023.10175335](https://doi.org/10.1109/ENBENG58165.2023.10175335) · [논문](https://arxiv.org/abs/2210.03600) · [확인한 본문 v3](https://arxiv.org/pdf/2210.03600v3) · [공식 데이터 안내](https://rdm.inesctec.pt/dataset/nis-2022-004)  
**확인 범위:** 본문 확인 — arXiv:2210.03600v3, 수집 절차 및 §III-E의 정성 평가.

- **자료·장비:** Azure Kinect로 RGB·IR·깊이를 수집합니다. 14명, 405개 영상, 303,965프레임과 8개 동작 시퀀스를 다룹니다. 이불 유무 등에 따라 동작을 반복하는 semi-synchronised 방식으로, 서로 다른 촬영의 모든 순간이 정확히 일치하는 것은 아닙니다.
- **사용 기술:** 데이터셋만 소개하는 데 그치지 않고, **HybrIK**의 사전학습 모델과 BlanketGen으로 미세 조정한 모델의 인체 mesh 결과도 비교합니다.
- **평가·검증:** 정량적인 관절 좌표 정답 대신 29명의 응답자가 결과를 0–10점으로 평가하는 정성 비교를 사용합니다. 시각적 평가 점수나 통계적 차이를 관절 정확도(PCK/MPJPE)로 바꾸어 해석할 수 없습니다.
- **한계·활용 제안:** 이불 조건을 바꾼 반복 촬영과 동작 수집 설계에 유용합니다. 대응 영상이 있다는 사실만으로 가려진 프레임의 완전한 좌표 정답이나 이탈 이벤트 라벨이 제공된다고 가정하지 않습니다. 실제 자료 이용은 공식 데이터 안내의 접근 조건을 따라야 합니다.


<a id="p15"></a>
### P15 · 침대 자세 추정 리뷰

**In-Bed Pose Estimation: A Review**

**저자·출처:** Ziya Ata Yazıcı, Sara Colantonio, Hazım Kemal Ekenel. HCCS'24 / PerCom 워크숍, 2024(arXiv 수록본).  
**링크:** [논문](https://arxiv.org/abs/2402.00700) · [본문](https://arxiv.org/html/2402.00700v1)  
**확인 범위:** 본문 확인 — arXiv:2402.00700v1, §II–IV 및 Tables I–II. 데이터 관련 내용은 P01·P14 원문과 교차 확인했습니다.

- **연구 범위:** RGB·열영상·깊이·압력 등 침대 자세 입력, 공개 데이터, 단일/복합 입력 모델을 정리한 리뷰입니다. 하나의 새 관절 추정기를 제안하거나 여러 모델을 같은 조건으로 재학습한 벤치마크가 아닙니다.
- **기술 내용:** CNN, 전통 특징, autoencoder, 도메인 적응, 합성 데이터, 영상 복원 및 attention 기반 입력 융합 등을 다룹니다. PCK와 MPJPE 같은 관절 지표와 데이터별 차이를 파악하는 데 적합합니다.
- **교차 검증:** Table I의 SLP에 대한 ‘3D pose/video’ 표기는 SLP 원문의 정적 자료·2D 관절 주석 설명과 맞지 않습니다. SLP의 3D 정성 실험과 3D 관절 정답 제공 여부는 별개입니다. 또한 리뷰의 BlanketSet LWIR 표기는 원 데이터 논문의 RGB·IR·깊이 설명과 구분합니다. 데이터 설명은 [P01](#p01)·[P14](#p14) 원 논문을 우선합니다.
- **한계·활용 제안:** 연구 지도를 얻는 출발점으로 사용하되 참가자 수, 입력 종류, 정답 차원, 점수는 각 원 논문에서 다시 확인합니다. 서로 다른 연구의 수치를 하나의 성능 순위로 만들지 않습니다.


<a id="p16"></a>
### P16 · 임상 침대 동작 리뷰

**Deep learning methods for single camera based clinical in-bed movement action recognition**

**저자·출처:** Tamás Karácsony, László Attila Jeni, Fernando De la Torre, João Paulo Silva Cunha. *Image and Vision Computing*, 143, 104928, 2024.  
**링크:** [DOI: 10.1016/j.imavis.2024.104928](https://doi.org/10.1016/j.imavis.2024.104928) · [출판사](https://www.sciencedirect.com/science/article/pii/S0262885624000313) · [저자 공개 PDF](https://humansensing.cs.cmu.edu/sites/default/files/Kara%CC%81csony%20et.%20al.%20_revision.pdf)  
**확인 범위:** 본문 확인 — [2023년 저자 프리프린트](https://www.researchgate.net/publication/372799787_Deep_Learning_Methods_for_Single_Camera_Based_Clinical_In-bed_Movement_Action_Recognition)의 임상 과제·전이 학습 논의 및 Table III. 2024년 최종판 전체를 대조한 것은 아닙니다.

- **연구 범위:** 간질 모니터링 등 침대 위 임상 동작을 중심으로 단일 카메라 3D motion capture와 행동 인식을 검토합니다. 새로운 모델의 단일 정확도를 제시하는 실험 논문이 아닙니다.
- **세부 제안:** 일반 이미지 학습 → 자세·인체 표현 학습 → 영상 움직임 추출 → 일반 행동 학습 → 임상 행동 미세 조정처럼 단계별 전이 학습을 설명합니다(Table III). **관절/움직임 추출과 임상 행동 분류를 분리**하는 구성을 논의합니다.
- **근거·한계:** 카메라 시점, 이불·의료진 가림, 야간 IR, 저해상도, 드문 임상 라벨을 별도 문제로 다룹니다. 두 단계 방식은 모듈 교체가 쉽지만 앞단 관절 오류가 뒷단 분류에 전파된다는 단점도 명시합니다.
- **검증·활용 제안:** 환자별로 학습·검증·시험을 분리하라는 본문 권고를 자체 실험에 반영합니다. 이 리뷰를 특정 모델의 임상 성공 증거로 사용하지 않습니다.


<a id="p17"></a>
### P17 · SaccpaNet

**SaccpaNet: A Separable Atrous Convolution-Based Cascade Pyramid Attention Network to Estimate Body Landmarks Using Cross-Modal Knowledge Transfer for Under-Blanket Sleep Posture Classification**

**저자·출처:** Andy Yiu-Chau Tam 외. *IEEE Journal of Biomedical and Health Informatics*, 온라인 공개 2024, 정식 호 30(2), 1593–1604, 2026.  
**링크:** [DOI: 10.1109/JBHI.2024.3432195](https://doi.org/10.1109/JBHI.2024.3432195) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/39042546/)  
**확인 범위:** 본문 확인 — [PolyU 공개 논문 PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/115296/1/Tam_SaccpaNet_Separable_Atrous.pdf), pp.1593–1604, §III–VI, Fig.1 및 Table III.

- **기술·흐름:** 깊이 영상에서 관절을 추정하는 JCE와, 깊이·추정 관절을 이용하는 자세 분류기 SPC를 연결합니다. JCE는 SegNeXt 계열 encoder, dilation 1·2·5·7의 separable atrous convolution과 cascade pyramid attention, Hamburger decoder, soft-argmax를 사용합니다. SPC는 residual CNN 구조이며 ResNet-152+SVM 등과 비교합니다.
- **정답의 출처:** RGB의 **OpenPose 18관절 좌표를 대응 깊이 영상에 옮겨 학습·평가 라벨로 사용**합니다. COCO-WholeBody 사전학습과 cross-modal transfer가 포함됩니다. 시험 시 입력이 깊이 영상이라는 점과 학습 라벨이 RGB 추정기에서 왔다는 점을 구분해야 합니다.
- **자료·분할:** RealSense D435i로 건강한 참가자 150명, 7자세 × 비가림/3종 이불의 4조건, 총 4,200쌍을 수집합니다. 비율은 학습 64%·시험 20%·검증 16%입니다. 확인한 분할 설명만으로 **참가자 독립 분할을 확정할 수 없습니다**.
- **결과·검증:** JCE의 PCK@0.1은 0.6518이며 박스 대각선으로 정규화합니다. OpenPose 유래 라벨과의 일치도라는 한계가 있습니다. 7클래스와 두 엎드림 변형을 합친 6클래스 F1은 서로 다른 과제입니다. 본문의 클래스 평균·가중 평균·이불 조건별 수치를 섞어 하나의 개선폭으로 계산하지 않습니다.
- **활용 제안:** 깊이 방식과 RGB 방식의 차이를 이해하는 비교 자료입니다. 원문이 사용한 pseudo-label을 독립적인 수작업 관절 정답과 동일시하지 않습니다.


<a id="p19"></a>
### P19 · 스켈레톤 + BP 신경망

**Skeleton-Based Sleep Posture Recognition with BP Neural Network**

**저자·출처:** Haozhou Lyu, Jinglan Tian. IEEE CCET, 2020, 99–104.  
**링크:** [학회 목차](https://www.proceedings.com/content/056/056128webtoc.pdf) · [DOI: 10.1109/CCET50901.2020.9213125](https://doi.org/10.1109/CCET50901.2020.9213125) · [IEEE](https://ieeexplore.ieee.org/document/9213125/)  
**확인 범위:** **본문 검증 보류** — IEEE/DOI 서지와 공개 초록 수준. IEEE PDF는 접근되지 않았고 공개 저자 사본을 확보하지 못했습니다.

- **확인된 기술:** 스켈레톤 특징을 BP(backpropagation) 신경망으로 분류하는 수면 자세 연구입니다. BP는 학습 방식이며 관절을 검출하는 제품·라이브러리 이름이 아닙니다.
- **검증하지 못한 내용:** 관절 추정기(OpenPose/MediaPipe 등), 정확한 특징식, 은닉층·활성화 함수, 데이터 규모, 참가자 분리, 이불·조명별 성능입니다.
- **판정:** 제목과 관련 논문만으로 앞단 모델을 추정하지 않습니다. 구체 구조 및 성능의 재현 근거로 사용하는 것은 보류합니다.
- **활용 제안:** 단순 특징+작은 신경망 기준선의 조사 대상으로 유지합니다. 본문 확보 후 특징 정의와 분할을 확인해야 비교 실험에 정확히 포함할 수 있습니다.


<a id="p20"></a>
### P20 · MediaPipe + CNN + LSTM

**A New Hybrid Algorithm for Vision-Based Sleep Posture Analysis Integrating CNN, LSTM and MediaPipe**

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
### P21 · HypnoPose

**Towards automated joint detection in sleep studies: bridging clinical insight and artificial intelligence**

**저자·출처:** Alexis Dorier 외. *Sleep*, 49(7), zsag108, 2026. HypnoPose 연구.  
**링크:** [DOI: 10.1093/sleep/zsag108](https://doi.org/10.1093/sleep/zsag108) · [출판사 원문](https://academic.oup.com/sleep/article/49/7/zsag108/8659223) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/42007581/) · [공개 본문](https://pmc.ncbi.nlm.nih.gov/articles/PMC13357495/)  
**확인 범위:** 본문 확인 — 출판사 공개 논문(PMC/Europe PMC)의 Dataset/Network training/Evaluation, Tables 2·3·5·6. 표의 단일 분할 결과와 교차 검증을 구분했습니다.

- **기술·흐름:** **HigherHRNet에 CBAM attention**을 여러 위치에 넣어 비교합니다. COCO에서 상체 관절로 사전학습한 뒤 수면 영상으로 미세 조정합니다. AlphaPose·ViTPose는 비교 모델입니다.
- **자료·관절:** 74명, 89회 기록, 198개 움직임 구간, 4,419개 주석 프레임입니다. 자료의 수작업 관절 주석은 13개지만 **모델 출력은 머리·양쪽 어깨/팔꿈치/손목/골반의 9개 상체 관절**입니다. ‘13개를 출력하는 모델’로 쓰지 않습니다.
- **분할·학습:** 주 실험은 사람을 분리한 59명 학습·15명 검증입니다. 긴 영상의 과대표집을 줄이도록 사람별 프레임 수를 조정합니다. 선택한 Stage 4 모델은 별도로 **참가자 단위 5-fold 교차 검증**을 수행합니다. 사전학습·미세 조정은 각각 50 epochs입니다. 표본 추출 후 시간적 연속성이 유지되지 않아 프레임 단위 자세 추정 자료입니다.
- **결과·검증:** Table 5의 Stage 4는 mAP 0.090, AP@0.5 0.335입니다. Table 6의 5-fold 결과는 mAP **0.120±0.031**, AP@0.5 **0.350±0.032**입니다. 초록의 0.088/0.326과 본문 표 값에는 차이가 있으므로 이 문서는 표 번호와 평가 설정을 붙여 인용합니다.
- **집계 단위 주의:** Table 3의 ‘recordings’ 합계는 198로, Table 2의 기록 수 89와 다르고 본문의 움직임 구간 수와 같습니다. 89회 기록·198개 구간을 같은 단위로 합치지 않습니다.
- **한계·활용 제안:** 이 값은 OKS 기반 관절 위치 AP이며 자세 분류 정확도가 아닙니다. 실제 수면 환경에서 엄격한 관절 위치 추정이 여전히 어렵다는 근거입니다. 검출 실패·가림·카메라 시점별 성능과 판정 불가 구간을 함께 보고합니다.


<a id="p22"></a>
### P22 · 상체·머리 자세 분류

**A Vision-Based System for In-Sleep Upper-Body and Head Pose Classification**

**저자·출처:** Yan-Ying Li, Shoue-Jen Wang, Yi-Ping Hung. *Sensors*, 22(5), 2014, 2022.  
**링크:** [DOI: 10.3390/s22052014](https://doi.org/10.3390/s22052014) · [출판사](https://www.mdpi.com/1424-8220/22/5/2014) · [공개 원문](https://pmc.ncbi.nlm.nih.gov/articles/PMC8914692/)  
**확인 범위:** 본문 확인 — §3.1–3.2의 SleePose-FRCNN-Net, §4.1–4.3.2의 SLP·iSP·실제 수면 평가.

- **기술·흐름:** **SleePose-FRCNN-Net**은 ImageNet 사전학습 ResNet-50 backbone, RPN, RoI 특징, 머리·상체의 검출/분류 head를 쓰는 Faster R-CNN 계열 멀티태스크 모델입니다. 전신 관절을 먼저 얻는 MediaPipe 방식이 아닙니다.
- **자료·분할:** SLP는 90명 학습·12명 검증·모의 병원 7명 시험을 사용합니다. 자체 iSP 통제 촬영은 36명(남 29·여 7), 여러 자세 변형과 3종 덮개 조건입니다. 25명·15,000장 학습 / 11명·6,600장 시험으로 분리합니다.
- **실제 수면 평가:** 별도의 성인 4명 야간 자료에서 **상체 분류 91.67%, 머리 분류 94.37%**를 보고합니다(§4.3.2). 그러나 같은 사람의 서로 다른 수면 구간을 80/20으로 나눈 조건이므로 새로운 사람에 대한 91.67%로 해석하지 않습니다.
- **속도·검증:** RTX 2070에서 영상 한 장 처리 약 0.7초를 보고합니다. 수집 영상의 20 FPS를 추론 속도 20 FPS로 옮기면 안 됩니다. 머리 방향과 상체 방향의 결과 역시 구분해야 합니다.
- **한계·활용 제안:** 하체 가림 때 상체·머리 영상 특징을 쓰는 보조 기준선입니다. 머리를 돌린 상태를 몸 전체의 옆누움 또는 침대 이탈로 곧바로 바꾸지 않습니다.


<a id="p23"></a>
### P23 · U-Net + MobileNetV3

**Classification of In-Bed Sleeping Position using U-Net and MobileNetV3**

**저자·출처:** Jomlowe Andres D. Gaco, Cyrel O. Manlises. ICISPC 2025, *Advances in Transdisciplinary Engineering: Imaging, Signal Processing and Communications*, 174–184, 2025.  
**링크:** [출판사 원문 / DOI: 10.3233/ATDE251143](https://journals.sagepub.com/doi/full/10.3233/ATDE251143)  
**확인 범위:** 본문 확인 — 출판사 §2.4–2.6, Tables 1–3. 혼동행렬 합계와 지표를 직접 재계산했습니다.

- **기술·흐름:** Raspberry Pi 4·Camera Module 3 영상에서 **U-Net으로 사람 영역을 분할하고 MobileNetV3로 바로 누움·좌측·우측을 분류**합니다. 관절 추출 과정은 없습니다.
- **시험 조건:** 18–26세 지원자, 복잡하지 않은 배경, 이불 없는 조건입니다. 시험은 자세별 100장, 총 300장입니다. 참가자 수와 사람 단위 독립 분할은 확인한 설명만으로 확정하기 어렵습니다.
- **검증된 산술:** Table 2의 정분류는 85+99+97=281장으로 **281/300=93.67%**가 맞습니다. 행은 예측, 열은 실제 클래스이므로 바로 누움·좌측·우측 recall은 각각 **85%·99%·97%**입니다.
- **주의할 표기:** Table 3의 클래스별 ‘accuracy’ 85·90.83·88.18은 위 recall과 다릅니다. 정의가 분명하지 않으므로 이 문서는 혼동행렬에서 재계산한 recall을 별도 명칭으로 사용합니다.
- **활용 제안:** 영상 분류 기준선으로 참고합니다. 전체 정확도의 산술 일치는 이불·환자·새 참가자 일반화나 장시간 오경보까지 검증됐다는 뜻이 아닙니다.


<a id="p25"></a>
### P25 · 물리 시뮬레이션 기반 낙상 위험

**Fall-from-Bed Risk Prediction Using Physics-Based Bed Simulation**

**저자·출처:** Jaeyong Kim 외. *Sensors*, 26(10), 2979, 2026.  
**링크:** [출판사 / DOI: 10.3390/s26102979](https://www.mdpi.com/1424-8220/26/10/2979) · [PDF](https://www.mdpi.com/1424-8220/26/10/2979/pdf) · 서지·초록 대조 [1](https://consensus.app/papers/fallfrombed-risk-prediction-using-physicsbased-bed-kim-kim/2033f2b2108c5c459e76d3cfcd7b0bf2/?utm_source=chatgpt)  
**확인 범위:** 본문 확인 — §3.1–3.2, §4.2–4.6, Tables 1–3·6–7. §4.6과 Table 7은 PDF p.12의 실제 영상 추가 평가까지 확인했습니다.

- **자료·라벨:** **MuJoCo 3.4.0**의 humanoid와 침대를 구성하고 초기 자세에서 3초간 제어 없는 움직임을 계산합니다. 손 접촉을 제외한 신체의 바닥 접촉으로 낙상 이벤트를 정하고, 발생까지의 시간으로 할인한 연속 위험 라벨을 만듭니다. 주 실험은 시뮬레이터의 13개 관절을 침대 좌표의 2D로 투영·정규화합니다.
- **모델:** 26차원 좌표를 **MLP 26→256→128→1(ReLU, dropout 0.1)**에 입력해 위험도를 회귀합니다. CNN·GCN·RandomForestRegressor도 비교합니다. LSTM 비교 모델은 **시작 5프레임**을 쓰므로 단일 정적 자세 모델들과 입력 정보량이 다릅니다.
- **학습·시험:** 기본 비교는 균형화한 합성 표본 100,000개, 학습/검증 약 9:1, 별도 자세 균형 시험 50,000개입니다. 신경망은 MSE·Adam·학습률 0.001·batch 512·최대 50 epochs, seed 41–45를 사용합니다. 임계값은 검증 자료에서 선택합니다.
- **결과·검증:** Table 3의 MLP는 AUROC **0.9755±0.0006**, F1 **0.9138±0.0015**입니다. LSTM은 AUROC 0.9750±0.0008로 비슷합니다. 동일 시뮬레이션 분포의 결과이며 실제 병동 낙상 빈도를 반영한 시험이 아닙니다.
- **실제 영상 평가:** §4.6은 FallVision에서 침대 가장자리가 식별되는 영상 100개(낙상 50·비낙상 50)를 선별합니다. 각 영상의 한 프레임에 사람이 13개 관절을 표시하고 재학습 없이 MLP를 평가합니다. Table 7은 AUROC **0.8175±0.0188**, F1 **0.7497±0.0265**입니다.
- **한계·활용 제안:** 이 추가 실험도 영상에서 관절을 자동 검출한 전체 시스템 시험이나 실제 병동의 전향적 검증은 아닙니다. 침대 상대 위치 특징을 참고하되, 합성 점수·선별 영상 평가·현장 이탈 경고를 분리합니다.
