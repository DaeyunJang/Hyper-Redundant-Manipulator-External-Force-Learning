# 구현 및 실험 계획

상태 갱신: 2026-09-26 실제 학습/예측 구현 및 사용자 지정 실험을 시작했다.
현재 실행 규약은 README, configs/tip_force.json, configs/body_force.json 및
docs/ASSUMPTIONS.md가 우선한다. 아래는 초기 설계 계획이며 무부하 실측 교정 도구 등
일부 항목은 아직 미구현이다. 측정 결과는 results의 보고서를 따른다.

## 1. 설정으로 조합 선택

입력 registry는 configs/feature_catalog.json, 선택은 experiment.example.json으로 정의한다.
그룹을 고르면 입력 차원을 계산한다. 포함/제외에 따라 모델 코드를 고치지 않게 구현한다.

| 비교 이름 | 입력 그룹 | 차원 |
|---|---|---:|
| full | wire_length + loadcell_tension + relative_angle | 26 |
| without_angles | wire_length + loadcell_tension | 8 |
| without_tension | wire_length + relative_angle | 22 |
| angles_only | relative_angle | 18 |
| tension_only | loadcell_tension | 4 |
| with_velocities | full + wire_velocity + relative_angular_velocity | 48 |

정답은 Kalman/raw, 입력은 위 조합, 모델은 아래 후보 중 독립적으로 선택한다.
실험마다 선택한 열 순서/차원, 정답 소스, split, seed, 유효 샘플, 교정 파일 hash를 저장한다.
같은 비교에서 force 정답 소스까지 바꾸면 원인을 분리할 수 없으므로 별도 실험 축으로 취급한다.
하나의 summary에 다른 연구 자료가 있어도 이를 삭제하거나 전부 X에 넣지 않는다.

## 2. 무부하 분석 도구 — 반드시 구현할 기능

입력: 작업자가 무부하라고 확인한 세션/시간 구간, sensor/filter/offset/frame/units 정보.
약 1분은 초기 측정 후보이며 충분성을 보증하지 않는다. 다른 시점의 반복 측정과
알려진 작은 실제 힘으로 검증한다. 첫 N초 또는 ID0라는 이유만으로 무부하를 자동 확정하지 않는다.

출력 보고서와 calibration JSON에 다음을 포함한다.

- raw/Kalman 각각의 Fx/Fy/Fz 시계열·분포, count, 결측, 평균, 중앙값, 표준편차, min/max.
- 축별 절대 잔차의 99%, 99.5%, 99.9% 경험적 분위수와 시간 구간별 drift.
- 사용한 baseline, 포함/제외 구간, 실제 단위, 필터 설정, 교정 시각/파일 hash.
- 세 축을 동시에 판정할 때 실제 무부하 초과 비율 및 독립 검증 데이터의 오경보율.
- 임계값 후보와 적용 한계. 물리적 contact가 전혀 없다는 증명이 아닌 검출 기준이다.

기본 후보 방법: 알려진 무부하 자료에서 축별 median baseline b를 구하고,
`s(t)=max(|Fx-bx|, |Fy-by|, |Fz-bz|)`의 경험적 99.5백분위수를 공통 반폭 T 후보로 잡는다.
`|Fi-bi|<=T`가 세 축 모두 성립하면 below-threshold 후보. 한 시점에서 축을 취하는 max이지
전체 녹화의 최대치를 임계값으로 쓰는 방식이 아니다. 향후 axis-specific bands와
vector-norm 방법도 설정으로 선택 가능하게 한다. 방식별 물리적 의미를 혼용하지 않는다.

min/max는 요약용이지 기본 임계값이 아니다. 한 번의 spike/녹화 길이에 민감하다.
평균의 신뢰구간은 개별 샘플 잡음 범위가 아니므로 무부하 판정 경계로 사용하지 않는다.
3σ를 선택할 경우 분포 가정과 세 축 동시 오경보를 확인한다.
분위수도 해당 관측 자료의 경험적 수치일 뿐 다른 날 데이터에 같은 coverage를 보장하지 않는다.

실사용 기준은 noise 분포, 허용 오경보, 최소 필요한 힘 감도를 함께 보고 정한다.
T_off와 T_on 사이의 ambiguity band 또는 hysteresis를 옵션으로 지원한다.
임계값 주변/비정상값은 억지로 확정 위치 라벨을 만들지 않는다. threshold 값은
교정 결과에서 제공하며 기본 예시에 임의의 50 mN을 박아 넣지 않는다.

센서의 잔여 bias 보정은 이미 적용된 offset과 구분한다. 실제 탄성 케이블 장력이나
센서 자세에 따른 실험의 힘을 영점으로 지우지 않는다. 분리된 케이블로 분석한 noise는
부착 후 fixture 중량/장력까지 보정했다는 뜻이 아니다. 설치/온도/필터가 바뀌면 재검증한다.
기본 force 회귀 정답은 선택한 측정값을 보존한다. baseline 보정을 Y에도 적용하려면
명시적 옵션/물리적 근거/역변환 규약이 필요하며 무부하라는 이유로 hard-zero하지 않는다.

raw/Kalman의 서로 다른 noise와 지연을 따로 보고한다. 정답 소스를 바꿨는데 이전 소스의
교정값을 조용히 재사용하지 않는다. 더 촘촘한 센서 CSV를 분석할 수 있어도 실제 학습에
쓰는 summary 샘플링에서의 범위/오경보도 확인한다.

## 3. 작은 모델부터

최신 모델 선정: 사용자가 제공한 기존 model_zoo의 9개 구조를 참조한다.
[모델 검토 및 비교 계획](MODEL_COMPARISON.md)이 최신 비교 범위이며 아래 4개는
작은 기준 모델 후보로 유지한다. 소형 Transformer도 포함한다. 출력은 aligned XYZ
저장 부호를 유지하며 HRM 제어용 -1 변환은 제어 연결 단계에서만 적용한다.


아래는 초기 비교 모델이다. 최대 정확도 모델이라고 주장하는 선택이 아니다.
동일한 작은 출력 head를 붙이고 feature dimension을 동적으로 받는다.

| 모델 | 입력 형태 | 초기 구조 | default26→22의 대략 파라미터 |
|---|---|---|---:|
| MLP | B×D, 한 시점 | Linear(D,128)-ReLU-Linear(128,64)-ReLU | 13,142 |
| GRU | B×T×D | unidirectional, hidden64, 1 layer, 마지막 hidden | 19,094 |
| LSTM | B×T×D | unidirectional, hidden64, 1 layer, 마지막 hidden | 24,982 |
| causal TCN | B×D×T | channels32, 3 residual blocks, kernel3, dilation1/2/4 | 약 20,000 |

위 count는 bias가 있는 단순 linear heads(force3/load1/location18), GRU/LSTM의
일반적인 2개 bias vector 구성을 가정한 계산값이지 실행 측정값이 아니다.
TCN은 **블록당 causal convolution 2개**이며 이때 receptive field는 29샘플이다.
왼쪽 padding만 허용하고 마지막 시점 feature로 출력한다. 정규화 등 구조를 추가하면
count를 다시 계산한다. 대형 Transformer/LLM은 초기 범위에 넣지 않는다.

첫 기준 실험은 MLP, 첫 시계열 후보는 GRU64다. LSTM/TCN은 같은 조건에서 비교한다.
약 100k 이하를 초기 크기 예산으로 두되 실제 latency/accuracy로 판단한다.
ONNX나 특정 배포 backend를 첫 단계의 필수 의존성으로 만들지 않는다.

## 4. 시계열과 비시계열

- 기본 temporal 예시: 과거 30샘플, 마지막 시점의 force/load/location을 예측한다.
  약 30 Hz일 때 29개 간격은 약 0.97초다. 프레임 변동을 확인하지 않고 정확한 1초라고 하지 않는다.
- 시작은 고정 rolling window, 호출마다 RNN state를 초기화하는 모드다. 나중에 persistent
  state를 도입하면 train/deploy 규칙과 reset 정책을 함께 바꾼다.
- 윈도우 내부 순서는 유지한다. train에서는 완성된 window의 순서만 섞을 수 있다.
  비시계열은 train 행 순서를 섞을 수 있다. 두 경우 모두 실제 trial split이 먼저다.
- 같은 실험이어도 reject된 행/큰 timestamp gap/clock discontinuity를 넘지 않는다.
- 윈도우를 채우는 최초 워밍업 시간과 steady-state inference latency는 별도 보고한다.
- CSV가 ordered라는 것은 uniform-time이라는 뜻이 아니다. timestamp는 X에서 빼되
  연속 구간 검사에 사용한다. timestamp 없는 자료는 사용자가 주기를 보증하는 별도
  명시 모드가 아닌 한 temporal 학습을 조용히 진행하지 않는다.
- 양방향 RNN, 미래 시점을 보는 smoothing/centered filter는 기본 실시간 경로에 금지한다.
  현재 summary 자체의 nearest ±25ms 연결에 미래 샘플 가능성이 있으므로 배포 시
  bounded buffering/availability 규칙 또는 원본 기반 causal 재정렬을 검증해야 한다.

## 5. 선택형 출력과 손실

초기 task mode는 `force_only` 또는 `force_load_location`으로 선택한다.

- force head: linear 3개, signed XYZ; magnitude만 예측하거나 abs를 취하지 않는다.
- load head: logit 1개, 추론 표시 시 sigmoid. F/T 교정으로 파생한 유효 load label로 학습.
- location head: logits18, 유부하 조건의 ID1..18. 내부 index0..17로 변환 후 보고는1..18.
- load 낮음이면 "무부하/위치 해당 없음"으로 표시한다. 위치 head의 argmax를 억지로 보여주지 않는다.

개념적 총 손실: force loss + λ_load·binary loss + λ_location·masked categorical loss.
force는 유효한 force 측정이 있는 모든 샘플, load는 유효하고 확정된 load 라벨,
location은 **load=1이고 위치 라벨이1..18인 샘플만** 사용한다.
각 항은 유효 샘플 수로 정규화하고 유효 location이 0개인 배치에서는 해당 항이 유한한0이
되도록 구현한다. invalid force를 무부하로 바꾸거나 배치의 0분모로 NaN을 만들지 않는다.
초기 loss 후보는 표준화 force에 SmoothL1, load에 BCEWithLogits, location에 CrossEntropy다.
가중치/학습률 등은 설정 가능하게 하고 검증 데이터로 선택한다.

force-only도 반드시 구현하여 하중 분류 설계나 위치 라벨 부족이 기본 force 실험을 막지 않게 한다.
하중/위치 auxiliary loss 유무 자체도 모델 비교 항목이다. 기본 표시 threshold0.5는
초기 예시이지 calibration된 확률/최적 기준이라고 주장하지 않는다.

## 6. 공정한 평가와 실시간 예산

- 같은 session split/동일한 평가 샘플에서 입력 조합과 모델을 비교한다.
- force: 축별 MAE/RMSE/bias, vector error, 무부하/유부하별, ID별, 힘 크기별 오차.
- load: precision/recall/F1, 무부하 false positive, 작은 힘 false negative.
- location: 정답 유부하 조건의 정확도/confusion 및 load 오판을 포함한 end-to-end 성능.
- 전체 평균만 보지 말고 변형이 작은 ID1 근방을 별도로 보고한다.
- raw/Kalman별 평가 시 smoother target 덕분의 오차 감소와 실제 응답 지연을 구분한다.
  교차 소스 평가도 같은 단위/좌표/시간 조건에서 보조로 보고한다.
- 배치1 CPU를 포함해 preprocessing+buffer update+model+postprocess p50/p95/p99를 측정.
  데이터 수집/기존 필터/버퍼링 지연도 별도 측정한다. CUDA가 항상 더 빠르다고 가정하지 않는다.
- 초기 steady-state 계산 목표는 p95 10ms 이내를 후보로 두고 실제 하드웨어/제어 요구에
  맞춰 합의한다. 이는 측정 전 목표일 뿐 실시간 보장이나 제어 안전성 보증이 아니다.
- 안전하게 기록된 replay/합성입력으로 평가한다. 모델 평가를 위해 실제 모터를 움직이지 않는다.

## 7. 구현 순서 및 검증 기준

1. **CSV 검증**: 헤더 기반 registry, trial identity, selected X/Y validity, 단위/frame,
   int64 time, gap report. 실제 읽기 전에는 합성 자료로 테스트.
2. **무부하 분석**: 알려진 구간, 원본 보존, raw/Kalman 별도 calibration/report.
3. **Dataset pipeline**: group split, train-only scaler, dynamic feature dimension,
   재현 가능한 row mask, causal window, 별도 test set.
4. **MLP/force-only**부터 shape/forward/backward/짧은 synthetic smoke test.
5. **다중 출력과 참조 9개 모델 및 추가 후보**: masked loss 및 경계 reset, 입력 조합별 shape tests.
6. **실험 runner**: 동일 split의 ablation matrix, 결과표, resume/checkpoint 규약.
7. **배포 bundle**: weights+architecture, ordered columns, scaler, source units/frame,
   raw/Kalman/filter/calibration, time policy, window/state, output semantics, config/hash/version.

필수 실패/회귀 테스트: 실제0/음수 보존, missing≠zero, 잘못된단위/정렬 거부,
선택되지 않은 태그 결측 무시, raw↔Kalman 전환, label0/9의 무부하 masking,
all-no-load 배치, blank ID, 그룹별 입력 차원, 시각 공백/파일 경계 window 금지,
동일세션 중복split 금지, scaler train-only, 원본 파일 hash 비변경.

## 8. 현재 하지 않을 일

로봇 패키지 변경, 모터 실행, 온라인 force 제어 연결, 실제 대규모 학습, 기존 데이터
삭제/변형, 수집 형식 변경은 이 문서 준비 작업에 포함하지 않는다.
의존성 버전/설치와 CLI 명칭은 첫 코드 구현 단계에서 검증 후 확정한다.

8:1:1 trial 그룹 분할을 초기 후보로 설정한다. 실제 세션 목록과 ID별 독립 반복 수를
검사한 뒤 배정을 확정한다. 역할과 제약은 MODEL_COMPARISON.md를 따른다.

## 2026-09-27 최신 연구 우선순위 및 제안

- 우선순위: 끝단 힘 정확도 개선 → 접촉 위치 구분 → body 접촉 힘 추정.
- 끝단 힘 RMSE 50–90 mN은 사용자 희망 목표다. XYZ 통합 및 축별 지표를 모두 보고하며,
  각 축별 합격 기준으로 확정하거나 달성 가능한 수치라고 보장하지 않는다.
  Fx의 낮은 변형 신호가 어려움의 원인이라는 가설은 아직 검증하지 않았다.
- 먼저 끝단 force 성능을 개선하고, 이후 위치 단독 학습과 기존 공동 학습을 비교한다.
  위치 단독 학습은 아직 구현/실행하지 않았다. body force 개선은 그 이후다.
- 위치는 18개 세부 ID 분류를 유지하며 세 구간 평가/직접 분류를 후보로 비교한다.
  겹치지 않는 후보 범위: under 1–9 / upper 10–15 / tip 부근 16–18.
  경계는 제안이며 확정 설정이 아니다. tip 부근과 정확한 끝단 ID18을 구별한다.
- 새 수집 시 세 구간을 골고루 포함하되 실제 contact_segment_id 1–18을 계속 기록한다.
  각 구간 안의 여러 위치, 경계 주변, 다양한 방향·힘·자세·장력 및 독립 반복 녹화를
  확보하는 것을 권한다. 구간마다 한 점만 수집하면 구간 전체의 일반화를 입증할 수 없다.
- 18개 ID 예측을 세 구간으로 합치면 같은 구간 내 오류가 정답 처리되어 정확도가
  높아질 수 있다. 이는 위치 해상도가 달라진 결과이며 모델 학습 개선의 증거가 아니다.
- 기존 body Transformer의 ID18 유부하 test 4,577개에서 정확 ID18 인식은 0.5025%,
  후보 tip 부근(16–18) 인식은 61.0444%. 전체 3구간 정확도가 아니며 이 test에서는
  항상 tip이라고 하는 모델도 100%다. 세 구간 모두의 독립 test를 확보해야 한다.
  이번 수치는 이미 관측한 test의 탐색적 진단이며 튜닝/모델 선택 근거로 쓰지 않는다.
- 향후 위치 평가는 구간별 재현율과 confusion matrix, balanced accuracy를 함께 본다.
  balanced accuracy는 클래스별 재현율 평균이다:
  https://scikit-learn.org/stable/modules/model_evaluation.html#balanced-accuracy-score
- 단일 접촉 가정에서 추정 XYZ를 접촉 위치에 연결할 수 있지만 위치 성공이 힘 추정
  정확도를 보장하지 않으므로 별도 평가한다. 현재 무부하 판정과 force 보존 규약은 유지.
- 이번 요청에서는 방향성 기록과 기존 예측 재집계만 수행했다. 추가 학습/설정 변경 없음.

## 2026-09-27 — ID 학습 유지 및 모델 용량 논의

- 사용자 방향: 기존처럼 세부 ID1–18을 학습하고, 구간 표시는 나중에 후처리로 수행한다.
  직접3클래스 학습은 우선안에서 제외하고 대안으로 남긴다. 구간 경계는 아직 미확정.
- 인접 segment의 유사한 변형은 혼동 원인 후보이며 현재 데이터로 확정한 물리 결론은 아니다.
- 후처리 후보: 최대확률 ID를 구간에 매핑하는 방법과 softmax ID 확률을 구간별로 합산하는
  방법을 구분한다. 후자는 한 구간 안에 분산된 모델 확률을 반영한다. 두 방법의 결과가
  다를 수 있으며, 확률합이 실제 정확도를 높이는지는 독립 validation에서 확인해야 한다.
  원래 ID 예측을 함께 보존하고 무부하 시 위치 해당없음 규약을 유지한다. 아직 구현 안 함.
- 입력26개 기준 실제 trainable parameter 수를 생성한 모델에서 다시 계산하고 기존22개
  학습 기록의 parameters와 모두 일치함을 확인했다. model_parameter_counts.csv에 저장.
- 끝단 모델9,540–54,724개 / body 모델10,134–55,894개. 30k로 통일된 비교가 아니다.
  이는 뉴런 개수가 아닌 학습 가능한 가중치/편향 등의 개수다.
- 용량 부족 여부는 미확정. body Transformer train92.91%/val65.21%의 격차는 단순한
  크기 부족만으로 설명하기 어렵다. body 위치 결과로 tip force 용량 충분성을 확정하지 않는다.
- 후속 끝단 비교 후보: 같은 구조·입력·split에서 약30k/100k/300k급 용량을 비교하고
  train/validation 축별 force RMSE로 판단한다. 실제 파라미터 수/지연도 보고한다.
  test로 크기를 선택하지 않는다. 이 크기들은 실험 제안이며 신규 모델 구현/학습은 미실행.
- 근거 참고: https://scikit-learn.org/stable/modules/learning_curve.html

## 2026-09-27 — 세 구간 위치 구분 및90% 신뢰 목표 논의

- 검토 요청: 아래/중간/끝단부근의3구간 경계와90%정도 신뢰를 위한 추가데이터 필요성.
- 추천 초기범위: 아래ID1–9 / 중간ID10–15 / 끝단부근ID16–18. 이전upper표현을
  사용자요청에 맞춰중간으로 부른다. 물리적불연속/최적경계를입증한것은아니며9/10,
  15/16경계는가까운위치라여전히혼동가능. 정확ID1–18원본라벨은계속보존.
- 기존validation선택bodyTransformer의저장예측을 true_load=1에대해구간매핑으로재집계.
  추가학습없음. train142051시점 정확ID92.91%→구간96.93%; val32499시점
  정확ID65.21%→구간84.04%, 구간균형평균재현율83.13%.
- val구간별: 아래재현율87.12%/precision88.99%, 중간83.22%/80.18%,
  끝단부근79.04%/81.14%. 무부하오판포함재현율은75.65%/63.08%/61.39%로낮아짐.
- 기존독립test는ID18유부하4577개뿐. tip부근재현율61.04%, 하중오판포함49.46%.
  다른구간test가없어3구간전체일반화성능평가불가. testtipprecision100%는ID18만있어
  자명한수치로실제신뢰보장아님. 이번front추가학습은ID18고정force모델로위치학습아님.
- 진단산출물 results/20260926_tip_body_v1/three_region_review/region_metrics.csv 및
  train/val/test_confusion.csv. 경계탐색/test튜닝/softmax확률합평가를수행하지않음.
- 90%권고기준: 실제유부하의독립테스트에서각구간precision과recall90%이상 목표.
  제안기준이며달성보장/사용자최종확정아님. 모델확률0.9와관측정확도90%를구별한다.
  확신낮은결과를보류한다면보류율/전체대상정확도도같이보고하여수치만올리지않는다.
- 수집권고: 정확ID를유지하고세구간내여러위치(예:1/5/9,10/12/15,16/17/18)를
  우선반복; 이후나머지ID도포함. 각구간한점만측정해서구간전체성능으로해석하지않는다.
  각위치에서방향/부호/힘크기/초기자세/장력을겹치게분포시켜ID와조건의혼동을줄인다.
  한녹화의프레임을늘리기보다접촉을해제/다시위치시키는독립반복을확보한다.
- 먼저선택한ID별3–5회정도를파일럿수집계획으로제안할수있지만90%달성에필요한
  확정개수가아니다. 녹화단위train/val/test를나누고세구간모두별도test를둔다.
  무부하/아주작은힘은위치단서부족가능성이있어유부하위치성능과하중검출을분리보고.
- 참고: https://scikit-learn.org/stable/modules/calibration.html
  https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data

## 2026-09-27 — 모델 분리 방향 확정 및 수집 부담 최소화

- 사용자: 위치/힘 모델을분리하는방향에동의. 데이터수집이어려워현재부족여부를질문.
- 결정: 위치인식과힘추정을별도모델로비교/운용하는방향을기록한다. 분리의성능우위는
  아직검증되지않았으며이번질문에서새학습/코드구현을시작하지않음.
- 확인: 기존body데이터37녹화206264행(유효206232), ID1–17각2녹화/ID18총3녹화.
  신규4녹화는모두ID18이라아래/중간독립반복과시험범위를늘리지는않음.
- 판단: 현재수집량만으로모델개발을못하는상태는아니다. 독립반복/조건다양성과
  아래·중간heldout평가가제한적이며, 성능부족이데이터양하나때문이라고단정할수없음.
- 다음실험우선순위권고: 기존데이터로위치전용학습(정확ID보존/3구간표시)을비교하고,
  개발녹화단위그룹검증으로취약구간·조건을찾은뒤추가수집요청을구체화한다.
  새분할의validation을이미학습한부모모델로검증하지않고fold별새초기화학습필요.
  과거와신규test는계속heldout유지. 추가행수/epoch만늘리면해결된다고보장하지않음.
- 수집부담관련: 앞서ID별3–5회는파일럿제안이지필수최소개수나90%충족조건아님.
  지금즉시모든ID를대량재수집하라고권하지않는다. 이후소량추가시새아래/중간의
  독립시험과그룹검증에서실패한조건을우선하며몇개의대표점만으로전체구간을보장하지않음.
- 센서로서로구분되는변형정보가약한조건은수집량만으로해결되지않을수있으므로
  데이터효과는그룹단위학습곡선/실패분석으로확인한다.
- 참고: https://scikit-learn.org/stable/modules/learning_curve.html#learning-curve
  https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data

## 2026-09-27 — 정지 자세와 사인 운동 데이터 수집 방식

- 사용자추가설명: ID1–18을다시수집가능. 기존수집은사인파운동중힘가하기/제거반복.
  segment별고정위치에서수집하는것이나은지질문했다.
- 해석: 고정위치는우선매니퓰레이터목표자세/구동명령고정으로해석. 접촉위치고정을
  뜻한다면기존라벨규약대로한녹화에서같은segment접촉을유지하고ID변경시새녹화필요.
- 제안: 기존동적데이터를대체하지않고정지자세데이터를보완한다. 특히현재부족한
  위치별변형비교를위해공통기준자세에서ID1–18을한차례씩수집하는것이유용한진단후보다.
  같은힘방향/크기범위를각ID에겹치게적용. 자세고정은목표명령유지이며외력에의한
  몸체변형을허용하는조건을뜻한다. 제어모드/초기장력도기록한다.
- 공통자세에서외력제거기준→힘증가→유지→제거를반복하고방향/크기를변경한다.
  가능하면다른공통자세에서도반복하되ID별로서로다른자세만수집하지않는다.
- 사인운동도유지: 모든ID에동일한운동조건을사용하고하중on/off시점이항상같은위상에
  고정되지않도록달리한다. 하중없는운동구간도함께보존한다. 추후다른주기/진폭평가는
  별도조건이며이번에수치나제어명령을지정하지않음.
- 정지데이터는자체운동의변동을줄인위치식별진단에유리할수있지만정지학습만으로
  움직이는상태성능을보장하지않는다. 동적이력/마찰등은현재낮은성능의확정원인이아니다.
- 오늘추가분의우선제안: 공통고정자세ID1–18 보완수집; 여유시같은ID에서사인운동도
  별도녹화. 정지/운동, 자세, 접촉ID, 반복번호를구분하고새녹화test는전체격리.
  같은접촉이벤트를잘라독립train/test처럼사용하지않는다. 몸체위치test도확보필요.
- 참고원저는내부구동과외부접촉변형의분리를다룬다. 다른로봇의논문성능을HRM에
  적용하거나이번프로토콜의90%성공을보장하지않는다.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11574004/
- 이번작업: 수집방식조언/문서기록. 새학습/데이터수정/모터명령실행없음.

## 2026-09-27 — ID1–4 저변형과 학습 제외 검토

- 사용자관찰: ID1–4는힘을가해도변형이거의없음. 데이터셋제외가나은지질문.
- 판단: 원본은보존하고제외여부는대조실험으로결정. 시각적으로작은변형이곧
  모든센서입력에서식별불가능함을뜻하지않으며26입력중장력/길이도확인필요.
- 수집권고: ID5–18을주요9자세수집으로우선하고ID1–4는공통자세에서
  외력제거/가압/제거를소량반복하여각도·장력변화가무부하잡음과구분되는지진단.
  1–4도한번에전량폐기하거나무부하라벨로바꾸지않는다. 권고이며수집범위미확정.
- 후속비교: 1–18포함 vs1–4제외모델을같은ID5–18 validation에서비교하고,
  ID1–4는별도미지원/실패평가로보존. 어려운정답을평가에서뺀평균상승을개선으로오인금지.
- 제외확정시지원범위는ID5–18이고구간표시의아래는5–9로명시해야한다.
  1–4접촉이실제로있다면제외모델의지원밖이며자동으로unknown/무부하구분을
  할수있다고보장하지않는다. 입력이구별안되면더많은반복학습만으로해결되지않을수있다.
- 접촉ID1–4녹화제외와입력relative_angle_1–4제외는다르다. 입력18각도는유지하며
  센서채널제외는별도근거/실험없이지정하지않는다.
- 참고: tendon force/length를접촉추정단서로사용한원저가있으나본HRM의1–4식별을
  입증하는결과는아니다. https://doi.org/10.1109/IROS55552.2023.10341897
- 이번에는질문답변/계획기록만수행. 원본/학습config/모델/구간경계변경없음.

## 2026-09-27 — 초기 접촉 구간 제외의 정량 근거와 논문 서술

- 사용자명확화: 입력18각도는모두유지. 접촉ID1–4 또는5/6까지의가압실험을
  학습에서제외할지, 각도반응추이를분석한후논문에제외근거를설명할지질문.
- 권고: 후자. 지금제외경계를확정하지않고개발/예비실험에서센서반응·반복성과
  무부하/유부하구분및위치구분을각각검증한뒤적용범위를정한다.
- 예비실험: 초기ID1–6와비교ID8/12/18등에공통목표자세·초기장력·힘방향을적용,
  aligned실측힘의겹치는크기범위를비교한다. 무부하→가압→해제를독립반복하고
  가압전/후무부하기준의drift·hysteresis와센서잡음도확인한다.
- 측정: 각18관절의동일조건무부하기준대비Δ각도/분포, 장력변화, 무부하변동대비크기,
  자세·힘방향·크기별반복성. contactID행×관절ID열의Δ각도heatmap을보고할수있다.
  특정관절만이아닌전체18각도반응을본다. 각도잡음은별도측정하고F/T45.4/43.6/72.9mN
  임계값을각도에전용하지않는다.
- 기존사인파자료는자세·위상을맞춰비교해야하며무부하전체평균을가압평균에서
  빼서접촉변형이라고단정할수없다. 정지예비실험이원인구분에적합한후보다.
- 각도변화가작아도장력으로하중을검출할수있다면'무부하와구분불가'주장은부적절.
  하중검출과접촉위치식별의한계를구분하고, 특정조건에서만약하면ID전체제외보다
  조건별적용범위제한이타당할수있다. 유의차없음만으로등가/식별불가능입증하지않는다.
- 제외기준/범위는독립최종test를보기전에고정. 이미예비결과를본뒤정한기준이면
  사후탐색임을밝힌다. 논문에는제외ID/세션/표본수와비교조건·정량근거·지원범위를표시.
- 포함/제외모델은동일공통ID validation에서비교하고전체ID결과/제외구간실패도보존.
  제외실험은'초기구간의관측신호제한으로범위제한'이며전체1–18성능향상으로표현금지.
- 논문문장예시는측정후채울템플릿으로만제시하며실측하지않은결과를사실처럼쓰지않음.
- 참고보고양식: https://www.nature.com/documents/nr-reporting-summary-flat.pdf
- 이번에는연구설계/기록만수행. 원본/입력/학습라벨/제외범위/모델변경없음.

## 2026-09-27 다음 데이터의 하중·위치 학습 정책

최신 상세 정책은 [NEXT_DATA_TRAINING_POLICY.md](NEXT_DATA_TRAINING_POLICY.md) 참조.
사용자는 초기 ID에서 각도와 장력 모두 거의 변하지 않는다고 정정했으며, ID1–18 전체
수집 후 분석하기로 했다. 이전 초기 구간 소량 우선 제안보다 이 계획을 우선한다.
전체/초기 제외 모델의 공통 ID validation 비교로 지원 범위를 결정한다. 제외 유부하를
무부하로 바꾸지 않으며 입력 18각도는 유지한다. 무부하는 하중 검출/힘 학습에 사용하고
위치 loss에서만 제외하는 구조를 권고한다. 위치+하중 모델과 힘 모델은 별도 운용,
표시 무부하 ID0/구간 없음, raw XYZ와 조건부 ID는 보존한다. ID18 힘으로 몸체 전체를
판정하지 않는다. 최종 검출/force-box/결합은 지원 범위를 맞춰 validation에서 비교한다.
현재 코드 적용이나 성능 우위가 검증된 정책이 아니다. 새 데이터 전 학습은 보류한다.

## 2026-09-27 폴더별 데이터 설정 구현

새 학습 입구는 [DATASET_FOLDERS.md](DATASET_FOLDERS.md)에 기록했다.
configs/{tip,body}_force_folders.json으로 trainsets를 탐색하며 testsets는 예측용으로
분리한다. 기본 validation은 ID별 녹화 단위이며 원본파일/session/hash를 결과에 고정한다.
기존 명시 목록 실험은 기존 시간순 분할을 유지한다. 이번에는 데이터 입구만 확장했으며
NEXT_DATA_TRAINING_POLICY의 위치/힘 분리 네트워크 구현이나 실제 학습은 하지 않았다.
현재 trainsets에 들어간 과거 right18 test는 학습 진입을 차단하므로 배치 정리가 필요하다.
