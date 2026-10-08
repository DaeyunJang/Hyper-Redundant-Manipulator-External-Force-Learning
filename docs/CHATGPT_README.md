# HRM 외력·접촉 위치 추정 — 현재 설계와 작업 기록

기준일: **2026-10-07, Asia/Seoul**. 요구사항·실제 구현·검증·후속 작업을 이 문서에서 관리한다.
사용자의 최신 요청이 우선이며 문서 안의 과거 기록이나 실행 예시는 새로운 실행 승인으로 해석하지 않는다.
이전 문서·설정·일지 등 41개 파일은 [보존 archive](../archive/legacy_materials_20260928.tar.gz)에 있다.
Archive에는 정리 전 이 문서와 WORK_LOG, 인계 문서, 과거 설정 및 분석 근거도 포함된다.
2026-10-05 실행 코드 단순화는 **38절**, 이후 승인받은 전체 재학습은 **39절**에 기록했다.
2026-10-06 사용자가 직접 재학습한 `20261006_095933`의 validation 분석은 **46절**, test 검산은 **47절**이다.
2026-10-06 무부하 기준을 YAML 수동 축별 범위로 변경한 내용은 **53절**이다. 과거 결과의 기준은 유지한다.
2026-10-06 기존 예측으로 수행한 위치 오류·힘 크기/방향·static/dynamic 원인 진단은 **55절**이다. 재학습은 하지 않았다.
2026-10-06 저장 Excel의 GT/모델 열 재정리 도구와 예측→정리 shell 추가는 **60절**이다.
2026-10-06 평가 허용 거리 `--id-tolerance N` 추가와 학습→예측→Excel 정리 명령 확인은 **70절**이다.
2026-10-06 새 학습/예측 `20261006_211528`/`20261006_221159`의 ±2·±3 분석과 id-tol 파일명 표시는 **73절**이다.
2026-10-07 기준 힘 이하를 운용상 ID18로 취급하는 의도 확인은 **76절**이다.
현재 실행 방법은9절/README를 따른다.
11–37절은 당시 구현/결과의 이력이며 그 안의 삭제된 스크립트 명령은 현재 명령이 아니다.

## 1. 현재 상태와 승인 범위

- 최신 결과 분석(73절): 사용자의 `20261006_211528` 학습/`20261006_221159` test는242조합 완료다.
  Validation 선택은 양방식 힘MLP/위치Transformer다. Body 동일녹화test ±2→±3 조건부는
  masked82.16→87.14%, class078.15→84.48%, class0 검출 포함60.66→64.21%다.
  독립tip 힘MLP XYZ RMSE138.56mN, 유부하tip 최종ID18 정답률(class0)32.69%다.
  두 정리 결과의 원본 예측이 같음을 검증했고 기본정리 폴더/파일명에 id-tol-N을 추가했다.
- 현재 핵심 코드는 루트 Python5개(train/predict/model_zoo/data_utils/analyze_no_load)다.
  독립 모델, 직접 CSV 열 지정, 두 무부하 방식, 모든 조합 학습, bundle 추론,
  validation 선택, 전 조합 test 평가, 실행별 Excel1개를 제공한다(38절).
  2026-10-06 요청으로 organize_results.py를 추가했다. 기존 Excel만 재정리하며,
  predict_and_organize.sh로 예측→정리를 연속 실행할 수 있다(60절).
  과거 그림·개별 분석·JSON 호환 도구는 정리 전 코드 압축본에 보관했다.
- 주 학습 [20260928_221428](../results/train/20260928_221428/)의 **242조합·484분기 학습을 완료**했다.
  Validation으로 선택한 두 bundle의 [test 평가](../results/predict/20260928_224418/)도 완료했다.
  Tip test XYZ RMSE는 123.85 mN이며 모든 축 90 mN 이하 목표는 달성하지 못했다.
  정확 ID의 독립 실험 일반화가 낮다. 최종 수치와 구간 탐색의 한계는 11절에 기록했다.
- 앞선 `20260928_220253` 학습은 TCN 실행 병목을 조사하기 위해 중단했다.
  그 부분 학습의 순위를 최종 결과로 사용하지 않으며 주 실행은 모든 조합을 다시 초기화했다.
- 2026-10-05 요청으로 당시 설정의 전체 재학습·test·실측/예측 Excel과 RMSE/MAE 검증을 승인받았다.
  **`20261005_194129`의242조합 학습과 전조합test, Excel88모델시트 검산을 완료했다**(39절).
  양방식 모두 validation 선택은 힘MLP/위치Transformer이며 독립tiptest XYZ RMSE136.53mN이다.
  원본 CSV는 수정·삭제하지 않는다.
  ROS·매니퓰레이터 제어 연결은 이번 범위 밖이다.
- 2026-10-06 사용자가 직접 실행한 `20261006_095933`은242개 checkpoint와 validation 비교표가 있다.
  힘MLP가 최저 validation XYZ RMSE154.26mN이며 선택 조합은 masked MLP/ResNet,
  class0 MLP/Transformer다. 최초 확인 당시 새test가 없었으나 후속 요청 시242조합test 결과가
  저장되어 있음을 확인했고, test Excel44모델시트 전수 검산을 완료했다(47절).
  선택MLP의 독립tiptest XYZ RMSE138.56mN/MAE96.46mN이다. Validation.xlsx0바이트 문제는
  이번 test 분석에서 복구하지 않았다.
- 주요 결과는 역할별 `comparison.csv`, `summary.json`과 Excel1개다.
  예측 폴더 `predictions.csv`는 방식별 validation 선택 모델의 행별 결과다.
  상세 지표·근거·학습 이력·경계 후보는 JSON/NPZ로 날짜 폴더 안에 보존한다.
- 2026-09-29 요청에 따라 MATLAB용 모델별 시트 Excel 내보내기를 완료했다.
  [Train/validation](../results/train/20260929_130543_excel/)과
  [test](../results/predict/20260929_130543_excel/)에 힘·ID masked·ID class0를 각각 저장했다.
  총 9개 파일·99개 모델 시트를 검증했으며 열·행·대표 checkpoint 계약은 13절에 기록했다.
- 추가 [ID18 전용 실행](../results/train/20260929_181303_id18_only/)의121조합 학습·test도 완료했다.
  위치는 ID0/18 이진 검출이다. Validation 선택CNN/LSTM의 test XYZ RMSE123.85 mN,
  검출 balanced accuracy81.42%이며 자세한 범위·기존 결과와의 비교는17절에 있다.
- 최신 무부하 설정은 `ft_sensor_calibration`에 unit과 fx/fy/fz의 `[최솟값, 최댓값]`을
  지정하는 수동 방식이다(53절). 세 축 모두 범위 안이면 무부하, 하나라도 밖이면 유부하로 정한다.
  자동 offset 차감·분위수·10% 확대·불확실 구간을 새 학습에서 제거했다.
  기존 학습 결과는 당시의 mean/1.1 교정 등을 보존하며 예측에도 저장 기준을 그대로 사용한다.
- 2026-09-29 의도 정정: 새 무부하 경계의 주 관심사는 ID1–18 위치 구분 성능이다.
  힘 회귀는 부하 상태와 무관하게 연속 실측값을 학습한다. 별도 비교 제안은 ID18 전용 힘 모델과
  ID1–18 전체 힘 모델이며, 위치 모델의 학습 범위는 두 경우 모두 ID1–18로 유지하는 방향이다(21절).
- 최신 우선순위 확인(22절): ID18 전용 연속 힘 추정 모델은 필수이며 정확도 개선이 최우선이다.
  Body contact의 구간 인식 약90% 이상을 목표로 한다. 2026-10-06 최신 운용 요구는 동시
  다중 접촉을 제외하고 무부하/tip/body를 상시 자동 구분하는 것이다(64절).
  직접3분류/별도 상태 출력 추가는 사용자 요청으로 제외했다. 기존 class0/masked ID 분류를
  유지하고 class0의ID0/18/1–17을 상태로 해석한다(69절). 기존 구간·±2 평가는 유지한다.
  전체 ID 힘 회귀는 현재 필수 작업이 아니며 앞선 비교 제안으로 남긴다. 제어 연결은 아직 미구현이다.
- Static 제외 끝단11종 비교 완료: [20260929_195732_no_static_tip](../results/train/20260929_195732_no_static_tip/).
  Validation 선택 GRU의 동일 test XYZ RMSE147.88 mN, 축별160.50/97.55/174.15 mN이다.
  ID18 train은 summary_18 한 파일, validation은 summary_18-2 한 파일이다. 기존에는 두 파일 모두
  train이고 static이 validation이었으므로 static 학습 유무만 통제한 비교는 아니다.
  ID1–6은 static 제외 시 각1녹화뿐이라 당시 전체 ID 위치 학습은 미진행했다.
- 2026-10-05 최신 데이터/실행(35절): 사용자가 수동 분리한 train48개(dynamic30+static18), test19개를
  확인했다. Test는 폴더의 파일 그대로 고정하며 ID별로 추가 분할하지 않는다. 별도 답변이 없어
  validation은 각 train CSV의 유효 숫자 행 앞80% 학습/뒤20% 검증으로 기본 설정했다.
  두 역할의30행 창과 scaler fit 행이 겹치지 않는다. Static ID10도 현재 파일에는 유효 힘이 있다.
  해당35절 단계에서는 새 학습 없이 데이터 준비/코드 검증만 수행했다. 이후 실제 재학습은39절이다.
- 최신 전처리 합의(34–35절)를 `preprocessing: numeric_compact`로 구현했다. 선택 X/Y의
  빈칸·비수치·NaN/Inf 행을 제외한 뒤 같은 파일/역할 안에서 원래 순서대로 연결한다.
  Valid flag/frame/matching-time/시간 간격 검사는 이 새 학습 데이터 경로에서 생략하고,
  원본 행/시간은 추적용으로 남긴다. 새 핵심 코드는 numeric_compact를 지원한다.
  과거 audited/whole_csv의 재현은 보관 코드를 사용하며 새 정책으로 자동 변경하지 않는다.

## 2. 연구 목표와 입력·출력 계약

목표는 단일 외력이 작용하는 segment와 Fx/Fy/Fz를 추정하는 것이다.
현재 우선순위는 **ID18 전용 연속 3축 힘 정확도 → 별도 body contact 감지 모드의 구간 인식 약90% 이상**이다.
범용 body 힘 회귀는 현재 필수 목표가 아니다. 끝단 힘 제어 모드와 body contact 감지 모드를 구분하며,
body 접촉이 판정된 상황에서 ID18 전용 모델 출력을 검증된 body 힘이나 끝단 힘으로 해석하지 않는다.
동시 복수접촉 분리, 분포하중 추정, 안전 제어 성능을 현재 결과로 주장하지 않는다.

| 구분 | 현재 계약 |
|---|---|
| 입력 그룹 | `wire_length` 4개, `loadcell_tension` 4개, `relative_angle` 18개; 기본 총 26개 |
| 각도 | Base→tip 순서, 홀수 tilt/짝수 pan, rad와 부호·0 유지; 총 18개이지 36개가 아님 |
| 힘 정답 | 기본 `fts_kalman.aligned_fx/fy/fz`, `hrm_base`; CSV mN→학습 N |
| 원본 위치 | `contact_segment_id`는 케이블 연결 위치; 무부하에서도 원본 ID 유지 |
| 신경망 출력 | 힘 3개 회귀값과 위치 logits; 물리 힘은 저장된 target scaler로 역변환 |
| 부하 정답 | 확인된 무부하 기준을 실측 F/T 정답에 적용한 파생 라벨 |
| 향후 제어 부호 | 학습·예측은 저장 부호 유지; HRM 제어에서 역정규화 XYZ에 -1을 한 번 적용 |

입력 열은 `input_columns`의 명시적 순서로 구성하고 개수에 맞춰 모델 입력 차원을 자동 결정한다.
Timestamp는 새 numeric_compact 경로에서는 결과 대응용이며 시간창의 제외 조건이 아니다.
과거 보관 코드의 audited 경로는 시간 경계 검사를 유지한다. F/T 정답, ID, 파일명, trial ID, GT 부하 상태는 입력에 넣지 않는다.
힘과 위치는 같은 종류의 입력을 쓰지만 지도 파일·유효 시점·정규화는 분기별로 다를 수 있다.
원본 CSV의 열을 지우거나 제한 ID 모델이라는 이유로 앞쪽 각도 채널을 자동 삭제하지 않는다.

## 3. 독립 모델과 모든 조합 학습

`HRMEstimator` 안에 공유 파라미터·공유 encoder가 없는 `force_net`과 `location_net`을 둔다.
각 조합에서 두 네트워크와 optimizer를 새로 만들고 힘·위치를 따로 학습한다.
두 분기의 best epoch가 달라도 각 validation best를 **현재 조합의 bundle 한 개**에 저장한다.
조합 간 가중치 재사용, warm start, 분기 동결, 부분 학습, resume는 새 기본 경로에 없다.
같은 실행의 best 복원과 완료 bundle의 추론용 로드는 제공한다.

후보 11개는 `mlp`, `cnn`, `convmixer`, `resnet`, `lstm`, `gru`, `tcn`,
`transformer`, `kalmannet`, `small_gru`, `residual_tcn`이다.
`kalmannet`은 이 저장소의 GRU+MLP 구현이며 물리 Kalman filter가 아니다.
두 무부하 방식 × 힘 11개 × 위치 11개 = **242개 조합, 484회 분기 학습**을 수행한다.
힘/위치별 구조 크기는 `force_params`/`location_params`에서 후보별로 지정한다.

기본 seed는 42, 위치 분기 seed는 43이다. 분할·분기 초기화·학습 순서를 기록한다.
같은 분기의 설정·데이터·seed가 같으면 다른 파트너와 조합해도 출력이 반복될 수 있다.
이 반복은 새로운 독립 seed 실험이 아니며, 파트너 네트워크의 상호 보완 학습을 의미하지 않는다.
여러 seed 반복 및 입력/시간/모드 요인별 비교는 별도 후속 실험이다.

힘은 확인된 tip trial의 유효한 유부하·무부하 실측값을 모두 사용한다.
Body trial을 tip 정답 0으로 바꾸거나 위치 유효 마스크를 힘 손실에 재사용하지 않는다.
기본 `force_loss: mse`, `target_scaling: true`이며 scaler는 분기별 train 행으로만 fit한다.
수동 부하 범위는 위치 라벨 생성에만 사용하고 회귀 정답에서 offset을 빼지 않는다.
`force_scope: all_single_contact` 실험은 tip 결과와 구분하며 재학습한다.

## 4. 실제 데이터와 고정 분할

입력은 `datasets/train/*.csv`, 최종 평가 입력은 `datasets/test/*.csv`다.
2026-10-05 기본 설정은 사용자가 분리한 test를 고정하고 각 train CSV 내부에서 앞80%/뒤20%를
학습/validation으로 나눈다. 같은 녹화에서 잘라낸 파일을 새 독립 실험으로 간주하지 않는다.
행·겹치는 창을 무작위로 나누지 않으며 다른 파일/역할 사이에 시간창을 연결하지 않는다.
모든 조합이 같은 목록·hash·분할을 사용하며 test는 scaler·학습·모델/경계 선택에 쓰지 않는다.
현재 수치와 재현 명령은35절에 있다. **아래는2026-09-28 실행 당시 데이터/whole_csv 정책의 기록**이다.

주 실행의 [data audit](../results/train/20260928_221428/data_audit.json) 및
[split manifest](../results/train/20260928_221428/split_manifest.json)에서 확인한 수치다.

| 역할 | CSV 수 | 원본 행 수 | 입력·힘 정답이 유효한 과거 30행 창 수 |
|---|---:|---:|---:|
| Train | 29 | 587,096 | 577,337 |
| Validation | 18 | 300,553 | 294,531 |
| Test | 2 | 8,371 | 7,933 |
| 합계 | 49 | 896,020 | 879,801 |

처음 검사 대상은 50 CSV/944,380행이었다. Static ID10 한 파일의 48,360행 모두에
Kalman aligned 힘/frame 정답이 없어 해당 파일을 감독 학습·validation에서 명시적으로 제외했다.
원본은 보존하고 raw로 자동 전환하지 않았다. 최종 49파일에는 입력 무효 1,268행,
힘 정답 무효 1,236행이 있으며 두 수는 중복 가능한 원인별 집계다.
GT 없이 입력만으로 만들 수 있는 추론 창은 총 879,805개다.

당시 tip train은 `summary_18-2.csv`, `summary_18.csv`의 유효 창 총 16,361개다.
Tip validation은 `summary_static_pan_-30to+30_tilt_-30to+30_interval-15deg_seg-id-18.csv`의 71,869개 창이다.
파일 길이뿐 아니라 자세·운동 조건도 달라 같은 분포의 반복 실험으로 간주하지 않는다.
Test는 `summary_test_18-2.csv` 2,601행과 `summary_test_18.csv` 5,770행이며 둘 다 ID18이다.
이 test로 body 전체 위치 정확도나 세 구간 경계의 보편적 최적성을 검증할 수 없다.

### 확인된 중복·시간·라벨 처리

- Train `summary_18-2.csv`의 원본 ID1은 과거 사용자가 확인한 ID18 실험이다.
  정확한 SHA-256 `269578…c3af`에만 학습용 ID18 매핑을 적용하며 원본은 유지한다.
- 이전 test `summary_18-3.csv`(`96a85d…fe203`)는 위 trial의 ID 정정/재출력본이다.
  사용자가 `datasets` 바로 아래로 옮겼고 현재 train/test 탐색에서 제외된다.
  두 hash의 개발 역할과 기존 보호 test hash를 보존해 재유입을 차단한다.
- Trim 이력이 있는 ID15·16·17 및 test ID18 네 파일은 저장 anchor 이동과 여러 독립 topic의
  시각/skew를 전 행에서 대조해 메모리에서만 복원했다. 허용 오차는 20 μs이며
  과학적 표기 저장 정밀도 수준의 복원이다. 원래 정확한 ns 값을 완전히 복구했다고 주장하지 않는다.
- 당시 예외·제외 근거는 `hrm_force/dataset_contracts.json`의 정확한 hash로 제한했다.
  원본은 정리 전 코드 압축본에, 현재 필요한 라벨/역할 예외는 `data_utils.DEFAULT_DATA_CONTRACTS`에 있다.
  파일명만 보고 다른 실험에 보정·제외를 확대하지 않는다.
- 결측·비수치·무효 flag·matching skew 초과를 0이나 무부하로 채우지 않는다.
  학습 창은 입력·힘 정답의 연속 유효 구간 안에서 생성하고 invalid 행을 가로질러 연결하지 않는다.
- 기본 matching skew는 25 ms, 큰 gap은 양의 간격 중앙값의 1.5배 초과다.
  추론은 입력 유효성만으로 창을 만들고 GT 누락 때문에 가능한 원시 예측을 버리지 않는다.
- Set-zero 이벤트 검출, trial별 영점·필터 안정화 시간의 자동 보정은 현재 제공하지 않는다.

## 5. 무부하 원기록 분석과 과거 자동 라벨

이 절의 수치는 2026-09-28 학습 및 기존 ID18 전용 모델이 사용한 median/1.0 기준이다.
2026-09-29 새로 적용한 mean/1.1 기준과 보정 좌표 범위는19절에 있다.
2026-10-06 이후 새 학습은53절의 수동 범위를 사용한다. 아래 자동 교정 수치는 과거 기록이다.

사용자가 지정한 기준은 `datasets/aidin_FT_sensor_validation_2/csv/summary.csv`다.
[무부하 분석 JSON](../results/train/20260928_221428/diagnostics/no_load.json)과
[실제 학습 calibration](../results/train/20260928_221428/calibration.json)에 근거·hash·수치를 저장했다.
Raw와 Kalman을 모두 분석했지만 현재 학습 부하 정답은 Kalman 기준이다.

| 기록 | 녹화 시작 KST | 행/길이 | Kalman XYZ 표준편차 mN | Raw XYZ 표준편차 mN |
|---|---|---|---|---|
| validation2, 기준 | 2026-09-26 22:22:33 | 2,797 / 93.30초 | 48.75 / 46.02 / 70.07 | 99.89 / 94.86 / 142.94 |
| validation1, 전이 점검 | 2026-09-26 22:24:25 | 2,808 / 93.63초 | 45.36 / 43.57 / 72.91 | 103.01 / 92.60 / 143.81 |

두 기록의 선택 F/T 유효성·시간 matching 검사에는 무효행이 없었다.
좌표 변환 snapshot `[-y, -x, -z]`와 LPF/MAF off 설정은 같지만 저장 force offset은 다르다.
Sensor-frame offset XYZ는 validation2의 `[1342, 623, -3010]`, validation1의 `[1314, 668, -2886]` mN이다.
동일 tare/Kalman 상태는 보장되지 않으며 Kalman 내부 Q/R은 캡처 자료에 없다.
Kalman 표준편차는 raw의 약 0.44–0.51배였지만 작은 실제 부하 민감도나 지연 개선을 입증한 결과는 아니다.

기존 학습 기준은 validation2 앞 70%인 1,957행으로 fit하고 뒤 840행으로 시간 holdout 점검했다.
축별 fit median을 `b`, 표준편차를 `s`라 할 때 `score = max_a |F_GT[a] - b[a]| / s[a]`이다.
Fit score의 95% 분위수 2.482539 이하는 무부하, 99.5% 분위수 3.245299 이상은 유부하,
그 사이는 uncertain이다. 이전 상태를 유지하는 시간 히스테리시스와는 다르다.

| 축 | 부하 라벨 center b, mN | 무부하 상자 반폭, mN | 유부하 판정 상자 반폭, mN |
|---|---:|---:|---:|
| Fx | -64.59 | 122.37 | 159.97 |
| Fy | 18.62 | 115.53 | 151.03 |
| Fz | -83.53 | 175.53 | 229.46 |

따라서 세 축이 모두 Fx **[-186.97, 57.78]**, Fy **[-96.91, 134.15]**,
Fz **[-259.05, 92.00] mN** 안이면 현재 무부하 라벨이다.
유부하 경계는 더 넓은 상자이며 그 사이를 uncertain으로 두어 위치 손실에서 제외한다.

뒤 840행의 무부하/uncertain/유부하 오경보 비율은 **97.02% / 2.74% / 0.238%**다.
기준을 다시 fit하지 않고 validation1 전체에 적용하면 **79.88% / 15.49% / 4.63%**다.
두 기록의 Kalman median 차이는 약 `[42.48, -35.36, 108.43]` mN으로 세션 영점 전이 한계가 보인다.
Raw에서 별도로 구한 기준의 validation1 오경보는 0.855%지만 raw가 더 우수한 검출기라는 결론은 아니다.
기존 0 중심 ±45.4/43.6/72.9 mN 상자는 Kalman validation2에서 92.10%를 유부하로 오경보했다.
과거 1σ 상자나 tip RMSE 약 90 mN을 새 무부하 기준으로 재사용하지 않는다.

이 비율은 알려진 무부하 기록의 경험적 포함률이며 상관된 행의 독립 신뢰구간이 아니다.
Validation1은 약 2분 뒤 같은 날짜 기록으로 다른 날짜·환경의 독립 교정 검증을 대신하지 않는다.
실제 미세 부하 민감도, 모든 trial로의 영점 전이, 센서의 절대 물리 교정은 아직 검증되지 않았다.
단위는 기존 프로젝트의 mN 계약을 유지하며 이번 통계 분석이 단위를 새로 교정한 것은 아니다.

## 6. masked와 class0, 시간창의 의미

새 수동 기준에서는 유효한 힘이 모두 무부하/유부하 중 하나가 되며 uncertain은 없다.
아래 uncertain 처리는 기존 이중 경계 bundle을 재현할 때 유지한다.

| 상태 | masked 위치 지도 | class0 위치 지도 |
|---|---|---|
| 활성 ID의 확실한 유부하 | 실제 ID에 대응하는 내부 class | 실제 ID에 대응하는 내부 class |
| 확실한 무부하 | 위치 손실 제외 | 일반 class0으로 학습 |
| uncertain·무효 정답 | 위치 손실 제외 | 위치 손실 제외 |
| 비활성 ID의 유부하 | 위치 손실 제외 | 위치 손실 제외; 무부하로 바꾸지 않음 |

Masked 출력은 활성 ID 수 M개, class0는 M+1개다. Class0의 0을 ignore index로 사용하지 않는다.
현재 코드는 유효한 위치 endpoint만 optimizer에 전달해 전부 무효인 배치의 NaN 평균을 피한다.
무부하 센서 행은 과거 이력에 남는다. 해당 시점의 위치 손실 제외와 입력 행 삭제는 서로 다르다.
LSTM 등에서는 이후 유부하 손실이 과거 무부하 입력 처리 경로에도 기울기를 전달할 수 있다.

시간창은 **현재 행을 포함한 W=30행(이전29행+현재1행)**으로 현재 하나를 예측하는 stateless sequence-to-one이다.
숫자 행을 연결한 각 파일/역할 내부에서 구성하며 창마다 recurrent state를 초기화한다.
MLP는 마지막 행만 사용하되 공통 평가를 위해 같은 30행 준비 조건을 사용한다.
30은 이 프로젝트 설정값이며 최적 길이를 검증한 값이 아니다. 예전 참조 저장소는 시계열5행,
MLP/CNN/ConvMixer/ResNet1행 기본값이었다(38절). 현재는 `window_samples`에서 변경한다.
미래 입력·중앙 필터·미래 보간을 추가하지 않는다. 준비 전 출력은 N/A이지 오차 0이 아니다.

Masked는 무부하를 검출하도록 학습하지 않는다. 배포 gate가 없으므로 위치는 `unverified`,
최종 ID/무부하 검출/시스템 지표는 N/A다. GT gate는 오프라인 진단에만 사용한다.
Class0 후보 판정은 0을 포함한 전체 class argmax이며 p0를 따로 저장한다.
이 규칙의 test 평가는 가능하지만 배포 gate의 교정·실시간 안전성을 입증한 것은 아니다.
Tip 힘 모델의 작은 출력으로 모든 body 접촉을 무부하라고 판정하지 않는다.

## 7. 구간 확률과 공정한 평가

기본 구간은 하단 1–10, 중부 11–15, 상단 16–18이다. 제한 ID에서는 활성 ID와의 교집합을 사용한다.
Softmax 뒤 원래 segment 확률을 더해 구간을 고른다. Logits를 더하거나 segment 수로 나누지 않는다.
Class0의 세 구간 확률합은 1-p0다. 히트맵은 원래 확률과 고정 0–1 색 범위를 유지한다.
전역 ID argmax와 선택 구간 내부 대표 ID는 별도로 기록한다.
높은 구간 확률은 평가 정답률이 아니며 히트맵 폭은 실제 접촉 길이가 아니다.

Validation에서 연속 3구간 경계 **136개 모두**를 계산한다. 기본 최소 구간 크기는 3이다.
선택에는 세 구간 모두 GT support가 있는 후보만 쓰고 모든 후보의 제약·support를 저장한다.
`region_balanced_id_macro_recall`은 region 안의 실제 ID별 region recall을 평균한 뒤
세 region을 동일 가중 평균한다. 한 region에 GT support가 없으면 전체 점수는 N/A다.
동률은 region macro recall → 전체 ID macro region recall → 기본 경계와 거리 → 작은 경계 순이다.
항상 하단만 예측하면 10/5/3, 12/3/3 모두 새 점수는 1/3이다. 원래 확률합은 바꾸지 않는다.
경계는 validation에서만 고르고 고정한 뒤 test에 적용한다. 탐색 validation 점수는 독립 평가가 아니다.

- 힘: 축별 RMSE/MAE와 `sqrt(sum(XYZ 오차²)/(3N))`인 pooled XYZ RMSE를 mN로 보고한다.
  축별 RMSE 평균, 벡터오차 norm RMSE, 힘 크기만의 RMSE와 구분한다.
- 위치: 동일 GT-loaded 활성 ID 시점에서 exact ID, 실제 ID 차이 ±1, ID별/macro recall을 보고한다.
  Class0에서 p0를 무시한 위치 진단과 검출 실패를 포함한 시스템 지표를 분리한다.
- 검출: 유부하 precision/recall/FPR/FNR, 무부하 precision/recall, balanced accuracy를 따로 기록한다.
  Unsupported loaded ID를 무부하로 바꾸지 않고 범위 밖 표본으로 집계한다.
- 향후 ID1–4 포함/제외 비교는 공통 ID5–18의 같은 시점에서 한다. 이번 실행은 ID1–18 전체를 유지했다.
  비활성 칸 N/A는 범위 밖 자동 검출이 아니다.
- Mode 간 CE 절대값, 기존 전체 시점 정확도와 새 유부하 정확도, 서로 다른 평가 시점을 직접 비교하지 않는다.

각 mode의 최종 bundle 선택은 validation pooled 힘 RMSE 최소를 우선한다.
최소값과 차이가 1e-3 mN(1 μN) 이내이면 수치적 동률로 보고 위치 macro recall 최대,
위치 CE 최소, 모델명 순으로 정한다. 동일 seed CUDA 재학습의 약 1e-5 mN 변동이
위치 후보 선택을 좌우하지 않게 하는 규칙이며 성능 허용폭이나 통계적 동등성 기준은 아니다.
이 규칙은 test 평가 전에 정했고 test 결과로 조정하지 않았다.
이미 학습한 해당 pair bundle을 그대로 사용하며 다른 조합의 가중치를 새로 섞지 않는다.
Test 수치는 선택된 행의 `test_*` 열에만 추가하고 최적 구간 test 지표는 별도 열로 구분한다.

## 8. 데이터 조건 진단과 해석 제한

[개발 자료 진단](../results/train/20260928_221428/diagnostics/dataset.json)은 중단 실행의 자료 점검에서 시작했다.
주 실행과 trial hash 순서·고정 split이 동일함을 확인했고 현재 주 실행의 diagnostics로 모았다.
이는 모델 성능이 아닌 데이터 기술 통계다. Train 유효 창의 유부하/무부하/uncertain 비율은
54.32%/31.45%/14.23%, validation은 60.77%/26.20%/13.03%로 같지 않다.
Train scaler 기준 입력 중 하나라도 |z|>3인 행은 train 6.91%, validation 24.97%였다.
이는 여러 상관된 채널의 기술 통계이며 교정된 이상 확률이 아니다.

Static ID3 validation의 `relative_angle_1`은 인접 부호 전환 비율 100%,
중앙 절대 변화량 약 1.777 rad로 다른 파일과 큰 차이가 관찰됐다. 원본을 임의 수정하지 않았다.
초기 ID의 약한 반응 관찰은 보존하되 자세·힘 방향을 맞춘 인과 비교를 하지 않았으므로
유부하/무부하 평균 차이만으로 base의 관측 불가능성이나 제외 경계를 확정하지 않는다.
ID별 힘 크기·방향·자세와 static/nonstatic 구성이 다르며 파일명만으로 운동 protocol을 단정하지 않는다.
이 진단에서 test는 정체성·유효성 metadata만 확인했고 test 분포로 학습 조건을 조정하지 않았다.

같은 CNN 위치 구조의 best epoch 1을 복원해 ID별 유부하 500행씩을 동일 규칙으로 뽑은
[추가 일반화 진단](../results/train/20260928_221428/diagnostics/location_generalization_sample.json)에서는
정확 ID macro recall이 masked train 65.67% → validation 3.41%,
class0 train 67.32% → validation 3.56%였다. 기본 세 구간의 구간균형 ID macro recall도
각각 84.86% → 45.02%, 85.92% → 43.78%로 낮아졌다.
이는 녹화 간 일반화 격차와 일치하지만 특정 센서·자세 차이가 원인이라는 증명은 아니다.
최종 선택 모델 평가가 아닌 동일 CNN 구조 진단이며 test는 사용하지 않았다.

같은 tip validation 71,869시점의 [상수 힘 기준선](../results/train/20260928_221428/diagnostics/force_validation_baselines.json)은
train 정답 평균 출력 시 XYZ RMSE/MAE 307.57/220.64 mN, 항상 0 N 출력 시 307.45/214.20 mN였다.
이는 모델 성능을 판단하는 참고선이며 힘을 0으로 강제하는 운영 정책이 아니다.

## 9. 설정과 실행

사용자가 수정하는 기본 파일은 [configs/train.yaml](../configs/train.yaml) 하나다.
데이터 예외·보호 hash는 내부 계약에 보존하고 실행 시 resolved 설정과 bundle에 넣는다.
아래는 기존 YAML의 해당 키를 바꾸는 예이며 입력/모델 변경은 새 학습으로 남긴다.

```yaml
input_columns: ["wire.Cable #1 length", "loadcell.Loadcell #1 tension", relative_angle_1]
force_columns: [fts_kalman.aligned_fx, fts_kalman.aligned_fy, fts_kalman.aligned_fz]
id_column: contact_segment_id
source_force_unit: mN
window_samples: 30
no_load_modes: [masked, class0]
force_candidates: [lstm, gru]
location_candidates: [lstm, tcn]
force_params:
  lstm: {hidden_sizes: [60, 30], projection_dim: 32}
location_params:
  lstm: {hidden_sizes: [48, 24], projection_dim: 24}
```

위 input_columns는3열 예시이며 기본 설정은26열이다. 형상을 제외하려면 상대각18열을 목록에서 뺀다.
Base 제외는 `active_ids: [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]`로 설정한다.
Raw 전환은 `force_columns`에 raw XYZ를 선택하고 `ft_sensor_calibration`의 범위도 그 열에 맞춘다.
임의 열 이름을 지원하지만 XYZ순서/단위/좌표계 의미는 사용자가 올바르게 지정해야 한다.
현재 기본은 60 epoch 상한, patience 10, batch 1,024, learning rate 0.001,
AdamW weight decay 0.0001, clipping norm 1.0, threads 4다. Test로 최적화한 값이 아니다.

```bash
bash scripts/hrm_python.sh train.py --config configs/train.yaml --check-data
bash scripts/hrm_python.sh train.py --config configs/train.yaml
bash scripts/hrm_python.sh predict.py --train-dir results/train/새학습날짜_시간
bash scripts/hrm_python.sh predict.py --checkpoint <조합폴더>/hrm_bundle.pt --input-dir datasets/test
bash scripts/hrm_python.sh analyze_no_load.py --config configs/train.yaml
```

`--check-data`는 검사·분할 저장까지, 일반 train은 전체 설정 조합 학습까지 수행한다.
Predict는 bundle의 구조·class 매핑·입력 순서·단위·scaler·calibration을 복원하고 새 YAML로 덮어쓰지 않는다.
**`HRMEstimator.forward()`의 force는 target scaling 사용 시 학습 정규화 단위다.**
직접 연결 시 분기별 저장 X scaler와 힘 Y 역변환이 필요하다. `predict.py`는 이를 적용한 N/mN를 저장한다.
자동 제어용 -1 곱은 하지 않는다. 낮은 수준의 forward 출력을 곧바로 물리 힘으로 사용하지 않는다.
정답 없는 CSV도 입력이 유효하면 예측한다. 모든 원본 행을 보존하고 준비 중/invalid 출력은 NaN이다.
Tip 적용이 확인되지 않은 파일에도 raw XYZ를 출력하되 `scope_unverified`로 표시하고 힘 지표에서 제외한다.
학습 후 `validation.xlsx`, 예측 후 `predictions.xlsx`를 자동 생성한다. 이 중 학습 Excel은
optimizer에 사용한 train행의 재예측이 아닌 validation 결과다. 모든 조합 지표와 대표 분기 시트의
차이/파트너 규칙은38절에 기록했다. 기존 audited/JSON/그림 도구는 압축본에서 따로 사용한다.

## 10. 환경, 실행 이력, 검증

Uv 환경 `env_hrm_force_estimation`은 Python 3.10.20, PyTorch 2.7.1+cu126/CUDA 12.6,
NumPy 1.26.4, pandas 2.3.1, matplotlib 3.5.1, PyYAML 6.0.2다.
`uv pip check`와 실제 CUDA 행렬 연산을 통과했고 장치는 NVIDIA GeForce RTX 4090이다.
Kernel module 580.173.02와 시스템 NVIDIA library 580.178.04가 달라 초기 CUDA 접근이 실패했다.
580.173.02 library를 `.runtime/nvidia-580.173.02`에 추출하고 **해당 프로세스 검색 경로만** 맞췄다.
시스템 driver 설치·kernel module 교체·재부팅은 하지 않았다. train/predict와 wrapper가 이를 지원한다.

22:02:53 실행에서 TCN 첫 epoch 약 172.7초 병목을 확인하고 부분 실행을 중단했다.
[분리 프로세스 벤치마크](../results/train/20260928_221428/diagnostics/convolution_benchmark.json)의
입력 `[1024, 30, 26]` TCN forward/backward 중앙값은 deterministic cuDNN 379.8 ms,
autotune cuDNN 0.964 ms였다. 이는 batch 학습 연산 시간이며 실시간 batch1 전체 지연이 아니다.
CPU float64 기준 출력·기울기 오차와 유한성을 확인했고 벤치마크 optimizer update는 0회였다.
주 실행은 `cudnn_deterministic: false`, `cudnn_benchmark: true`로 바꿔 22:14:28에 전 조합을 새로 시작했다.
같은 seed라도 비트 단위 재현성과 장치·버전 간 동일 학습 결과는 보장하지 않는다.

- 요청/수행 순서: 문서 이해 → 현황 점검 → 사용자 무부하 원본·무인 실행 승인 → 환경 준비 →
  전체 CSV/calibration 점검 → 독립 모델 구현 → 합성 검증 → 실제 학습 → 병목 검증 후 새 전체 실행.
- 해당 학습 실행 당시 전체 회귀검증: **140개 테스트, 2.675초, 통과**. 로그는 `diagnostics/tests.log`에 보존한다.
  이 검증은 코드 계약 검사이며 모델 정확도나 전체 학습 완료를 뜻하지 않는다.
- Bundle 저장 전후 두 분기 출력 일치, 입력만 있는 추론, 무부하/불확실/범위 밖 구분,
  GT 없는 force scope, validation만의 선택, 136경계, 확률 동률·균형 점수를 검증했다.
- 독립 재검산에서 첫 checkpoint validation 힘 RMSE는 원본 재계산 174.239578684 mN,
  저장 지표 174.239578640 mN으로 수치오차 내 일치했다. 이는 최종 선택 모델의 성능 보고가 아니다.
- 그림은 합성 두 mode·invalid·시간 gap으로 5개 PNG를 렌더링하고 원본 CSV hash 불변을 확인했다.
- 원본 무부하 두 기록과 개발 자료의 분석 전후 hash를 확인했다. 상세 수치·환경은 실행 JSON에 보존한다.
- 예비 실행 폴더는 삭제하지 않고 `.runtime/development_checks/train_<이전실행>`으로 이동했다.
  무부하·개발 자료·연산 벤치마크 근거는 주 실행의 `diagnostics/`에 JSON/PNG로 모았다.

## 11. 최종 결과 — 2026-09-28 22시 44분 학습·test 완료

사용자의 무인 실행 요청에 따라 환경 설치, 무부하 재분석, 고정 파일 분할, 242개 새 조합 학습,
validation 선택, test 두 파일 평가와 결과 정리를 완료했다. 주 학습은 약 30분 소요됐다.
242개 bundle 및 각 분기의 이력·분할을 확인했고, 총 484회 분기 학습이 저장되어 있다.
실행 시작과 비교한 원본 CSV/무부하 기준 51개의 hash가 일치한다.
140개 회귀검증, CSV의 확률합·원본행 보존·힘 오차 재계산 검사도 통과했다.

### 먼저 볼 파일

| 파일 | 내용 |
|---|---|
| [comparison.csv](../results/train/20260928_221428/comparison.csv) | 242조합의 validation 지표; `selected_for_test=True` 두 행에만 test 지표 추가 |
| [predictions.csv](../results/predict/20260928_224418/predictions.csv) | 두 mode × 원본 8,371행 = 16,742행; 연속 XYZ, p0/p1–p18, 기본/탐색 구간 확률 |
| [metrics.json](../results/predict/20260928_224418/metrics.json) | 모델 선택 근거, 파일별 지표, 혼동행렬, 모든 경계 후보와 support |
| [학습 그림](../results/train/20260928_221428/figures/) / [test 그림](../results/predict/20260928_224418/figures/) | 모델 비교 2개 PNG와 파일별 힘·mode별 히트맵 6개 PNG |
| [최종 검사](../results/train/20260928_221428/diagnostics/final_verification.json) | 조합/분기 수, 분할·bundle·CSV 확률합·물리 단위 재계산 검증 |

`results/` 아래 CSV는 위 두 개다. 예비·중단 실행은 `.runtime/development_checks`에 보존했다.
비교표에서 접두사 없는 성능 열은 validation, `test_`는 기본 구간의 test,
`test_optimized_`는 validation에서 경계를 정한 구간의 test 지표다.
RMSE/MAE는 mN, 정확도·recall·확률 열은 0–1이다. N/A는 성능 0이 아니다.
추론 준비 행은 각 mode 7,933개이고, 위치 조건부 test 평가의 GT 유부하는 3,536개다.
준비 전 행은 그대로 남고 예측은 NaN이다. 무부하에서도 준비된 힘 예측은 연속 실수값이다.

### 힘 모델 비교와 최종 test

아래 validation 값은 동일 힘 모델의 파트너·mode 반복 실행 중앙값이다.
새 seed 반복이나 신뢰구간 추정은 아니다. 같은 tip validation 71,869시점을 평가했다.

| 힘 모델 | Validation XYZ RMSE mN | XYZ MAE mN |
|---|---:|---:|
| CNN | 171.93 | 123.42 |
| MLP | 174.24 | 126.40 |
| small_gru | 174.69 | 126.79 |
| ResNet | 176.74 | 129.18 |
| Transformer | 181.12 | 131.72 |
| KalmanNet/GRU+MLP | 183.51 | 134.96 |
| TCN | 183.63 | 135.65 |
| GRU | 187.48 | 135.60 |
| LSTM | 189.89 | 135.50 |
| residual_tcn | 191.88 | 144.11 |
| ConvMixer | 218.86 | 169.24 |

두 mode 모두 힘 CNN이 선택됐다. 위치는 masked CNN, class0 LSTM이다.
힘 학습은 위치 방식과 독립이므로 두 선택 bundle의 힘 오차는 표시 정밀도에서 같다.

| 평가 | XYZ RMSE mN | XYZ MAE mN | Fx/Fy/Fz RMSE mN |
|---|---:|---:|---|
| Validation | 171.93 | 123.42 | 228.14 / 145.81 / 123.98 |
| Test 전체 | 123.85 | 81.28 | 158.56 / 80.26 / 120.15 |
| Test `summary_test_18-2.csv` | 90.49 | 69.08 | 파일별 축 지표는 metrics.json |
| Test `summary_test_18.csv` | 137.01 | 87.14 | 파일별 축 지표는 metrics.json |

Test 유부하 시점만의 XYZ RMSE는 **168.14 mN**, 무부하 시점은 **67.46 mN**이다.
전체 123.85 mN만으로 유부하 힘 정확도를 설명하지 않는다. 두 파일 간 성능 차이도 크다.
항상 0을 출력하는 validation 기준선 307.45 mN보다 학습 모델은 개선됐지만,
**모든 축 RMSE 50–90 mN 목표는 달성하지 못했다.**
과거 같은 녹화 앞/뒤 분할의 결과와 이번 파일 단위 validation은 평가 조건이 달라 직접 순위를 매기지 않는다.

### 위치·무부하와 구간 경계

정확 ID는 충분히 일반화하지 못했다. 아래 test ID/구간 recall은 GT 유부하 조건의 위치 진단으로,
class0의 무부하 검출 실패를 포함한 시스템 값과 구별한다.

| 방식/위치 모델 | Validation 정확 ID macro recall | Test ID18 recall | 기본 16–18 구간 test recall | 탐색 상단 구간 test recall |
|---|---:|---:|---:|---:|
| masked / CNN | 3.42% | 9.22% | 50.48% | 58.57% |
| class0 / LSTM | 6.64% | 10.27% | 31.31% | 66.09% |

Class0 test 유부하 recall은 **82.47%**, 무부하 recall은 **90.98%**, 검출 balanced accuracy는 **86.72%**다.
검출 실패까지 포함하면 유부하 ID18 정확도는 **7.92%**, 탐색 상단 구간 정확도는 **60.58%**다.
Masked에는 자체 무부하 검출기가 없어서 이 시스템 지표를 제공하지 않는다.
이 검출 평가는 무부하 범위로 파생한 라벨에 대한 것이며 실제 접촉의 별도 계측 검증이 아니다.

| 선택 위치 모델 | Validation 탐색 경계 | 기본 → 탐색 구간균형 ID macro recall | 탐색 구간의 행 가중 정확도 |
|---|---|---:|---:|
| masked CNN | 1–8 / 9–14 / 15–18 | 44.90% → 64.05% | 75.04% |
| class0 LSTM | 1–8 / 9–12 / 13–18 | 50.13% → 66.88% | 79.74% |

두 결과는 하단 경계 8에서 일치하지만 중간/상단 경계는 다르다. Class0 운용 후보로는
**1–8 / 9–12 / 13–18**을 검토할 수 있지만, 상단의 범위가 넓어져 얻은 이점과
validation 경계 탐색의 낙관성을 함께 고려해야 한다. 해부학적·기계적 최적 경계로 확정하지 않는다.
79.74%는 경계를 고르는 데 쓴 validation의 행 가중 정확도이고,
66.09%는 ID18-only test의 상단 구간 recall이다. 전체 3구간 독립 정확도 80%로 표현하지 않는다.
또한 선택 모델의 구조가 CNN과 LSTM으로 달라 이 차이를 class0 처리만의 효과라고 단정하지 않는다.

### 추론 시간과 다음 우선순위

[batch1 연산 측정](../results/predict/20260928_224418/inference_timing.json)에서
CNN/CNN의 CPU/GPU 중앙값은 0.095/0.161 ms, CNN/LSTM은 0.276/0.239 ms였다.
각 20회 준비 후 100회 측정했으며 분기별 정규화·두 네트워크·힘 역변환·softmax를 포함한다.
합성 입력이 장치에 이미 준비된 경우다. 센서/필터, 30행 준비, 파일 읽기, 장치 전송,
ROS 스케줄링은 제외하므로 전체 제어 지연이나 실시간 마감 보장이 아니다.

현재 결과에서는 모델 종류 추가보다 아래 확인이 우선이다.

1. Static ID3 각도의 매 행 부호 반전 원인을 원 수집/형상 계산 단계에서 확인한다.
2. 각 녹화의 무부하 구간·tare 상태를 함께 보존해 세션 간 영점 전이와 작은 실제 부하 검출을 검증한다.
3. ID마다 공통 자세·힘 방향·크기를 갖춘 독립 녹화를 추가해 조건과 ID가 뒤섞이는 문제를 줄인다.
4. 전체 body test와 여러 seed로 구간 경계를 재검증하고, base 제외 실험은 공통 ID의 동일 validation에서 비교한다.

이번 작업에서 body 전체 힘 모델 학습, base 제외 비교, 물리 접촉 gate 교정,
동시 다중접촉 분리와 ROS 연결은 수행하지 않았다. Tip 연속 힘·전체 ID 위치 모델의 현재 결과와 구별한다.

## 12. 2026-09-29 — 실측 XYZ와 모델별 예측값의 저장 위치 확인

- 요청: RMSE 요약 외에 정답 `fx/fy/fz`와 `fx_pred_모델명/fy_pred_모델명/fz_pred_모델명`
  형태의 시점별 자료가 있는지 확인.
- 수행·검증: 기존 test `predictions.csv`의 실제 헤더와 모델 조합을 확인했다.
  `true_fx_mN/true_fy_mN/true_fz_mN` 및 `pred_fx_mN/pred_fy_mN/pred_fz_mN`가 있으며
  N 단위 열도 별도로 있다. 파일·원본 행·시간으로 대응시킬 수 있다.
  현재 test CSV는 validation에서 선택한 두 조합만 담고, 두 조합의 **힘 모델은 모두 CNN**이다.
  `location_model=lstm`을 LSTM 힘 예측으로 해석하지 않는다.
- Validation은 242조합 각각의 `validation_predictions.npz`에 시점별 힘 예측과
  원본 trial/행 참조를 저장했다. `comparison.csv`는 이 예측을 집계한 성능 비교표다.
  확인한 CNN/CNN 파일의 `force_N`은 역정규화된 예측 71,869×3, `force_refs`는
  trial 인덱스/원본 행 71,869×2다. GT XYZ는 NPZ 안에 없으며 참조 원본 CSV의
  `fts_kalman.aligned_fx/fy/fz`와 연결해야 한다.
- 미실행/다음: 11개 힘 모델의 test 예측을 모델별 열로 합친 가로형 CSV는 아직 없다.
  필요 시 저장된 bundle로 추론·열 재구성할 수 있으며 재학습은 필요하지 않다.
  이번 확인에서는 새 학습·추론·결과 파일 생성이나 기존 모델 선택 변경을 하지 않았다.

## 13. 2026-09-29 — MATLAB 분석용 모델별 Excel 내보내기

### 요청과 구성

사용자는 모델을 직접 필터링하지 않고 Excel 시트별로 실측/예측을 읽도록 요청했다.
RMSE·MAE는 MATLAB에서 직접 계산할 예정이므로 이번 Excel은 정답·예측 행을 중심으로 구성한다.
기존 242조합의 저장된 best 분기를 사용하며 **새 학습과 기존 모델 선택 변경은 하지 않는다.**
Train replay는 학습에 사용된 CSV, validation은 고정된 개발 검증 CSV, test는 보호된 두 CSV다.
학습 데이터에 대한 replay를 일반화 성능으로 해석하지 않는다.

아래 위치에 **9개 Excel·99개 모델 시트 저장과 실제 파일 정합성 검증을 완료**했다.

```text
results/train/20260929_130543_excel/
  train/
    force_estimation_all_models.xlsx
    id_estimation_masked.xlsx
    id_estimation_class0.xlsx
  validation/
    force_estimation_all_models.xlsx
    id_estimation_masked.xlsx
    id_estimation_class0.xlsx
  export_manifest.json
  verification.json
  verification_tests.log
results/predict/20260929_130543_excel/
  force_estimation_all_models.xlsx
  id_estimation_masked.xlsx
  id_estimation_class0.xlsx
  export_manifest.json
  verification.json
```

각 Excel에는 `MLP`, `CNN`, `ConvMixer`, `ResNet`, `LSTM`, `GRU`, `TCN`,
`Transformer`, `KalmanNet`, `Small_GRU`, `Residual_TCN`의 11개 데이터 시트가 있다.
`_INFO`는 단위·행 의미·사용한 bundle 정보, `_FILES`는 숫자 file_id와 원본 파일·hash의 대응표다.
데이터 시트 안에서 서로 다른 모델이나 train/validation/test가 섞이지 않는다.

### 열과 행 계약

- 힘의 주요 열: `gt_fx_mN`, `gt_fy_mN`, `gt_fz_mN`, `pred_fx_mN`, `pred_fy_mN`, `pred_fz_mN`.
  역정규화한 N을 mN으로 변환했으며 무부하 강제0·제어용 부호반전을 적용하지 않는다.
- ID의 주요 열: `ground_truth_id`, `pred_id`, `contact_id_effective`.
  Ground truth는 확실한 유부하의 effective ID, 확실한 무부하의0이다.
  Masked의 pred_id는 조건부 segment argmax라 무부하 검출기가 아니다.
  Class0의 pred_id는0을 포함한 전체 class argmax다. 어느 방식도 예측을 GT로 덮어쓰지 않는다.
- 공통 추적 열: `file_id`, `source_row`(원본 CSV의0부터 시작하는 데이터 행),
  `elapsed_s`(파일 내 초), `continuous_block`, `load_state`.
  19자리 절대 ns 시각을 Excel 숫자로 저장하지 않아 정밀도 손실을 피한다.
- 힘은 원래 학습과 같은 입력·F/T 유효성 및 연속30행 조건을 만족하는 tip 시점만 사용한다.
  Force의 부하 판정 uncertain 행은 XYZ 정답이 유효하므로 유지한다.
- ID는 같은 유효 시점에서 load_state가 loaded/unloaded로 확정된 행만 사용한다.
  Uncertain 행은 모든 위치 모델·두 방식에서 동일하게 제외하여 정답 열을 빈칸 없이 저장한다.
- 행 제거는 **생성하는 Excel에만 적용**한다. 원본 CSV는 수정하지 않는다.
  파일 변경·행 누락·시간 공백마다 continuous_block이 바뀌므로 이를 가로질러 신호를 이어 붙이지 않는다.
  같은 역할/종류에서는 모든 모델의 file_id/source_row 목록이 동일하다.
- Masked의 조건부 ID 정확도는 load_state=loaded에서 해석한다. 무부하 행의 조건부 위치 출력이
  ID0 검출 결과가 아니므로 class0 전체 시스템 정확도와 그대로 비교하지 않는다.

| 역할 | 각 힘 모델 행 수 | 각 ID 모델 행 수(두 방식 공통) |
|---|---:|---:|
| Train | 16,361 | 495,204 |
| Validation | 71,869 | 256,152 |
| Test | 7,933 | 6,761 |

### 대표 checkpoint와 재현

힘은 `masked__force_<모델>__location_mlp`, 위치는 `<방식>__force_mlp__location_<모델>`을 사용한다.
이는 독립 네트워크의 상대 분기를 고정하는 규칙이며 test 결과로 좋은 checkpoint를 고른 것이 아니다.
동일 구조의 반복 학습은 CUDA 수치 차이가 있을 수 있어 각 시트에 정확한 bundle/hash를 기록한다.
Validation은 저장된 NPZ의 예측과 원본 행 참조를 재사용하고, train/test는 저장 모델을 replay한다.
힘은 현재 tip 전용이며 body 전체 CSV를 힘 정답 비교에 섞지 않는다.

```bash
bash scripts/hrm_python.sh scripts/export_model_workbooks.py --train-dir results/train/20260928_221428
```

```matlab
T = readtable('force_estimation_all_models.xlsx', 'Sheet', 'CNN');
fx_gt = T.gt_fx_mN;
fx_pred = T.pred_fx_mN;
```

### 수행·검증·후속 작업

- `XlsxWriter==3.2.9`를 설치하고 requirements에 추가했다. 패키지 호환 검사 통과.
- 큰 시트는 행 단위 constant-memory 방식으로 기록한다. Excel 행 한도, 중복 시트,
  기존 파일 덮어쓰기, 숫자/빈칸·수식문자열 처리와 원본 시간창 유효성 검사를 구현했다.
- 표 생성·Excel 저장 관련15개 테스트 및 전체 **155개 테스트(2.734초)**가 통과했다.
- 실제 test의 MLP로 3종 Excel 시범 실행과 전체 11종·3역할 내보내기를 마쳤다.
  13:12:38 KST 완료, 내보내기 415.50초, Excel 총 736,787,210바이트다.
  원본 CSV 49개의 hash를 전후 대조해 변경 없음을 확인했다.
  Train/predict의 export_manifest.json은 동일하며 실행 완료·정확한 bundle·행 cohort·산출물 hash를 보존한다.
- 실제 MLP 시범 파일의 전체 정답 대조와 별도 CPU 예측 복원도 통과했다.
  Excel GT와 원본 mN→학습 float32 N→mN 값의 최대 차이는 4.55e-13 mN,
  원본 CSV mN 자체와의 차이는 최대 5.94e-5 mN이었다.
  독립 CPU 복원의 대표 4개 행 예측과 Excel 차이는 최대 2.24e-5 mN이었다.
- 최종 9개 Excel의 ZIP CRC·XML 문법·헤더·행/셀 수·SHA256를 전수 검사했다.
  모델 시트 99개, 데이터 17,736,367행, 헤더 포함 145,065,206셀을 확인했으며
  오류 셀·수식·NaN/Inf 값은 없었다. 모든 모델의 시트 수·행 수가 manifest와 일치했다.
- Validation 힘 11모델의 790,559행/2,371,677개 예측 값을 저장 NPZ와 전수 대조했다.
  원본 행 참조가 모두 일치하며 예측·GT의 최대 직렬화 차이는 4.55e-13 mN이었다.
  Validation ID 22개 시트의 대표 1,430행은 18개 녹화·유부하/무부하를 포함해
  예측·GT·원본 행·부하 상태를 대조했고 모두 일치했다.
- Test 33개 시트의 236,005행을 실제 XLSX에서 전수 검사했다.
  모든 모델의 공통 행·GT·상태·원본 매핑이 일치하고 빈칸·중복 key가 없었다.
  ID의 무부하 GT0는 각 시트 3,225행이며 masked 예측에는0이 없어 GT gate 미적용을 확인했다.
- 독립 CPU 복원의 test 표본 ID 88개는 모두 일치했다. Force 표본은 Transformer에서
  최대 0.01124 mN 차이를 관측해, 주 프로세스에서 기존 CUDA·batch_size=1024 조건으로
  Transformer test 7,933행을 다시 추론했다. 행 대응은 전부 일치했고 XLSX와 예측 차이는
  최대 5.68e-14 mN이었다. 장치·batch가 다른 표본 비교와 같은 조건의 재현 검사를 구분한다.
- [통합 검증 결과](../results/train/20260929_130543_excel/verification.json)와
  [실제 테스트 로그](../results/train/20260929_130543_excel/verification_tests.log)를 실행 폴더에 보존했다.
  같은 verification.json을 test 폴더에도 저장했다. `git diff --check`도 통과했다.
- 이번 Excel 요청의 미완료 작업은 없다. 사용자는 위 MATLAB 예시로 원하는 모델 시트의
  축별 정답/예측을 직접 읽고 RMSE·MAE를 계산할 수 있다.

## 14. 2026-09-29 — 축별 RMSE 재집계와 Excel 시트 위치 확인

### 요청과 수행

- 사용자 요청: Excel에서 Fx/Fy/Fz가 보이지 않는다는 확인 요청에 이어,
  실제 예측을 보니 Fx가 특히 부정확해 보이므로 전체 XYZ 대신 축별 RMSE를 계산해 달라고 요청했다.
- 실제 Excel을 읽어 `_INFO`, `_FILES` 다음에 11개 모델 시트가 있고,
  `CNN` 등 모델 시트의 A–C열이 실측 XYZ, D–F열이 예측 XYZ임을 확인했다.
  처음 열리는 기본 시트는 `_INFO`다. 실제 사용자 화면은 보지 않았으므로 이것이
  사용자가 값을 보지 못한 원인이라고 확정하지 않는다. 이번에는 Excel 자체를 변경하지 않았다.
- `scripts/summarize_force_axes.py`를 추가해 3개 force Excel의 실제 숫자 셀에서
  11모델 × train/validation/test의 축별 RMSE·MAE를 float64로 재계산했다.
  기존 모델·원본·Excel·comparison.csv를 변경하지 않았으며 재학습/새 추론은 수행하지 않았다.
- 주 결과는 역할·모델·표본 수·축별 RMSE 3열·축별 MAE 3열만 담은 CSV다.
  [Train/validation 22행](../results/train/20260929_171211_axis_rmse/force_axis_metrics.csv),
  [test 11행](../results/predict/20260929_171211_axis_rmse/force_axis_metrics.csv)에 저장했다.
  부하 상태/원본 CSV별 지표·편향·실측 표준편차는 같은 폴더의 `analysis.json`,
  독립 계산과 출력 검증은 `verification.json`에 보존했다.

### 계산 조건과 결과

축마다 `sqrt(mean((pred_axis - gt_axis).^2))`를 계산한다. 단위는 **mN**이며,
기존 ID18 tip 힘 모델의 내보낸 유효 행을 그대로 사용한다. 무부하를0으로 만들거나,
편향을 빼거나, 부호를 뒤집지 않는다. 전체 지표는 loaded/unloaded/uncertain을 모두 포함하고
여러 CSV의 유효 행에 동일 가중치를 주므로 녹화별 RMSE의 단순 평균과 다르다.
Train 결과는 학습에 사용한 데이터의 재생 결과이며 독립 일반화 성능이 아니다.

| Test 모델 | 표본 수 | Fx RMSE (mN) | Fy RMSE (mN) | Fz RMSE (mN) |
|---|---:|---:|---:|---:|
| MLP | 7,933 | 157.20 | 96.96 | 138.06 |
| CNN | 7,933 | 158.56 | 80.26 | 120.15 |
| ConvMixer | 7,933 | 155.42 | 107.26 | 174.82 |
| ResNet | 7,933 | 159.30 | 91.57 | 115.09 |
| LSTM | 7,933 | 165.89 | 90.24 | 136.08 |
| GRU | 7,933 | 156.29 | 99.15 | 141.51 |
| TCN | 7,933 | 160.74 | 85.43 | 120.46 |
| Transformer | 7,933 | 159.93 | 108.73 | 142.35 |
| KalmanNet | 7,933 | 156.01 | 87.00 | 135.31 |
| Small_GRU | 7,933 | 154.46 | 90.68 | 131.83 |
| Residual_TCN | 7,933 | 156.66 | 119.98 | 150.18 |

11모델 중 10모델에서 Fx RMSE가 가장 크다. ConvMixer만 Fz가 더 크다.
기존 validation 선택 힘 모델 CNN의 축별 결과는 다음과 같다.

| CNN 역할/구간 | 표본 수 | Fx RMSE (mN) | Fy RMSE (mN) | Fz RMSE (mN) |
|---|---:|---:|---:|---:|
| Train 전체 | 16,361 | 97.54 | 69.98 | 90.79 |
| Validation 전체 | 71,869 | 228.14 | 145.81 | 123.98 |
| Test 전체 | 7,933 | 158.56 | 80.26 | 120.15 |
| Test 유부하 | 3,536 | 225.79 | 93.80 | 158.21 |
| Test 무부하 | 3,225 | 63.51 | 66.17 | 72.40 |
| Test 판정보류 | 1,172 | 72.58 | 70.77 | 88.15 |

CNN test 유부하 Fx 실측 표준편차는206.93 mN, 예측 표준편차는43.89 mN으로
예측의 변화폭이 현저히 작다. 같은 구간의 Fy/Fz 실측 표준편차는229.64/297.22 mN이라
Fx 실측 변동이 가장 커서 절대 RMSE도 가장 큰 상황은 아니다.
유부하 Fx 편향(pred−GT)은+84.72 mN이고 편향을 제외한 오차 표준편차도209.29 mN이라
일정 offset만으로 전체 오차를 설명할 수 없다. 센서 감도·학습 분포·모델 구조 중
원인을 특정하거나 현재 test에 맞춰 수정하지 않았다. 기존 validation 모델 선택을 유지한다.

### 검증·실패 이력·후속 작업

- 첫 집계 시도는 load_state 문자열 열의 헤더까지 행으로 세어 유효성 검사에서 중단됐다.
  결과 파일 생성 전이었으며, 헤더를 분리한 뒤 다시 실행해 33개 모델 시트를 모두 집계했다.
- 세 원본 Excel hash가 기존 export_manifest 및 집계 전후에 일치했다.
  같은 역할의 11모델은 원본 행·GT·부하 상태가 모두 동일했다.
- Validation 11모델의 축별 RMSE·MAE를 기존 comparison.csv의 같은 대표 bundle과 대조했다.
  최대 차이는5.68e-14 mN이었다. 축별 제곱 RMSE의 평균과 pooled XYZ RMSE 제곱의 관계도 확인했다.
- 별도 test 계산과 11모델의 축별 RMSE·MAE가 일치했고 최대 차이는0 mN이었다.
  CNN의 부하 상태별 축 RMSE도 일치했다. 저장 CSV 22/11행의 숫자·중복·누락 검사와
  `git diff --check`가 통과했다. 이번 집계에는 학습 코드를 바꾸지 않아 전체 학습 테스트를 반복하지 않았다.
- 이번 요청의 미완료 작업은 없다. Fx 원인 규명을 위한 입력 반응·훈련 범위 분석이나
  모델 수정 실험은 이번 축별 지표 재집계와 구분되는 후속 작업이다.

재현 명령:

```bash
env_hrm_force_estimation/bin/python scripts/summarize_force_axes.py \
  --export-manifest results/train/20260929_130543_excel/export_manifest.json
```

## 15. 2026-09-29 — 직전 축별 RMSE 표의 평가 대상 확인

- 요청: 방금 제시한 결과가 testset으로 비교한 것인지 확인.
- 수행·검증: `results/predict/20260929_171211_axis_rmse/force_axis_metrics.csv`와
  `analysis.json`을 다시 읽었다. 표의 11모델 모두 dataset_role=test, 표본 수7,933이었다.
  대상은 `datasets/test/summary_test_18-2.csv`, `summary_test_18.csv` 두 독립 녹화이며
  둘 다 effective ID18 tip이다. Train/validation 축별 결과는 별도 CSV다.
  기존 validation 기준 모델 선택이 유지되었음을 확인했다.
- 미완료/다음: 없음. 새 학습·추론·평가 파일 변경은 수행하지 않았다.

## 16. 2026-09-29 — Segment ID 추정 성능 재요약

- 요청: segment_id 추정 능력을 다시 요약.
- 수행·검증: 주 학습 `comparison.csv`의 selected_for_test 두 행과 기존 test
  `metrics.json`의 overall/optimized_overall을 대조했다. 위치 모델은 masked CNN과
  class0 LSTM이며 모두 validation 선택 결과다. 정확 ID·구간·유무부하 지표가 일치했다.
  `independent_evaluation.py`를 읽어 conditional ID는 ID0을 제외한 argmax,
  class0 실제 ID는 ID0을 포함한 argmax임을 확인했다.

정확한 ID1–18 구별 성능은 낮다. Validation 유부하178,978행에서 ID별 재현율을
같은 가중치로 평균한 macro recall은 masked CNN3.42%, class0 LSTM6.64%다.
이 수치를 단순 행 가중 정확도나 무부하를 포함한 시스템 정확도와 혼동하지 않는다.

독립 test는 ID18 두 녹화이며 아래 비교는 **GT 유부하3,536행** 기준이다.
Class0는 ID0 오판을 오답에 포함한다. Masked는 조건부 위치 출력만 있으며 자체 무부하 검출은 없다.

| Test 유부하 위치 지표 | Masked CNN | Class0 LSTM |
|---|---:|---:|
| 정확히 ID18 출력 | 9.22% | 7.92% |
| 기본 끝단 구간16–18 인식 | 50.48% | 28.73% |
| Validation 탐색 상단 구간 인식 | 58.57% | 60.58% |

구간 인식은 해당 구간의 ID 확률 합으로 선택한다. Class0에서 전체 class argmax가0이면
구간 출력도 무부하로 처리하므로 유부하 구간 평가에서는 오답이다.
탐색 경계는 masked1–8/9–14/15–18, class0 1–8/9–12/13–18이다.
탐색 상단 폭이 서로 달라58.57%와60.58%만으로 구조나 무부하 처리 방식의 우열을 단정하지 않는다.
기존에 보고한 class0 ID18 10.27%, 기본 상단31.31%, 탐색 상단66.09%는
무부하 판정을 적용하지 않은 조건부 위치 진단이며 위 실제 출력 기준과 다르다.

Class0 LSTM의 test 부하 검출은 유부하 재현율82.47%(2,916/3,536),
무부하 재현율90.98%(2,934/3,225), 두 재현율 평균86.72%다.
판정보류1,172행은 위치·검출 평가에서 제외된다. 이는 무부하 범위로 파생한 라벨의 검출 성능이며
정확 ID 분류 성능이나 독립 계측 접촉 검증이 아니다.

탐색 경계의 validation 구간 행 가중 정확도75.04%/79.74%는 경계 선택에 사용한
동일 validation의 위치 진단이다. 구간·ID를 균형 있게 평균한 점수는64.05%/66.88%다.
독립 test에 ID18만 있으므로 이 실험만으로 전체18개 ID나 아래/중간/끝단3구간의
독립 성능을 검증했다고 주장할 수 없다. 현재는 정확 ID보다 넓은 구간 구분이 나은 수준이며,
정확 ID를 안정적으로 알아내는 수준에는 도달하지 못했다.

- 미완료/다음: 이번 요약 요청은 완료했다. 새 학습·추론·모델/구간 선택 변경 및 결과 파일 변경은 없다.
  전체 ID의 독립 test 검증은 기존 후속 과제로 남는다.

## 17. 2026-09-29 — ID18만 사용한 별도 학습·test 비교 (완료)

- 요청: segment_id18만 학습·test하고 ID1–17은 학습에서 제외한 결과 확인.
  기존 힘 분기는 이미 ID18 전용이었고 위치 분기는 ID1–18 전체였음을 설명했다.
  앞선 유무부하 검출 수치는 class0 LSTM의 결과이며 masked CNN 자체에는 검출기가 없음을 설명했다.
- 범위 질문을 제시한 뒤 별도 답변이 없는 동안 데이터 준비를 검증했다.
  이후 ID18 전용 힘 추정 + class0 무부하/ID18 이진 분류 비교로 해석하고 진행한다고 알렸다.
  ID18 단일 class의 masked 위치 출력은 상수18이므로 유의미한 위치 정확도 비교에서 제외한다.
- 데이터 준비: active_ids만 바꾸면 다른 ID의 무부하 행과 위치 scaler가 남는 현 구현을 확인했다.
  기존 audit의 정확한 hash로 ID1–17 녹화 전체를 제외해, 분할/정규화/시간창 학습 전에
  ID18 CSV5개만 남겼다. 원본은 수정·이동하지 않았다.
  Train2개·validation1개·test2개의 경로/hash가 이전 ID18 분할과 정확히 일치했다.
  유효 시점은 각각16,361/71,869/7,933개다. 기본 입력26개와 무부하 교정·학습 설정은 유지한다.
- 새 실행: `results/train/20260929_181303_id18_only`.
  실험 설정은 `.runtime/20260929_181303_id18_only/config_requested.yaml`이며
  학습 실행 폴더의 resolved 설정에도 저장한다. Class0만 사용해 힘11×위치11=121조합을
  새로 학습한다. 기존242조합 결과를 덮어쓰지 않는다.
- 진행 상태: **121조합·242분기 학습 및 test 평가 완료**. 원본 ID18 분할과 무부하 교정은
  이전 실험과 동일하다. 단일ID 조건부 정확도100%를 접촉 위치 식별 성능으로 주장하지 않는다.
  이번 실험에서 의미 있는 위치 지표는 ID0/18 검출이다.

### 모델 선택과 test 결과

단일ID에서는 conditional ID macro recall이 항상1이므로 모델 선택 지표로 쓸 수 없다.
Test 평가 전에 validation 힘 RMSE 최저(기존 수치 동률 허용1e-3 mN),
validation 부하 balanced accuracy 최고, CE 최저 순으로 선택한다고 정했다.
`predict.py --location-selection-metric load_balanced_accuracy`를 추가했고 class0 전용으로 제한했다.
기존 전체ID 기본 선택 방식은 그대로 유지한다. 선택된 bundle은 힘CNN/위치LSTM이다.
기존 bundle을 가져오거나 가중치를 조합하지 않고 새121조합 중 해당 bundle 그대로 사용했다.

| 선택 모델 지표 | Validation | Test |
|---|---:|---:|
| CNN Fx RMSE (mN) | 228.14 | 158.56 |
| CNN Fy RMSE (mN) | 145.81 | 80.26 |
| CNN Fz RMSE (mN) | 123.98 | 120.15 |
| CNN XYZ RMSE (mN) | 171.93 | 123.85 |
| LSTM 유무부하 balanced accuracy | 77.07% | 81.42% |

Test 유부하3,536행 중 ID18로 검출한 행은2,815개(79.61%), 놓친 행은721개다.
무부하3,225행 중 ID0으로 검출한 행은2,684개(83.22%), 오검출은541개다.
전체 확정 라벨6,761행의 ID0/18 정확도는81.33%다. 판정보류1,172행은 검출 평가에서 제외했다.
이는 접촉 위치가18로 제한된 상황에서의 유무부하 검출이고, ID1–18 중 위치를 식별한 정확도가 아니다.

| LSTM test 부하 검출 | 기존 전체ID 학습 | 새 ID18 전용 학습 |
|---|---:|---:|
| 유부하 재현율 | 82.47% | 79.61% |
| 무부하 재현율 | 90.98% | 83.22% |
| 두 재현율 평균 | 86.72% | 81.42% |

이번 비교에서 ID18 전용의 balanced accuracy는5.30%p 낮았다.
접촉 class 수·학습 녹화·위치 scaler가 함께 바뀐 비교이므로 차이의 원인을 한 요인으로 단정하지 않는다.
힘 분기는 이미 ID18만 학습하던 구조였고, 새 force scaler가 이전 것과 정확히 일치했다.
새 location scaler도 ID18 train2개만 사용해 force scaler와 정확히 일치했다.
힘 성능은 기존 결과와 표시 정밀도에서 같다.

고정 파트너 대표 bundle의 test 검출 결과는 다음과 같다. LSTM 선택은 위 validation 규칙으로 고정했으며,
이 표에서 test 점수가 높다는 이유로 모델을 바꾸지 않았다.

| ID0/18 모델 | 유부하 재현율 | 무부하 재현율 | Balanced accuracy |
|---|---:|---:|---:|
| MLP | 88.97% | 70.05% | 79.51% |
| CNN | 90.87% | 67.63% | 79.25% |
| ConvMixer | 79.52% | 88.43% | 83.98% |
| ResNet | 93.58% | 50.08% | 71.83% |
| LSTM | 79.61% | 83.22% | 81.42% |
| GRU | 63.09% | 41.89% | 52.49% |
| TCN | 92.85% | 47.60% | 70.22% |
| Transformer | 85.21% | 26.26% | 55.74% |
| KalmanNet | 80.12% | 83.47% | 81.80% |
| Small_GRU | 58.54% | 42.67% | 50.60% |
| Residual_TCN | 90.50% | 60.96% | 75.73% |

### 산출물·검증·남은 작업

- [학습 실행](../results/train/20260929_181303_id18_only/)에121조합 비교표·bundle·이력·설정·원본 목록을 보존했다.
- [Test 실행](../results/predict/20260929_181303_id18_only/)에 선택 bundle의 predictions.csv/metrics.json을 저장했다.
- 각 실행의 `summary/force_metrics.csv`, `summary/contact_detection_metrics.csv`에
  모델별 지표를 정리했다. Train 폴더는 train/validation 각각11행, predict 폴더는 test11행이다.
  검출 비율 열은0–1, 힘 지표 열은mN이다. `validation_selected_architecture`는 선택된 구조 표시이며,
  대표 Excel은 힘 class0/force_MODEL/location_mlp, 검출 class0/force_mlp/location_MODEL을 사용한다.
- `excel/`에는 모델별 정답/예측 시트를 저장했다. Train/validation 각각 힘1개+ID class0 1개,
  test 힘1개+ID class0 1개로 총6개 workbook·66개 모델 시트다.
  새 workbook은 처음 열면 MLP 데이터 시트가 보이도록 활성화했다. 기존 Excel은 변경하지 않았다.
- 단일 class0 모드를 지원하도록 exporter를 일반화했고, 실제66개 시트의 유한값·헤더·행 대응·GT·hash를
  다시 읽어 확인했다. ID 출력은0/18만 있으며 train13,332/validation64,212/test6,761개의 확정 라벨 행이다.
  각 모델의 validation force·검출 지표를 같은 bundle의 comparison.csv와 대조해 최대 차이1.14e-13이었다.
- Test 선택 결과를 predictions.csv에서 재집계했다. ID 혼동행렬이 정확히 일치했다.
  처음 힘 RMSE 검산 허용오차1e-9 mN은 CSV 숫자 직렬화/재읽기 차이1.27e-7 mN으로 실패했다.
  차이를 기록하고 허용오차1e-6 mN으로 확인했다. 학습·Excel 값이나 정답을 수정하지 않았다.
- Binary 선택이 형식적 ID100%나 test 지표로 고르지 않는 회귀검증을 추가했고
  전체 **156개 테스트(2.786초)**가 통과했다. 기존 전체ID 선택 테스트도 통과했다.
  5개 원본 CSV hash·기존 ID18 분할·동일 무부하 교정을 최종 확인했다.
  `verification.json`, 실제 실행/테스트 로그, 코드 snapshot을 새 실행 폴더에 저장했다.
- 이번 요청의 미완료 작업은 없다. ID18 전용 모델의 ID1–17 접촉 구별·거절 능력은 학습/검증하지 않았고,
  기존 전체ID 모델을 대체하도록 배포하거나 제어 코드에 연결하지 않았다.

재현 예시(새 output 경로를 지정한다):

```bash
bash scripts/hrm_python.sh train.py \
  --config results/train/20260929_181303_id18_only/config_requested.yaml --output results/train/새날짜_id18_only
bash scripts/hrm_python.sh predict.py --train-dir results/train/새날짜_id18_only \
  --location-selection-metric load_balanced_accuracy --output results/predict/새날짜_id18_only
```

## 18. 2026-09-29 — 유무부하 힘 범위 설명 및 10%·20% 확대 민감도

- 요청: 검출률 계산에 쓰인 힘 범위의 설정 방법과 범위를 조금 넓히는 방안 문의.
- 수행: 현재 ID18 실험의 calibration.json과 `calibrate_no_load`/`load_states` 구현을 대조했다.
  원본 무부하 기록2 및 ID18 train/validation만 읽고, 중심은 고정한 채 off/on 두 경계의 반폭을
  각각1.0/1.1/1.2배로 바꾼 복사 배열의 라벨 변화를 계산했다. Test는 이번 분석에서 읽지 않았다.
  모델 추론·재학습·기존 라벨/설정/결과 수정은 하지 않았다.

현재 기준은 `aidin_FT_sensor_validation_2/csv/summary.csv`의 Kalman aligned hrm_base XYZ다.
앞70%(1,957행)에서 축별 median 중심과 표준편차를 구하고,
`max(|F_axis-center_axis|/std_axis)`의95%/99.5% 경험적 분위수로 off/on을 정했다.
이는 각 축95% 신뢰구간이나 무접촉 물리 보증이 아니다. 뒤840행은 같은 녹화의 시간 holdout이다.

| 축 | 현재 무부하 범위 (mN) | 현재 유부하 경계 상자 (mN) |
|---|---:|---:|
| Fx | -186.97 ~ 57.78 | -224.57 ~ 95.38 |
| Fy | -96.91 ~ 134.15 | -132.41 ~ 169.65 |
| Fz | -259.05 ~ 92.00 | -312.98 ~ 145.93 |

세 축이 모두 무부하 범위 안이면 ID0 정답이다. 한 축이라도 더 넓은 on 경계에 도달하거나
벗어나면 유부하 정답이며, 나머지는 판정보류로 위치 loss/검출 평가에서 제외한다.
중심은[-64.59,+18.62,-83.53]mN이다. 0 중심 범위가 아니며 이 중심을 힘 회귀 정답에서 빼지 않는다.
이는 **실측 F/T로 정답 라벨을 만드는 규칙**이다. 현재 ID18 class0 모델의 실제 예측은
신경망의 p0/p18 중 큰 확률(동률은0)을 선택하므로, F/T 범위 숫자만 바꾸어도 저장 모델의
출력이 바로 바뀌는 것은 아니다. 현재 검출률은 그 예측과 기존 범위의 정답을 비교한 값이다.

### 폭을 넓혔을 때의 실제 라벨 변화

| 반폭 배율 | 무부하 holdout840행 중 무부하 라벨 | 유부하 오라벨 | ID18 train 기존 유부하→판정보류 |
|---|---:|---:|---:|
| 현재1.0 | 815행(97.02%) | 2행(0.238%) | 0행 |
| 1.1(+10%) | 832행(99.05%) | 1행(0.119%) | 1,024행 |
| 1.2(+20%) | 835행(99.40%) | 0행(0.000%) | 1,770행 |

표는 힘 범위 규칙의 라벨 포함률이며 **LSTM의 무부하 재현율83.22%를 재계산한 표가 아니다.**
원래 train 유부하 라벨은6,892행이므로10% 확대 시14.86%,20% 확대 시25.68%가 판정보류로 빠진다.
Validation에서는 기존55,963개 유부하 라벨 중 각각3,410/6,617행이 판정보류로 이동했다.
이번10%/20% 확대에서 기존 확정 유부하가 곧바로 무부하로 이동한 행은0개이며,
기존 판정보류에서 무부하로 이동한 train 행은각1,039/2,081개다.
실제 작은 접촉이 그 판정보류 영역에 있을 수 있으므로 무부하 포함률 상승만으로
실제 접촉 검출 성능 향상을 단정할 수 없다. 840행에서0회라는 값도 미래 오경보0 보장은 아니다.

10% 확대는 비교 후보로 검토할 수 있으나 아직 새 기준을 선택하지 않았다.
적용을 비교할 때는 정답 생성 기준과 모델을 함께 고정해 학습/validation에서 확인해야 하며,
test 정답만 넓혀 점수가 올라간 것을 모델 개선으로 해석하지 않는다.
연속 힘 회귀의 실측 정답·예측값은 범위 확대의 직접 변경 대상이 아니므로 전체 힘 RMSE도 그대로다.

- 산출물: [range_sensitivity.csv](../results/train/20260929_182936_no_load_range_analysis/range_sensitivity.csv),
  같은 폴더 analysis.json에 정확한1.0/1.1/1.2배 경계·방법·원본 hash·전체 라벨 수를 기록했다.
- 검증: 현재 배율1.0의 무부하 fit/holdout 포함률이 기존 calibration과 일치했고,
  ID18 train/validation 시점의 기존 라벨이 loader 결과와 전부 일치했다.
  확대 시 무부하 라벨 수 비감소·유부하 라벨 수 비증가를 확인했고, 읽은 원본4개 hash가 유지됐다.
- 미완료/다음: 범위 설명과 민감도 분석은 완료. 확대 기준의 모델 재학습이나 최종 기준 변경은 수행하지 않았다.

## 19. 2026-09-29 — 평균 offset 보정 및 무부하 경계10% 확대 적용

### 요청과 적용 범위

- 요청: 무부하 기록의 평균이0이 아니므로 offset으로0을 맞춘 뒤 범위/확률을 비교하고,
  무부하 범위를10% 늘리기로 함. 이전 문맥의 범위 확대 요청으로 해석했고 녹화 길이/행 수는 늘리지 않았다.
- 수행: 무부하 기록2의 기존 fit 앞70%(1,957개 유효 행) 산술평균을 offset으로 정했다.
  `F_corrected = F_recorded - mean_fit`으로 판정용 좌표를 만들고, corrected 힘의
  max-axis 정규화 score에95%/99.5% 분위수를 적용한 뒤 두 경계 반폭을1.1배 했다.
  원본 CSV·기존 model bundle·과거 calibration·힘 회귀 정답은 변경하지 않았다.
- 설정: `configs/train.yaml`의 `calibration.center_method: mean`, `range_multiplier: 1.1`에 반영했다.
  이번 ID18 실험 범위를 유지한 재현용 설정과 데이터 준비 결과는
  [20260929_185223_mean_zero_range110](../results/train/20260929_185223_mean_zero_range110/)에 저장했다.
  다른 ID의 녹화 제외·기존 ID18 train/validation/test 파일과 hash가 유지됐다.

### 평균0 좌표의 범위와 포함률

빼는 평균은 Fx **-67.36210**, Fy **+19.59298**, Fz **-85.57272 mN**이다.
따라서 corrected Fx=기록 Fx+67.36210, Fy=기록 Fy−19.59298, Fz=기록 Fz+85.57272 mN이다.
Offset은 fit 구간만 사용했다. Fit 구간 corrected 평균은 수치 오차 수준0이고,
후반840행의 corrected 평균은[+5.45476,-2.47038,-18.43771]mN이다.
전체2,797행의 corrected 평균도[+1.63818,-0.74191,-5.53724]mN으로,
확인 구간까지 별도로 다시 영점 조정해0으로 만든 것은 아니다.

아래 모든 경계는 **평균 offset을 한 번 뺀 corrected 힘**에 적용하는 대칭 범위다.

| 축 | 평균 중심 기본 무부하 범위 (mN) | 적용:10% 확대 무부하 범위 (mN) | 적용:10% 확대 유부하 경계 (mN) |
|---|---:|---:|---:|
| Fx | ±122.11 | ±134.33 | ±176.51 |
| Fy | ±115.29 | ±126.81 | ±166.64 |
| Fz | ±175.15 | ±192.67 | ±253.17 |

세 축 모두 무부하 범위 안이면 ID0, 한 축이라도 on 경계에 도달하거나 넘으면 유부하,
나머지는 판정보류다. 저장 calibration의 `center_N`/`offset_to_subtract_N`은 기록 좌표의 offset이고,
`corrected_off/on_lower/upper_N`은0 중심 경계다. `load_states`는 기록 좌표의 힘을 받아
내부에서 center를 한 번 빼므로 이미 보정한 힘에 같은 offset을 중복 적용하지 않는다.

| 기준 | 무부하 holdout840행 중 무부하 | 판정보류 | 유부하 오라벨 |
|---|---:|---:|---:|
| 기존 median 중심 | 815 (97.02%) | 23 (2.74%) | 2 (0.238%) |
| 평균 중심, 확대 전 | 816 (97.14%) | 22 (2.62%) | 2 (0.238%) |
| 평균 중심,10% 확대 적용 | 832 (99.05%) | 7 (0.83%) | 1 (0.119%) |

단순 좌표 평행이동만으로는 데이터 분포 폭이나 기존 판정이 변하지 않는다.
실제 force와 기존 bounds/center를 같은 평균만큼 함께 옮겼을 때 모든 기존 라벨이 유지됨을 검증했다.
위 첫 행과 둘째 행의 차이는 기존 median 중심을 mean 중심으로 바꾸고 분위수를 다시 계산한 영향이며,
둘째 행과 셋째 행의 차이는 반폭10% 확대한 영향이다.
99.05%는 **알려진 무부하 기록의 포함률**이며 모델 검출률·posterior 확률·미래 무접촉 보증이 아니다.

ID18 train16,361개 유효 시점의 새 라벨은 무부하7,295/보류3,146/유부하5,920이다.
Validation71,869개는 무부하10,230/보류8,751/유부하52,888이다.
기존 median 기준 유부하 중 train972개·validation3,075개가 판정보류로 이동했다.
따라서 확대된 기준이 작은 접촉에 미치는 영향과 새 모델의 검출 성능은 구분해 평가해야 한다.

### 검증·산출물·완료 상태

- [bounds_comparison.csv](../results/train/20260929_185223_mean_zero_range110/bounds_comparison.csv)에
  기존/평균 중심/평균 중심+10%의 offset과 기록/보정 좌표 경계를 저장했다.
  [coverage_comparison.csv](../results/train/20260929_185223_mean_zero_range110/coverage_comparison.csv)에
  무부하 fit/holdout 및 ID18 train/validation 포함률을 저장했다.
- 같은 폴더 `applied_mean_zero_plus10_calibration.json`과 `prepared_data/`에
  적용 교정·원본 목록·고정 분할·해결된 설정을 저장했다. 기본 설정에서 구한 교정이
  ID18 준비 설정의 교정과 정확히 일치했다. Test는 분할/원본 검증 단계에서만 읽었고,
  offset·경계 결정이나 포함률 비교에 사용하지 않았다.
- 평균0·경계1.1배·동일 좌표계 라벨 동치·후반 데이터가 offset/경계 fit에 영향을 주지 않음·
  힘 회귀 정답 보존·잘못된 옵션 거절을 검사하는 테스트2개를 추가했다.
  전체 **158개 테스트(2.814초)**가 통과했다. 옵션 없는 옛 설정은 median/1.0으로 유지했다.
- 초기 부가 JSON 저장은 NumPy 배열을 기본 JSON encoder가 처리하지 못해 중단됐다.
  이미 성공한 계산/준비 결과를 사용하고 저장소의 배열 지원 JSON 저장 함수로 마무리했다.
  입력·기준 값·모델을 오류 해결 과정에서 변경하지 않았다.
- 최종 원본6개(무부하1+ID18 실험5) hash와 기존 파일 분할을 확인했다.
  Train/validation 힘 회귀 정답과 유효 시간창이 이전과 동일했고, 설정/기록/CSV 간 값이 일치했다.
  `analysis.json`과 실제 테스트 로그를 보존했다.
- 이번 요청의 평균 보정·범위 비교·10% 확대 설정 적용은 완료했다.
  모델 재학습/새 모델 검출률은 아직 미실행이며, 기존81.42% 검출률은 이전 라벨 기준 결과로 유지한다.

## 20. 2026-09-29 — 새 무부하 경계와 ID1–18 힘 학습의 영향 질문

- 요청: 평균 offset 보정·10% 확대 경계로 ID1–18 힘 추정을 학습하면 결과가 달라지는지 설명.
- 확인: 현재 `configs/train.yaml`은 `force_scope: tip`이다. 기존 전체 ID 비교에서도
  위치 모델만 ID1–18을 학습했고 힘 모델은 ID18만 학습했다.
  `independent_engine.py`의 시간창 선택·정답·eligible 조건·회귀 loss를 확인했다.
  힘 모델은 유효한 실측 XYZ를 무부하/판정보류까지 사용하며 부하 라벨로 회귀를 마스킹하거나
  정답을0으로 바꾸지 않는다. 따라서 경계만 바꾸면 힘 학습 데이터/정답은 그대로이며,
  위치 학습 라벨과 유부하·무부하별 평가 집계는 달라질 수 있다.
- ID1–18 녹화를 힘 학습에 실제 포함하려면 `force_scope: all_single_contact`가 필요하다.
  `active_ids`만 변경하는 것은 힘 학습 범위 확대가 아니다. 전체 ID를 포함하면 학습 자료와
  train 정규화가 바뀌므로 힘 결과도 달라질 수 있으나, 끝단/Fx 개선을 보장하지 않는다.
  입력 변화가 작은 초기 ID의 구분 한계가 있으며, 이때 목표는 각 단일 접촉 위치에 가한 힘이지
  body 접촉 중 별도 끝단 힘을 측정한 정답이 아니다.
- 다음 비교 제안: 새 무부하 기준과 기존 녹화 역할을 고정하고 ID18 전용/전체 ID 힘 모델을
  공통 ID18 validation·test의 축별 RMSE/MAE로 비교한다. 전체 ID 모델의 body 성능은
  ID별/구간별 validation으로 따로 평가한다. 현재 test는 ID18뿐이므로 독립 body 성능은 확인할 수 없다.
- 수행 범위: 코드와 설정 확인 및 설명 기록만 완료. 이번 질문으로 설정을 변경하거나
  재학습하지 않았으며 새 성능 수치는 없다. 실행 코드 변경이 없어 테스트는 재실행하지 않았다.

## 21. 2026-09-29 — ID 성능 질문 의도 정정과 두 힘 모델 비교 범위 확인

- 사용자 정정: 힘은 유부하/무부하와 무관하게 연속 회귀하며, 새 경계로 좋아지는지 확인하려던
  대상은 ID 구분 성능이었다. ID18 전용/ID1–18 전체 힘 모델을 별도 학습하자는 제안인지 확인했다.
- 설명: 경계 확대는 입력 변화가 작은 무부하 근처 표본에 실험 ID를 강제하는 부담을 줄일 수 있어
  ID 성능 개선 가능성이 있으나 실측 개선은 아직 모른다. 작은 실제 접촉이 판정보류 또는
  무부하로 분류되는 효과도 있어, 정확 ID·세 구간 성능과 무부하/유부하 검출을 따로 평가해야 한다.
  기존/신규 위치 모델은 공통 평가 행과 동일한 평가 라벨 기준으로 비교하고, 경계 변경으로
  평가에서 빠지거나 라벨이 바뀐 행 수를 함께 보고한다. 쉬운 표본만 남은 효과를 모델 개선으로 단정하지 않는다.
- 힘 모델 비교 제안은 ID18 자료만 학습한 모델과 ID1–18 자료를 학습한 모델을 각각 두는 것이다.
  두 경우 모두 위치 모델의 범위는 ID1–18이다. ID18 전용 힘 모델이라는 말은 위치까지 ID18만
  학습한다는 뜻이 아니다. 독립 분기이므로 힘 모델 범위 확대가 위치 모델 성능을 직접 높이지 않는다.
  기존 17절의 ID0/18 이진 위치 실험과 이번 전체 위치 비교를 구별한다.
- 수행/검증: 현재 요약과20절을 확인하고 사용자 의도와 비교 범위를 기록했다.
  이번 확인 질문에 대해 재학습·설정 변경·새 수치 산출은 하지 않았다. 문서만 변경했다.

## 22. 2026-09-29 — 끝단 힘 최우선·body 구간 감지 모드와 과거80 mN 확인

- 요청: 끝단 ID18 힘 추정 정확도가 최우선이며 전용 모델이 반드시 필요함을 재확인.
  끝단 힘 제어와 선택적으로 활성화하는 body contact 감지 모드를 구분하고,
  body 구간 인식은 약90% 이상을 목표로 한다. 과거 약80 mN과 현재100 mN대 차이에 의문을 제기했다.
- 확인 근거: `archive/legacy_materials_20260928.tar.gz` 안의 `CODEX_HANDOFF.md` 및
  `docs/WORK_LOG.md`를 읽었으며 원본을 복원/수정하지 않았다. 과거 front 추가학습 기록에는
  test 최저 ResNet XYZ RMSE83.43 mN(Fx108.97/Fy60.81/Fz72.86), validation 선택 LSTM
  XYZ92.65 mN(Fx119.63/Fy69.70/Fz81.14)이 있다. 사용자가 기억한80 mN이 어느 값인지 확정하지 않는다.
  당시 새 test는2,572행이며 같은 녹화 앞/뒤 validation과 부모 가중치/scaler 기반 추가학습이었다.
  현재는 파일 단위 validation·새 초기화 학습이며 선택 CNN test7,933행의 XYZ RMSE123.85 mN,
  Fx158.56/Fy80.26/Fz120.15 mN, XYZ MAE81.28 mN이다. 현재 CSV와 기록의 수치를 대조했다.
- 해석: test 최저모델과 validation 선택모델, 평가 녹화/표본, 학습·분할 조건이 다르므로
  83.43→123.85 mN을 같은 조건에서의 성능 악화로 단정하거나 원인을 특정하지 않는다.
  당시에도 ResNet의 Fx는108.97 mN으로 모든 축90 mN 이하를 달성한 것은 아니다.
  현재 MAE81.28와 RMSE123.85도 구별한다. 과거 결과 원본/체크포인트는 현재 results 목록에서
  확인되지 않아 이번에는 보존 문서 확인이며 과거 예측 재계산은 수행하지 않았다.
- 방향: 필수 모델은 ID18 전용 힘 모델과 별도 위치/무부하 모델이다. 전체 ID 힘 모델은
  현재 우선 작업에서 제외하고 이전 비교 제안으로 보존한다. Body 모드의 출력은 접촉 여부·구간·
  ID 확률이며, 모드 전환/제어 연결/접촉 시 제어 동작은 아직 구현하거나 확정하지 않았다.
  구간90%는 목표이지 달성 수치가 아니다. 구간별 재현율과 무부하 오경보·접촉 미검출을 함께
  확인해야 하며 현재 ID18-only test로 body 전체 독립 성능을 입증할 수 없다.
- 수행/검증/다음: 과거 기록과 현재 CSV를 읽고 현재 요약·작업 규칙을 갱신했다.
  학습/설정/제어 코드는 변경하지 않았고 새 학습·테스트는 실행하지 않았다.
  끝단 개선의 후속 비교는 동일 평가 데이터와 지표로 진행하며 과거 모델 원본 가용성을 먼저 확인한다.

## 23. 2026-09-29 — 과거 추가학습의 의미 확인

- 요청: 앞서 언급한 과거 추가학습이 무엇인지 확인.
- 확인: 보존 archive의 HANDOFF(2026-09-27 완료 항목), WORK_LOG, 당시
  `configs/tip_front_finetune_20260927.json`을 대조했다. 기록상9월26일 학습한 기존 tip11종의
  가중치를 출발점으로9월27일 신규 ID18 front_1/2/3을 각180epoch 학습한 fine-tuning이다.
  부모 정규화 통계는 고정하고 optimizer는 새로 시작했으며 front_testset_1은 학습에서 제외했다.
  같은 새 test에서 ResNet91.39→83.43 mN, validation 선택 LSTM98.72→92.65 mN이었다.
- 구분: 현재9월28일 전체 조합과9월29일 ID18 전용 실험은 각각 새 초기화 학습이며,
  위 과거 checkpoint를 이어서 학습한 결과가 아니다. 과거 실행 사실의 근거는 보존 문서와
  설정이며 이 세션에서 과거 checkpoint/예측을 직접 재검증한 것은 아니다.
- 수행/검증/미완료: 기록과 설정의 일치 확인 및 용어 설명만 수행했다. 코드·학습 설정 변경이나
  새 학습은 없고 테스트는 재실행하지 않았다. 과거/현재 오차 차이의 원인은 아직 분리 검증하지 않았다.

## 24. 2026-09-29 — static 제외 요청, 끝단 힘11종 학습·동일 test 평가

### 요청과 데이터 범위

- 사용자 요청: summary_1부터 summary_18-2까지의 CSV로 static을 제외하고 학습·test.
  목록 확인 결과 동적 CSV30개(ID1–6 각1개, ID7–18 각2개), static18개가 있다.
  원본은 이동/수정하지 않았으며 이번 설정의 정확한 hash 제외 목록으로 static을 차단한다.
- ID1–6은 각1녹화여서 기존 whole-CSV per-ID 분할은 오류로 중단된다. 무단 시간분할 대신
  사용자에게 (1)ID1–6 학습 전용/ID7–18 validation, (2)이번에는 끝단만,
  (3)ID1–6에 한해 시간분할 중 선택을 질문했다. 답변 전에는 전체 ID 위치 학습을 시작하지 않았다.
- 독립적으로 진행 가능한 최우선 ID18 힘11종은 학습·평가를 완료했다.
  train `summary_18.csv` 9,485개 창, validation `summary_18-2.csv` 6,876개 창,
  test 기존 두 파일7,933개 창이다. ID18의 seed42 녹화 단위 분할이며 test 역할/hash는 이전과 동일하다.
  summary_18-2의 raw ID1→effective18은 기존의 정확한 hash 한정 확인 계약을 유지한다.

### 학습과 모델 선택

- 실험 설정: [config_requested.yaml](../results/train/20260929_195732_no_static_tip/config_requested.yaml).
  26입력·30행 창·Kalman 실측 힘·단위·부호·회귀 loss·정규화·60epoch 상한/patience10 등 기존 설정을 유지했다.
  평균 offset 및1.1배 경계는 위치 라벨에만 적용하며 회귀 정답/영점은 바꾸지 않는다.
- 힘11종을 새 가중치로 각각 학습했다. 기존 bundle 저장/내보내기 경로를 사용하기 위해
  고정 MLP ID0/18 보조 분기를 함께 학습한11조합이다. 이 보조 분기는 전체 ID 위치 실험이 아니며
  사용자 목표인 body 구간 성능으로 보고하지 않는다. 힘/위치는 독립 파라미터다.
- Validation XYZ RMSE 최저 GRU(epoch13,147.77231 mN)를 test 전에 선택했다.
  힘 선택 후 보조 위치 동률 기준은 load_balanced_accuracy이며 test로 대표 모델을 바꾸지 않았다.
  기존242 전체 조합을 완료했다고 주장하지 않는다. 전체 ID 위치/조합 범위는 질문 답변 후 진행한다.

### Test 결과 (mN)

| 모델 | XYZ RMSE | Fx RMSE | Fy RMSE | Fz RMSE | XYZ MAE |
|---|---:|---:|---:|---:|---:|
| MLP | 170.48 | 157.94 | 116.73 | 220.49 | 112.16 |
| CNN | 155.37 | 168.51 | 104.81 | 181.76 | 104.86 |
| ConvMixer | 183.51 | 158.66 | 121.97 | 246.95 | 115.33 |
| ResNet | 171.51 | 160.14 | 112.48 | 223.49 | 109.81 |
| LSTM | 201.09 | 157.17 | 133.84 | 280.52 | 127.39 |
| **GRU (validation 선택)** | **147.88** | **160.50** | **97.55** | **174.15** | **96.98** |
| TCN | 161.52 | 156.16 | 125.33 | 195.38 | 105.96 |
| Transformer | 159.25 | 157.24 | 102.39 | 202.18 | 102.70 |
| KalmanNet | 178.28 | 157.22 | 122.94 | 235.62 | 112.47 |
| Small_GRU | 148.29 | 159.17 | 96.90 | 176.77 | 97.73 |
| Residual_TCN | 187.98 | 157.46 | 127.92 | 254.66 | 121.99 |

기존 선택 CNN test123.85 mN보다 이번 선택 GRU147.88 mN이 높다. 같은 CNN도155.37 mN이다.
다만 기존 끝단 학습은 이미 dynamic 두 파일만 사용했고 static은 validation에만 있었다.
이번에는 summary_18-2가 train에서 validation으로 이동하여 train창16,361→9,485로 줄었다.
학습 데이터 양과 validation/epoch 선택이 함께 달라졌으므로 static 포함이 성능을 좋게/나쁘게
만든다는 인과 결론을 내리지 않는다. 새 무부하 경계도 힘 학습의 표본/정답을 마스킹하지 않는다.

### 산출물·검증·남은 작업

- [학습/validation 힘 지표](../results/train/20260929_195732_no_static_tip/force_metrics.csv),
  [test 힘 지표](../results/predict/20260929_195732_no_static_tip/force_metrics.csv)에 축별 RMSE/MAE와 XYZ를 저장했다.
- 모델별 시트의 실측/예측 Excel은 학습 폴더 `excel/train/`, `excel/validation/`,
  [test Excel](../results/predict/20260929_195732_no_static_tip/excel/force_estimation_all_models.xlsx)에 있다.
  고정 보조 MLP의 ID Excel도 생성됐지만 이것은 body 위치 비교 결과가 아니다.
- 힘33시트(train/validation/test×11종)의 동일 역할 내 원본 행·정답·부하 라벨 일치,
  중복 행 없음, 유한값, 저장 Excel에서 재계산한 validation지표와 comparison 일치,
  선택 모델 test 지표와 metrics.json 일치를 검사했다. 최대 validation 차이는5.68e-14 mN이다.
  원본 hash 불변과 기존 test 목록/hash 일치, 모든 입력의 static 제외도 확인했다.
- 설정·분할·교정·환경·코드 snapshot·학습/예측/내보내기 로그·verification.json을 실행 폴더에 보존했다.
  실행 코드는 수정하지 않았고 기존 전체 단위 테스트는 재실행하지 않았다. 이번 산출물 검증을 수행했다.
- 미완료: 전체 ID 위치 학습은 ID1–6의 분할 방식 답변 대기. 끝단11종 결과는 완료이며
  이번 실험을 summary_1–18 전체 위치 학습 완료로 표현하지 않는다.

## 25. 2026-09-29 — static 포함 설정 결과 해석 확인

- 요청: static도 포함한 쪽의 결과가 더 좋았는지 확인.
- 답변: 동일 test의 validation 선택 모델 기준으로 기존123.85 mN(CNN)이
  static 제외147.88 mN(GRU)보다 낮다. 따라서 기존 실험 설정의 결과가 더 좋았다는 해석은 맞다.
  그러나 기존 끝단 힘 모델에서 static은 validation 전용이었다. 기존에는 dynamic ID18 두 CSV가
  학습에 들어갔고, 제외 실험에서는 하나를 validation으로 옮겼다. Static을 학습에 추가해서
  개선됐다는 뜻이나 static 자체의 인과 효과를 입증한 결과는 아니다.
- 수행/검증:24절의 학습 역할·동일 test 수치와 대조하여 설명을 기록했다.
  새 학습·설정 변경·코드 변경은 없으며 추가 검증 실행은 하지 않았다.

## 26. 2026-10-02 — 기존 데이터 분할과 hrm_bundle.pt 의미 확인

- 요청: static 포함 개발 데이터로 학습하고 별도 test18/18-2를 평가하는지,
  모델 조합 폴더의 hrm_bundle.pt가 네트워크 파일인지와 bundle 명칭의 의미 확인.
- 검증: 주 실행20260928_221428의 split_manifest.json을 확인했다. 전체 train29개,
  validation18개, test2개이며 static은 train12개/validation5개에 분포한다.
  끝단 힘 분기는 train summary_18.csv와 summary_18-2.csv, validation static ID18이다.
  test는 datasets/test/summary_test_18.csv 및 summary_test_18-2.csv로 학습/정규화에 넣지 않았다.
  사용자의 현재 설명은 기존 실험 구성 확인으로 해석했으며 새 학습 지시로 확대하지 않았다.
- 실제 models/class0__force_cnn__location_lstm/hrm_bundle.pt를 weights_only=True로 읽었다.
  state_dict의 두 접두사는 force_net/location_net이며 각각 CNN 힘·LSTM 위치 가중치다.
  config, 각 분기 scalers, feature_columns, calibration, 입력26/시간창30, 모델 구조 파라미터,
  데이터 감사·분할·학습/validation 지표가 함께 들어 있다.
- Bundle은 두 독립 네트워크와 추론 재현에 필요한 정보를 묶은 checkpoint라는 뜻이다.
  하나의 공유 네트워크로 학습됐다는 의미가 아니며 모든 모델11종이 한 파일에 든 것도 아니다.
  restore_bundle은 이 메타데이터로 모델을 만들고 가중치를 복원한다. pt 단독 실행 파일은 아니므로
  추론에는 해당 모델 정의/로더 코드도 필요하다. optimizer 상태 복원용 resume 파일은 아니다.
- 수행: 현재 요약/최신 기록·분할·저장/복원 코드·실제 체크포인트를 읽고 설명을 기록했다.
  새 학습·추론·설정/코드 변경은 하지 않았다. 기존 전체 ID 결과는 이전 무부하 기준이며
  새 평균/1.1 기준의 전체 ID 위치 학습은 아직 미실행 상태를 유지한다.

## 27. 2026-10-05 — train 결과 폴더별 학습 범위와 분석 전용 자료 구분

- 요청: 학습 결과부터 분석하기 위해 no_static_tip, mean_zero_range110,
  no_load_range_analysis, id18_only의 의미와 사용 데이터를 확인.
- 실제 각 폴더의 split_manifest(준비 전용은 prepared_data 하위), analysis.json,
  comparison.csv 및 models/*/hrm_bundle.pt 개수를 읽어 확인했다.

| 폴더 접미사 | 실제 네트워크 학습 | 학습/validation 또는 분석 내용 |
|---|---|---|
| no_static_tip | 힘11종, 고정 보조 위치MLP의11조합 | train summary_18.csv, validation summary_18-2.csv. Static 전부 제외. ID1–17은 학습하지 않음. 보조 위치는 ID0/18뿐. |
| mean_zero_range110 | 없음, bundle0개 | 무부하 기록의 fit 평균을 판정용으로 빼서0 중심으로 만들고 경계 반폭1.1배 적용. 범위/포함률 비교와 ID18 데이터 준비만 수행. 준비 목록의 static ID18은 validation이지만 학습을 실행한 것은 아님. |
| no_load_range_analysis | 없음, bundle0개 | 기존 median 중심 무부하 경계의 폭 확대에 따른 무부하/보류/유부하 행 수 비교. 모델 정확도나 학습 결과가 아님. |
| id18_only | 힘11×위치11의 class0 121조합 | train summary_18.csv와 summary_18-2.csv, validation static ID18. 위치는 ID0/18 이진 검출이며 ID1–17 제외. 당시 이전 무부하 기준으로 학습. |

- 따라서 no_static_tip을 ID1–18 전체 학습으로 이해하거나 id18_only를 summary_18 한 파일만
  학습한 것으로 이해하면 안 된다. Static 제외 전체 위치 학습은 여전히 미실행이다.
- 학습 결과 분석 대상으로는 원래 전체 위치 실험20260928_221428(242조합),
  id18_only(121조합), no_static_tip(11조합)을 구분한다. 원래 실험도 힘은 tip 전용이고 위치가 전체ID다.
  mean_zero_range110/no_load_range_analysis는 이름과 상위 train 경로에도 불구하고 분석/준비 자료다.
- comparison.csv의 일반 force_rmse_xyz_mN·축별 force_rmse_*·location 지표는 validation 기준이며,
  train 폴더 아래 있다는 이유로 학습 표본의 오차로 해석하지 않는다. test_ 접두사 지표는 test다.
  실제 학습 표본의 힘 오차/정답·예측은 별도 force_metrics/summary와 Excel의 train 역할을 확인한다.
- 수행/검증: 문서와 실제 파일 목록·분할·조합 수를 대조했고 현재 날짜와 기록을 갱신했다.
  새 학습/추론/폴더 이동/설정·코드 변경은 하지 않았으며 단위 테스트 재실행은 필요하지 않았다.

## 28. 2026-10-05 — dynamic 전체와 static 전체를 학습했는지 명확화

- 요청: summary ID1–18 및 summary_static_* 모두를 학습한 실행이 없는지 확인.
- 답변 범위: 해당 데이터군을 함께 사용해 train/validation으로 나눈 실행은20260928_221428이다.
  모든 CSV를 validation 없이 가중치 업데이트에 사용한 실행은 없다. 앞선 '전체/static 포함 학습'
  표현은 데이터군과 실제 가중치 학습 대상을 구별하지 못할 수 있어 구체적인 역할/수를 설명한다.
- 실제 split_manifest/data_audit 재확인: 위치 모델 train29CSV(dynamic17+static12),
  validation18CSV(dynamic13+static5). 양쪽 모두 effective ID1–18을 포함한다.
  Static ID10 한 CSV는48,360행 모두 유효 Kalman aligned force/frame이 없어 학습/검증 제외다.
  Test는 별도 ID18 두 CSV다. 끝단 힘 모델은 train dynamic ID18 두 CSV,
  validation static ID18 한 CSV이며 ID1–17 힘을 학습한 모델은 아니다.
- 따라서 '모든 CSV를 실제 학습에 투입' 또는 'static ID18을 힘 가중치 학습에 투입'한 결과는 없다.
  모델 선택에 사용할 validation을 남겨둔 기존 실험이 있다는 점과 구분한다.
- 수행/검증: 현재 요약/최신 기록 및 원본 저장 분할·제외 근거를 읽어 대조 후 기록했다.
  질문에 대한 설명만 수행했으며 새 학습/추론/설정 변경은 하지 않았다.

## 29. 2026-10-05 — static ID10 누락 열/구간 실측 확인과 validation 분할 설명

- 요청: static ID10에서 실제로 빠진 F/T 부분을 확인하고, CSV 전체를 분리하는 validation과
  각 CSV 후반 비율을 분리하는 방식 중 어떤 것이 보통 적절한지 설명. 사용자는 수정/재학습을 요청하지 않았다.
- 대상 원본: `datasets/train/summary_static_pan_-30to+30_tilt_-30to+30_interval-15deg_seg-id-10.csv`.
  전체48,360행, SHA256 `c1c6ec1e7bbee8dfd7a731dd6e6d1c24cf69aca4ba964a37eb25f8c9fa06fb1d`.
  Pandas 문자열 읽기로 빈칸과 유한 숫자를 분리 집계하고 읽기 전후 hash 불변을 확인했다.

| 열 | CSV/Excel 열 위치 | 확인 결과 |
|---|---|---|
| fts_kalman.aligned_fx/fy/fz | 46–48번째, AT–AV | 앞11,551행은 세 축 모두 유한 숫자, 이후36,809행은 세 축 모두 빈칸 |
| fts_kalman.aligned_force_valid | 49번째, AW | 전체48,360행 빈칸 |
| fts_kalman.aligned_frame_id | 50번째, AX | 전체48,360행 빈칸 |
| fts_kalman.fx/fy/fz | 40–42번째 | 전체48,360행 유한 숫자. 학습 기본 정답인 aligned XYZ와 다른 열 |
| fts.fx/fy/fz | 29–31번째 | 전체48,360행 유한 숫자. 센서 좌표의 raw 열 |
| fts.aligned_force_valid / fts.aligned_frame_id | 38–39번째 | raw aligned도 전체48,360행 빈칸 |
| fts_kalman.matched / fts.matched | 202번째 /196번째 | 각각 True48,252행, False108행 |

- Kalman aligned 숫자가 있는 구간: 원본 데이터0-based행0–11,550, 헤더 포함CSV줄2–11,552,
  기록 elapsed_s0.600157715–385.701540527.
  비어 있는 구간: 원본행11,551–48,359, CSV줄11,553–48,361,
  elapsed_s385.734882324–1612.991803955.
- 정정: 'F/T가 전혀 없다'는 표현은 부정확하다. 센서 F/T 숫자는 존재하지만 현재 필요한
  Kalman aligned XYZ가 후반에 빠지고, 전체에서 aligned 유효성/좌표계가 확인되지 않는다.
  현재 loader는 유한 XYZ, matched=True, aligned_force_valid=True, aligned_frame_id=hrm_base,
  시간 매칭 조건 등을 함께 요구하므로 정답 유효행0이다. 센서 고장/내보내기 누락 원인은 미확인이다.
  숫자 존재만으로 matched/좌표 변환 유효성을 보증하지 않으며 원본 자동복구/raw대체는 하지 않았다.
- Validation은 반드시 서로 다른 파일이어야 한다는 일반 규칙이 아니다. 새 독립 녹화에서의
  일반화가 목적이면 물리 실험/세션을 그룹으로 통째 분리하는 방식이 적합하고, 같은 녹화의 미래
  구간 성능이 목적이면 앞부분 학습/후반 validation도 가능하다. 파일명보다 같은 물리 실험의 공유 여부가 핵심이다.
  HRM의 반복 힘 주기/센서 영점/자세 등 세션 특성이 겹치는 평가와 새 실험 평가는 구별해야 한다.
- 시계열 창을 만든 뒤 랜덤으로 나누면 인접30행 창의29행이 겹칠 수 있으므로 새 실험 성능을
  낙관적으로 평가할 수 있다. 시간분할은 먼저 구간을 나누고 역할 간 창 중복을 피하며 필요한
  시간 간격을 둬야 한다. 창 중복 제거만으로 세션 상관이 모두 없어지는 것은 아니다.
- 현재 녹화 단위 분할은 목적에 맞는 합리적 선택이지만 유일한 정답/최적 구성은 아니다.
  특히 tip의 train dynamic/validation static 구성은 녹화뿐 아니라 동작 조건 변화도 함께 평가하고,
  녹화 수가 적어 어느 파일을 보류하느냐에 민감하다. 유효 녹화를 번갈아 검증하는 그룹 교차검증은
  대안이며 아직 실행하지 않았다. 모든 개발 자료를 최종 가중치에 사용하려면 모델/epoch 등 설정을
  validation으로 먼저 정한 뒤 train+validation으로 새 최종 모델을 학습하고 별도 test로 평가할 수 있다.
  이 단계도 현재 미실행이며 test로 설정을 고르는 것은 아니다.
- 근거: scikit-learn 공식 [grouped/time-series cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data),
  [TimeSeriesSplit와 gap](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
  프로젝트에 대한 적용/권고는 위 일반 원칙과 현재 데이터 구조를 바탕으로 한 판단이다.
- 수행/검증: 원본 열별 수치·빈칸/flag와 구간 경계를 직접 집계하고 loader 조건 및 공식 문서를 확인했다.
  결과와 설명만 기록했다. 원본/설정/코드는 변경하지 않았으며 새 학습·추론·단위 테스트는 수행하지 않았다.

## 30. 2026-10-05 — ID 학습 누락 오해와 무부하 휴식 경계의 수동 분할 제안

- 요청: 파일 통째 validation/test 분리로 해당 ID가 학습되지 않는지 질문하고, 직접 수집한
  실험에서 외력이 없는 휴식 구간을 경계로 수동 분할해 test를 만드는 방안 검토.
- 기존20260928_221428 split_manifest를 다시 확인했다. train/validation 모두 ID1–18을 포함한다.
  ID1–6과10은 train1녹화, 나머지 ID는 train2녹화이며 validation은 각ID1녹화다.
  예: ID1은 static train/dynamic validation, ID10은 summary_10 train/summary_10-2 validation,
  ID18은 dynamic2개 train/static validation이다. Test는 별도ID18 두 녹화다.
  동일ID의 다른 녹화를 분리한 것이며 특정ID 전체를 test로 빼서 미학습한 구성이 아니다.
  ID당 정말1녹화만 있다면 그 녹화 전체를 보류할 때 학습 표본이 사라지는 우려는 맞다.
  Static을 제외할 때 ID1–6의 분할 질문이 생긴 이유가 이것이다.
- Validation은 다른 녹화이더라도 epoch/모델 선택에 사용했으므로 최종 test와 역할이 다르다.
  새 녹화 검증이라는 점과 최종 성능 평가용 독립 test라는 점을 혼동하지 않는다.
- 무부하 휴식의 중간을 경계로 완전한 접촉/해제 반복 블록을 나누는 것은 같은 실험 내 평가를
  위한 합리적 후보다. CSV를 나눠도 동일 물리 세션의 자세/영점/조건을 공유하므로 새 독립 실험이 되지는 않는다.
  무부하 구간만 test로 떼어내면 오경보/무부하 힘 오차만 평가할 수 있고 접촉ID/유부하 힘 성능은 평가할 수 없다.
- 수동 분할 시 원본은 보존하고 파생본의 부모파일/hash, 원본행/시작끝시간, ID와 session/block 연결을 남긴다.
  분리한 평가 구간은 train/validation 및 scaler fit에서 제외하고 경계의30행 입력 창 중복과 시간 인접성을 고려한다.
  평가 구간 제거 후 남은 앞뒤를 시간상 연속처럼 이어붙이지 않는다. 무부하만 남기거나 쉬운 구간만 선별하지 않고
  평가 목적에 맞는 자세/힘 방향/유부하·무부하를 포함한 블록을 미리 고정한다.
- 이미 해당 구간을 본 기존 모델/정규화로 평가하면 새 test 성능이 아니다. 해당 구간을 제외한 새 학습이
  필요하며, 과거 자료를 다시 분할한 결과는 같은 실험 내부의 재분할 평가로 기록하고 새로운 수집 test와 구별한다.
  현재 loader는 완전한 독립CSV 분할을 전제로 하므로 잘라낸 파일을 기존 test폴더에 추가하는 것만으로
  올바른 분할이 적용됐다고 보장하지 않는다. 적용 전 부모 구간/역할 보호를 포함한 명시적인 설계가 필요하다.
- 근거: [scikit-learn grouped CV](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).
  같은 그룹 내부 평가와 새로운 그룹 일반화의 구별을 프로젝트 데이터에 적용한 설명이다.
- 수행/검증: 분할 기록/보호 코드와 공식 자료를 읽고 의견만 기록했다. 사용자 수동 작업을 대신
  실행하지 않았으며 원본·설정·코드·학습 결과를 변경하지 않았다. 분할 방식 변경은 아직 미적용이다.

## 31. 2026-10-05 — 긴 녹화의 앞 train/뒤 test 분할 의도 확정

- 사용자 명확화: 녹화 파일 수가 제한적이므로 긴 학습 데이터에서 무부하 휴식을 경계로
  앞 전체를 train, 뒤 전체를 test로 쓰려는 것이다. 독립 실험 성능과 구별한다는 점은 이미 이해하고 합의했다.
  무부하 구간만 추출하거나 새 독립 녹화처럼 해석하려는 요청이 아니다.
- 반영: 앞선31절 이전의 분할 방식 질문은 이 구체적인 시간 블록 분할 방향으로 정리했다.
  선택한 녹화를 학습에도 활용하고 후반의 유부하/무부하가 포함된 전체 블록을 보류 평가에 사용한다.
  독립 녹화 test 결과는 별도 평가로 보존한다. 앞으로 이 차이를 이미 합의한 사항으로 취급하고
  같은 주의사항을 되풀이하며 의도 확인을 요구하지 않는다.
- 아직 정하지 않은 실행 세부사항: 대상 CSV와 절단 시간, 모델 선택용 validation 확보 방법.
  사용자가 경계를 수동으로 지정할 계획이며 이번 메시지를 자동 절단/재학습 요청으로 확대하지 않았다.
  실제 실행 시 원본/행·시간 대응과 세션 연결을 보존하고, 학습/scaler에 후반 test가 들어가지 않게 한다.
- 수행/검증: 현재 요약·최신 기록과 AGENTS를 읽고 합의 방향을 두 문서에 반영했다.
  데이터·설정·학습 코드 변경이나 새 학습은 없다. 문서 변경만 수행했다.

## 32. 2026-10-05 — valid 검사 복잡도와 동일 열 구성의 행 분할 호환성

- 요청: 사용자는 학습 시 입력/출력 열을 지정하는 간단한 사용 방식을 원하며,
  valid 열 검사가 내부 코드를 지나치게 복잡하게 만드는지 질문했다. 수동 분할은 특정 행을
  경계로 동일한 열 구성을 유지해 저장할 계획이다.
- 코드 확인: independent_data의 feature_spec/force 계약은 X/Y 외에 선택 소스의 matched,
  aligned_force_valid, frame_id, timestamp 및 시간차 열을 읽는다. _validity는 유한 숫자·flag·
  시간차·좌표계 조건을 행별 boolean mask로 합친다. valid_endpoints는 무효 행/시간 경계에서
  연속 길이를 초기화하고30행 연속 유효한 창만 허용한다. Flag들은 기본 모델 입력/출력이 아니다.
  검사는 데이터 준비 단계이며 각 학습 배치에서 별도 검증 네트워크를 실행하는 구조가 아니다.
- 평가: 핵심 valid 검사는 단순하고 모델 학습과 분리되어 있다. 다만 전체 loader에는 timestamp
  정합성 감사와 특정 원본hash에 한정된 과거 ID/시간 복구 예외도 있어 전체가 단순 X/Y CSV 로더인 것은 아니다.
  사용자 조작은 간단하게 유지하면서 내부적으로 유효성을 검사하는 방식은 양립 가능하다.
- 현재 설정의 범위도 구별한다. X는 길이/장력/각도 feature_groups 선택이며 임의 개별 열 리스트
  인터페이스는 없다. 힘Y는 선택한 raw/Kalman 소스의 aligned Fx/Fy/Fz 순서를 검증한다.
  자유로운 모든 input/output 열 매핑 기능을 이미 구현했다고 설명하지 않는다.
- 동일 헤더·열·원래 값·timestamp/flag를 보존하며 전체 행 단위로 자르면 일반적인 행 유효성
  규칙은 그대로 적용된다. 경계마다30행 창은 새로 구성한다. 단, 파일hash가 달라지므로
  summary_18-2의 기존 ID 보정 및 알려진 trim 시간복구 예외를 새 파생파일에 자동 승계하지 않는다.
  부모 원본과 절단 범위를 기록해 대응을 확인해야 하며, 앞train/뒤test의 새로운 분할 정책 지원도
  아직 미구현이다. 따라서 열 구성이 같다는 것만으로 현재 명령에 바로 넣어 모든 처리가 보장되는 것은 아니다.
- 수행/검증: 현재 기록과 실제 로더/설정/feature_spec/valid_endpoints/hash 계약을 읽고 설명을 기록했다.
  존재하지 않는 features.py 검색은 data.py의 실제 정의로 확인했다. 코드/설정/데이터는 변경하지 않았고
  새 학습·추론·테스트 실행은 없다. 사용성 요구를 기록했으며 실행 지시로 확대하지 않았다.

## 33. 2026-10-05 — set-zero 빈칸 제외, timestamp 사용, 숫자 유효성만의 간소화 희망

- 요청: set-zero 때 생기는 빈칸이 학습에서 제외되는지, 수동 삭제가 필요한지,
  timestamp도 확인하는지 질문. 별도 valid flag 확인은 필요하지 않다는 사용자 선호와,
  간단한 X/Y 학습에서 Fx/Fy/Fz 빈칸이 오류를 일으키는지 확인했다.
- 현재 구현 확인: _number는 빈칸/비수치를 NaN으로 변환하고 _validity의 isfinite mask에서 제외한다.
  선택한 입력/힘 정답이 무효인 행과 그 행을 포함하거나 가로지르는30행 창을 제외한다.
  결측 이후30행이 다시 연속 유효해야 학습 창이 생기므로 원본을 수동 삭제할 필요가 없다.
  정상 숫자로 저장된 set-zero 전후까지 이벤트를 알아서 검출/제외하는 기능은 아니다.
- Timestamp는 실제로 읽는다. 모델 feature는 아니며 순서/간격/소스 시간 정합성을 검사한다.
  valid_endpoints는 시간 비증가나 median 간격×1.5 초과에서 창을 끊는다.
  행을 수동 삭제하더라도 원래 timestamp를 보존하면 충분히 큰 시간 공백은 경계로 남는다.
- 단순 loader가 빈칸을 그대로 숫자로 변환하면 변환 예외가 날 수 있고, NaN 상태로 loss에
  넣으면 반드시 예외가 나지 않더라도 loss/gradient가 NaN으로 전파되어 학습이 실패할 수 있다.
  선택한 X/Y의 유한 숫자 여부만 자동 검사해 제외하는 처리는 간단히 구현 가능한 별도 절차다.
  'valid flag를 보지 않음'과 '빈칸/NaN을 학습에 투입'은 다른 정책이다. 빈칸을0으로 바꾸지 않는다.
- 사용자 의도: 입력/정답 숫자만 유효하면 사용하고 빈칸은 자동으로 제외하는 간소화 방향.
  이번은 동작 확인 질문으로 응답했으며 flag 검사를 끄거나 timestamp 검사를 제거하는 코드를
  즉시 적용하지 않았다. Timestamp를 모델 입력으로 넣지 않는다는 사실과 시계열 경계 검사는 구별한다.
- 수행/검증: 현재 요약/직전 기록 및 실제 숫자 변환·mask·timestamp·창 구성 코드를 대조했다.
  문서/작업 규칙의 구현 상태와 선호를 갱신했으며 원본·실행 설정·코드·모델은 변경하지 않았다.
  새 학습·추론·단위 테스트는 수행하지 않았다.

## 34. 2026-10-05 — 빈칸 행 제외 후 연결 확정, 사용자 데이터 준비

- 사용자 확인: 선택한 입력/출력의 빈칸 행을 제외하고 다시 숫자가 있는 행을 이어붙이면 된다.
  사용자가 직접 test용 데이터셋을 잘라 준비한 뒤 돌아오겠다고 했다.
- 합의: 각 파일/분할 역할 안에서 선택 X/Y의 빈칸·비수치·NaN/Inf 행을 제외하고 남은 행을
  원래 순서로 연결한다. 선택하지 않은 열의 빈칸은 제외 근거로 삼지 않는 간소화 방향이다.
  Valid flag 확인 생략과 결측 전후 연결을 사용자가 명시적으로 확인한 것이다.
  연결된 행으로 시간창을 만들 때 결측 제거로 생긴 원래 시간 공백을 다시 창 단절 사유로 삼는
  과거 방침을 자동 적용하지 않는다. 원본 시간/행 대응은 추적용으로 보존하고 train/test와
  서로 다른 파일을 가로질러 연결하지 않는다. 빈칸을0 또는 무부하로 대체하는 방식은 아니다.
- 구현 상태: 현재 코드는 여전히 이전 정책이다. 사용자 데이터 준비 발언에 맞춰 합의만 기록했으며
  원본 자동 절단, 코드/설정 변경, 새 학습은 실행하지 않았다. 실제 대상/절단 위치·새 자료가 준비되면
  새 전처리/분할을 반영할 작업이 남아 있다. 같은 전처리 방향에 대한 확인을 반복 요청하지 않는다.
- 수행/검증: 현재 요약·직전 기록과 AGENTS를 확인하고 최신 합의로 갱신했다. 문서 변경만 수행했다.

## 35. 2026-10-05 — 사용자 분할 데이터 적용 및 직접 실행 명령 (학습 미실행)

- 요청: 사용자가 ID별 train/test 파일을 다시 저장했으며, 직접 학습할 명령과 폴더 역할을 질문했다.
  **학습은 실행하지 말라는 지시를 우선했다.** 모델 성능 수치를 새로 만들지 않았다.
  앞서 합의한 숫자 행 연결/수동 test 분할을 지원하도록 로더와 기본 설정을 반영하고 데이터 준비만 실행했다.
- 실제 구성: `datasets/train/*.csv`48개(dynamic30+static18), `datasets/test/*.csv`19개.
  Test는 ID1–17 각1개와 ID18 두 파일이며 그대로 고정한다. Train에서 특정 ID나 파일을 test로 더 빼지 않는다.
  Static ID10의 현재 파일은 선택 X/Y가 유효한48,252행을 포함하며 학습/validation에 참여한다.
  ID18 힘은 dynamic2개+static18 파일의 train 부분을 사용하고 위치는 전체ID1–18을 사용한다.
- Validation 질문은 선택 사항으로 전달했으며 작업 중 답변이 없었다. 각 train CSV의 숫자 행을
  앞80% 학습/뒤20% validation으로 나누는 기본값을 알리고 적용했다.
  `validation_strategy: per_file_tail`, `validation_fraction: 0.2`에서 조정할 수 있다.
  따라서 모든48파일의 일부가 학습에 들어가되 각 파일 전체를 optimizer에 투입하는 것은 아니다.
  Validation은 epoch/모델/구간 경계 선택용이고 test는 최종 평가용이다.
- `preprocessing: numeric_compact`: 선택 X/Y의 빈칸·비수치·NaN/Inf 행을 제외하고 같은 파일 안에서
  남은 행을 순서대로 연결한다. 선택하지 않은 열의 빈칸, valid/matched/frame flag, matching skew,
  timestamp 간격으로 추가 제외하지 않는다. Timestamp는 모델 입력이 아니며 추적용일 뿐이다.
  일부 새 CSV의 timestamp가 과학적 표기로 반올림되어 있으므로 행 순서를 유지하고 정밀 시간을 복원했다고 주장하지 않는다.
  시간 메타데이터가 없으면 추론/Excel의 시간은 빈칸으로 남긴다. 기존 무부하 교정 기록의 감사 경로는 유지한다.
- 창 길이는30행이다. 유효 숫자 행으로 만든 각 역할 안에서만 창을 생성하므로 validation 첫29행은
  해당 역할의 이력 확보용이다. 파일/역할 경계를 가로지르는 창은 없다. Scaler도 학습 구간에서만 fit한다.
  Bundle에 설정·hash·역할별 구간을 저장하며 예측 CSV/Excel의 `source_row`는 삭제 전 원본 행 번호다.
  과거 옵션 없는 설정/bundle은 audited 전처리와 whole_csv 분할을 유지한다.
- 중복 점검: 최초 ID1 train의 원본행3365와 test의0행이 선택 X/Y 전체에서 같았다.
  한시적으로 정확hash 행 제외를 설정했으나, 확인 도중 train `summary_1.csv`가 사용자 측에서
  3,365행으로 다시 저장된 것을 감지했다(hash `820aa89a…46408`). 최신 파일에는 중복 행이 없어
  임시 제외 설정을 제거하고 다시 준비했다. Agent는 원본 CSV를 쓰거나 삭제하지 않았다.
  선택 X/Y가 완전히 같은 train/test 행을 거부하는 검사를 추가했다. 이것만으로 부모 세션 관계까지 증명하는 것은 아니다.
- 최종 데이터 준비 결과(숫자 행 연결 후30행 창 수):

  | 역할 | 참여 CSV 수 | 전체ID 지도 가능 창 수 |
  |---|---:|---:|
  | Train | 48 | 730,320 |
  | Validation | 48 | 181,560 |
  | Test | 19 | 27,785 |

  같은48개 train파일의 서로 겹치지 않는 앞/뒤 구간이다. 위치 loss에서는 무부하 방식에 따라
  uncertain 또는 unloaded 끝점이 추가로 제외된다. 이 수를 실제 위치 loss 표본 수와 혼동하지 않는다.
  기존 독립 ID18 test 두 파일과 사용자 수동 분할 ID1–17 test는 평가 해석을 구별한다.
  `test_evaluation_scope`에 혼합 구성을 기록했고 예측 결과는 파일별로도 보고한다.
- 수행 파일: `configs/train.yaml`, `numeric_data.py`, 독립 data/engine/prediction 경로 및 Excel 내보내기를
  갱신했다. 준비 결과와 감사는 `.runtime/20261005_manual_split/prepared_latest/`에 있으며
  학습 결과로 혼동하지 않도록 새 `results/train` 실행을 만들지 않았다.
- 검증: 실제67CSV 준비 성공, 최종 준비 이후67개 원본hash 불변 확인, 저장 test 목록의 추론 보호 검사 통과.
  데이터/engine/추론/Excel/새 전처리 관련55개 단위 검증 통과. 새7개 검증에는 compact 행 대응,
  flags/time 무관 처리, 단일 파일 validation, scaler 누수 방지, 경계 중복 검출,
  미학습 임시 bundle 저장·복원·합성 입력 추론, `--check-data`의 모델/학습 미호출 검사가 있다.
  실제 optimizer를 실행하는 기존 단위 테스트1개는 이번 지시에 맞춰 제외했다. 새 데이터 학습이나
  기존 모델의 실제 데이터 추론/Excel 생성은 실행하지 않았다. Train/predict CLI `--help`도 확인했다.
- 사용자가 프로젝트 루트에서 직접 실행할 명령:

  ```bash
  HRM_RUN_ID="$(date +%Y%m%d_%H%M%S)"
  bash scripts/hrm_python.sh train.py --config configs/train.yaml --output "results/train/$HRM_RUN_ID"
  ```

  위 학습이 정상 완료된 뒤 같은 터미널에서 test 평가:

  ```bash
  bash scripts/hrm_python.sh predict.py --train-dir "results/train/$HRM_RUN_ID" --output "results/predict/$HRM_RUN_ID"
  ```

  학습은 기본11×11×2=242조합이다. 예측 명령은 validation으로 무부하 방식별 조합1개를 선택하여
  학습 당시 고정한 test19파일을 평가한다. 모든 구조의 MATLAB용 시트가 필요하면 학습 완료 후:

  ```bash
  bash scripts/hrm_python.sh scripts/export_model_workbooks.py --train-dir "results/train/$HRM_RUN_ID" --train-output "results/train/$HRM_RUN_ID/excel" --predict-output "results/predict/$HRM_RUN_ID/excel"
  ```

  새 터미널에서는 `$HRM_RUN_ID`를 실제 학습 폴더의 날짜_시간으로 다시 지정한다.
  기존 날짜 폴더는 덮어쓰지 않는다. 다음 단계는 사용자 직접 학습이며 성능 개선 여부는 아직 미측정이다.

## 36. 2026-10-05 — 학습/예측 파일 구성 설명과 기능별 최소화 희망

- 요청: scripts와 hrm_force 전체가 학습/예측에 필요한지, train.py·model_zoo.py·predict.py와
  Aidin 무부하 분석 파일 중심으로 단순화할 수 있는지 현재 구조 설명을 요청했다.
  사용자는 사용하는 파일 수 자체를 최소화하는 구성을 선호한다.
- 확인한 현재 구성: scripts에는 실행 보조10개(8Python+2shell), hrm_force에는18Python 파일이 있다.
  현재 YAML 경로의 주요 흐름은 train.py → independent_engine.py → independent_data.py/numeric_data.py,
  independent_models.py/models.py, independent_evaluation.py다. predict.py → independent_prediction.py가
  같은 로더·모델·정규화·평가 함수를 재사용한다. feature_catalog.json과 dataset_contracts.json도 읽는다.
  hrm_force는 실제 구현이므로 현재 상태에서 폴더를 지우면 학습/예측이 작동하지 않는다.
- 루트 model_zoo.py는3줄의 기존 MODEL_NAMES/build_model/count_parameters 재노출 파일이다.
  현재 독립 힘/위치 네트워크의 실제 구현과 생성은 models.py 및 independent_models.py에 있다.
  학습할 구조 선택은 configs/train.yaml의 force_candidates/location_candidates에서 한다.
- scripts 전체가 학습 필수는 아니다. hrm_python.sh는 환경 Python 및 이 PC GPU 보조 라이브러리
  선택용 런처다. train.py/predict.py 자체에도 runtime.ensure_driver_runtime 진입 처리가 있다.
  setup_environment.sh는 환경 설치용, analyze_no_load.py는 무부하 통계/교정 진단,
  analyze_dataset.py는 데이터 분포 진단, export_model_workbooks.py는 Excel 내보내기,
  summarize_force_axes.py는 축별 지표 정리, plot_independent_results.py는 그림,
  benchmark_convolution.py/benchmark_inference.py는 속도 점검, fine_tune_all.py는 과거 추가학습용이다.
  기본 train/predict가 이 분석/벤치마크 스크립트들을 자동 실행하는 것은 아니다.
- 파일이 늘어난 이유: 기능별 모듈 분리와 함께 기존 JSON/folder/warm-start 호환 코드가 남아 있다.
  기존 engine.py/evaluation.py/folder_*는 새 핵심 학습 기능과 구별해야 한다. 단, train.py/predict.py의
  최상단 legacy import 및 현재도 공유하는 data.py/models.py 때문에 이름만 보고 바로 삭제하면 안 된다.
- 단순화 제안(아직 미적용): train.py(학습), predict.py(예측/결과 저장·Excel), model_zoo.py(실제 모델 정의),
  data_utils.py(CSV·빈칸 제외·분할·정규화·창 및 공통 저장/복원), metrics.py(힘/ID 지표),
  analyze_no_load.py(센서 무부하 교정/분석) 중심의6Python 구조와 configs/train.yaml.
  옛 호환/개발 진단은 기존 보존 정책에 따라 archive로 정리하고 실제 기능을 새 위치로 통합할 수 있다.
  정확한 파일 수는 결과 내보내기 기능을 합치는 범위에 따라 달라지며3~4파일이 기술적 필수 제한은 아니다.
  모델 종류를 고르는 것은 설정으로 유지하고 네트워크 구현을 수정할 때 model_zoo.py를 사용하는 방향이다.
- 추가 정적 발견/미완료: analyze_dataset.py의 pooled_role 및 역할별 집계는 아직 파일 전체 x/endpoints를
  사용하여 per_file_tail의 role_rows를 반영하지 않는다. 새 기본 설정에 그대로 사용하면 같은 파일 전체가
  train/validation 통계에 각각 들어갈 수 있다. 메인 학습 WindowStore/scaler의 역할 분리는35절에서
  검증한 경로이며 이 진단 스크립트를 호출하지 않는다. 해당 선택 도구는 정리 시 수정하거나 보관해야 한다.
- 수행/검증: 현재 문서·진입점·import·스크립트 호출을 읽기 전용으로 확인하고 이 기록을 추가했다.
  학습/예측 실행, 파일 삭제/이동, 런타임 코드 재구성은 수행하지 않았다. 이번은 현재 구조 설명이며
  제안한 최소 파일 구조를 이미 구현했다고 설명하지 않는다.

## 37. 2026-10-05 — 원래 저장소와 비교한 코드 읽는 순서 및 필수 기능 설명

- 요청: 사용자는 [LSTM-force-estimation](https://github.com/DaeyunJang/LSTM-force-estimation)의 작은
  핵심 파일 구성을 참고해 현재 hrm_force가 왜 많은지, 각 코드가 어떻게 쓰이는지 설명을 요청했다.
  파일이 많아 읽고 수정하기 어렵다는 것이 핵심 문제다. 앞선 '현재 폴더를 바로 지우면 안 됨'은
  '모든 파일이 기능상 반드시 필요함'이라는 뜻이 아니다. 현재 import 의존성과 필요한 기능을 구별한다.
- 참조 저장소 읽기 전용 확인: humble의 commit `c3238661f26199180b0b89f4b3f74f346d8c2221`.
  현재 핵심 경로는 README의 오래된 scripts/LSTM_train.py 예시가 아닌 scripts_model이다.
  [train_models.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/c3238661f26199180b0b89f4b3f74f346d8c2221/scripts_model/train_models.py)는
  CSV/JSON 병합, 입력/정답 열, 결측 제거, 창 생성, scaler, Keras 학습 및 저장을 담고 있다.
  [predict_models.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/c3238661f26199180b0b89f4b3f74f346d8c2221/scripts_model/predict_models.py)는
  저장 모델/정규화 복원과 test 처리·역정규화·CSV 저장을 담당한다.
  [model_zoo.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/c3238661f26199180b0b89f4b3f74f346d8c2221/scripts_model/model_zoo.py)는9종 모델,
  [meta_utils.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/c3238661f26199180b0b89f4b3f74f346d8c2221/scripts_model/meta_utils.py)는 실행 기록이다.
  크기/입력 변형과 보조 도구를 제외하면 핵심4파일이라는 사용자 설명과 맞는다. 참조의2축 회귀보다
  현재3축 회귀·독립ID 분류·무부하 처리 요구가 늘었지만18개 모듈 분리는 기술적 필수 조건이 아니다.
  Keras fit과 현재 직접 작성한 PyTorch 학습 루프의 차이도 코드 길이 차이의 한 이유다.

**현재 train.py를 실행하면 실제로 일어나는 일**

1. train.py가 YAML 경로를 보고 `independent_engine.main()` → `train_experiment()`를 호출한다.
   메인 학습 흐름을 읽으려면 `independent_engine.py:276`부터 보면 된다. 루트 train.py의
   `legacy_main()`은 현재 YAML 방식에서 실행되는 학습 함수가 아니다.
2. `independent_data.load_config()`가 YAML을 읽고 입력 그룹을 실제 열 이름으로 펼친다.
   `prepare_data()`가 폴더 목록과 파일hash를 고정하고 교정을 준비한다.
   `numeric_data.load_numeric_trial()`은 선택한 X/Y를 숫자로 변환하여 빈칸·NaN/Inf 행을 제외한다.
   남은 행을 연결하고 삭제 전 source_row 대응을 보존한다. 학습 대상CSV의 valid/frame/시간차 검사는 생략한다.
3. 각 train파일의 남은 행을 앞80% 학습/뒤20% validation으로 나눈다. Test파일은 고정된다.
   `fit_scaler()`는 학습 부분의 평균·표준편차만 구하고 힘/위치 분기별로 보관한다.
   힘 전용 학습은 ID18, 위치 학습은 ID1–18이므로 두 분기의 정규화 대상도 다를 수 있다.
4. `WindowStore`는 한 표본의 과거30행 입력과 마지막 행 정답을 연결한다. 기본 X 모양은
   `(batch,30,26)`이며 Y_force는 `(batch,3)`, Y_location은 표본마다 정수라벨1개다.
   MLP는 마지막 행만 쓰는 별도 처리다. 파일/학습·검증 경계는 입력 창이 넘지 않는다.
5. `models.py`의 기본 layer/encoder를 `independent_models.py`가 조합한다.
   `build_estimator()`가 별도 파라미터를 가진 force_net과 location_net을 만든다.
   힘 출력3개, 전체ID masked 위치 출력18개, class0 위치 출력19개다. 학습 중에는 위치 logits이며
   예측 시 softmax로 확률값으로 바꾼다. ID/실측 힘은 네트워크 입력이 아니다.
6. `train_branch()`가 AdamW, forward, loss, backward, step, validation, early stopping을 실행한다.
   힘 기본 loss는 표준화된 실측3축에 대한 MSE, 위치는 cross-entropy다. 무부하 방식은 위치 정답/loss에
   적용하고 힘 회귀를 무부하에서0으로 바꾸지 않는다. 확정 무부하를 class0는0으로 학습하고
   masked는 위치 loss에서 제외한다. 불확실 부하 위치라벨은 두 방식 모두 loss에서 제외한다.
7. 힘×위치×무부하 방식의 각 조합에서 새 모델/optimizer로 위 과정을 반복한다.
   `independent_evaluation.py`가 역정규화 후 축별/전체 RMSE·MAE, ID/구간/부하 지표를 계산한다.
   `bundle_for()`가 가중치·정규화·설정·교정·분할을 hrm_bundle.pt에 담고 비교표를 기록한다.

**현재 predict.py를 실행하면 실제로 일어나는 일**

- `--train-dir` 경로는 `independent_prediction.select_and_evaluate()`가 validation 비교표로
  방식별 기존 bundle을 선택한다. `restore_bundle()`이 구조/가중치/학습 당시 정규화를 복원한다.
- `predict_trials()`가 test를 같은 입력 순서/전처리/창 길이로 만들고 저장 scaler를 적용한다.
  Test에서 scaler를 다시 fit하지 않는다. 힘은 역정규화하고 N/mN 열로, 위치는 ID/확률로 저장한다.
  힘 지표는 현재 tip 학습 범위가 확인된ID18에서 평가하고 위치는 활성ID 전체를 구별한다.
- `independent_evaluation.py`가 정답과 예측을 비교한다. 구간 탐색은 저장 validation으로 하고
  test는 선택한 구간으로 평가한다. CSV/JSON 결과와 모델별 Excel은 별도 출력 경로이며
  Excel 요청 때만 `excel_export.py → excel_tables.py → excel_writer.py`를 사용한다.

**hrm_force 파일을 목적별로 읽는 지도**

| 현재 파일 | 실제 역할 | 핵심 작업에서의 위치 |
|---|---|---|
| independent_engine.py | 전체 조합 반복, scaler, 창 배치, 학습 루프, bundle 저장/복원 | 먼저 볼 학습 본체 |
| numeric_data.py | 숫자 X/Y 행 선택 및 연결, 원본 행 대응 | 현재 CSV 로더 |
| independent_data.py | 설정/분할/교정/라벨; 과거 audited 로더도 포함 | 새 데이터 준비와 과거 정책 혼재 |
| data.py | 열 그룹, hash, 숫자/시간/JSON 보조 및 과거 데이터 로더 | 일부 공통 함수가 현재도 필요 |
| models.py + independent_models.py | 실제11종 모델과 독립 힘/위치 모델 구성 | 현재 model_zoo 구현 본체 |
| independent_prediction.py | 저장 모델 선택/복원 후 test 예측 및 결과표 | 예측 본체 |
| independent_evaluation.py | 축별 힘/ID/구간/무부하 지표와 구간 탐색 | train/validation/test 공통 평가 |
| excel_export.py + excel_tables.py + excel_writer.py | 모델별 시트 선택, 행 정렬, Excel 쓰기 | Excel 내보내기 선택 기능 |
| engine.py + evaluation.py + folder_datasets.py + folder_prediction.py + time_repair.py | 이전 JSON/folder/추가학습·시간 복구 경로 | 현재 기능과 분리해 보관할 후보 |
| runtime.py | 이 PC NVIDIA 라이브러리 선택 | 학습 알고리즘과 무관한 환경 보조 |
| __init__.py | 패키지 표시 | 현재 기능 구현 없음 |

**현재 설정 또는 코드를 바꾸려면 어디를 보는가**

| 변경 목적 | 현재 수정 위치 |
|---|---|
| 사용할 모델 조합 | configs/train.yaml의 force_candidates / location_candidates |
| 모델 너비·층수 | 같은 설정의 force_params / location_params; 허용 옵션은 independent_models.DEFAULT_PARAMS / resolve_params |
| epoch·batch·학습률·창 길이·validation 비율 | configs/train.yaml의 max_epochs / batch_size / learning_rate / window_samples / validation_fraction |
| 길이·장력·각도 입력 그룹 | configs/train.yaml의 feature_groups |
| raw/Kalman 힘 정답 | configs/train.yaml의 force_source + force_columns; 현재 aligned XYZ 계약 검사 유지 |
| 숫자 행 선택/빈칸 처리 방식 | numeric_data.load_numeric_trial |
| loss/optimizer 로직 | independent_engine.train_branch |
| 새로운 네트워크 구조 | independent_models의 encoder 생성 및 models 기본 layer; 현재 루트 model_zoo.py만 수정해서는 반영되지 않음 |
| 평가식/구간 지표 | independent_evaluation.force_metrics / location_metrics |

현재 입력은 그룹을 실제 열 목록으로 바꾸는 방식이며 자유로운 input_columns 목록 인터페이스는 아직 없다.
사용자가 원하는 '입력/출력 열 지정 → 학습 → 실측/예측 저장'과 비교하면 이 제한도 정리 대상이다.

- 설계 판단: 숫자 결측 제거, train만으로 정규화, 파일/분할 경계 유지, scaler/입력 순서의 저장·복원,
  두 위치 loss 방식 및 힘 역정규화는 기능상 유지해야 한다. 그러나 각각 별도 파일일 필요는 없다.
  독립 분기 학습·무부하 비교·Excel 요구가 코드 증가의 일부를 설명하지만, 과거 호환과 세부 모듈 분리는
  구현 선택이다. 현재 사용성 문제를 '모두 필요한 파일이니 읽어야 한다'고 답하지 않는다.
- 단순화 방향은 사용자가 익숙한 train/predict/model_zoo/공통처리의4핵심 + 무부하 분석1개도 가능하다.
  앞선6개 제안에서 metrics를 공통처리에 합치는 선택이 가능하다는 뜻이며 아직 어느 재구성도 적용하지 않았다.
  같은 기능을 유지하며 기존 가중치 구조·정규화·결과 대응을 검증할 필요가 있다. 참조 저장소는
  창을 생성한 뒤 shuffle=True로 분할하므로, 파일 배치는 참고하되 현재 창 경계 분할을 그 방식으로 되돌리지 않는다.
- 수행/검증: 참조 GitHub 코드와 현재 파일/함수/import를 정적으로 대조하고 통합 기록에 읽는 지도를 추가했다.
  외부 저장소 clone/실행/수정, 새 학습·추론, 코드 이동·삭제는 하지 않았다. 실행 코드 변경이 없어
  단위 테스트는 재실행하지 않았다. 다음 재구성 시 사용자 직접 편집 가능성과 적은 파일 수를 우선한다.

## 38. 2026-10-05 — 핵심 Python5파일로 통합, 직접 열 지정과 자동 Excel (실제 학습 미실행)

- 요청: 사용자 직접 수정/관리 편의가 우선이다. 독립 힘/ID 네트워크, 모든 모델 조합,
  class0/masked, validation, CSV 열 선택, 날짜별 모델/메타데이터, 모델별 시트의 Excel1개,
  최선 결과 요약을 유지하며 필수 코드 위주로 정리하도록 요청했다. 30행의 출처도 질문했다.
- 수행: 기능을 아래 실제 구현5개로 합쳤다. 루트 파일이 다른 패키지의 함수를 호출만 하는 구조는
  없앴다. scripts에는 환경 설치/실행 shell2개만 남겼다. 과거 JSON/folder/추가학습/그림/
  개별 분석/Excel 모듈은 현재 실행 경로에서 제거했다. 기본 모델11종과 모델 파라미터는 유지했다.

| 수정 목적 | 현재 파일/함수 |
|---|---|
| 학습 전체 흐름, loss/optimizer/early stopping | `train.py`: train_experiment, train_branch |
| 새로운 모델, layer/너비, 힘/위치 독립성 | `model_zoo.py`: DEFAULT_PARAMS, build_branch, build_estimator |
| 예측/평가, 최선 조합 선택, Excel 열/시트 | `predict.py`: select_and_evaluate, predict_trials, ModelWorkbook |
| CSV 열/빈칸/분할/공통 지표 | `data_utils.py`: load_config, load_trial, prepare_data, force_metrics, location_metrics |
| 무부하 기록 범위/라벨 | `analyze_no_load.py`: calibrate_no_load, load_states |

- 보존: [코드 정리 전 압축본](../archive/code_before_simplification_20261005_172216.tar.gz)에
  57개 원본 파일을 저장하고 바이트/hash 일치를 확인한 후 구형 실행/테스트47개를 활성 트리에서
  제거했다. 원본 데이터·기존 결과·가상환경은 변경하지 않았다. 새 테스트는 모델/지표/파이프라인3파일이다.
  확인 근거는 `.runtime/simplification/archive_manifest.json`, `cleanup.json`에 있다.

**30행과 모델 입력**

- 참조 저장소 commit `c3238661f26199180b0b89f4b3f74f346d8c2221`의
  [model_zoo.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/c3238661f26199180b0b89f4b3f74f346d8c2221/scripts_model/model_zoo.py)에서
  LSTM/GRU/TCN/Transformer/KalmanNet 기본 창은5행, MLP/CNN/ConvMixer/ResNet은1행이었다.
  이 값은 확인한 코드 기본값이며 사용자가 과거 실행마다 실제 선택한 길이를 모두 증명하지는 않는다.
- 현재30행은 현재 행+이전29행의 입력으로 마지막 행의 정답을 맞추는 설정이다. 최적값 검증은 하지 않았다.
  이번 구조 정리에서는30을 유지했으며 `window_samples`로 변경할 수 있다. 현재 MLP는 마지막 행만
  사용하지만 다른 모델과 공통 비교하기 위한30행 준비 조건은 동일하다. 변경하면 새 학습이 필요하다.

**설정·데이터·학습에서 유지한 동작**

- `configs/train.yaml`에 `input_columns`, XYZ순서의 `force_columns`, `id_column`,
  `source_force_unit`을 명시했다. 임의 숫자 열을 선택할 수 있고 입력 차원은 자동 결정한다.
  calibration 기록은 별도 `calibration.force_columns`/단위를 사용한다. 더 이상 예전 그룹 JSON을
  수정할 필요가 없다. 기본26입력/3출력, mN→N, 부호, force_scope: tip을 유지했다.
- 기본 힘 학습은 ID18, 위치는 ID1–18이다. 위치 class0/masked만 다르게 처리하며 힘은 모든 유효
  부하 상태에서 연속 학습한다. 조합별 새 모델/optimizer를 유지하고 분기 재사용은 추가하지 않았다.
- CSV 선택 X/Y의 비숫자/NaN/Inf 행을 제외한 뒤 이어붙인다. 학습 대상 ID는 유효한 정수1–18이며
  파일 내 하나의 실험ID인지 확인한다. 선택하지 않은 열/valid flag/timestamp 간격은 제외에 쓰지 않는다.
  train 파일의 앞80%/뒤20%와 test 폴더 고정, train만의 scaler, 파일/역할을 넘지 않는 창,
  원본 source_row 대응, 확인된 hash의 라벨/역할 보호, train/test 중복 차단을 유지했다.
- 무부하 기록2의 mean center와 경계×1.1을 유지한다. 회귀 정답 offset/부호를 변경하지 않았다.
  valid/time 검사를 간소화하면서 이전 audited 경로를 함께 숨겨 유지하지 않았다. 과거 audited
  bundle의 가중치 구조는 복원 가능하지만 그 데이터 정책의 재현은 보관 코드에서 해야 한다.
  새 예측/Excel 경로는 과거 audited bundle을 명시적으로 거절하며 숫자행 정책으로 자동 변환하지 않는다.

**결과물**

- Train: `results/train/날짜_시간/`에 모든 조합 `comparison.csv`, 방식별 validation 최선
  `summary.json`, `validation.xlsx`, 설정·교정·분할·데이터·환경 기록을 저장한다.
  조합별 `models/방식__force_모델__location_모델/hrm_bundle.pt`는 두 가중치와 정규화/설정을 담는다.
  학습 이력과 validation_predictions.npz도 같은 조합 폴더에 둔다.
- Predict `--train-dir`: 모든 완료 조합을 고정 test 파일로 평가한다. 새 예측 날짜 폴더에
  `comparison.csv`(기존 validation열 + test_지표), `summary.json`, `predictions.xlsx`, 상세 JSON을 쓴다.
  `predictions.csv`는 방식별 validation 선택 bundle의 행별 결과다. Train 비교표는 변경하지 않는다.
  Test로 최선 조합이나 구간 경계를 선택하지 않는다. 입력만 있는 CSV의 단일checkpoint 추론도 지원한다.
- Excel은 힘/ID를 합친 실행별1개다. 학습에서는 validation 결과를 저장하며 train행의 재예측은
  자동 생성하지 않는다. 기본44모델시트(11모델×힘/ID×두방식)+2요약시트다.
  힘 시트의 첫6열은 gt_fx_mN/gt_fy_mN/gt_fz_mN/pred_fx_mN/pred_fy_mN/pred_fz_mN이다.
  ID 시트는 ground_truth_id/pred_id와 확률, source_file/source_row/시간/부하 상태를 남긴다.
  masked의 p0는 없으므로 빈칸이며 GT로 무부하 예측을0으로 바꾸지 않는다.
- 행별 Excel은 파트너를 **각 설정 후보 목록의 첫 모델**로 고정한 대표 분기 결과다.
  모든242조합의 개별 행을44시트에 담았다는 뜻이 아니다. 모든 조합의 성능은 비교표에 남기고
  대표 checkpoint/파트너/역할은 `_models`와 manifest에 명시한다. Test점수로 대표를 고르지 않는다.
  스트리밍 Excel 저장으로 전체 workbook 셀을 메모리에 누적하지 않으며 원본 행 정렬을 검사한다.

**실제 검증과 미실행 항목**

- 전체 `unittest discover -s tests -v` **30개 통과**. 증거 `.runtime/simplification/tests.log`.
  독립 분기/causal 입력/저장복원, force단위/평가식, 무부하/masked, 결측연결, train-only정규화,
  임의 열 이름, 정답 없는 추론, 분할/중복/고정test 변경 거절을 검증했다.
- 모델11종×입력/창3조건×출력class2조건×기본/변형2조건=132구성에서 정리 전/후 state_dict의
  키·순서·초기값·엄격복원·두 분기 출력을 CPU에서 오차0으로 확인했다.
  `.runtime/simplification/model_equivalence.json`; optimizer 갱신0회다.
- 합성 CSV에서 학습 함수를 mock하여 2×2×2=8조합의 모델 생성/저장, validation Excel,
  전8조합 test 평가/Excel/요약, 학습 비교표 불변을 검증했다. 이는 모델을 실제 학습한 결과가 아니다.
- 실제 CSV67개에 `--check-data`만 실행했다. 직전 데이터 준비와 source hash, 역할별 행/endpoint,
  부하 라벨 수가 같고 calibration center/std/경계/fit·holdout 포함률도 정확히 같았다.
  Train48파일730,320창, validation48파일181,560창, test19파일27,785창이다.
  `.runtime/simplification/prepared`, `data_equivalence.json`에 근거를 남겼다.
- Train/predict/무부하 분석의 `--help` 및 `git diff --check` 통과. 삭제한 패키지 import가 남지 않았음을 확인했다.
- 최종 원본 CSV67개의 hash 불변을 다시 확인했다. `.runtime/simplification/final_verification.json`.
- **실제 데이터 재학습·새 모델 성능 평가·실데이터 추론은 실행하지 않았다.** 최신 학습 명령은9절/README다.
  새 구조의 실제 성능/학습 소요시간은 사용자가 이후 학습을 실행해야 확인할 수 있다.

## 39. 2026-10-05 — 현재 데이터·설정으로 전체242조합 재학습과 Excel 검산 (완료)

- 요청/승인: 사용자가 퇴근 후 작업을 맡기며 현재 기준의 실제 재학습·test를 요청했다.
  최우선 결과물은 Excel의 ground truth/예측 대응 열이고 축별/전체 RMSE·MAE도 확인한다.
  사용자가 과거 results를 별도 보관하므로 이를 이동/덮어쓰지 않는다. 앞선 '학습 미실행' 지시를 대체한다.
- 모델 선택: shell은 가상환경 실행용이고 YAML의 force_candidates/location_candidates 또는
  train.py --models로 후보를 정한다. 이번에는 기본11×11×2의242조합을 모두 새로 학습한다.
  힘은 ID18 전용, 위치는 ID1–18, 30행입력, 각 CSV80/20, max_epochs60/patience10,
  무부하 mean center/경계×1.1을 유지한다. 입력26·힘XYZ열과 숫자행 연결 정책도 유지한다.
- 사전 검증: 전체30테스트 통과. 현재67CSV와 무부하 기록hash가 직전 준비와 동일하다.
  실행 sandbox에서는 GPU 장치가 보이지 않아 승인된 일반 실행으로 확인했고 RTX4090 CUDA 연산에 성공했다.
  현재 로드된 driver580.178.04에서는 과거580.173.02 우회를 강제하지 않았다.
- 고정 실행: train `results/train/20261005_194129`, predict `results/predict/20261005_194129`.
  설정snapshot/소스hash/진행상태/로그/검증기는 `.runtime/run_20261005_194129/`에 저장한다.
  학습 완료 후 test 전체조합 평가를 이어 실행하도록 시작했다. 결과가 나오면 Excel 셀을 다시 읽어
  원본 GT·행매핑과 prediction 배열, 축별/전체 RMSE·MAE를 별도로 대조한다.
- 평가 범위: validation은 train CSV 내부 후반20%다. Body ID1–17 test는 사용자가 같은 녹화에서
  분리한 후반 구간이며 tip ID18의 두 test파일은 기존 별도실험 보호hash와 동일하다.
  19파일 전체 위치지표는 혼합test로 표시하고 독립 body 일반화 성능으로 부르지 않는다.
  기대 창수: train730,320/validation181,560/test27,785, 그 중 tip71,007/17,687/8,283.
  Test body19,502창의 loaded8,578/unloaded7,893/uncertain3,031,
  tip8,283창의 loaded3,308/unloaded3,821/uncertain1,154를 구분한다.
- 완료: **242조합/484분기 실제 학습, 242조합test 평가, validation/test Excel 생성과 전수 검산**을 마쳤다.
  각 방식121조합이며 조합별 모델/optimizer를 새로 생성했다. 분기 학습시간 합계는2,705.09초
  (약45.1분)이며 데이터 준비·Excel·test·검산 시간은 별도다. 최대60epoch/early stopping을 적용했다.
  학습 비교표·checkpoint242개·test 비교표의 고유 조합242개가 모두 일치한다.

**사용자가 먼저 볼 결과**

| 목적 | 파일 |
|---|---|
| 모델별 validation 실측·예측 | [validation.xlsx](../results/train/20261005_194129/validation.xlsx) |
| 모델별 test 실측·예측 | [predictions.xlsx](../results/predict/20261005_194129/predictions.xlsx) |
| Validation 힘 모델22행 오차표 | [force_axis_metrics.csv](../results/train/20261005_194129/force_axis_metrics.csv) |
| Test 힘 모델22행 오차표 | [force_axis_metrics.csv](../results/predict/20261005_194129/force_axis_metrics.csv) |
| 선택 모델의 validation/body/tip/혼합test 요약8행 | [selected_model_summary.csv](../results/predict/20261005_194129/selected_model_summary.csv) |
| 모든242조합 지표 | 각 역할 폴더의 comparison.csv |
| 최선모델 및 범위·구간 상세 | summary.json, metrics.json, scope_summary.json |
| 재현/검증 | execution_manifest.json, verification.json; 학습 폴더 source_snapshot.tar.gz |

- 힘 Excel의 첫6열은 `gt_fx_mN, gt_fy_mN, gt_fz_mN, pred_fx_mN, pred_fy_mN, pred_fz_mN`이다.
  유부하/무부하/uncertain을 모두 포함하며 회귀값을0으로 바꾸지 않았다.
  기본 힘scope가tip이므로 모든 힘 시트는 ID18 정답이 확인된 행만 포함한다.
  Validation 힘 시트당17,687행, test8,283행이다. ID 시트는 확정 부하 행만 사용하여 각각154,898/23,600행이다.
- 각 Excel은44모델시트+2요약시트다. 대표 분기는 첫 파트너 고정 규칙이며 모든242조합의
  행별 결과를44시트에 담았다는 뜻은 아니다. 전체 조합의 지표는 comparison에 있다.
  MATLAB에서 개별 시트를 지정해 읽을 수 있다. 파일 크기는 validation1,038.2MiB/test170.7MiB다.
- 원본 과거 결과는 사용자가 `results_legacy_1004`로 보관했다. 이동/덮어쓰기하지 않았고
  `.gitignore`에 `results_legacy_*/`를 추가해 큰 기존 결과가 Git에 포함되지 않도록 했다.

**Validation으로 선택한 힘 결과**

양방식 모두 **힘MLP + 위치Transformer**가 선택됐다. Test 점수로 선택을 변경하지 않았다.
선택된 두 방식의 MLP 힘 결과는 동일하다. 단위는mN이며 XYZ RMSE는 모든 행×3축의 제곱오차를
모아 평균한 후 제곱근을 취한다. 축별 RMSE의 단순 평균이나 힘벡터 오차의norm RMSE와 다르다.

| 평가 | 표본 수 | Fx RMSE | Fy RMSE | Fz RMSE | XYZ RMSE | XYZ MAE |
|---|---:|---:|---:|---:|---:|---:|
| Validation, 각 train CSV 후반 | 17,687 | 215.87 | 111.86 | 109.98 | 154.07 | 104.09 |
| ID18 별도실험 test 두 파일 | 8,283 | 175.60 | 94.59 | 127.05 | 136.53 | 95.03 |
| summary_18_test.csv | 5,711 | 193.94 | 94.19 | 139.70 | 148.33 | 100.70 |
| summary_18_test_2.csv | 2,572 | 125.63 | 95.48 | 93.00 | 105.75 | 82.45 |

ID18 test 축별MAE는 **Fx116.43 / Fy76.49 / Fz92.17mN**이다. Fx 오차가 가장 크다.
이 실행에서 약80mN 수준이나 모든축90mN 이하 달성을 주장하지 않는다. 이전 실행과는 학습/validation
분할·전처리·유효 평가행이 달라 static 효과나 모델 자체 개선만의 통제 비교로 해석하지 않는다.

**위치·구간·무부하 결과: 힘으로 고른 동일 조합의 위치Transformer**

아래 기본3구간은1–10/11–15/16–18이다. 정확ID/구간 점수는 유부하 조건부이며 class0도
이 열은0을 제외한 조건부 위치 argmax로 계산한다. 접촉 검출과 최종 구간 판정 성공은 별도로 본다.

| 평가 범위 | 유부하 수 | masked 정확ID / 구간 | class0 정확ID / 구간 |
|---|---:|---:|---:|
| Validation 내부후반 | 89,507 | 63.34% / 85.70% | 64.73% / 87.04% |
| Body ID1–17 동일녹화test | 8,578 | 35.81% / 77.90% | 29.35% / 72.91% |
| Tip ID18 별도실험test | 3,308 | 20.47% / 62.39% | 35.88% / 69.17% |
| 19파일 혼합test | 11,886 | 31.54% / 73.58% | 31.17% / 71.87% |

Body test의 기본 구간별 유부하support는6,000/1,945/633이다. Recall은 masked84.03/66.17/55.77%,
class078.60/63.65/47.39%다. Body 부분에서 upper에 실제 포함되는 ID는16–17이다.
Class0 body 유부하recall68.54%, 무부하recall97.17%, balanced accuracy82.86%다.
유부하에서 접촉 검출과 기본 구간을 모두 맞춘 비율은48.88%다. Masked는 자체 무부하 검출 기능이 없다.

Validation의 ID별 균형 구간recall로 선택한 경계는 두 방식 모두 **1–4 / 5–10 / 11–18**이다.
이를 고정한 body 동일녹화test 조건부 구간정확도는 **masked80.96% / class077.40%**이며,
class0의 검출 누락까지 포함한 body 구간 성공률은54.44%다. 혼합test 조건부 정확도는84.70/82.81%다.
ID18 test의 넓어진 upper구간 정확도94.41/96.86%를 독립body 구간90% 달성으로 해석하면 안 된다.
구간 탐색 전체 후보/선택근거는 metrics.json, 범위별 추가 재계산은 scope_summary.json에 보존했다.

**검산 근거와 후속 범위**

- Excel **88모델시트, validation3,796,870행 + test701,426행**을 XML 스트리밍으로 전수 확인했다.
  원본 CSV의 source_file/source_row와 실제 XYZ, 원본/유효ID, 부하 라벨, 모델 확률·argmax를 대조했다.
  Validation 예측은 저장NPZ를 원본행으로 다시 대응하여 검사했다. Masked를 GT로0으로 만드는 처리가 없는지도 확인했다.
- Excel에서 전체/축별 RMSE·MAE를 재계산해 comparison/파일별metrics와 일치함을 확인했다.
  원본GT와의 최대차이는4.55e-13mN, 저장 지표와 재계산 지표 최대차이는8.81e-13 수준이었다.
  이는 소수 표기/연산 반올림 수준이다. 검산 약419.6초, 새 학습/모델추론 없이 수행했다.
- `predictions.csv`의 선택 모델 결과도 다시 계산해 기존 overall metrics와 일치했다.
  Body/독립tip/혼합test를 따로 재집계했고 선택checkpoint와 고정파일19개/support를 검사했다.
  원본67CSV·무부하 기록·학습 실행의 소스7파일hash가 불변이다. 최초30코드테스트도 통과했다.
- 실행·검증 상세는 각 폴더 verification.json/execution_manifest.json과
  `.runtime/run_20261005_194129/`의 실행/검산 로그에 있다. 모델별22행 CSV의 지표 열에도 빈값이 없음을 확인했다.
- 이번 요청의 학습·test·Excel·RMSE/MAE 정리는 완료했다. 정확도 개선, 입력 이력/손실 변경,
  추가 독립body 데이터 수집, 제어 연결은 이번에 실행한 작업이 아니다. 목표body90%는 아직 달성하지 못했다.

## 40. 2026-10-06 — 유부하 조건부 정확도의 의미 확인

- 요청: 결과의 ‘유부하 조건부 정확도’가 무엇인지 설명한다.
- 정의: 정답 F/T와 저장된 무부하 교정 경계로 loaded인 평가 행 중 학습 대상 ID에 속하는 행을
  분모로 삼는다. 모델이 유부하로 검출한 행만 고르는 것이 아니다. Unloaded/uncertain은 제외한다.
  조건부 정확ID는 ID0을 제외한 개별 ID 확률의 argmax, 조건부 구간은 각 구간의 ID 확률합의
  argmax로 평가한다. Class0가 실제로 무부하를 예측한 행도 이 위치 진단에서는 제외하지 않는다.
- 최종 판정과의 차이: class0는 먼저 p0와 개별 ID 확률 전체의 argmax로 final_id를 정한다.
  final_id=0이면 최종 구간도 무부하이고, 그 외에만 구간별 ID 확률합의 argmax를 사용한다.
  p0와 구간 확률합을 직접 비교하는 규칙은 아니다. `system_loaded_region_accuracy`는 같은
  유부하 분모에 이 무부하 판정까지 적용하므로 검출 누락을 오답으로 센다.
- 현재 body 동일녹화 test 유부하8,578행, validation 선택 구간1–4/5–10/11–18 기준으로
  class0 조건부 구간77.40%, 검출과 구간을 모두 맞춘 비율54.44%다. Masked80.96%는 위치
  조건부 지표이며 masked 자체에는 무부하 검출기가 없다. 무부하에서의 오경보는 별도 검출
  지표로 확인해야 하므로54.44%도 전체 유무부하 행을 합친 정확도를 뜻하지 않는다.
- 검증: `data_utils.py`의 location_predictions/location_metrics 구현을 읽어 분모와 gate를
  확인했다. 코드·데이터·기존 결과 변경, 재학습·추론은 수행하지 않았다. 추가 실행 작업은 없다.

## 41. 2026-10-06 — ID 확률 저장, 구간 선택 및 masked의 의미

- 요청: ID별 확률 저장 여부, 세 구간의 선택 기준, 약80%/54%의 의미와 masked가 무부하를
  검출하지 않는 이유를 설명한다. 학습이나 판정 규칙 변경 요청은 아니다.
- 결과 확인: `results/predict/20261005_194129/predictions.xlsx`의 `id_masked_*`와
  `id_class0_*` 시트에는 `ground_truth_id`, `pred_id`, `p0`부터 `p18` 열이 있다.
  p1..p18은 행별 ID softmax 확률이며 masked의p0는 빈칸이다. Validation Excel도 같은 형식이다.
  방식별 선택 조합은 같은 폴더 `predictions.csv`에 저장되고 model/mode 및 p0..p18 열로 구분된다.
  확률값 자체와 정답을 맞힌 행의 비율인 정확도는 서로 다른 값이다.
- 구간 선택 확인: ID 순서가 연속인 세 구간의 경계136개를 기록하고, 각 구간 최소3개 ID 및
  유부하 support 조건을 만족하는55개 후보 중 validation 점수로 선택했다. 각 구간 안에서
  정답 ID별 구간recall을 평균하고 그 세 값을 동등하게 평균한 지표
  `region_balanced_id_macro_recall`이 우선 기준이다. 데이터가 많은 ID/구간의 쏠림을 줄이는
  선택 기준이며 전체 행 정확도를 단순 최대화한 것은 아니다. 선택은 양방식 모두1–4/5–10/11–18이다.
  구간 점수는 소속 ID 확률의 합이며 ID 확률을 변경하거나 임의 가중치를 준 것은 아니다.
  Test는 선택한 경계를 고정해 평가했다. 이 결과가 가능한 모든 설계의 최적 경계라는 보장은 없다.
- 수치 해석: body 동일녹화 test 유부하8,578행에서 masked 조건부 구간정확도80.96%,
  class0 조건부77.40%, class0 검출과 구간을 모두 맞춘 비율54.44%다. 모두 행별 정답률이며
  모델의 평균 예측확률이 아니다. 검출 누락 효과는 같은 class0의77.40%와54.44%를 비교한다.
  54.44%의 분모에는 무부하 행이 없으므로 전체 유무부하 통합 정확도와도 구별한다.
- Masked 구현: 위치 loss는 GTloaded인 행에서만 계산하고 무부하/uncertain 행은 제외한다.
  출력은 ID1–18의18개뿐이며 무부하ID0은 없다. 무부하 입력에서도 p1..p18 합은1이고 어느
  ID 하나가 가장 높으므로 높은 softmax값을 접촉 검출로 해석할 수 없다. Class0는 ID0–18의
  19개 출력과 무부하 정답 학습을 추가하고 uncertain은 제외한다. 힘 회귀는 독립이며 유무부하
  연속 실측값을 학습한다. 예측 힘을 이용해 masked를 무부하로 판정하는 연결은 현재 없다.
  Masked를 실제 접촉 유무 판정과 함께 쓰려면 별도 검출 기능이 필요하며 이번에 추가하지 않았다.
- 검증: Excel의 실제 시트명/헤더, CSV 헤더, 저장 metrics.json의 후보/선택 기준,
  train.py/model_zoo.py/data_utils.py/predict.py의 loss·출력·판정 경로를 읽어 확인했다.
  문서 설명만 추가했으며 코드/데이터/결과 수정이나 학습·추론은 수행하지 않았다.

## 42. 2026-10-06 — 현재 무부하 경계 수치 재확인

- 요청: 현재 적용한 무부하 경계값을 확인한다. 값 변경 요청은 아니다.
- 근거: `results/train/20261005_194129/calibration.json`과 현재 calibration 설정,
  `analyze_no_load.py`의 load_states 구현을 대조했다. 기록2 앞70% mean center,
  최대 표준화 축편차 score의95%/99.5% 분위수 경계에1.1을 곱한 설정이다.
- 판정용 보정은 `F_corrected = F_recorded - center`이며 center XYZ는
  [-67.362099, +19.592977, -85.572715]mN이다. 이미10% 확대된 아래 경계에 또1.1을 곱하지 않는다.

| 축 | 보정 후 무부하 반폭(mN) | 보정 후 유부하 반폭(mN) | 원본값 기준 무부하 구간(mN) |
|---|---:|---:|---:|
| Fx | 134.326254 | 176.508704 | -201.688353 ~ +66.964155 |
| Fy | 126.814159 | 166.637587 | -107.221183 ~ +146.407136 |
| Fz | 192.669986 | 253.174107 | -278.242701 ~ +107.097270 |

- 세 축 절댓값이 모두 무부하 반폭 이하이면 unloaded, 어느 한 축이라도 유부하 반폭 이상이면
  loaded다. 그 사이이면 uncertain으로 위치 loss에서 제외한다. 경계값은 각각 포함한다.
  회귀 정답에 center를 빼거나 무부하 힘을0으로 치환하지 않는다.
- 검증은 저장값 읽기/단위 환산과 코드 확인으로 수행했다. 문서만 추가했으며 교정 재계산,
  설정/결과 변경, 재학습·추론은 하지 않았다. 추가 작업은 없다.

## 43. 2026-10-06 — 학습 시 offset 적용 대상 재확인

- 요청: 학습 전에 offset을 뺀 것인지 확인한다. 학습 방식 변경 요청은 아니다.
- 답변: 무부하 기록의 mean center를 빼는 것은 GT 유부하/무부하/uncertain 라벨 생성에만
  적용된다. 힘 회귀 정답은 선택 CSV의 연속 실측 XYZ를 유지한다. 힘 정답의 단위 변환과
  학습용 평균/표준편차 표준화는 무부하 영점 보정과 별개이며, 추론 시 표준화를 역변환하므로
  Excel 실측/예측도 무부하 offset을 제거하지 않은 원본 힘 기준이다.
- 검증: data_utils.py의 CSV 힘 읽기/단위 변환과 load_states 호출, train.py WindowStore의
  force_N/표준화 정답 및 추론 역변환 경로를 확인했다. 문서만 추가했으며 코드/설정/데이터/
  결과 변경, 재학습·추론은 수행하지 않았다. 추가 실행 작업은 없다.

## 44. 2026-10-06 — train/test 모든 파일의 초기100행 힘 평균

- 요청: 사용자가 각 파일 초기 구간은 외력이 없는 상태라고 설명했고, 초기 offset 확인을 위해
  모든 train/test CSV의 처음100개 Fx/Fy/Fz 평균을 요청했다. 보정 적용이나 재학습 요청은 아니다.
- 대상/정의: configs/train.yaml의 train48(dynamic30+static18)/test19, 총67개 CSV 전부를 읽었다.
  `fts_kalman.aligned_fx`, `fts_kalman.aligned_fy`, `fts_kalman.aligned_fz`를 원본mN 단위로 사용했다.
  헤더 제외 원본 데이터행0–99 안에서 축별 유효 숫자만 평균했다. Valid flag/X열/tip/역할 분할
  필터나 offset/scaler는 적용하지 않았다. 빈칸을0으로 채우거나101행 이후에서 보충하지 않았다.
- 결과는 한 파일에 저장했다:
  [initial_100_force_means.csv](../results/train/20261006_075401_initial100_offsets/initial_100_force_means.csv).
  열은 split/file, fx_mean_mN/fy_mean_mN/fz_mean_mN, 원본 조회 행수, 축별 유효 개수,
  XYZ 공통 유효 개수, 축별 표본표준편차(ddof=1)다. UTF-8 BOM CSV로 Excel에서 열 수 있다.
- 전 파일100행 이상이다. Train static ID16은1행 결측으로99개, static ID18은3행 결측으로97개를
  사용했다. 나머지65파일은 각100개다. 이번 데이터는 XYZ 결측 위치가 일치한다.

| 구분 | 파일 수 | Fx 파일별 평균 범위(mN) | Fy 파일별 평균 범위(mN) | Fz 파일별 평균 범위(mN) |
|---|---:|---:|---:|---:|
| Train | 48 | -286.48 ~ +224.54 | -132.35 ~ +403.53 | -563.30 ~ +286.98 |
| Test | 19 | -89.19 ~ +94.92 | -516.00 ~ +100.73 | -232.73 ~ +620.09 |

| ID18 파일 | 구분 | Fx 평균(mN) | Fy 평균(mN) | Fz 평균(mN) |
|---|---|---:|---:|---:|
| summary_18.csv | train | 29.129101 | 22.675559 | -57.640554 |
| summary_18-2.csv | train | -45.204937 | -39.122755 | -23.383666 |
| static seg-id-18 | train | 73.987535 | 3.301895 | 5.623966 |
| summary_18_test.csv | test | 22.185113 | 42.353397 | 60.471487 |
| summary_18_test_2.csv | test | -4.534859 | 8.730982 | 21.430823 |

- 가장 큰 축별 평균을 가진 파일은 test summary_2_test.csv로 XYZ평균은
  [41.944558, -516.001907, 620.094581]mN이다. Train static seg-id-1_right도
  [-286.480296, 403.527989, -563.295504]mN이다. 초기 무부하라는 사용자 설명을 전제로 하면
  일부 파일의 초기 영점 차이가 크며, 공통 기록2 경계만으로는 무부하가 유부하로 표시될 수 있다.
  이 분석만으로 원인이나 전체 시간 동안의 offset 안정성을 판정하지 않았다.
- 검증: pandas 평균을 독립 csv.DictReader+math.fsum 계산과67파일 전부 대조했다.
  최대차이는1.14e-13mN이다. 저장 CSV를 다시 읽어67고유행/평균 소수9자리 반올림 일치를 확인했다.
  원본 CSV는 읽기만 했고 기존 calibration/모델/결과를 바꾸지 않았다. 요청 분석은 완료했다.
  파일별 offset 적용, 교정 경계 재설정, 재학습은 수행하지 않았다.
- 후속 사용자 요청: 별도 테스트 파일은 만들 필요가 없다. 향후 이번 유형의 분석에서는
  테스트 파일을 추가하지 않고 필요한 검산을 임시 실행으로 수행한다. 이번 작업에도 테스트
  코드를 파일로 추가하지 않았으며 결과 CSV1개와 기존 문서 기록만 저장했다. 기존 파일 삭제 요청은 아니다.

## 45. 2026-10-06 — 사용자 직접 전체 조합 학습 및 test 명령 안내

- 요청: 사용자가 수정 후 직접 학습/test를 실행할 예정이며, 에이전트는 실행하지 말고
  모든 조합을 학습한 뒤 test하는 명령만 안내한다.
- 확인: 현재 configs/train.yaml은 힘11종×위치11종×masked/class0=242조합이다.
  힘은 force_scope: tip(ID18), 위치는ID1–18이다. Train/test 경로는 datasets/train 및
  datasets/test, validation은 각 train CSV의 앞80%/뒤20% 분할이다.
- 프로젝트 루트에서 사용자가 실행할 명령(이 기록은 실행 승인이 아니다):

```bash
HRM_RUN_ID="$(TZ=Asia/Seoul date +%Y%m%d_%H%M%S)"

bash scripts/hrm_python.sh train.py --config configs/train.yaml \
  --output "results/train/$HRM_RUN_ID" &&
bash scripts/hrm_python.sh predict.py --train-dir "results/train/$HRM_RUN_ID" \
  --output "results/predict/$HRM_RUN_ID"
```

- &&로 학습이 성공한 경우에만 test를 이어 실행한다. 후보 제한 옵션을 주지 않으므로
  YAML의 모든 조합을 학습하고 --train-dir로 모든 완료 조합을 평가한다. Test 파일은 해당
  학습에서 저장한 test 목록/hash를 사용한다. 이 모드에는 --input-dir를 따로 지정하지 않는다.
  결과 폴더는 프로그램이 생성하며 validation.xlsx/predictions.xlsx 및 comparison.csv,
  summary.json, 조합별 checkpoint를 저장한다. 대표 시트 규칙은 기존과 같다.
- 수행/검증: 현재 YAML, shell 실행기, train/predict CLI 및 전체 조합 평가 경로를 읽어 확인했다.
  학습·추론·코드 테스트·데이터 준비 명령을 실행하지 않았고 테스트 파일도 만들지 않았다.
  다음 실행은 사용자가 수행한다. 최신 수정 데이터의 준비 성공이나 성능을 검증했다는 뜻은 아니다.

## 46. 2026-10-06 — 사용자 재학습20261006_095933의 모델별 결과 분석

- 요청: 사용자가 새로 학습했다며 가장 좋은 모델과 다른 모델의 결과를 요청했다.
  기존의 에이전트 학습/test 실행 금지 지시를 유지하고 저장 결과만 읽었다.
- 완료 상태: comparison.csv의242행이 모두complete이며 checkpoint/validation_predictions.npz도
  각각242개다. summary.json은 dataset_role=validation이다. Progress는242/242와 마지막 조합을
  기록했지만 최종status=complete 항목은 없다. Validation.xlsx는0바이트, workbook manifest는
  없고 `results/predict/20261006_095933`도 없다. Excel 저장 이후 전체 실행/test 완료는 확인할 수
  없으며 원인을 단정하지 않는다. 이전20261005 test 결과를 새 모델 test로 사용하지 않았다.
- 데이터: 저장된 설정은 이전 실행과 config_path 외 동일하다. Audit hash 비교에서 train29개,
  test10개가 이전 실행과 달라졌다. Static ID7 유효 숫자 행은22,072→18,445다. 변경의 원인이나
  모든 수정 내용을 이 분석에서 확인한 것은 아니다. 힘 validation은ID18의17,687창,
  위치 validation은180,834창(유부하87,183/무부하69,514/불확실24,137)이다.
- 선택: 최저 validation 힘 RMSE를 먼저 선택하고0.001mN 수치 동률 안에서 ID macro recall이
  가장 큰 조합을 선택한다. 저장된 최선은 masked 힘MLP/위치ResNet, class0 힘MLP/위치Transformer다.
  두 힘MLP 결과는 XYZ RMSE154.261339mN, XYZ MAE105.208080mN,
  축별 RMSE Fx216.526716/Fy110.898059/Fz110.487483mN이다. 구간/검출 지표를 직접 최대화한 선택은 아니다.

**모델별 힘 validation: 위치 파트너MLP 고정, 단위mN**

| 힘 모델 | masked RMSE | class0 RMSE | masked MAE | class0 MAE |
|---|---:|---:|---:|---:|
| MLP | 154.26 | 154.26 | 105.21 | 105.21 |
| CNN | 168.86 | 168.86 | 119.57 | 119.57 |
| ConvMixer | 162.25 | 162.25 | 110.49 | 110.49 |
| ResNet | 157.88 | 156.54 | 109.59 | 108.77 |
| LSTM | 168.86 | 168.86 | 111.91 | 111.91 |
| GRU | 172.83 | 172.83 | 123.73 | 123.73 |
| TCN | 180.50 | 180.50 | 125.29 | 125.29 |
| Transformer | 162.22 | 162.22 | 116.26 | 116.26 |
| KalmanNet | 166.33 | 166.33 | 114.45 | 114.45 |
| Small GRU | 159.74 | 159.74 | 109.96 | 109.96 |
| Residual TCN | 178.34 | 179.43 | 126.16 | 126.82 |

- 독립 재학습된 조합마다 일부 분기 지표가 달라 이 표는 기존 대표 파트너 규칙을 따른다.
  모든 조합에서의 범위와 대표값은 구별한다. 예를 들어 class0 ResNet RMSE는 전체 파트너에서
  155.43–158.30mN, residual TCN은167.07–180.23mN이다. MLP가 전체 최저인 점은 동일하다.

**모델별 위치 validation: 힘 파트너MLP 고정, 단위%**

정확ID와 조건부 구간은 실제 유부하87,183창에서 평가한다. 이번 표는 설정의 기본 구간
1–10/11–15/16–18이다. 이전 실행의 최적화 경계1–4/5–10/11–18을 적용한 수치가 아니다.
‘검출+구간’도 같은 유부하 분모에 검출 누락을 오답으로 포함한다.

| 위치 모델 | masked 정확ID | masked 구간 | class0 정확ID | class0 구간 | class0 검출+구간 |
|---|---:|---:|---:|---:|---:|
| MLP | 56.23 | 83.57 | 45.40 | 79.49 | 60.62 |
| CNN | 54.78 | 82.49 | 51.05 | 81.30 | 62.95 |
| ConvMixer | 57.22 | 82.65 | 54.40 | 80.99 | 62.59 |
| ResNet | 62.32 | 84.01 | 50.50 | 80.57 | 64.56 |
| LSTM | 42.03 | 79.72 | 43.56 | 81.34 | 65.40 |
| GRU | 50.09 | 78.29 | 50.41 | 82.23 | 66.11 |
| TCN | 51.80 | 82.18 | 48.82 | 78.35 | 60.59 |
| Transformer | 60.99 | 84.25 | 62.58 | 86.29 | 65.36 |
| KalmanNet | 49.33 | 78.40 | 48.51 | 79.05 | 61.29 |
| Small GRU | 46.74 | 78.70 | 49.99 | 81.58 | 64.96 |
| Residual TCN | 46.87 | 79.65 | 45.88 | 78.45 | 60.21 |

- 선택된 masked ResNet ID macro recall60.16%, class0 Transformer59.91%다.
  모든 조합에서 위치ID만 우선하면 masked 힘TCN/위치ResNet의 ID macro61.62%, 정확ID63.11%가
  가장 높지만 힘 오차가 커 현재의 힘 우선 선택에서는 제외된다.
- Class0 Transformer 유부하 recall73.33%, 무부하 recall92.85%, balanced accuracy83.09%,
  유부하 검출+구간65.36%다. 전체 유무부하156,697창의 최종 구간정확도는77.56%로 분모가 다르다.
  검출/검출+구간은 class0 GRU가 각각balanced accuracy84.63%/66.11%로 더 높다.
  Masked 자체에 무부하 검출 기능이 없다는 해석은 유지한다.
- 검증: 저장 comparison/summary/progress/config/audit와242개 파일 존재를 읽어 대조하고
  모델별 표를 재정렬했다. 학습·추론·Excel 재생성이나 새 테스트 파일 생성은 하지 않았다.
  확인 가능한 validation 결과 분석은 완료했으며 새 test 성능/Excel 완료 확인은 미완료다.

## 47. 2026-10-06 — 최신242조합 test 결과 확인·전수 검산

- 요청: 사용자가 ‘test로도 해봐’라고 새 test 평가를 승인했다. 사전 확인 중
  `results/predict/20261006_095933`의242조합 평가 결과가 이미 완료·저장되어 있음을 발견했다.
  Summary/metrics는 정확히 `results/train/20261006_095933`을 참조하고 manifest와 Excel도 있었다.
  따라서 에이전트가 새로242조합을 추론했다고 기록하지 않는다. 기존 완료 결과를 사용해
  test 범위별 지표를 재계산하고 Excel 전수 검산을 수행했다. 새로운 테스트 코드는 파일로 만들지 않았다.
- 대상: 고정 test19파일27,785창이다. Body ID1–17은 동일녹화 분할19,502창
  (유부하8,045/무부하9,185/불확실2,272), ID18은 기존 독립실험 두 파일8,283창
  (유부하3,308/무부하3,821/불확실1,154)이다. Tip 두 파일hash가 보호된 독립실험과 일치한다.
  전체 혼합test의 유부하11,353/무부하13,006/불확실3,426을 구별한다.
- Validation 선택 유지: masked 힘MLP/위치ResNet, class0 힘MLP/위치Transformer다.
  Test 최저 점수로 선택 모델이나 구간을 변경하지 않았다.

**선택된 힘MLP의 ID18 test 결과, 단위mN**

| 평가 파일 | 창 수 | Fx RMSE | Fy RMSE | Fz RMSE | XYZ RMSE | XYZ MAE |
|---|---:|---:|---:|---:|---:|---:|
| 독립실험 두 파일 합계 | 8,283 | 177.19 | 94.73 | 131.25 | 138.56 | 96.46 |
| summary_18_test.csv | 5,711 | 197.15 | 94.39 | 142.95 | 150.79 | 102.03 |
| summary_18_test_2.csv | 2,572 | 121.68 | 95.46 | 100.49 | 106.49 | 84.08 |

합계 축별MAE는 Fx116.98/Fy76.46/Fz95.92mN이다. 두 무부하 방식의 선택 힘 결과는 같다.
힘은 유무부하/불확실 상태의 연속 정답을 모두 평가하며 body 행을 tip 힘0으로 포함하지 않는다.

**모델별 힘 test: 위치 파트너MLP 고정, 단위mN**

| 힘 모델 | masked RMSE | class0 RMSE | masked MAE | class0 MAE |
|---|---:|---:|---:|---:|
| MLP | 138.56 | 138.56 | 96.46 | 96.46 |
| CNN | 135.30 | 135.30 | 93.57 | 93.57 |
| ConvMixer | 144.46 | 144.46 | 100.40 | 100.40 |
| ResNet | 132.99 | 131.62 | 92.73 | 91.59 |
| LSTM | 138.06 | 138.06 | 94.61 | 94.61 |
| GRU | 135.17 | 135.17 | 89.16 | 89.16 |
| TCN | 142.30 | 142.30 | 96.64 | 96.64 |
| Transformer | 139.39 | 139.39 | 94.76 | 94.76 |
| KalmanNet | 133.66 | 133.66 | 87.58 | 87.58 |
| Small GRU | 132.49 | 132.49 | 89.82 | 89.82 |
| Residual TCN | 131.63 | 132.23 | 87.79 | 88.46 |

전체242조합에서 관측된 최저test XYZ RMSE는 masked 힘Residual TCN/위치TCN의129.940945mN이다.
이는 test 관측 최저값이며 validation으로 선택된 MLP138.56mN과 구별한다. 이 표의 대표 분기는
첫 파트너 고정으로, 각 모델에서 test가 제일 좋은 조합만 골라 만든 표가 아니다.

**선택 위치 모델의 test 범위별 결과, 단위%**

기본 구간1–10/11–15/16–18과 validation 선택 구간1–4/5–10/11–18을 모두 남긴다.
선택 구간은 두 방식 모두 동일하며 test로 경계를 조정하지 않았다. 정확ID/조건부 구간/검출+구간은
모두 각 범위의 실제 유부하를 분모로 삼는다.

| 범위 | 방식/위치 모델 | 정확ID | 기본 구간 | 선택 구간 | 검출+선택 구간 |
|---|---|---:|---:|---:|---:|
| Body1–17 동일녹화 분할 | masked ResNet | 25.98 | 72.08 | 77.86 | 해당 없음 |
| Body1–17 동일녹화 분할 | class0 Transformer | 31.91 | 76.72 | 81.18 | 64.67 |
| ID18 독립실험 | masked ResNet | 39.39 | 76.12 | 96.92 | 해당 없음 |
| ID18 독립실험 | class0 Transformer | 42.59 | 68.38 | 97.52 | 76.06 |
| 19파일 혼합test | masked ResNet | 29.89 | 73.26 | 83.41 | 해당 없음 |
| 19파일 혼합test | class0 Transformer | 35.02 | 74.29 | 85.94 | 67.99 |

Body class0 유부하recall76.68%, 무부하recall97.05%, balanced accuracy86.87%다.
유무부하 검출 분모는17,230창이며 불확실2,272창은 제외한다. Masked는 자체 무부하 검출이 없다.
Body 선택 구간recall은 masked76.97/68.42/95.38%, class066.96/77.55/93.66%다.
ID18-only의 넓은상단구간96–97%를 전체body90% 달성으로 해석하면 안 된다. 독립 body 일반화도
검증한 것이 아니다. 이전 실행에서 body test 데이터/부하 라벨수가 바뀌어 단순 전후 수치 차이를
모델이나 offset 변경만의 개선 효과로 단정하지 않는다.

**다른 위치 모델의 body1–17 test: 힘 파트너MLP, 기본 구간, 단위%**

| 위치 모델 | masked 정확ID | masked 구간 | class0 정확ID | class0 구간 | class0 검출+구간 |
|---|---:|---:|---:|---:|---:|
| MLP | 27.57 | 77.84 | 21.43 | 72.28 | 48.46 |
| CNN | 24.19 | 75.04 | 23.73 | 72.14 | 51.08 |
| ConvMixer | 20.05 | 71.35 | 17.19 | 64.59 | 44.01 |
| ResNet | 25.98 | 72.08 | 19.37 | 73.04 | 50.01 |
| LSTM | 14.79 | 68.96 | 17.85 | 74.28 | 55.41 |
| GRU | 18.78 | 68.15 | 30.18 | 82.61 | 64.18 |
| TCN | 25.31 | 73.61 | 26.53 | 72.52 | 50.88 |
| Transformer | 27.43 | 73.86 | 31.91 | 76.72 | 59.83 |
| KalmanNet | 19.50 | 74.12 | 28.22 | 71.82 | 52.59 |
| Small GRU | 17.23 | 68.03 | 18.60 | 75.49 | 50.98 |
| Residual TCN | 19.75 | 71.34 | 21.48 | 74.03 | 50.68 |

- 저장 결과: 같은predict 폴더의 기존predictions.xlsx/comparison.csv/metrics.json을 유지하고,
  `force_axis_metrics.csv`22행, `selected_model_summary.csv`8행, `scope_summary.json`,
  `verification.json`을 추가했다. selected_model_summary.csv의 비율 단위는%이고 원본metrics는0–1이다.
- 검증: 기존 검산 유틸을 임시 Python 실행에서 재사용해 test Excel44모델시트+2요약시트를 검사했다.
  총718,124모델시트 행(힘시트당8,283/ID시트당24,359)을 원본CSV 행·정답·라벨과 대조했다.
  ID 확률/argmax, 무부하masked p0빈칸, Excel 힘축별/전체 RMSE·MAE 및 파일별 지표를 확인했다.
  GT 최대차이2.27e-13mN, 지표 최대차이1.03e-12(반올림 수준)이며 검산50.46초에 통과했다.
  Test 원본19파일hash와 대표checkpoint/Excel hash, 모든242조합의 validation 열 보존도 확인했다.
  선택모델 predictions.csv에서 기본/선택구간의 지표를 재계산하여 저장 metrics와 일치했다.
- 이번 test 결과 확인·검산·범위별 분석은 완료했다. 새 모델 추론/재학습은 실행하지 않았다.
  기존0바이트 validation.xlsx 복구는 이번 test 요청에서 수행하지 않았다. Body90% 목표 미달이다.

## 48. 2026-10-06 — 학습/test 입력 경로 설정 위치 안내

- 요청: train/test에서 사용하는 파일의 경로를 어디서 지정하는지 확인한다.
- 현재 입력 형식은CSV이며 configs/train.yaml의 train_directory: datasets/train,
  test_directory: datasets/test에서 지정한다. 데이터 준비는 각 폴더 바로 아래의*.csv를 읽는다.
  Validation.xlsx와 predictions.xlsx는 모델별 실측/예측을 담는 결과 출력물이다.
- Predict의 --train-dir 전체 조합 평가에서는 bundle에 저장된 학습 당시test파일목록/hash를
  사용한다. 이후 YAML의test_directory만 바꿔도 이미 학습된 모델의 고정test목록은 바뀌지 않는다.
  개별 --checkpoint 평가에서는 --input-dir로 입력CSV폴더를 지정한다.
- 설정과 data_utils.py/predict.py의 파일 수집 경로를 읽어 확인했다. 문서 안내만 추가했으며
  설정/코드/데이터 변경이나 학습·추론은 수행하지 않았다. 추가 실행 작업은 없다.

## 49. 2026-10-06 — 구간 합산 전 ID별 test 정답률과 평균 예측확률

- 요청: 구간을 묶기 전 ID별 예측확률/성능을 확인한다. 최신test20261006_095933의 validation
  선택 모델(masked ResNet, class0 Transformer; 힘 파트너MLP)을 사용했다.
- 실제 유부하이고 location_ready인 행에서 정답ID별로 집계했다. 조건부 정답률은 ID0을 제외한
  ID1–18 argmax의 정답률이다. 평균확률은 해당 정답ID의 원본softmax값 p_ID 평균이다.
  Class0 평균확률은p0도 포함해 합1인 원본 출력에서 구했으며 p0를 제외한 재정규화를 하지 않았다.
  최종ID 정답률은 class0가 ID0으로 예측한 검출 누락도 오답으로 포함한다. 단위는 모두%다.

| 정답ID | 유부하 수 | masked 조건부 정답률 | class0 조건부 정답률 | masked 정답ID 평균확률 | class0 정답ID 평균확률 | class0 최종ID 정답률 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 253 | 99.60 | 76.68 | 95.16 | 33.60 | 40.71 |
| 2 | 155 | 64.52 | 86.45 | 55.51 | 30.21 | 32.90 |
| 3 | 342 | 28.65 | 26.32 | 25.71 | 14.58 | 10.53 |
| 4 | 279 | 63.08 | 51.97 | 59.06 | 34.40 | 45.16 |
| 5 | 299 | 31.44 | 9.03 | 29.08 | 12.17 | 5.35 |
| 6 | 345 | 41.74 | 40.00 | 37.89 | 32.33 | 33.62 |
| 7 | 1314 | 6.93 | 55.94 | 8.10 | 39.86 | 50.15 |
| 8 | 1026 | 12.28 | 7.99 | 13.48 | 14.38 | 6.73 |
| 9 | 739 | 22.87 | 29.36 | 22.93 | 25.03 | 23.27 |
| 10 | 802 | 12.72 | 14.46 | 13.57 | 17.28 | 13.97 |
| 11 | 124 | 88.71 | 92.74 | 80.93 | 80.49 | 91.13 |
| 12 | 247 | 24.29 | 33.20 | 19.65 | 21.03 | 31.58 |
| 13 | 252 | 6.35 | 8.33 | 11.04 | 11.66 | 5.56 |
| 14 | 490 | 21.43 | 12.24 | 19.78 | 15.34 | 12.04 |
| 15 | 745 | 42.01 | 30.74 | 35.88 | 24.11 | 30.60 |
| 16 | 414 | 14.73 | 10.63 | 16.82 | 10.55 | 8.70 |
| 17 | 219 | 33.33 | 63.01 | 37.53 | 49.50 | 58.45 |
| 18 | 3308 | 39.39 | 42.59 | 37.27 | 33.61 | 37.30 |

- 전체19파일 혼합 유부하11,353개 조건부정답률은 masked29.89%, class035.02%이며,
  class0의 검출 누락까지 포함한 최종ID 정답률은29.51%다. Body1–17 동일녹화test8,045개에서는
  각각25.98%,31.91%,26.30%다. ID18 독립실험 유부하3,308개는39.39%,42.59%,37.30%다.
- 예를 들어 class0의 ID2 조건부정답률86.45%와 정답ID 평균확률30.21%는 다른 지표다.
  평균확률이 낮더라도 다른 ID보다 높으면 조건부 정답이 될 수 있고 p0가 가장 높으면 최종은
  무부하가 된다. 구간확률 합이나 구간정답률을 개별ID 성능으로 읽지 않는다.
- 검증: 기존predictions.csv에서36개 방식×ID 집계의 support/정답률을 재계산해 metrics.json의
  location_id_XX_support/recall과1e-12 허용오차로 일치함을 확인했다. 평균확률과 최종ID 정답률도
  동일 CSV에서 계산했다. 기록 문서만 추가했으며 학습·추론이나 별도 테스트 파일 생성은 하지 않았다.

## 50. 2026-10-06 — 끝단 힘·어드미턴스·body 접촉 시스템 구조 제안

- 요청: 끝단 힘 추정과 이를 이용한 어드미턴스 제어, body 접촉 구분이라는 연구 목적에서
  현재 독립 힘/위치 모델보다 적절한 방법이 있는지 검토한다. 이번 요청은 설계 상담이다.
- 수행/확인: 현재 상태와 47–49절 결과, model_zoo.HRMEstimator 및
  data_utils.location_predictions의 판정 규칙을 읽고 관련 원 논문을 확인했다.
  현재는 독립 force_net/location_net을 하나의 저장·추론 객체로 묶으며 가중치를 공유하지 않는다.
  하나의 bundle이라는 사실이 공통 특징 추출기를 사용하는 다중 작업 학습을 의미하지 않는다.

**추천 방향 — tip 힘은 독립 유지, 접촉 분류는 목적에 맞게 계층화한다.**

1. ID18 전용 힘 모델은 유무부하 모두 연속 Fx/Fy/Fz를 출력한다. 별도의 접촉 모델은
   접촉 유무와, 접촉 조건에서 tip 또는 body 하단/중단/상단을 추정하는 방향을 비교한다.
   접촉 모델 내부에서 특징 추출기를 공유하고 검출/구간/보조 ID 출력을 만들 수 있다.
   이는 아직 구현하지 않은 후보이며, 현재의 독립 두 모델을 기준 모델로 보존한다.
   정밀 ID 분포는 히트맵용 보조 출력으로 남기고 실제 목표인 구간 분류에도 직접 loss를 준다.
   기존 validation 선택 구간 1–4/5–10/11–18은 tip18과 body11–17을 섞으므로
   body 모드 판단에는 tip18을 따로 분리해야 한다. Body1–17의 새 경계도 validation에서만 정한다.
2. 가장 작은 비교 실험은 재학습 없이 가능한 class0 판정 규칙 변경이다. 현재는 p0와
   각 개별 ID 확률의 최대값을 비교한다. 예를 들어 p0=0.35, 접촉 ID 확률 합=0.65라도
   각 ID 확률이 0.35보다 작으면 무부하로 판정한다. 후보는 접촉 점수 1-p0에 임계값을 적용하고,
   접촉이면 ID/구간을 고르는 방식이다. 임계값은 validation에서 미검출/오검출을 함께 보고 정한다.
   0.5가 최적이라고 가정하지 않으며 softmax 합을 보정된 물리적 접촉 확률로 보증하지 않는다.
   필요하면 validation 내 분리된 교정 구간에서 확률 보정과 진입/해제 문턱을 비교한다.
   새 검출기의 개선 여부는 아직 계산하지 않았다.
3. 근거: 선택 class0 Transformer의 body 동일녹화 test에서 유부하 조건부 구간 정답률은
   81.18%, 검출 누락까지 포함한 유부하 구간 정답률은64.67%다. 유부하 recall76.68%,
   무부하 recall97.05%이므로 위치 학습과 함께 검출 누락을 줄이는 비교가 필요하다.
   이를 독립 body 실험 성능이나90% 목표 달성으로 보고하지 않는다.
4. 힘 모델과 접촉 모델까지 공통 encoder로 합치는 방식은 후속 비교 후보로 둔다.
   Tip 회귀는 ID18, 접촉 분류는 전체 ID를 사용하므로 데이터 범위와 목적함수가 다르다.
   다중 작업에서 gradient 충돌이 생길 수 있다는 연구가 있으나, 현재 HRM에서 실제로
   충돌이 확인된 것은 아니다. 독립 모델보다 좋아지는지는 동일 분할/예산의 비교로 확인해야 한다.

**입력과 제어 관점의 후속 후보**

- 무접촉 운동에서 기대되는 장력/형상과 실제 센서값의 차이를 특징으로 추가하면 구동에 따른
  변형과 외부 접촉에 따른 변형을 구별하는 데 도움이 될 가능성이 있다. 현재 입력에 이 차이를
  추가하는 통제 실험으로 검증하며, 기존 입력을 임의로 제거하지 않는다. 명령/상태 기반 기대
  형상과 실제 형상을 비교한 continuum robot 연구가 있으나 로봇과 센서가 달라 성능을 전용할 수 없다.
- 끝단 회귀는 축별 RMSE/MAE 외에 무부하 bias, 잡음, 시간 지연, 부하 변화 응답도 비교한다.
  Force 필터의 지연과 구동기의 추종 대역폭은 어드미턴스의 안정성/수동성에 영향을 줄 수 있다.
  실제 제어 연결에서는 좌표계·부호·시간 정렬, 속도 제한과 접촉 시 모드 전환을 별도로 검증한다.
  기존 회귀의 부호·영점은 이번 상담에서 바꾸지 않는다. 파일별 영점 보정 후보가 필요하면
  실제 사용 시 확보 가능한 무부하 교정 절차를 먼저 정하며 전체 test F/T로 보정하지 않는다.
- 접촉 분류 결과로 연속 힘 출력을 임의로0으로 바꾸지 않는다. 반대로 tip 전용 회귀의 힘 크기를
  body 검출 근거로 바로 쓰지 않는다. Body 접촉은 tip 회귀의 학습 범위 밖이므로 그때의 출력이
  실제 tip 힘이라고 보장할 수 없다. Body 검출 시 제어 사용/모드 전환은 별도 설계 대상이다.
  현재 단일 접촉 데이터만으로 tip/body 동시 접촉 분리 성능을 주장하지 않는다.

참고한 원 자료:
- [Gradient Surgery for Multi-Task Learning, NeurIPS 2020](https://arxiv.org/abs/2001.06782):
  공유 다중 작업 학습의 gradient 간섭과 이를 줄이는 방법에 대한 근거.
- [Sensing expectation enables simultaneous proprioception and contact detection in an intelligent soft continuum robot, Nature Communications 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11574004/):
  기대 형상과 측정 형상 차이를 활용하는 접촉 감지 개념. 현재 HRM과 다른 센서/구조다.
- [Admittance control for physical human–robot interaction, 2018](https://journals.sagepub.com/doi/10.1177/0278364918768950):
  힘 필터, 움직임 제어 대역폭, 감쇠 등이 어드미턴스 안정성/수동성에 미치는 영향.
- [On Calibration of Modern Neural Networks, ICML 2017](https://proceedings.mlr.press/v70/guo17a.html):
  softmax confidence와 실제 정확도 사이의 보정 문제.
- [A Learning-Based Approach for Contact Detection, Localization, and Force Estimation of Continuum Manipulators With Integrated OFDR Optical Fiber, 2026 preprint](https://arxiv.org/abs/2603.12347):
  접촉 검출 뒤 위치/힘을 추정하는 단계별 구성의 관련 사례. OFDR 센서를 사용하며 미심사 사전논문이다.

- 미완료/다음 후보: 기존 판정 규칙 대비1-p0 검출 → 직접 구간 지도학습/보조 ID → 필요시
  기대 장력·형상 차이 특징과 공유 encoder를 순차 비교한다. 모든 선택은 validation에서 하고
  고정 test와 독립 body 녹화의 결과를 구별한다. 이미 여러 번 분석한 test를 바탕으로 구조를
  제안했으므로, 최종 일반화 주장을 위해서는 새 독립 실험 평가가 필요하다.
- 이번에는 문서 기록만 추가했다. 코드/설정/원본/기존 결과 변경, 학습·추론·제어 실행은 없으며
  제안으로 성능이 개선됐다고 주장하지 않는다. 제어 연결은 여전히 미구현이다.

## 51. 2026-10-06 — 무부하 경계와 class0 학습 라벨 생성 위치 확인

- 요청: 현재 센서 무부하 경계값과 학습 코드에서 class0로 처리하는 위치를 설명한다.
- 확인: configs/train.yaml의 calibration(63–74행)은 기록2 csv/summary.csv의 앞70%를 사용하고,
  mean center, 표준화 잔차의 축별 절댓값 최댓값 score의95%/99.5% 분위수에1.1을 곱한다.
  현재 교정 원본 SHA256이 최신 학습20261006_095933/calibration.json의 저장 hash와 동일하다.
  설정의 교정 조건도 저장값과 일치한다. 아래는 저장 N값을 mN으로 환산한 수치다.

| 축 | 라벨 판정에서 빼는 center (mN) | 보정 후 무부하 범위 (mN) | 보정 후 유부하 절댓값 경계 (mN) | 원본 CSV 값 기준 무부하 범위 (mN) |
|---|---:|---:|---:|---:|
| Fx | -67.362099 | ±134.326254 | 176.508704 | -201.688353 ~ 66.964155 |
| Fy | 19.592977 | ±126.814159 | 166.637587 | -107.221183 ~ 146.407136 |
| Fz | -85.572715 | ±192.669986 | 253.174107 | -278.242701 ~ 107.097270 |

- F_corrected=F_recorded-center를 라벨 판정에서만 계산한다. 세 축 모두 무부하 범위 안이면
  load_state=0, 어느 한 축이라도 유부하 경계 이상이면1, 그 외는 불확실-1이다.
  이중 경계는 매 행의 불확실 구간이며 이전 상태를 유지하는 시간적 hysteresis는 아니다.
- 코드 흐름: data_utils.py:310에서 mN→N, 318에서 load_states 호출 →
  analyze_no_load.py:104–110에서 상태 생성 → train.py의 WindowStore:103–108에서 위치 target 생성.
  label을-100으로 초기화하고 유부하에는 원래 ID에 대응하는 class index를 할당한다.
  `if mode == 'class0': label[trial.load_state[ep] == 0] = 0`이 실제 무부하 class0 변환이다.
  각 입력 창의 마지막 행 ep 상태로 정답을 정하며 원본 CSV의 contact_segment_id는 바꾸지 않는다.
- train.py:127은 위치 label>=0만 학습 대상으로 선택하고, 174–184에서 해당 배치에
  cross_entropy를 계산한다. 불확실/무효 라벨은 위치 loss에서 제외된다.
  Masked에서는 무부하가-100으로 남아 위치 loss에서 제외된다. Masked의 내부 class index0은
  기본 active_ids의 ID1에 해당하며 의미상 무부하 class0와 다르다.
- 힘 분기는 유효한 ID18 실측 힘을 유무부하/불확실 상태와 무관하게 회귀한다.
  이 교정 center를 회귀 정답에서 빼거나 무부하 Fx/Fy/Fz를0으로 치환하지 않는다.
  추론의 class0 판단은 입력 센서에 대한 신경망 출력으로 수행하며, 위 F/T 경계는 학습/평가의
  정답 라벨을 만들 때 사용한다. 최근 제안한1-p0 규칙은 아직 적용하지 않았다.
- 수행/검증: 소스 코드와 저장 교정 수치를 대조하고 원본 교정 파일 hash 일치를 확인했다.
  문서 기록만 추가했으며 코드/설정/CSV 수정, 학습·추론 및 새 테스트 파일 생성은 없다.
  이번 설명 요청은 완료했으며 추가 실행 작업은 없다.

## 52. 2026-10-06 — 수동 ±경계 선호와 두 경계 사이 데이터 처리 설명

- 요청/선호: 사용자는 train.yaml에서 축별 힘 범위를 직접 ±로 지정하는 구성을 선호한다.
  현재 summary.csv 평균 기반 자동 계산 여부와 무부하/유부하 경계 사이의 처리 방식을 질문했다.
- 현재 동작: 교정 기록2 앞70%에서 평균 center와 축별 표준편차를 구하고,
  max_axis(abs(F-center)/std) 점수의95%/99.5% 분위수에1.1을 곱해 두 경계를 만든다.
  각 train/test 파일의 초기 평균을 자동 계산하여 영점을 맞추는 처리는 아니다.
- 두 경계 사이 값은 불확실 load_state=-1이다. 세 축 모두 무부하 경계 안이면0,
  어느 한 축이라도 유부하 경계 이상이면1이므로, 예를 들어 보정 후 XYZ=(150,0,0)mN은
  Fx134.326~176.509mN 사이에 있어 불확실이다.
- 불확실 시점을 마지막 행으로 하는 창은 class0/masked 모두 위치 loss에서 제외한다.
  조건부 ID/구간 및 검출/system 평가 분모에서도 제외하고 support는 별도로 기록한다.
  숫자가 유효한 불확실행 자체를 CSV/입력 배열에서 삭제하지 않으므로 후속 창의 과거 입력으로
  들어갈 수 있다. 힘 회귀는 현재 ID18 범위의 유효한 실측값을 부하 상태와 무관하게 사용한다.
- 수동 설정 후보는 축별 offset, 무부하 반폭, 유부하 반폭을 명시하는 구성이다.
  ±단일 경계로 안쪽 무부하/바깥 유부하를 정하면 불확실 구간이 없어져 현재 정책과 달라진다.
  또한 ±범위가 CSV0 중심인지 offset 보정 후0 중심인지 구분해야 한다. 이미 영점 보정된 CSV에
  과거 센서 center를 다시 적용하면 판정 중심이 이동한다. 이번에는 offset을 임의 변경하지 않았다.
- 수행/검증: configs/train.yaml, analyze_no_load.py:48–60/104–110,
  data_utils.py:271–318/653–722, train.py:99–137의 계산·필터·입력 창 흐름을 읽어 확인했다.
  이번 질문에는 현재 동작과 수동 설정 시 구분할 항목을 설명했다. 수동 경계 기능 구현,
  코드/설정/데이터 변경, 학습·추론은 수행하지 않았다. 기록 문서만 갱신했다.
  향후 설정 변경 시 사용자가 정할 경계값과 중심/불확실 구간 정책을 반영한다.

## 53. 2026-10-06 — YAML 수동 Fx/Fy/Fz 범위로 변경

- 요청: 사용자가 축별 힘 구간을 직접 지정하도록 바꾸고, 학습 시 무부하 기록의 자동 평균/
  분위수 계산과10% 확대 인자를 제거한다. Kalman aligned 힘 정답 열은 유지한다.
- 구현: configs/train.yaml의 calibration을 다음 ft_sensor_calibration으로 교체했다.
  unit은 아래 범위의 단위이며 CSV 단위 source_force_unit과 각각 N으로 변환한 뒤 비교한다.

```yaml
ft_sensor_calibration:
  unit: mN
  fx: [-201.688353, 66.964155]
  fy: [-107.221183, 146.407136]
  fz: [-278.242701, 107.097270]
```

- 각 축은 `[최솟값, 최댓값]`이다. ±150mN이면 `[-150, 150]`으로 지정한다.
  기본값은 이전 무부하 영역을 CSV 원값 기준으로 환산해6소수 mN으로 적었다. 비대칭인 이유는
  과거 offset을 경계값에 반영하여 기존 무부하 행을 보존했기 때문이다. 새 코드에서 offset을
  추가로 빼지는 않는다. 대칭 범위를 원하면 사용자가 두 끝값을 직접 바꿀 수 있다.
- 새 판정: 세 축 모두 범위 안(양끝 포함)이면0, 어느 한 축이라도 범위 밖이면1,
  비수치/NaN/Inf 등 무효 힘은-2다. 별도의 유부하 경계나 불확실 구간은 없다.
  기존 불확실 시점은 유부하로 들어가므로 예전 결과와 위치 평가 분모가 달라질 수 있다.
  Class0는 무부하0/유부하 원래ID를 학습하고 masked는 무부하 위치 loss만 제외한다.
- 힘 정답은 계속 `fts_kalman.aligned_fx`, `fts_kalman.aligned_fy`,
  `fts_kalman.aligned_fz`다. 질문의ftx가 아니라 현재 CSV/설정의 정확한 접두사는fts다.
  원본 실측값·부호·회귀용 영점·입력 열·분할·모델 구조·242조합 정책은 바꾸지 않았다.
  mN→N 단위 변환과 train scaler 정규화/역변환은 기존대로이며 무부하 힘을0으로 만들지 않는다.

| 제거한 기존 교정 인자 | 이전 역할 | 현재 대체 |
|---|---|---|
| path, calibration.force_columns, source_force_unit | 별도 무부하 기록의 경로/열/단위 | 학습 시 기록을 읽지 않고 force_columns와 수동 범위를 사용 |
| fit_fraction | 교정 기록 앞70% 선택 | 필요 없음 |
| center_method | 교정 기록의 평균/중앙값 offset 계산 | 필요 없음, CSV 값 직접 비교 |
| off_quantile, on_quantile | 두 통계적 경계와 불확실 영역 생성 | 축별 최솟값/최댓값 한 쌍 |
| range_multiplier | 자동10% 범위 확대 | 필요 없음, 입력한 숫자 그대로 적용 |
| confirmed_no_load, basis, zero_transfer_basis | 자동 교정 기록과 offset 전이 근거 | 새 수동 기준에는 필요 없음; 기존 결과에는 보존 |

- 코드 변경: analyze_no_load.calibrate_no_load는 파일 접근 없이 설정을 검사하고 N 단위 경계를
  반환한다. load_states는 수동 범위를 직접 비교한다. data_utils.load_config에서 범위 누락,
  역전, 비수치/NaN/Inf/bool, 잘못된 단위와 알려지지 않은 교정 인자를 빠르게 거절한다.
  기존 calibration 블록은 새 학습에서 자동 계산하지 않고 수동 설정으로 바꾸라는 오류를 낸다.
  함수 이름과 결과 calibration.json/bundle 키는 저장·호출 호환성을 위해 유지했다.
- 기존 모델 호환: 저장된 center_N/scale_N/off_score/on_score를 읽는 작은 분기는
  과거 bundle 재현용으로 유지했다. 기존 예측은 새 YAML을 읽어 기준을 덮어쓰지 않는다.
  새 수동 기준으로 학습된 bundle에는 manual_axis_ranges와 lower_N/upper_N가 저장된다.
- analyze_no_load.py는 기본 실행 시 수동 기준만 확인/저장한다. 선택 옵션
  `--input datasets/aidin_FT_sensor_validation_2/csv/summary.csv`를 주면 같은 힘 열의
  평균/표준편차/최솟값/최댓값·범위 내외 비율을 추가로 계산한다. 이 통계는 경계를 바꾸지 않는다.
  새 실행 Python/테스트 파일은 추가하지 않았다. 기존 tests/test_pipeline.py를 수동 기준으로
  갱신했고 README/AGENTS/이 문서의 현재 안내와 YAML 학습 인자 설명을 맞췄다.

**검증 결과**

- `bash scripts/hrm_python.sh -m unittest discover -s tests -v`: 34개 통과(1.436초).
  각 축의 양끝 포함과 바로 바깥값, 단위 변환, 무효값, class0/masked loss 대상,
  실측 힘 보존, 저장/복원 및 입력만 추론, 과거 이중 경계 재현을 확인했다.
  저장/Excel 경로의 합성8조합 검증은 train_branch를 mock했으며 실제 가중치 학습은 없다.
- CLI 기준 출력과 선택 무부하 기록2의2,797행 통계가 정상 동작했다. 지정 범위 내 비율은
  97.8191%이며 이는 센서 기록의 기술 통계다. 임시 출력은 /tmp에서 검사 후 제거했다.
- 실제67CSV를 prepare_data로 읽고 기존 저장 교정과 비교했다. 무부하 행의 소속 변화0행,
  기존 불확실118,047개 숫자행은 새 유부하 라벨로 전환됨을 확인했다(아래 입력 창 수와 다름).
  새 데이터 준비에서 calibration CSV를 자동으로 읽거나 모델을 생성하지 않았다.

| 역할 | 파일 수 | 입력 창 수 | 무부하 | 유부하 | 불확실 |
|---|---:|---:|---:|---:|---:|
| train | 48 | 727,419 | 274,328 | 453,091 | 0 |
| validation | 48 | 180,834 | 69,514 | 111,320 | 0 |
| test | 19 | 27,785 | 13,006 | 14,779 | 0 |

- 위 숫자는 전체 위치 데이터 창이며 tip 전용 힘 창 수와 구분한다. 경계 선택/튜닝을 test로
  수행하지 않았다. 코드 리뷰와 git diff --check에서도 추가 문제가 없었다.
- 완료 범위: 설정/코드 변경, 관련 기존 검증 갱신, 실제 데이터 준비 점검, 문서 정리.
  실제 재학습이나 새 실험 성능 평가는 실행하지 않았으며 성능 개선을 주장하지 않는다.
  원본 CSV·기존 결과·checkpoint를 덮어쓰지 않았다. 새 기준을 학습에 적용하려면 일반 학습
  명령을 다시 실행하면 되며, 사용자가 정할 범위는 위 YAML의4개 항목만 수정하면 된다.

## 54. 2026-10-06 — 다른 AI의 연구 방향 제안 검토, 적용 없음

- 요청: 다른 AI가 제안한 직접3구간 분류, 순서/거리 손실, 기대 무부하 형상 차이,
  예측 힘 보조 입력, 힘 크기별 confusion, quartic fitting 정보 손실 가능성,
  여러 body 위치에서의 힘 회귀 검증을 읽고 판단한다. 사용자가 적용하지 말고 확인만 요청했다.
- 수행: 현재 문서/설정, 독립 분기와 tip 지도 범위, 위치 지표/혼동행렬 구현을 읽었고
  순서 학습과 기대/실제 형상 비교에 관한 원 논문을 확인했다. 모델·설정·데이터·결과 변경,
  학습·추론·새 성능 분석은 하지 않았다. 이 검토 내용만 기존 기록 문서에 추가한다.

**검토 의견**

1. 독립 힘/위치 구조를 원인으로 단정할 근거가 없다는 의견에 동의한다. 현재 tip 힘 모델을
   비교 기준으로 유지하면서 위치 목표/특징을 하나씩 바꾸는 실험은 원인 해석에 유리하다.
   다만 현재 힘 모델이 최적이거나 제어용으로 충분히 검증됐다는 뜻은 아니다.
2. 직접 구간 지도학습은 목표와 잘 맞는 우선 후보다. 실사용에서 tip/body를 구별하려면
   무부하+tip+body 하/중/상으로5상태 또는 이에 대응하는 계층 구성이 필요하다.
   단순 무부하+3구간의4class는 tip을 상단 구간과 합치거나 body 전용 범위를 전제한다.
   Body1–17 구간을 정할 때 tip18을 분리하고 경계는 validation에서만 선택한다.
   정밀 ID 분포/히트맵도 필요하면 직접 구간 loss에 보조18ID 출력을 유지하는 비교가 가능하다.
3. 순서/거리 손실은 먼 위치로 틀리는 예측을 줄이기 위한 타당한 후보다. 그러나 검출률이나
   정확ID 정답률을 반드시 높이지는 않으므로 정확ID·±1/±2 segment·평균 위치 오차를 구분한다.
   무부하0은 base보다 앞에 있는 위치가 아니므로 공간 순서 loss에서 제외해야 한다.
   ID 간 간격이 다르면 ID 차이 대신 중심선상의 물리 거리를 고려할 수 있다.
   현재 일반 CE를 유지하는 대조군, 직접 구간 지도, 거리 보조 손실을 순차 비교하는 편이 좋다.
4. 기대 무부하 형상/장력과 관측의 차이를 기존 입력에 추가하는 접근은 유망하다.
   기대값은 운용 시 얻을 수 있는 명령/상태와 train의 무접촉 자료로 구성하며 검증 자료로
   기준을 학습하지 않는다. 접촉으로 변형된 형상을 그대로 기대값에 재현하면 잔차에서
   접촉 특징이 사라질 수 있다. 관련 soft continuum robot 사례는 있으나 HRM 효과는 미검증이다.
5. 예측 힘을 위치 모델에 추가하는 방법은 후순위의 조건부 후보다. 현재 force_scope는tip이고
   실제 학습도ID18뿐이므로 body 접촉 시 출력은 검증된 body 힘이 아니다. 이를 같은 X의
   학습된 특징으로 시험할 수는 있으나 정확한 body 힘이라는 가정을 해서는 안 된다.
   운용에 없는 GT F/T를 입력하면 누출이다. 또한 force 모델이 이미 학습한 행의 예측만으로
   위치 모델을 학습하면 운용 시와 오차 분포가 달라질 수 있다. 시행할 경우 원녹화별 그룹을
   제외하여 만든 예측(OOF)을 위치 학습에 사용하고, validation/test는 train만 본 모델로 만든다.
   같은 녹화의 잘라낸 파일/겹치는 창을 서로 다른 독립 그룹으로 취급하지 않는다.
6. 힘 크기별 confusion 분석은 모델 변경 전 우선 진단으로 적절하다. 인접 위치 오차와
   먼 구간 오차를 구별하되 한 패턴만으로 해상도/센서/데이터 원인을 확정하지 않는다.
   힘 크기뿐 아니라 힘 방향·자세·static/dynamic·ID별 support 차이가 결과를 설명하는지 살핀다.
   유부하 조건부 위치 행렬과 무부하 오판을 포함한 검출/구간 지표를 함께 보고해야 한다.
   현재 confusion과location_within1_accuracy는 구현돼 있고 힘 크기별 집계는 이번에 실행하지 않았다.
7. 전역 quartic fitting에 의한 정보 손실은 확인되지 않은 가설이다. 현재 핵심 코드와 설정에는
   quartic/polyfit 생성 경로가 없고 CSV의 relative_angle을 읽는다. 실제 상류 형상 추정 코드와
   원측정/국소 추정/전역 fitting의 비교 없이 정보가 제거됐다고 결론내릴 수 없다.
   다른 저장소나 카메라/ROS 코드는 이번에 읽거나 실행하지 않았다.
8. 위치 해상도와 힘 벡터 오차는 다른 과제이므로18ID 정답률이 낮다는 이유만으로 body 힘
   추정을 불가능하다고 할 수 없다는 의견에 동의한다. 그러나 tip 전용 모델을 그대로 body
   힘 모델로 간주할 수도 없다. 이미 제공된 all_single_contact는 별도 회귀 실험 후보다.
   Body 힘을 주장하려면 각 부위에서 측정한 같은 좌표계의 힘 정답과 별도 실험 평가가 필요하다.
   현재 body test는 같은 녹화 분할이므로 독립 실험 일반화와 구분한다. 위치 모델 입력에
   정답ID를 넣은 body 힘 성능이라면 운용 중 ID를 안다는 추가 가정을 명시해야 한다.
9. 인용된 리뷰 코멘트 원문은 제공되지 않았다. 붙여넣은 내용의 '붙여넣은 마크다운(1)' 표시는
   원문을 확인할 수 있는 자료가 아니므로 '리뷰어가18ID를 요구하지 않는다'는 해석을 확정할 수 없다.
   실제 요구가 body 힘 추정이면 body 접촉 검출/3구간 위치 결과만으로 대체할 수 없다.
   기존 우선순위 tip 힘/어드미턴스와 body 위치를 임의로 body 힘 중심 연구로 바꾸지는 않는다.

- 우선순위 판단: 같은 라벨/분할의 힘 크기별 검출·위치 오류 진단 → tip을 분리한 직접 구간
  지도학습 비교 → 필요에 따라 거리 손실/기대 형상 차이 → 마지막에 예측 힘 보조 입력.
  Body 회귀가 논문 필수 주장으로 확인되면 별도 body 실험 평가를 병행하는 방향이 타당하다.
- 비교 시 주의: 53절의 수동 기준으로 기존 불확실 행이 유부하에 포함됐지만 아직 재학습하지
  않았다. 이전 성능을 새 기준의 성능으로 읽지 않고, 기준을 고정한 비교에서 개선 여부를 판단한다.

참고한 원 자료:
- [Cao et al., Rank consistent ordinal regression, Pattern Recognition Letters 2020](https://arxiv.org/abs/1901.07884):
  순서가 있는 정답을 일반 다중 클래스 CE와 다르게 다루는 방법의 근거. HRM 성능 근거는 아니다.
- [Wang et al., Sensing expectation, Nature Communications 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11574004/):
  명령 기반 기대 형상과 측정 형상의 차이로 접촉을 감지한 사례. 센서/구조가 다른 로봇이다.
- 이번 검토는 완료했다. 제안 적용이나 추가 실험은 승인된 작업으로 해석하지 않는다.

## 55. 2026-10-06 — 재학습 전 기존 예측의 오류 원인 진단

**요청과 수행 범위**

- 사용자는54절 우선순위에 따라 원인 분석부터 진행하고, 재학습/비교 여부는 결과를 본 뒤
  결정하라고 요청했다. 후속 연구 후보로 tip+body 하/상, tip+body 하/중/상을 기록한다.
- 기존 `20261006_095933`의 validation NPZ와 test predictions.csv를 읽어 재집계했다.
  신경망 학습·새 신경망 추론·모델/설정/CSV/checkpoint 변경은 하지 않았다.
  원인 진단용 계산은 /tmp에서 수행했으며 새 실행 Python/테스트 파일을 프로젝트에 추가하지 않았다.
- 모델 선택은 과거 validation 결과 그대로다: masked 힘MLP/위치ResNet,
  class0 힘MLP/위치Transformer. 상세 모델별 validation은 첫 파트너MLP로 고정한22분기씩
  집계했으며 test를 보고 모델을 바꾸지 않았다.
- 결과는 아래 날짜 폴더에 **Excel1개와 그림1개**로 저장했다.
  - [contact_diagnostics.xlsx](../results/predict/20261006_190950_contact_diagnostics/contact_diagnostics.xlsx)
  - [contact_diagnostics.png](../results/predict/20261006_190950_contact_diagnostics/contact_diagnostics.png)
  Excel의 Readme/Findings가 안내·요약이며 ID별/파일별/힘 크기·방향별 지표, 두 종류의 혼동행렬,
  tip 축별 회귀 오차, 데이터 구성, 라벨 전환, 출처 hash와 검산 결과를 총28시트에 보존했다.

**평가 기준과 분모**

- 본문의 주 수치는 저장된 과거 mean center/off·on 이중 경계 라벨이다. 불확실 라벨은
  위치·검출 지표에서 제외했다. 힘 norm은 CSV 실측XYZ의 크기(mN)이며 offset을 더 빼지 않았다.
  힘 크기별 구간은 분석용 집계 범위이며 새로운 무부하 판정 경계가 아니다.
- Validation은 전체180,834창/유부하87,183창, test는27,785창/유부하11,353창이다.
  Test의 body1–17은 같은 녹화 분할19,502창(유부하8,045/무부하9,185/불확실2,272),
  tip18은 별도 실험2파일8,283창(유부하3,308/무부하3,821/불확실1,154)이다.
  Body 결과를 독립 실험 일반화로 부르지 않는다. 겹치는 창 수는 독립 표본 수가 아니다.
- 정확ID는 GT 유부하에서 ID1–18 중 최대 확률의 조건부 후보를 평가한다.
  구간은 ID 확률을 합산해 선택한다. 검출 포함 구간 정답률은 **전체 GT 유부하** 중
  접촉 검출과 구간 정답이 모두 성립한 비율이다. 검출에 성공한 행만의 정답률과 다르다.
- 구간은 기존 validation 선택1–4/5–10/11–18을 고정했다. 기존 예시1–10/11–15/16–18도
  Excel에 별도 남겼다. 이번에 경계를 탐색하지 않았다. 두 방식 모두 tip을 body와 분리하지
  않으므로 높은 상단 구간 정답률을 tip/body 구별 성능으로 해석하지 않는다.

**1. 인접 ID 혼동과 검출 누락이 동시에 존재**

| Body test, 유부하8,045창 | Masked ResNet | Class0 Transformer |
|---|---:|---:|
| 정확ID, 조건부 | 25.98% | 31.91% |
| 정답에서±2ID 이내 | 79.48% | 76.53% |
| 평균 절대 ID오차 | 1.931 | 1.728 |
| 4ID 이상 오차 | 13.37% | 12.54% |
| 구간 정답률, 조건부 | 77.86% | 81.18% |
| 유부하 검출률 | 해당 없음 | 76.68% |
| 무부하 정답률 | 해당 없음 | 97.05% |
| 검출과 구간 정답 동시 성공 | 해당 없음 | 64.67% |

- Class0의 유부하8,045창은 **구간 검출 성공5,203(64.67%) + 무부하 오판1,876(23.32%) +
  검출했으나 구간 오판966(12.01%)**으로 정확히 분해된다.
  구간을 조건부로 맞혔지만 무부하로 판단한1,328창이 조건부81.18%와 동시 성공64.67%의 차이다.
- 인접 ID 혼동이 상당하므로 직접 구간 지도/순서 손실을 비교할 근거는 있다.
  먼 ID로의 오차도 남으며, 검출 누락을 줄이지 않으면 조건부 구간 정답률만 높아져도
  최종 접촉 위치 성능은 제한된다. 이것만으로 물리적 위치 관측 한계를 확정하지는 않는다.

**2. 약한 힘에서 검출 누락이 집중됨**

| Body test 실측 힘 norm | 유부하 창 수 | Class0 유부하 검출률 | 검출+구간 정답률 |
|---|---:|---:|---:|
| 100–200mN 미만 | 565 | 11.33% | 8.14% |
| 200–300mN 미만 | 1,162 | 35.63% | 29.52% |
| 300–500mN 미만 | 1,791 | 77.95% | 62.87% |
| 500–1,000mN 미만 | 3,064 | 95.30% | 81.98% |
| 1,000mN 이상 | 1,463 | 93.98% | 80.38% |

- 전체 body 검출 누락의66.58%가300mN 미만이다. 단순히 강도군마다 ID 구성이 다르기 때문인지
  확인하려고 같은 ID 안에서 비교했다. <300mN와≥500mN에 각각30창 이상 있는16개 body ID의
  동일 ID 가중 평균 검출률은 **28.76%→91.01%**,16/16ID 모두 강한 힘에서 높았다.
  같은 비교의±2ID 정답률52.30%→87.27%, 조건부 구간 정답률68.07%→87.19%다.
- 힘 방향·자세·시간까지 통제한 실험은 아니다. 약한 힘에서의 낮은 검출률은 확인됐지만,
  실제 추가 변형이 센서 해상도보다 작아서인지, 학습 표본/라벨/특징 때문인지는 미확정이다.

**3. Static/dynamic 및 힘 방향 분포 차이**

- 전체 train727,419창 중 static603,447(82.96%), dynamic123,972창이다.
  유부하363,099창은 static313,207(86.26%), dynamic49,892창이다. Test19파일은 모두dynamic이다.
- Body class0 조건부 정확ID는 static validation61.18%, dynamic validation43.05%,
  dynamic test31.91%다. 조건부 구간 정답률은 각각94.35%,84.02%,81.18%다.
  Static 비중이 큰 전체 validation의 구간92.79%만 보고 test81.18%와 비교하면
  동작 구성의 차이가 섞인다. Dynamic끼리 비교해도 정확ID 저하는 남는다.
- 대표 위치22분기 모두 static validation 정확ID가 dynamic보다 높았다.
  이 결과는 static을 제거하면 좋아진다는 인과 근거가 아니며, 동작 종류별 평가가 필요하다는 근거다.
- 전체ID 유부하의 우세 방향−Fy 비율은 dynamic train13.18%, dynamic validation51.54%,
  test53.40%다. 우세 방향은 절댓값 최대 힘 축과 부호로 정의했다. 같은ID의 dynamic train/test
  6방향 분포 total variation도0.43–0.89로 차이가 컸다. 힘 방향만의 인과 효과는 분리하지 못했다.
- 전체 train 범위를 벗어난 입력이 하나 이상인 test 숫자행은1,599/28,336(5.64%)이며,
  이 중1,589행이 summary_18_test_2.csv에 집중된다. Body 전체를 입력 범위 이탈 문제로
  설명할 근거는 부족하다. 숫자행 수는 warmup을 제외한 위치 입력 창 수와 다르다.
- relative_angle norm은 자세의 크기이지 접촉으로 생긴 추가 변형량이 아니다.
  Quartic fitting 상류 코드/원 형상을 이번에 조사하지 않았으므로 smoothing 정보 손실은 미확정이다.

**4. 검출 규칙만 바꾸면 해결되는가: 적용 없는 고정 예시**

- Class0는 현재0..18 중 최대 확률 class가0이면 무부하다. Body test 누락1,876창의p0 중앙값은
  0.8513이며, 접촉 확률 합1−p0가0.5 이상인 누락은327창(17.43%)뿐이다.
  누락 대부분을 여러 ID에 확률이 분산됐기 때문이라고 설명하기 어렵다.
- `1−p0≥0.5`를 한 번 가정한 재집계에서 body test 검출률76.68→80.75%,
  무부하 오검출률2.95→4.54%, 검출+구간 정답률64.67→67.64%였다.
  전체 validation의 검출 balanced accuracy는83.094→83.060%로 개선되지 않았고
  무부하 오검출은1,954창 늘었다. Body validation만의 balanced accuracy 변화도
  82.928→82.938%로 매우 작았다. 임계값 탐색이나 코드 적용은 하지 않았다.

**5. 우선순위인 tip Fx도 별도 문제로 확인**

- 선택MLP의 tip test8,283창 RMSE는 XYZ138.56mN, Fx/Fy/Fz177.19/94.73/131.25mN이다.
  Pred−GT bias는+78.46/−62.96/−66.93mN이다. 두 방식의 힘 예측은 동일해 중복 집계하지 않았다.
- 합산 test 축별 GT/예측 상관은0.004/0.893/0.882다. Fx는 파일별로는−0.036/+0.257,
  bias+108.37/+12.04mN로 다르므로 합산 상관을 모든 파일에서 무관하다는 뜻으로 읽으면 안 된다.
  교차 축 상관도 확인했지만 일관된 XYZ 축 교환 패턴은 확인되지 않았다.
- MLP dynamic validation의 Fx 상관0.099, GT표준편차166.40mN/예측44.98mN,
  bias+63.92mN로 test 이전에도 동적Fx 추종·진폭·bias 문제가 보인다.
  대표11힘 모델 모두 dynamic Fx 상관−0.202~0.349라 MLP만의 문제로 단정할 수 없다.
- Tip validation 전체 RMSE는 static157.42/dynamic139.75mN이지만, GT 유부하로 제한하면
  static172.84/dynamic223.10mN으로 뒤집힌다. 전체 RMSE만으로 동적 성능을 판단하지 않는다.
  입력 특징/방향/자세 구성 또는 동기·영점 문제 중 무엇이 원인인지는 이 분석으로 확정하지 못했다.

**현재 수동 경계의 별도 민감도 표**

- 분석 시점 YAML은 사용자가 수정한 대칭 범위 Fx±134.326, Fy±126.814, Fz±192.670mN다.
  53절 최초 이관값인 비대칭 원값 경계와 다르며, 이번에 설정을 수정하지 않았다.
- 같은 과거 예측을 현재 범위로 재라벨하면 test 유부하11,604/무부하16,181창이다.
  Body만은 유부하8,242창, class0 검출률75.26%, 검출+구간 정답률63.49%다.
  **새 기준으로 재학습한 성능이 아니며** 라벨 정의에 대한 민감도다. Excel의label_policy로
  기존 평가와 구별한다. GT 힘 회귀값·예측값은 어느 분석에서도 보정/영점 변경하지 않았다.

**검증·완료·미완료와 다음 판단**

- 원본67CSV hash가 저장 audit와 일치했다. NPZ의trial/compact row를 원본source_row로
  연결하고 ID·실측XYZ·부하 라벨을 확인했다. Test도 원본GT/라벨과 일치했다.
- 위치384지표/48조건을 현재location_metrics와1e−12 오차 이내로 대조했고,
  힘 대표22분기의 전체/유부하 RMSE44개는 저장 비교표와 최대5.68e−14mN 차이였다.
  검출 혼동행렬, support, 누락/정답/오답 합계, 두 방식의 동일 힘 출력을 교차 검증했다.
- Excel28시트의 이름·열·행 수, ZIP 무결성, 저장된핵심지표8045/1876/5203과 비율을 다시 읽어
  확인했다. 그림을 열어 축/라벨/분모를 확인했다. 설정·핵심Python5개·선택checkpoint hash가
  분석 시작 시점과 같음을 확인했다. 새 코드 기능 변경이 없어 전체 단위테스트는 재실행하지 않았다.
- 완료: 재학습 전 오류/분포/라벨 민감도 진단과 보고서. 근본적 물리 원인 확정이나 성능 개선은 아님.
- 후속 비교 후보: 현재 라벨을 고정한 대조군 및 동작/강도별 평가 → 직접 구간 지도
  (무부하+tip+body 하/상=총4class, 무부하+tip+body 하/중/상=총5class) → 필요시 순서 손실,
  예상 무부하 형상 잔차 → 예측 힘 보조 입력. 각 구간 경계는 validation에서만 선택한다.
  Tip Fx의 dynamic 추종 문제를 별도 추적하며, 이번 분석으로 힘 모델이 충분히 정확하다고 주장하지 않는다.
- 새 구간 경계, 모델/가중치 변경, 재학습은 아직 수행하지 않았다. 분석 결과를 본 뒤 사용자가
  다음 비교를 결정한다는 이번 요청을 유지한다.

## 56. 2026-10-06 — 현재 데이터로 진행할 body contact 연구 설계 제안

- 요청: 기존 데이터로 납득할 수 있는 body contact 결과를 만들 연구 순서를 제안한다.
  직접 구간 분류, 먼 ID 오차 패널티, ID1–6 학습 제외를 검토한다.
- 수행: 현재 YAML/55절 결과/기존 위치 loss를 확인하고, 저장된 dynamic validation의 ID별
  지표를 다시 읽었다. 순서·거리 기반 손실의 원 논문을 확인했다. 이번에는 연구 계획과 판단만
  기록하며 학습·설정·모델·원본 데이터는 변경하지 않았다. 새 성능을 측정했다고 주장하지 않는다.

**권장 연구 목표와 순서 — 아직 실행하지 않은 후보**

- 주장할 목표는 '끝단 힘 추정과 별도로 body 접촉을 검출하고 접촉 구간을 식별한다'다.
  18ID 완전 분류와 body 힘 회귀를 달성 조건으로 추가하지 않는다. Tip 힘 정확도와 어드미턴스
  검증은 독립 축으로 유지하며 현재 Fx의 dynamic 추종 한계도 따로 보고한다.
- 접촉 검출·조건부 위치·검출 포함 위치·tip/body 혼동을 나눠 평가한다.
  특정 유부하 조건부 수치만으로 시스템의 body contact 성공률을 대표하지 않는다.
- 우선 위치 backbone은 ResNet/Transformer 두 종류로 좁히고 tip 회귀 설정은 고정한다.
  이는 연구 후보 제안이며 기존242조합 학습 정책을 이번에 바꾸거나 가중치를 재사용한 것은 아니다.
  실행 시 비교 실험마다 새 초기화/optimizer를 사용하고 유망한 설정은3개 seed로 반복한다.

| 단계 | 비교 실험 | 확인할 질문 |
|---|---|---|
| A | 현재 수동 무부하 라벨로 기존18ID+class0 대조군 | 과거 이중 경계와 구별된 새 기준 성능 |
| B | A와 같은 구조/목표, ID 및 static/dynamic 균형 샘플링 | 긴 static 파일의 표본 비중이 성능에 미치는 영향 |
| C | 선택한 데이터 가중 방식 고정, 무부하+tip+body2구간 직접 분류 | 검출을 포함한 실용적 위치 구분이 개선되는가 |
| D | C와 같은 조건, 무부하+tip+body3구간 직접 분류 | 해상도를 높였을 때 성능을 얼마나 잃는가 |
| E | 18ID 대조군에 CE+거리/순서 손실만 추가 | 먼 오분류를 줄이면서 ID 분포를 유지할 수 있는가 |
| F | 선택 설정의 전체body1–17 vs 제한body7–17 학습 | 적용 범위를 제한할 실질적 이득이 있는가 |

- B는 class0를 포함한 class별 기여와 ID별·static/dynamic 구성을 train 안에서 조절한다.
  현재 위치 loss는 가중치 없는 cross_entropy다. 균형 샘플링을 추가하면 배치 크기/업데이트
  예산 등도 맞춰 샘플링 효과와 학습량 효과가 섞이지 않게 한다. 약한 힘 표본을 없애거나
  복제로 새로운 정보가 생긴다고 가정하지 않는다. 분포 조절에 validation/test 정답을 쓰지 않는다.
- C의 예시 경계는 body1–8/9–17, D는1–6/7–12/13–17이다. 단순 출발 후보이며 최적값이 아니다.
  Tip18은 항상 독립 class다. C는 무부하 포함4class, D는5class다. 경계 비교는 사전에 좁힌
  후보를 validation에서만 평가하고, 구간 수 자체의 효과를 보려면 중첩된 경계 후보도 고려한다.
  구간을 늘릴수록 위치 해상도와 난이도가 달라지므로 처음부터 많은 구간을 목표로 삼지 않는다.
- E는 CE를 유지하고 유부하 위치에만 거리/순서 보조 손실을 적용하는 독립 비교다.
  예: 정답9를8로 예측하는 경우보다17로 예측하는 경우에 더 큰 위치 비용을 준다.
  ID 확률 전체에 거리를 반영하는 EMD 계열 또는 순서 모델 CORAL이 참고 후보이나
  둘을 동시에 바꾸지 않는다. 무부하0은 공간 위치가 아니므로 순서/거리에서 제외한다.
  Class0 포함 모델이라면 유부하 행의 접촉ID 조건부 분포에 거리항을 적용하고 무부하 검출
  학습은 별도로 보존한다. ID 간 실제 간격이 다르면 물리적 위치 거리도 고려한다.
  거리항의 가중치는validation에서만 선택하며 검출률 개선까지 보장하지 않는다.
- 단순class0 직접 구간 모델을 먼저 비교한다. 검출 누락이 계속 지배하면 후속 대안은 위치
  네트워크 안의 접촉 여부 출력+유부하 위치 출력이다. GT 부하가 아니라 예측 접촉 출력으로
  운용하며 masked 단독 모델을 완성된 검출기로 간주하지 않는다. 이번 구현 범위에는 포함하지 않았다.

**ID1–6 제외에 대한 판단**

- 먼저 전체1–17을 유지한 직접 구간 실험을 권한다. 기존 class0 dynamic validation에서
  ID1의 조건부 정확ID86.89%/검출37.62%, ID6은69.69%/77.95%다.
  ID1–6의 위치 정보가 모두 없다고 결론내리거나 제외하면 반드시 좋아진다고 보기는 어렵다.
- 제외 실험은 정당한 적용 범위 축소 연구가 될 수 있다. 다만 ID1–6 유부하를 무부하0으로
  바꾸지 않는다. 원본 파일도 삭제하지 않는다. 무부하 데이터의 유지 여부를 명시하고,
  tip18 학습은 유지하며 body 유부하 위치 지도 범위만 제한하는 실험으로 정의한다.
- 전체 학습 모델도 동일한 ID7–17 평가 부분집합에서 점수를 내고 제한 학습 모델과 비교한다.
  전체1–17 점수와 제한7–17 점수를 직접 비교해 학습 개선이라고 주장하지 않는다.
  제외한 ID1–6 접촉 때 제한 모델이 무부하로 놓치는지/지원 구간으로 잘못 내보내는지도 별도 보고한다.
  제외 모델의 주장 범위는 'ID7–17 body contact'이며 전체body 검출 성능이 아니다.

**선택 지표와 연구 해석**

- Primary: 무부하 오검출률을 함께 본 body 접촉 recall, 검출과 올바른 구간 예측의 동시 성공률.
  Dynamic validation에서 각 body ID를 동일 가중하는 macro 지표를 주로 보고 static 지표도 병기한다.
  오검출 허용수준/최종 선택 규칙은 학습 전에 정하며 현재 확인된 결과에 맞춰 정답 라벨을 바꾸지 않는다.
- Secondary: 조건부 구간 recall/정확ID/±1·±2ID/평균ID거리/먼오류비율, tip↔body 혼동,
  ID별 support와 힘 크기·방향별 성능. Force 축별 RMSE/MAE는 별도다.
- 특정 힘 이상에서의 신뢰성이 확인되면 '이 데이터/부하 조건에서 가능한 검출·위치 해상도'로
  연구 결과를 구성할 수 있다. 약한 힘 결과도 같이 남기고 최소 성능 범위는validation에서 정한다.
  GT 힘으로 나눈 평가 범위는 운용 중 GT 없이 해당 힘 이상인지 알아내는 기능을 뜻하지 않는다.
- 현재 body test는 같은 녹화 분할이고 이미 분석과 연구 방향 설정에 사용했다.
  고정해 계속 보고하되 완전히 손대지 않은 최종 평가로 포장하지 않는다. 현재 데이터로는
  방법 비교/적용 범위·한계 분석을 진행하고, 독립 body 일반화 주장은 향후 별도 실험 자료가 필요하다.
  Test에서 구간/모델/손실 가중치/강도 경계를 선택하지 않는다.
- 완료: 연구 순서와 비교 조건 제안/기록. 미완료: A–F 구현·학습·성능 비교 및 최종 방법 선정.

참고 원 논문(방법의 근거이며 HRM 개선의 증거는 아님):
- [Hou et al., Squared Earth Mover’s Distance-based Loss](https://arxiv.org/abs/1611.05916):
  클래스 간 거리와 확률 분포를 손실에 반영하는 방법.
- [Cao et al., Rank consistent ordinal regression](https://arxiv.org/abs/1901.07884):
  순서가 있는 라벨을 위한 CORAL 구조. 구체 적용은 후속 비교 후보로 남겼다.

## 57. 2026-10-06 — 고정 구간 대신 ID 거리 허용 평가를 주 방향으로 선택

- 사용자 합의: ±2ID 정답률이 주변 ID 확률의 합이 아니라 최대 확률 위치 후보가 정답에서
  2segment 이내인지 세는 지표임을 확인한 뒤, 정답 근처의 위치를 찾는 이 방향을 선택했다.
- 18개 접촉ID 출력과 ID별 확률 분포는 유지한다. 고정된 하/중/상 구간 대신 정확ID,
  ±1ID, ±2ID 정답률, 평균 절대 ID오차를 함께 보고한다. 56절의 직접 구간 분류는
  우선 실행안에서 후속 비교 후보로 내리고, 기존 ID 모델의 거리 오차 평가를 주 방향으로 둔다.
- 조건부 지표 정의: 실제 유부하 행에서 ID1–18 중 최대 확률 후보를 y_hat으로 정하고
  abs(y_hat-y_true)<=k인 비율을 계산한다. Class0의 무부하 확률은 이 위치 후보 선택에서 제외한다.
  정답9라면 예측7–11이±2 성공이다. 이는 P(7)+...+P(11)의 평균과 다른 지표다.
- 검출 포함 지표는 전체 실제 유부하 행 중 접촉으로 검출하고 abs(y_hat-y_true)<=k인 비율이다.
  무부하0을 공간 ID로 해석해 ID1/2에 가까운 예측으로 성공 처리하지 않는다.
  Masked 단독은 접촉 검출기가 없어 조건부 위치 지표로 제한한다. 무부하 오검출률도 별도 유지한다.
- 기존 class0 body test의76.53%는 조건부±2ID 정답률이며, 검출 포함±2 성공률이나
  새 학습 성능이 아니다. ±2는 허용 위치 오차이지 보정된 신뢰구간이 아니다.
  운용 중 정답을 알아야만 산출되는 출력이 아니라, 정답이 있는 평가에서 예측의 오차를 재는 기준이다.
- Tip/body 구별은 거리 평가와 별도로 유지한다. 예를 들어 정답body17에tip18을 출력하면
  ±1에는 들어가더라도 tip/body 판정은 틀린 것이다. 거리 지표로 운용 모드 오류를 감추지 않는다.
- 이번 수행은 합의 기록뿐이다. 코드/설정/라벨/데이터/가중치를 수정하거나 재학습하지 않았다.
  다음 비교 후보는 같은 라벨/분할에서 기존 CE와 거리/순서 보조 손실을 대조하는 것이다.
  ±2 지표 채택 자체가 학습 loss나 18ID 정답을 바꾸지는 않는다.

## 58. 2026-10-06 — 무부하 학습2방식 × 위치 평가2방식으로 연구 구성

- 사용자 제안: 상/중/하 구간 평가와 ID 거리 평가를 모두 유지하고, 각각 class0와 loss masking을
  비교하는2×2 구성을 검토한다. 독립 힘 모델의 두 방식별 RMSE/MAE가 비슷한 이유도 확인한다.
- 최신 방향은57절의 거리 평가 우선/구간 후순위에서 **두 평가 관점을 함께 제시**하는 것으로
  정리한다. 정확한 표현은 '무부하 처리 학습2방식 × 접촉 위치 평가2방식'이다.
- 현재 class0는 무부하0을 포함한 위치 분류를 학습하고 masked는 무부하 위치 loss를 제외한다.
  기존 구간 방법은 접촉ID 확률을 구간별로 합산하는 후처리이며 직접 구간 class로 학습한 것이 아니다.
  거리 방법은 최대 확률 ID의 정답과의 차이를 평가한 것이며 거리 패널티를 loss에 넣은 것이 아니다.
  따라서4개 비교 칸은 만들 수 있지만 '서로 다른4개 학습 알고리즘을 구현/학습했다'고 쓰지는 않는다.
  직접 구간 학습과 거리 손실은 별도 후속 실험으로 유지하며 완료했다고 주장하지 않는다.
- 공정한 위치 비교는 같은 평가 행의 실제 유부하 조건에서 양방식 모두 수행한다.
  Class0의 접촉 후보는0을 제외하고, masked는 원래 접촉ID 확률을 사용한다.
  검출 포함 성능·무부하 오검출은 별도 표다. Masked 단독에는 검출기가 없으므로0%가 아니라
  해당없음으로 남기며 GT를 이용해 무부하 출력을 생성하지 않는다.
- 기존 body test 진단에서 masked ResNet은 조건부 구간77.86%/±2ID79.48%,
  class0 Transformer는81.18%/76.53%다. 각각 validation 선택 모델이므로 이 수치만으로
  class0 대masking 처리 자체의 효과를 분리할 수 없다. 처리 방식 비교는 같은 backbone,
  분할/입력/무부하 경계/구간 경계/평가 행으로 짝지어 하고 여러 초기화의 변동도 구별한다.
- 과거 구간1–4/5–10/11–18에는tip이 상단에 포함된다. 이를 body만의3구간 또는 tip/body
  구별 성능으로 잘못 부르지 않는다. Tip/body 혼동은 거리 허용 평가에서도 별도 보고한다.
- 코드 확인: train.py의 force_stores/scaler는 no_load_modes 반복문 밖에서 같은 자료로 구성되고,
  force eligible은 유효 연속 실측힘 기준이다. 위치 mode별 loss 대상과는 분리된다.
  force_net/location_net을 따로 train_branch로 학습하며 class0/masked가 회귀 loss를 바꾸지 않는다.
  동일 force 구조/입력/분할/정답/정규화/seed/학습설정에서는 결과가 같거나 매우 비슷한 것이
  예상된다. GPU 비결정성/초기화 등 조건 차이로 완전 동일함을 항상 보장하는 것은 아니다.
  모든 조합의 모델/optimizer 새 생성 정책은 그대로이며 비슷한 결과가 가중치 재사용 증거는 아니다.
- 보고 구성: 힘은 모델별 축별/전체 RMSE·MAE 표, 위치는 위2×2 조건부 비교표와 별도의
  검출/검출 포함 위치 표로 정리한다. 힘 성능 차이를 위치 무부하 처리 효과라고 해석하지 않는다.
- 수행/검증: 현재 문서·WindowStore의 라벨/회귀 대상·학습 분기·구간 확률 후처리 코드를 읽고
  설명을 확인했다. 이번에는 문서만 갱신했으며 코드 변경·재학습·새 성능 평가를 실행하지 않았다.

## 59. 2026-10-06 — 사용자 예시와 같은 모델 열 배치로 test Excel 재정리

- 요청: `results/force-estimation_loss-mask_testset-results.xlsx`를 참고해 class0 힘 GT/11모델
  예측을 정리하고, ID도 GT/모델별 예측·유부하 여부·±2 성공 여부를 하나의 Excel에 담는다.
- 예시를 확인한 결과 fx/fy/fz 시트 각각 첫 열은GT, 다음11열은 모델 예측이며 8,283행이다.
  예시의 모든GT/33개 모델·축 예측열이 `results/predict/20261006_095933/predictions.xlsx`와
  1e−9mN 이내로 일치했다. 이 실행의 저장된44개 모델 시트를 원본으로 사용했다.
- 재학습·신경망 추론 없이 저장 예측을 재배열하고 지표만 계산했다. 원본 예시·예측 Excel,
  CSV·설정·모델은 수정하지 않았다. 실행 Python은/tmp에만 만들었으며 기본 predict.py의
  자동 내보내기 형식은 이번에 변경하지 않았다.

**저장 파일: 결과 폴더 하나에 새 Excel2개**

- [force-estimation_class0_testset-results.xlsx](../results/predict/20261006_195034_excel_layout/force-estimation_class0_testset-results.xlsx)
  - fx/fy/fz 시트: `gt_fx_mN`/`gt_fy_mN`/`gt_fz_mN`가 첫 열이고 다음 열은
    mlp,cnn,convmixer,resnet,lstm,gru,tcn,transformer,kalmannet,small_gru,residual_tcn 순서다.
  - 예시와 행 순서/모델 순서/단위를 동일하게 맞췄다. 힘은mN이고 역정규화된 저장 예측이다.
    ID18 독립 test2파일의8,283행이며 body 시점 출력을 검증된 힘으로 넣지 않았다.
  - `_rows`는 원본 파일/행과 부하 정답, `_summary`는 양방식 힘모델의 축별/전체RMSE·MAE다.
    `_guide`, `_models`, `_checks`를 포함해 총8시트다. 기존loss-mask 예시는 그대로 유지한다.
- [id-estimation_all-models_testset-results.xlsx](../results/predict/20261006_195034_excel_layout/id-estimation_all-models_testset-results.xlsx)
  - 두 방식의11개 위치모델을 한 파일에 담았다. 각 데이터 시트는 첫2열GT/loaded_gt,
    다음11열은 위와 같은 모델 순서이며 총24,359행이다.
  - 모델마다 시트를 만드는 대신 예측/평가 항목마다 시트를 나눠 모델을 열로 비교한다.
    아래12개 데이터 시트와 `_rows`, `_summary`, `_guide`, `_models`, `_file_counts`,
    `_checks`의6개 보조 시트로 총18시트다.

| ID 시트 | 모델 열의 의미 |
|---|---|
| loss-mask_id | ID1–18 중 최대 확률 위치 후보; 무부하에서도 원래 예측 유지 |
| class0_id | 0..18 최대 확률의 최종ID; 0은 예측 무부하 |
| class0_id_conditional | p0를 제외한 ID1–18 위치 후보 |
| loss-mask_ID_error / class0_ID_error_conditional | GT 유부하에서 위치 후보와 정답의 절대 ID차이 |
| loss-mask_within2 / class0_within2_conditional | GT 유부하에서 위치 후보가 정답±2 이내면1, 밖이면0 |
| class0_within2_detected | GT 유부하에서 접촉 검출과±2 위치 성공이 모두 성립하면1; 놓치면0 |
| class0_loaded | 모델의 부하 판정: 유부하1/무부하0 |
| loss-mask_region / class0_region_conditional | 확률합으로 선택한 기존3구간 후보 |
| class0_region_detected | 예측 무부하0 또는 확률합으로 선택한 구간1–3 |

- ID오차·±2 성공 시트의 GT 무부하 행은 **빈칸**이다. 0은 평가 실패이고 빈칸은 해당없음이다.
  Class0의 최종0을 body1/2와 가까운 위치로 계산하지 않는다. Masked에는 부하 검출 결과를
  임의 생성하지 않았으며 GT로 예측ID를0으로 바꾸지 않았다.
- GT ID는 유부하에서 접촉ID1–18, 무부하에서0이다. 케이블 부착ID는 `_rows`에 별도로 남겼다.
  ±2 성공 시트의1은 녹색,0은 빨강이며 ID오차 시트도2 이하/초과로 색을 구분했다.
  값은 MATLAB에서 읽을 수 있는 숫자이며 수식 계산에 의존하지 않는다.
- 모든모델을 `(source_file, source_row)`로 대조/정렬했다. 같은 Excel행은 모든 해당 작업
  시트에서 같은 원본 행이다. `_rows.excel_row`는 결과Excel행번호,source_row는 원본CSV
  헤더 제외0기준,source_csv_line은 헤더 포함1기준이다.
- 위치 지표는 원본 ID Excel의 확정 라벨24,359행(유부하11,353/무부하13,006)을 유지했다.
  과거 이중 경계의 불확실3,426행은 원본ID Excel부터 제외됐다. 이를 센서 무효행이라고
  부르지 않는다. 힘 표는 유효 회귀값인 불확실1,154행도 유지하며 이행의loaded_gt는빈칸이다.
- 부하 상태는 **저장 모델 당시 교정 기준**이며 현재YAML의 수동 경계로 다시 판정하지 않았다.
  구간은 이전validation 선택1–4/5–10/11–18을 모든모델에 동일 적용하고1/2/3으로 표시했다.
  새test 구간 탐색은 없다. Tip18은구간3에 포함되어 있으므로tip/body 구별과 구분한다.
- 대표 분기는 원본과 동일하다: force모델은location partner MLP, 위치모델은force partner MLP다.
  Test로 대표를 고르거나 조합별 가중치를 합치지 않았다. `_models`에checkpoint와hash를 보존했다.
- ID `_summary`는22모델×전체/body1–17/tip18의66행이다. 정확ID/±1/±2/평균ID오차,
  조건부 구간, 검출 포함±2/구간, 무부하 오검출,tip/body 구별과 support를 구분했다.
  Body는같은녹화분할,tip은독립실험이라는 범위를 명시했다.

**검증과 완료 범위**

- 예시3시트와 GT/모델별 값 전체를 대조했다. 원본44시트의 원본 행키 중복 없음,
  모델 간 GT·라벨·행집합 일치를 확인했다.
- 힘 RMSE/MAE176개를 저장 test 비교표와1e−8mN 이내로 대조하고,
  위치·support·검출176개를1e−12 이내로 대조했다. Validation 열과 test_열을 혼동하지 않았다.
- 새Excel26시트 전체의 열·행·모든셀을 다시 읽어 원 데이터/계산값과 대조했고 빈칸도 일치했다.
  Class0 최종ID만으로 검출 포함±2 표시를 독립 재계산해11모델 모두 일치함을 확인했다.
  원본예시와원본예측Excel의 생성 전후SHA256도 같다.
- 기존 선택모델의body±2 조건부 결과는masked ResNet79.48%,class0 Transformer76.53%로
  재현됐다. Class0의검출포함body±2 성공률은63.65%다. 새모델성능으로 해석하지 않는다.
- 완료: 요청한class0힘표/양방식ID표 생성, 모델별요약, 전체셀검증 및 작업기록.
  새학습/새추론/기본학습·예측내보내기코드 변경은 수행하지 않았다.

## 60. 2026-10-06 — 저장 Excel 재정리 Python과 예측→정리 shell

**요구사항과 구현**

- 사용자 요청: `predictions.xlsx` 경로만 주면59절처럼 GT와 각 모델을 열로 비교하는
  Excel을 만드는 별도 Python을 추가한다. 예측부터 정리까지 연결하는 shell도 제공하고,
  predict.py가 긴 이유와 수정할 위치를 설명한다.
- [organize_results.py](../organize_results.py)를 추가했다. 모델·CSV·현재 YAML을 읽지 않고
  프로젝트 Excel의 저장된 숫자/부하 라벨을 사용한다. 모델 종류·개수는 시트에서 읽는다.
  기존 pandas/numpy/XlsxWriter와 표준 라이브러리를 사용하며 추가 패키지는 없다.
  학습5개 핵심 파일은 그대로이고, 명시적 요청에 따른 결과 정리 파일1개를 추가한 것이다.
- `force_tables()`는 힘 표/지표, `id_tables()`는 ID 표/지표, `write_workbook()`은 표시 형식이다.
  같은 `(source_file, source_row)`를 기준으로 행을 정렬한다. 행 집합·GT가 다르거나
  원본 행키가 중복되면 결과를 섞지 않고 오류를 낸다. 동일 형식 `validation.xlsx`도 지원한다.
- [scripts/predict_and_organize.sh](../scripts/predict_and_organize.sh)는 지정한 학습 폴더로
  기존 predict.py를 실행하고 성공한 경우 그 실행의 predictions.xlsx를 정리한다.
  다른 실행의 최신 폴더를 추측하지 않는다. 경로의 공백을 보존하고 예측 실패 시 중단한다.
  기존 hrm_python.sh를 통해 프로젝트 가상환경을 사용한다.

```bash
# 저장된 Excel만 재정리: 학습/모델 예측 없음
bash scripts/hrm_python.sh organize_results.py results/predict/20261006_095933/predictions.xlsx

# 새 test 예측 + 정리: 재학습 없음
bash scripts/predict_and_organize.sh results/train/20261006_095933
```

- 단독 정리는 `--output 새폴더`를 지원한다. Shell의 선택적 두 번째 인자는 새 예측 폴더다.
  폴더가 이미 있으면 중단하며 원본·기존 결과를 덮어쓰지 않는다.
- 정리 폴더는 입력 Excel 옆 `organized_날짜_시간/`이다. 입력에 있는 방식에 따라
  `force-estimation_loss-mask_results.xlsx`, `force-estimation_class0_results.xlsx`,
  `id-estimation_all-models_results.xlsx`를 만든다. validation에도 쓸 수 있어 파일명에
  testset을 고정하지 않았다. 빈 모델 시트는 건너뛰고 `_guide`에 남긴다.
- 힘 파일은 fx/fy/fz 각각 GT + 모델별 예측(mN)이다. `_summary`는 해당 방식의
  모델별 축별/전체 RMSE·MAE다. 원래 회귀 값/부호와 불확실 부하의 유효 힘 행도 유지한다.
- ID의12개 데이터 시트 의미는59절과 같다. 조건부 ID·절대 거리·±2 성공과 class0 검출을
  구별한다. 무부하 GT의 거리/±2 평가는 빈칸이며 masked에 검출 기능을 만들지 않는다.
  `_summary`는 전체/body ID1–17/tip ID18을 나눠 support와 지표를 담는다.
  ID 범위만으로 독립 실험 여부를 추정하지 않으며 원래 실험 기록을 따른다.
- 기본 구간은 이전 비교와 같은1–4/5–10/11–18로 고정했다. `--regions 1-8,9-17,18`처럼
  명시할 수 있으나 현재 YAML을 읽거나 test로 최선 구간을 탐색하지 않는다.
  합산 확률로 구간을 정하며 최대 확률 ID의 구간과 다를 수 있다.
- 세 파일 모두 `_rows`에 원본 행 대응, `_guide`에 해석과 입력 SHA256,
  `_models`에 원본의 대표 파트너/checkpoint 기록을 보존한다(원본에 해당 시트가 있을 때).
  기존 predict.py만 실행하면 기존 predictions.xlsx까지 생성하는 동작은 그대로다.

**predict.py의 길이와 읽을 위치**

- 현재878행에는 추론뿐 아니라 저장 전처리 복원/원본 대응, 전체 조합 평가,
  validation 기준 모델 선택, 구간 지표, Excel 저장과 validation Excel 내보내기가 함께 있다.
  따라서 모든 행이 단일 모델 추론 자체에 필요한 것은 아니다.
- `predict_trials()`의 약52행이 배치 신경망 추론과 결과 대응의 핵심이다.
  `select_and_evaluate()`는 전체 조합 test, `ModelWorkbook`은 원래 Excel 저장,
  `export_validation_workbook()`은 학습 후 validation Excel 내보내기다.
- 이번 요청은 별도 결과 정리 도구로 구현했다. predict.py를 더 늘리거나 기존 평가 경로를
  재구성하지 않았다. GT/모델 열 편집은 새 organize_results.py에서 하면 된다.

**수행과 검증**

- 기존 `results/predict/20261006_095933/predictions.xlsx`의44개 모델 시트를 실제로 읽어
  [정리 결과 폴더](../results/predict/20261006_095933/organized_20261006_202740_875138/)에
  세 파일을 생성했다. 힘 시트는8,283행, ID 시트는24,359행이다.
- 새 양방식 힘6시트와 ID12시트의 **4,396,380개 데이터 셀**을 사용자 예시/59절 결과와
  대조했다. 힘은1e−9mN 이내, ID 값과 빈칸은 동일하다. Class0 Transformer의 body
  조건부±2 76.53%/검출 포함±2 63.65%도 재현됐다. 새 모델 성능으로 해석하지 않는다.
- 단위 검증은 기존 tests/test_pipeline.py에 추가했다. 모델별 행 순서 차이, GT/행 불일치,
  무부하 빈칸, 검출 누락, tip/body 혼동, 단일 방식/일부 ID/빈 시트, 덮어쓰기 방지,
  shell의 공백 경로와 실패 전파를 확인했다. shell 검증은 가짜 실행기로 수행했다.
- 전체 `bash scripts/hrm_python.sh -m unittest discover -s tests -v`: **38개 통과**.
  기존 학습 경로 검증은 학습 함수를 mock한 합성 검증이며 실제 재학습이 아니다.
  정리 도구만 import할 때 torch가 로드되지 않는 것도 확인했다.
- 미실행/후속: 실제 전체 예측→정리 shell 실행과 새 학습은 하지 않았다. 저장 결과 정리와
  shell 연결은 검증 완료했고, 사용자가 새 예측을 원할 때 위 shell 명령으로 실행하면 된다.

## 61. 2026-10-06 — 유부하 조건부 ±2 ID 정확도의 의미 재확인

- 요청: masked/class0 두 방식의 위치 학습과 유부하에서 정답±2 ID 정확도가 약70%인지 확인한다.
- 저장된 정리 Excel의 `_summary`를 다시 읽었다. Validation 선택 모델의 body ID1–17
  test GT 유부하8,045행에서 masked ResNet79.48%, class0 Transformer76.53%다.
  이 값은 확률을 정답 주변에서 더한 값이 아니라 접촉 위치 후보의 절대 ID오차≤2인 행 비율이다.
- 유부하 조건은 실제 정답 라벨 기준이다. Class0는 p0를 제외한 위치 후보로 조건부 성능을
  계산하며, 접촉 검출까지 동시에 성공해야 하는 body ±2 성공률은 같은 분모에서63.65%다.
  Masked 단독에는 무부하 검출이 없다. Body test는 같은 녹화에서 분리한 평가다.
- 수행/검증: 기존 숫자와 의미만 확인하고 문서에 기록했다. 코드 변경·재학습·새 추론은 없으며
  이번 확인 요청에서 남은 작업은 없다.

## 62. 2026-10-06 — tip ID18 판정과 거리 허용 평가 구분

- 요청: 현재 위치 모델에서 tip ID18을 어떻게 구분하는지 확인한다.
- data_utils.location_predictions와 predict.predict_trials를 확인했다. Masked는 ID1–18
  최대 확률의 위치 후보가18이면 tip 후보이며, class0는 ID0–18 전체 최대 확률이18이면
  최종 tip,0이면 무부하,1–17이면 body 위치를 출력한다. Tip 전용 분류 head는 없다.
  기존3구간 후처리는18을 상단에 포함하므로 별도 tip 구간을 만든 결과가 아니다.
- 정답18의 ±2 성공은 예측16/17/18을 포함한다. 따라서 tip과 인접 body를 구별하는
  정확18 성능과 구분해야 한다. 앞61절 body 지표에는 정답18 행을 넣지 않았다.
- 저장 Excel `_summary`와 validation 선택 모델의 predictions.csv를 대조했다.
  독립 tip test의 GT 유부하3,308행에서 masked ResNet 정확18 후보39.39%/±2 76.27%,
  class0 Transformer 정확18 후보42.59%/±2 69.86%다. Class0의 후보는 p0를 제외한다.
  실제 class0 최종 출력은18이1,234행(37.30%),0이23.70%,body1–17이39.00%다.
- 기본 force_scope는tip이다. 힘 모델은ID18 자료로 유무부하 연속 회귀를 학습하며,
  predict에서 힘/위치 분기를 각각 실행한다. 위치 예측으로 힘 추론을 켜고 끄지 않는다.
  Body 입력에서 나온 tip 힘 출력은 범위가 검증되지 않은 것으로 표시하며 운용/제어 전환은 미구현이다.
- 수행/검증: 코드와 기존 저장 결과만 확인했다. 재학습·새 추론·실행 코드 변경은 없으며
  이번 설명 요청에서 남은 작업은 없다.

## 63. 2026-10-06 — body contact 감지 ON/OFF 운용 방향 논의

- 요청: 현 성능에서 body contact detection 모드를 사용자가 켜고 끄는 구성이 적절한지 검토한다.
- 제안: OFF에서는 tip에만 외력을 가하는 실험 조건 아래 연속 tip 힘 추정/어드미턴스 제어를
  평가하고, ON에서는 접촉 여부와 위치 후보의 표시·기록을 추가한다. OFF는 body 접촉이
  없음을 검출한 상태가 아니다. ON/OFF만으로 tip/body 분류 성능이 개선되지는 않는다.
- 힘 계산은 계속할 수 있지만 body 접촉 때의 출력은 검증된 tip 힘으로 사용할 근거가 없다.
  현재는 접촉 모니터링부터 검증하고 ID 예측에 따른 자동 제어 전환은 별도 평가 대상으로 둔다.
  Class0는 무부하 판정 출력을 제공하고 masked는 별도 검출기가 필요하다.
- 수행/검증: 현재 설계와61–62절 결과를 근거로 방향을 설명했다. 이는 제안이며 확정된 운용
  구현이나 실행 승인이 아니다. 코드·설정·모델 변경, 학습·추론·제어 실행은 하지 않았다.
  후속 검증 대상은 tip/body 오인식과 검출 누락이며 이 논의에서 구현 작업은 요청되지 않았다.

## 64. 2026-10-06 — 단일 접촉 가정에서 무부하/tip/body 상시 판정 요구

- 사용자 정정: 여러 위치에 동시 외력이 작용하는 상황은 제외한다. 다만 실행 중 접촉 위치는
  계속 tip인지 body인지 구분해야 한다. 따라서63절의 수동 ON/OFF 제안은 최종 운용 요구가 아니다.
- 현재 학습된 위치 모델도 매 입력 창에서 후보/최종ID를 출력할 수 있다. 필요한 것은 항상
  실행하는 것 자체뿐 아니라 무부하/tip/body 판정의 신뢰성이다. ±2 평가는 tip18에 대한
  body16/17 예측도 성공으로 세므로 이 상태 구별의 대체 지표가 될 수 없다.
- 제안: 독립 tip 힘 회귀는 유지하고 위치 네트워크의 학습 목표로 무부하/tip/body 상태 분류를
  명시적으로 비교한다. 필요하면 같은 위치 네트워크의 다른 출력으로 body ID/구간을 유지하고
  실제 body 유부하 행에서 세부 위치 loss를 적용한다. 이는 새 비교 설계이며 구현/학습하지 않았다.
  기존 class0의 ID0/ID18/ID1–17 대응을 기준선으로 사용하고, masked는 상태 검출 분기가 있어야
  무부하까지 포함한 상시 판정을 구성할 수 있다. 별도 세 번째 독립 네트워크가 필수인 것은 아니다.
- 학습 라벨은 기존 무부하 기준을 우선 적용하고, 유부하 중 ID18을tip,ID1–17을body로 매핑할 수 있다.
  상태 목표를 직접 주어도 입력에 tip/인접body 차이가 부족하면 성능 향상을 보장할 수 없다.
  힘 원본/회귀 loss는 그대로 유지하며 body 행의 힘 정답을tip힘0으로 바꾸지 않는다.
- 추론 시 힘 계산과 접촉 상태 출력은 계속 유지할 수 있다. 힘을 제어에 사용할지 여부와
  추론을 실행할지 여부는 구분한다. Body 상태의 tip 전용 회귀값은 검증된 끝단 힘으로 취급하지 않는다.
- 후속 평가 기준은 무부하/tip/body 혼동행렬, 실제tip을body/무부하로 놓치는 비율, 실제body를tip으로
  오인하는 비율, 검출 포함 body 위치 성공률이다. 상태 전환 지연은 연속 실행 검증에서 별도 측정한다.
  모델/판정 기준 선택에는 validation만 사용한다. 이번 대화에서 새 학습 실행을 요청한 것은 아니다.
- 관련 1차 연구 확인: [Ha et al., Contact Localization of Continuum and Flexible Robot Using Data-driven Approach](https://research.tudelft.nl/en/publications/contact-localization-of-continuum-and-flexible-robot-using-data-d/)
  는 접촉 검출과 위치 추정을 구분하는 구조다. 센서와 방법이 다르므로 우리 데이터의 성능 근거나
  위3상태 학습 설계 자체의 검증으로 인용하지 않는다.
- 수행/검증: 현재 설정·저장 진단 기록과 관련 연구의 설명을 확인하고 요구를 문서에 반영했다.
  실행 코드·설정·모델 변경이나 학습·추론·제어 실행은 하지 않았다. 상시 운용 구현과 새 분류 실험은 미완료다.

## 65. 2026-10-06 — YAML 부하 경계와 기존 모델 저장 경계 구분

- 요청: 현재 유부하 구간이 YAML 설정을 따르는지 확인한다.
- 새 학습은 configs/train.yaml의 ft_sensor_calibration을 사용한다. 현재 mN 기준
  Fx[-134.326,134.326], Fy[-126.814,126.814], Fz[-192.670,192.670]이다.
  fts_kalman.aligned_* 실측 세 축이 모두 범위 안(끝값 포함)이면 무부하, 하나라도 밖이면
  유부하다. 추가 offset 차감/확대/중간 불확실 구간은 없다. 회귀 정답은 변하지 않는다.
- 지금까지 분석한20261006_095933 결과는 수동 경계 변경 전의 저장 교정(평균 중심과
  무부하/유부하 이중 경계)을 사용한다. calibration.json과 predict의 bundle 교정 로딩을 확인했다.
  현재 YAML을 수정한 뒤 기존 모델로 predict해도 학습 당시 교정을 현재 기준으로 바꾸지 않는다.
- 이 경계는 학습/평가용 부하 GT를 만들기 위한 것이다. 실제 추론의 class0 유무부하 출력은
  네트워크의 클래스 예측이며 정답 F/T로 대체하지 않는다. Masked 단독에는 검출 기능이 없다.
- 수행/검증: 현재 설정과 라벨 판정/저장 교정 복원 코드를 확인하고 기록했다.
  코드·설정 변경, 학습·추론 실행은 하지 않았다. 이번 확인 요청에 남은 작업은 없다.

## 66. 2026-10-06 — 이전 자동 경계의 실제 축별 수치 재확인

- 요청: 이전 자동 경계의 구간 수치가 기록되어 있는지 확인한다.
- 근거는 [20261006_095933/calibration.json](../results/train/20261006_095933/calibration.json)이다.
  기록2 앞70%에서 중심/표준편차를 계산하고 max-axis 정규화 score의95%/99.5% 분위수에
  1.1을 곱해 무부하/유부하 두 경계를 정했다. off_score=2.725001350697114,
  on_score=3.580733037356144이다. 아래 수치는 mN, 소수 셋째 자리 반올림이다.

| 축 | 라벨용 차감 offset | 보정 후 무부하 절댓값 이하 | 보정 후 유부하 절댓값 이상 |
|---|---:|---:|---:|
| Fx | -67.362 | 134.326 | 176.509 |
| Fy | 19.593 | 126.814 | 166.638 |
| Fz | -85.573 | 192.670 | 253.174 |

| 축 | CSV 원값의 무부하 범위 | CSV 원값의 유부하 경계 |
|---|---|---|
| Fx | [-201.688, 66.964] | ≤-243.871 또는 ≥109.147 |
| Fy | [-107.221, 146.407] | ≤-147.045 또는 ≥186.231 |
| Fz | [-278.243, 107.097] | ≤-338.747 또는 ≥167.601 |

- 세 축 모두 무부하 범위 안이면 무부하, 어느 한 축이라도 유부하 경계에 도달/초과하면
  유부하이며 나머지는 불확실이다. 불확실 행은 위치 loss/확정 라벨 평가에서 제외했지만
  유효한 연속 힘 회귀 정답은 유지했다. 라벨 판정의 offset을 힘 회귀값에서 차감하지 않았다.
- 현재 YAML의0중심 수동 범위는 위 보정 후 무부하 반폭을 CSV 원값에 직접 적용한다.
  따라서 이전 자동 경계와 판정이 같지 않으며 새 수동 방식에는 중간 불확실 구간도 없다.
- 수행/검증: 저장 교정 수치를 읽어 N→mN으로 변환하고 load_states의 경계 포함 규칙을
  확인했다. 문서 기록만 추가했고 설정·모델·데이터 변경, 재학습·추론은 하지 않았다.

## 67. 2026-10-06 — 경계 변경에 따른 재학습 필요 범위

- 요청: 이전 자동 경계에서 현재 YAML 수동 경계로 바꾸었으므로 다시 학습해야 하는지 확인한다.
- 새 경계에 맞춰 학습된 위치 모델을 얻으려면 재학습이 필요하다. Class0의 무부하0/접촉ID
  정답과 masked의 위치 loss 포함 행이 바뀐다. 기존 결과는 당시 경계 기준의 결과로 보존한다.
  기존 모델을 다시 predict하거나 GT를 새 경계로 재평가하는 것은 새 기준으로 학습하는 것과 다르다.
- 경계만 바뀌고 CSV/입력/분할/회귀 설정이 같다면 힘 회귀 정답·유효 학습 행은 변하지 않으므로
  힘 모델 자체는 이 이유만으로 재학습할 필요가 없다. 다만 현재 train.py는 모든 조합의
  두 네트워크를 새로 만들어 학습하므로 기존 명령을 실행하면 힘 모델도 다시 학습한다.
- 무부하/tip/body를 직접 분류하는 출력은 아직 제안이며 현재 코드에 없다. 기존 학습 명령은
  새 수동 경계를 사용하는 기존 ID 분류 구조를 학습한다. 상태 분류 비교에는 먼저 구현이 필요하다.
- 수행/검증: WindowStore의 라벨 생성과 train_experiment의 분기별 학습을 확인하고 기록했다.
  재학습 필요성에 대한 질문으로 처리했으며 학습·추론·코드/설정 변경은 실행하지 않았다.

## 68. 2026-10-06 — 기존 ID 분류와 직접3상태 분류의 차이, 변경 최소화

- 요청: 직접 무부하/tip/body 분류가 기존과 어떻게 다른지 명확히 설명한다. 이후에는 변경을
  최소화하며 모호한 사항은 먼저 확인한다. 이 선호를 작업 규칙에 반영했다.
- 정정/명확화: 기존 class0도 최종ID0→무부하,18→tip,1–17→body로 해석할 수 있다.
  따라서 상시 상태 판정을 위해 직접3클래스 학습이 필수인 것은 아니다. 현재 출력의 상태 해석과
  새로운 상태 학습 목표를 구별한다. 기존 성능의 한계와 실시간 제어 연결 미구현은 그대로다.
- 기존 class0는19클래스(0..18)의 정답ID를 cross-entropy로 학습한다. 직접3분류는 정답을
  무부하/tip/body로 묶어 학습한다. 예를 들어 실제ID9와 예측ID12는 기존ID 학습에서는 오답이지만
  3상태 관점에서는 둘 다body다. 실제18을17로 예측하면 두 방식 모두 tip/body 구별 실패다.
- 단순히 기존 출력을3클래스로 교체하면 body 내부 ID를 출력할 수 없다.64절에서 제안했던
  상태 출력+세부 위치 출력 구성은 이를 유지하기 위한 추가 출력/손실을 둔 확장안이며,
  단순 후처리가 아니다. 구현·재학습이 필요하고 성능 향상은 검증되지 않았다.
- 변경 최소화 방향: 독립 힘/ID 네트워크와 class0/masked 비교를 유지한다. Class0 최종ID를
  세 상태로 해석해 상태 혼동을 평가하고 masked는 기존 유부하 조건부 위치 비교로 유지할 수 있다.
  Masked 자체에는 무부하 출력이 없다. 확률 합산 후 상태를 고르는 별도 규칙은 이번에 추가하지 않는다.
- YAML 부하 경계를 바꾸는 일과3상태 학습 목표를 추가하는 일은 서로 다른 변경이다.
  직접3상태 분류는 미채택 제안으로 남기며 사용자의 상시 상태 구별 요구만으로 추가 구현을 승인받았다고
  해석하지 않는다. 이후 모호한 목표/라벨/구조 변경은 사전에 설명하고 확인한다.
- 수행/검증: train.py의 ID 라벨/cross-entropy와 data_utils.location_predictions의 클래스
  argmax를 확인했다. 문서만 갱신했으며 실행 코드·YAML 변경, 학습·추론은 하지 않았다.

## 69. 2026-10-06 — 직접3분류 제안 제외 확정

- 사용자 결정: 직접 무부하/tip/body 3분류는 제외한다. 별도 상태 출력/손실 추가 제안도
  진행하지 않는다.64·67·68절의 관련 제안은 이 결정으로 종료하며 후속 구현 대상으로 두지 않는다.
- 유지: class0는ID0–18, masked는ID1–18의 기존 위치 학습을 사용하고 독립 tip 힘 모델을 유지한다.
  Class0 출력0→무부하,18→tip,1–17→body 해석과 기존 구간/±2 위치 평가는 그대로다.
  Masked 자체에는 무부하 검출이 없다. 무부하 YAML 경계는 이번 결정으로 변경하지 않는다.
- 수행/검증: 현재 상태와 작업 규칙에 제외 결정을 반영했다. 실행 코드·설정·모델 변경,
  학습·추론은 없으며 직접3분류 관련 남은 작업도 없다.

## 70. 2026-10-06 — 학습/예측 산출물 확인과 ±n ID 평가 옵션

- 요청: 사용자가 기존 결과 폴더를 정리하고 재학습할 예정이다. 학습→예측→정리 Excel 생성
  흐름과 class0/masked 구분을 확인하고, 정답±n ID 평가가 코드로 실행 가능한지 설명한다.
- 기존±2 수치는 눈으로 그래프를 판단한 값이 아니라 저장 예측에 대해
  `abs(conditional_id - ground_truth_contact_id) <= 2`를 코드로 계산한 것이다.
  이번에는 기존 정리 코드의 고정값2를 `--id-tolerance N`으로 지정할 수 있게 했다.
  기본2, 정수0–17이며0은 정확ID 일치다. 학습 목표/출력 구조/무부하 경계는 바꾸지 않았다.
- `organize_results.py`의 ±n 표시 시트, ID별 평균 및 검출 포함 지표에 같은 n을 적용한다.
  N=3이면 loss-mask_within3/class0_within3_conditional/class0_within3_detected 시트다.
  `_summary`의 id_tolerance와 `_guide`에 사용한 값을 남긴다. 기존 정확ID/±1/±2 요약은 유지한다.
  기본N=2일 때 기존 시트명과 계산 결과는 그대로다. 무부하 GT는 빈칸, class0 접촉 검출 누락은
  검출 포함 평가에서0이다. Masked에 검출 기능을 추가하지 않았다.
- `scripts/predict_and_organize.sh`에 동일 옵션을 전달할 수 있다. 잘못된 n은 비용이 큰
  예측을 시작하기 전에 거절한다. 기본 호출/선택 출력 폴더/공백 경로 처리는 유지한다.
- 학습 명령은 현재 YAML의 force11종×location11종×class0/masked=242조합을 새로 학습한다.
  `results/train/날짜_시간`에는 모델별 bundle/지표/설정과 **validation.xlsx**가 저장된다.
  Shell 예측 명령은 모든 완료 조합을 평가하고 `results/predict/날짜_시간/predictions.xlsx`를
  만든 뒤, 그 옆 organized_날짜_시간 폴더에 양방식 힘 파일2개와 양방식 ID파일1개를 만든다.
  `predict.py`만 직접 실행하면 정리 단계까지 자동 실행하지 않는다.

```bash
# 사용자가 실행할 명령: 학습
bash scripts/hrm_python.sh train.py --config configs/train.yaml

# 완료된 실제 학습 폴더를 지정: test 예측 + ±2 기준 Excel 정리
bash scripts/predict_and_organize.sh results/train/학습날짜_시간 --id-tolerance 2

# 저장된 예측을 ±3으로 재평가/정리: 재학습·모델 재실행 없음
bash scripts/hrm_python.sh organize_results.py results/predict/예측날짜_시간/predictions.xlsx --id-tolerance 3
```

- n은 결과 평가 기준이며 model selection/학습loss/정답라벨/예측값을 바꾸지 않는다.
  상중하 구간 경계와도 다른 설정이다. 원본comparison.csv는 기존 계산을 유지하고
  임의 n의 결과는 정리 Excel에 남긴다. Validation Excel에도 같은 정리 명령을 사용할 수 있다.
  Tip18을16/17로 예측하는 경우 ±2 성공이어도 tip/body 구별에서는 오류라는 의미는 그대로다.
- 검증: 기존 tests/test_pipeline.py에 n=0/3/17의 CLI→Excel 왕복, 원본GT/예측/힘값 보존,
  접촉 검출 누락, 무부하 빈칸, 기본±2 요약 유지, ID1/18 최대거리17의 경계 포함을 검증했다.
  Shell의 기본/명시n/자동출력폴더/잘못된옵션/실패전파를 가짜 실행기로 확인했다.
  `bash scripts/hrm_python.sh -m unittest discover -s tests -v`: **39개 통과**.
  Shell 구문 검사, 두 명령의 --help, git diff --check도 통과했다.
- 완료 범위: 정리 Python/shell의 평가 옵션과 사용 문서 수정. 실제 새 학습·전체 예측은
  실행하지 않았으며 기존 결과를 삭제하지 않았다. 테스트의 학습은 mock이며 실제 학습이 아니다.
  기존 결과 삭제는 사용자가 수행하겠다고 한 것으로 이해했다. 이후 실제 실행은 위 명령으로 진행한다.

## 71. 2026-10-06 — 실시간 출력 요구와 낮은 확률의 ID18 기본값 논의

- 사용자 요구: 실제 제어에서는 상시 유무부하 확인, 접촉ID 확인, 주변±n 구간 확률과 향후
  ID 확률 히트맵을 표시하고 힘 추정도 실시간 표시한다. 위치 확률이 낮으면 부하 판정과
  관계없이 ID18을 기본값으로 사용하고 싶다는 요청이다. 단일 접촉 가정과 직접3분류 제외는 유지한다.
- 의미 구분: 정답이 있는 test의 ±n 성공률은 `abs(pred_id-gt_id)<=n`의 비율이다.
  실시간에는 GT가 없으므로 같은 성공 여부를 계산할 수 없다. 예측ID를 중심으로 범위를
  정한다면 예측10/n=2의 주변 합은 p8+p9+p10+p11+p12이고 ID1–18 경계 안에서 계산한다.
  이 확률 합은 성공률과 다른 값이다. 구간 선택 규칙 자체도 확정 전에 변경하지 않는다.
- 현재 class0는 p0를 포함한19개 확률과 최종ID를 출력하며, masked는 접촉ID 확률만 출력한다.
  Class0의 원래 p1..p18 합은1-p0이고 masked는1이므로, 위치 조건부 재정규화 여부까지
  포함한 확률 정의를 명확히 한 뒤 기본값 임계값을 정해야 한다. 코드 확인만 했으며 변경하지 않았다.
- 구현 가능한 후처리 의미: 지정한 위치 점수가 임계값보다 낮으면 운용ID18과 기본값 적용
  표시를 함께 출력한다. 원래ID/확률분포/유무부하 판정은 그대로 보존한다. 예를 들어
  무부하 판정과 기본ID18이 함께 나올 수 있으며 이것을 tip 접촉 검출로 해석하지 않는다.
  기본값을 적용했다고 p18을1로 만들거나 기존 정확도 계산의 원 예측을 바꾸지 않는다.
- 히트맵은 원래 위치 분포와 원래 선택 구간을 바탕으로 표시하고, 기본ID18 표시는 별도로
  구별한다. 낮은 확률만으로 body 접촉이 없다고 판단하지 않는다. Tip 전용 힘 계산/표시는
  계속할 수 있지만 body 상태의 출력을 검증된 tip 힘으로 보는 것은 아니며 제어 사용 정책은 별도다.
- 질문: 낮은 확률의 기준이 단일ID 최대 확률인지 예측주변±n의 확률 합인지와 원하는
  임계값(%)을 사용자에게 확인했다. 답을 기다리는 상태이며 임계값을 임의로 선택하지 않았다.
- 관련 근거: [Guo et al., On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html)
  는 신경망 확률과 실제 정답률이 일치하지 않을 수 있음을 다룬다. 우리 모델의 보정 성능을
  측정한 것으로 해석하지 않으며, 확률 합을 실제 접촉 성공률로 보증하지 않는다.
- 수행/검증: predict.py의 힘/위치 독립 출력과 data_utils.location_predictions의 확률·ID
  의미를 확인하고 요구를 기록했다. 기존 코드에 기본ID18 정책이나 실시간±n 히트맵은 없다.
  이번에는 문서만 갱신했으며 학습·추론·제어 실행/코드·YAML 변경은 하지 않았다.
  미완료: 기본값 기준/임계값 확정, 후처리 및 실시간 제어·표시 연결. 신규 학습 완료 여부는 이번에 재검증하지 않았다.

## 72. 2026-10-06 — 학습→test 예측→Excel 정리를 한 번에 실행하는 명령

- 요청: 기존 세 단계를 한 번에 실행하는 방법을 안내한다.
- train.py의 --output과 기존 predict_and_organize.sh를 연결하면 새 shell 파일 없이 가능하다.
  실행 시각을 한 번 저장해 train/predict 폴더 이름을 맞추고 &&로 학습 성공 시에만 예측을 실행한다.
  Shell 내부 set -euo pipefail에 의해 예측이 실패하면 정리를 실행하지 않는다.

```bash
HRM_RUN_ID="$(TZ=Asia/Seoul date +%Y%m%d_%H%M%S)"
bash scripts/hrm_python.sh train.py --config configs/train.yaml --output "results/train/$HRM_RUN_ID" &&
bash scripts/predict_and_organize.sh "results/train/$HRM_RUN_ID" "results/predict/$HRM_RUN_ID" --id-tolerance 2
```

- 프로젝트 루트에서 블록 전체를 실행한다. 가상환경은 hrm_python.sh가 사용하며 class0/masked와
  후보 모델은 현재 YAML을 따른다. n을 바꾸려면 --id-tolerance 뒤 숫자만 변경한다.
  새 train/predict 날짜 폴더와 그 예측 폴더 아래 organized_날짜_시간의 비교 Excel을 생성한다.
- 수행/검증: 두 실행 파일의 인자와 성공/실패 연결을 읽고 위 블록을 bash -n으로 구문 확인했다.
  사용법 안내만 했으며 실제 학습·예측·정리나 기존 결과 삭제는 실행하지 않았다.
  실행.txt와 실행 코드·YAML은 수정하지 않았다. 이 안내 요청의 남은 작업은 없다.

## 73. 2026-10-06 — 새 test의 ±2/±3 비교와 정리 파일명에 허용거리 표시

- 요청: predict 실행 시 자동 정리 여부를 확인하고 정리된 파일/폴더 이름에 id-tol을 표시한다.
  사용자가 이미 만든 n=2와 n=3 결과를 분석한다. 재학습·재추론은 요청 범위가 아니며 실행하지 않았다.
- 자동 실행은 기존 동작 그대로다. `scripts/predict_and_organize.sh`는 예측 성공 후 organize를
  실행하고 `predict.py` 단독은 predictions.xlsx까지 생성한다. 학습→예측→정리는72절 명령을 사용한다.
- 변경: organize_results.py의 기본 폴더명을 `organized_날짜_시간_id-tol-N`, Excel 이름을
  `force-estimation_loss-mask_id-tol-N_results.xlsx`, `force-estimation_class0_id-tol-N_results.xlsx`,
  `id-estimation_all-models_id-tol-N_results.xlsx`로 바꿨다. 명시한 --output 폴더 이름은 존중한다.
  힘 파일의 n은 같은 정리 실행을 식별하는 표시이며 힘 예측값·지표는 n과 무관하다.
- 이번에는 사용자의 기존 두 organized 폴더와 내부6개 파일에도 저장된 _guide의 n을 확인해
  같은 이름 규칙을 적용했다. 각 파일의 SHA256이 변경 전후 동일하며 Excel 내용은 수정하지 않았다.
  새 이름·이전 이름·SHA256 대응은 분석 Excel의 renamed_files 시트에 보존했다.
- 평가 대상: 사용자가 실행한 train `20261006_211528`의242조합 완료 결과와
  predict `20261006_221159`의242조합 test다. 이번 작업에서 모델 학습/추론을 수행했다는 뜻이 아니다.
  Validation 선택은 **양방식 힘MLP/위치Transformer**다. 과거 실행의 masked ResNet 선택과 혼동하지 않는다.
  비교 Excel은 원래 정책대로 고정 첫 파트너MLP의 대표11모델×2방식이며 test로 대표를 바꾸지 않았다.
- 두 정리 실행은 동일한 predictions.xlsx를 사용했고 원본 SHA256은
  `cccfc5e88ee1bf7bf4892b8ba040051d9dfd362ca179e84305809a52c883f578`이다.
  ID는27,785행, 힘은8,283행이다. Body1–17은 동일 녹화 분할 test이며 유부하8,242/무부하11,260행이다.
  Tip18은 기존 독립 실험2개 test이며 유부하3,362/무부하4,921행이다.
- 이번 bundle의 무부하 기준은 manual_axis_ranges: Fx±134.326/Fy±126.814/Fz±192.670mN이다.
  세 축 모두 경계 포함 범위 안이면 무부하, 나머지는 유부하이고 offset 차감/불확실 구간은 없다.
  과거 자동 경계 결과와는 GT 유부하 집합도 달라 단순 수치 차이를 모델 개선으로 해석하지 않는다.

**해석과 대표 결과**

조건부 평가는 **GT 유부하 전체**에서 위치 후보를 비교한다. Class0는 p0를 제외한 최대 확률
ID를 사용한다. 모델이 유부하로 판단한 행만 골라 계산한 값이 아니다. 검출 포함 평가도 동일한
GT 유부하 전체가 분모이며 최종ID0은 실패다. Masked는 자체 무부하 검출 기능이 없다.
±n은 `abs(pred_ID-GT_ID)<=n`의 성공률이고 확률합이 아니다.

| 범위·방식 | 정확ID 조건부 | ±2 조건부 | ±3 조건부 | ±2 검출 포함 | ±3 검출 포함 |
|---|---:|---:|---:|---:|---:|
| Body masked Transformer | 30.49 | 82.16 | 87.14 | 해당 없음 | 해당 없음 |
| Body class0 Transformer | 32.89 | 78.15 | 84.48 | 60.66 | 64.21 |
| Tip masked Transformer | 30.10 | 61.09 | 74.99 | 해당 없음 | 해당 없음 |
| Tip class0 Transformer | 37.75 | 70.88 | 77.10 | 62.52 | 66.09 |
| 전체 masked Transformer | 30.38 | 76.06 | 83.62 | 해당 없음 | 해당 없음 |
| 전체 class0 Transformer | 34.30 | 76.04 | 82.34 | 61.20 | 64.75 |

위 표는 %다. Body masked는6,772→7,182/8,242행(+410행, **+4.97%p**), class0 조건부는
6,441→6,963행(+522행, **+6.33%p**)이다. Class0 검출 포함은5,000→5,292행(+292행,
**+3.54%p**)이다. 늘어난 성공은 모두 정확히3개ID만큼 틀린 예측이다. n은 학습/예측을 바꾸지 않는다.
±2는 내부ID 기준 최대5개 후보, ±3은 최대7개 후보를 허용한다(끝 경계에서는 잘림).

- Body의 ID별 동일 가중 평균(macro)도 masked **80.29→85.21%**, class0 **74.12→82.17%**다.
  행 가중 평균만 높아진 현상은 아니지만 모든 위치에서 균일하게 잘 되는 것은 아니다.
- Class0 body 유부하 검출률은 **72.23%**, 무부하 정답률은 **98.50%**다.
  유부하8,242행 중2,289행(27.77%)을 놓친다. n을 키워도 이 누락은 바뀌지 않으며
  검출 포함 ±n 성공률의 상한은 같은 모델/판정에서72.23%다. 현재90% 달성으로 보고할 수 없다.
- Tip의 class0 최종ID18 정답률은 **1,099/3,362=32.69%**다. 같은 유부하tip 중
  **1,372행(40.81%)은 body**, **891행(26.50%)은 무부하**로 예측했다.
  ±3에서15/16/17도 성공으로 세지만 tip/body 구별에서는 오류다. Masked tip 정확ID는30.10%다.
- Body에서 class0 최종ID가1–17인 비율은 **69.63%**, ID18 오분류는 **2.60%**다.
  Body의 검출+±3 성공에 `예측ID<18`까지 요구하면 **61.81%**로, 단순 검출+±3의64.21%와 다르다.
  이 상태 분석은 기존 ID0/1–17/18의 해석일 뿐 새로운 직접3분류 모델/출력은 추가하지 않았다.
- 현 결과는 **근처 위치를 찾는 능력**을 보여주는 근거가 된다. ±2와±3를 함께 보고하며
  독립 body 실험 성능·실시간 상태 구별 성능과 구분해야 한다. ±3의 높은 숫자만으로 기준을 대체하지 않았다.
  행들이 시계열로 상관되어 있으므로 행 수를 독립 실험 수로 간주한 유의성 검정은 하지 않았다.

**모든 대표 위치 모델: body GT 유부하8,242행, 단위%**

| 모델 | masked ±2 | masked ±3 | class0 ±2 조건부 | class0 ±3 조건부 | class0 ±2 검출 포함 | class0 ±3 검출 포함 |
|---|---:|---:|---:|---:|---:|---:|
| mlp | 79.40 | 86.58 | 77.94 | 86.33 | 57.06 | 61.96 |
| cnn | 77.76 | 85.87 | 72.99 | 82.15 | 57.10 | 62.62 |
| convmixer | 75.08 | 84.97 | 68.78 | 79.82 | 47.76 | 53.36 |
| resnet | 75.59 | 83.31 | 74.69 | 83.24 | 57.81 | 62.86 |
| lstm | 77.70 | 88.41 | 73.66 | 84.05 | 55.44 | 60.68 |
| gru | 68.09 | 80.05 | 77.35 | 83.28 | 59.20 | 62.39 |
| tcn | 82.52 | 87.38 | 71.68 | 84.40 | 47.79 | 55.08 |
| transformer (validation 선택) | 82.16 | 87.14 | 78.15 | 84.48 | 60.66 | 64.21 |
| kalmannet | 70.43 | 83.54 | 70.20 | 82.73 | 50.90 | 58.65 |
| small_gru | 63.09 | 75.88 | 67.85 | 83.88 | 50.64 | 63.59 |
| residual_tcn | 70.87 | 84.41 | 78.31 | 86.17 | 59.21 | 63.92 |

Test 표에서 masked ±2는TCN82.52%, ±3는LSTM88.41%가 가장 높다. Class0 조건부 ±3는
MLP86.33%가 가장 높지만 검출 포함은Transformer64.21%가 가장 높다. 이는 대표11모델의
test 관찰 결과이며 **validation 선택을 test 최댓값 모델로 바꾸지 않는다**.

**선택 Transformer의 ID별 결과: 단위%, n=3**

| 정답ID | 유부하행 | masked ±2 | masked ±3 | class0 ±2 조건부 | class0 ±3 조건부 | class0 유부하 검출 | class0 ±3 검출 포함 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 294 | 95.92 | 95.92 | 95.92 | 95.92 | 36.73 | 36.73 |
| 2 | 142 | 80.99 | 81.69 | 52.82 | 80.28 | 9.86 | 2.11 |
| 3 | 338 | 98.82 | 98.82 | 89.94 | 89.94 | 44.97 | 43.79 |
| 4 | 279 | 56.63 | 84.59 | 57.71 | 87.10 | 65.95 | 60.22 |
| 5 | 410 | 28.78 | 30.49 | 46.34 | 47.80 | 39.27 | 21.46 |
| 6 | 338 | 67.75 | 67.75 | 75.74 | 75.74 | 67.75 | 64.79 |
| 7 | 1378 | 85.99 | 95.07 | 87.88 | 88.61 | 84.83 | 76.34 |
| 8 | 973 | 99.28 | 99.49 | 98.25 | 99.79 | 64.13 | 64.13 |
| 9 | 761 | 98.95 | 99.47 | 95.40 | 96.98 | 79.24 | 79.24 |
| 10 | 807 | 62.95 | 63.32 | 55.51 | 60.47 | 79.93 | 54.28 |
| 11 | 119 | 94.12 | 94.12 | 94.96 | 94.96 | 91.60 | 91.60 |
| 12 | 253 | 71.15 | 76.68 | 44.66 | 47.83 | 69.17 | 31.62 |
| 13 | 248 | 72.58 | 87.50 | 45.97 | 60.48 | 85.08 | 56.05 |
| 14 | 494 | 85.83 | 88.46 | 83.40 | 83.60 | 86.44 | 75.51 |
| 15 | 802 | 87.16 | 98.88 | 79.05 | 97.38 | 80.67 | 80.67 |
| 16 | 384 | 82.55 | 90.89 | 60.94 | 92.71 | 77.86 | 77.34 |
| 17 | 222 | 95.50 | 95.50 | 95.50 | 97.30 | 88.29 | 88.29 |
| 18 | 3362 | 61.09 | 74.99 | 70.88 | 77.10 | 73.50 | 66.09 |

- Masked의 주요 잔여 위치 오류는ID5(±3 30.49%), ID10(63.32%), ID6(67.75%)다.
  ID4는56.63→84.59%, ID15는87.16→98.88%로 완화 효과가 크지만, ID5/10은±3에서도 낮다.
- Class0 ID2는 위치 후보 ±3가80.28%여도 유부하 검출은9.86%, 검출+±3는2.11%다.
  ID1/3도 검출률36.73%/44.97%로 낮다. 이 경우 허용거리 확대만으로 문제가 해결되지 않는다.
  따라서 ID1–6을 통째로 제외하는 것보다 위치오류와 검출누락을 분리해 보고하는 편이 현재 자료에 맞는다.
  이번에 ID 제외·무부하 경계/손실 변경은 하지 않았다.

**독립 tip 힘 추정: GT 유무부하 전체8,283행, 단위mN**

±2·±3 정리의 모든 힘 GT/예측/지표는 동일하다. Validation 선택MLP는 양방식 동일하게
XYZ RMSE **138.56**, MAE **96.46**이다. 축별RMSE Fx/Fy/Fz는 **177.19/94.73/131.25**,
축별MAE는 **116.98/76.46/95.92**다. Fx오차가 가장 크다.

| 힘 모델 | masked XYZ RMSE | masked XYZ MAE | class0 XYZ RMSE | class0 XYZ MAE |
|---|---:|---:|---:|---:|
| mlp | 138.56 | 96.46 | 138.56 | 96.46 |
| cnn | 135.42 | 93.63 | 136.27 | 94.20 |
| convmixer | 144.46 | 100.40 | 144.46 | 100.40 |
| resnet | 132.59 | 92.61 | 131.54 | 91.93 |
| lstm | 138.06 | 94.61 | 138.06 | 94.61 |
| gru | 135.17 | 89.16 | 135.17 | 89.16 |
| tcn | 142.30 | 96.63 | 142.30 | 96.63 |
| transformer | 139.39 | 94.76 | 139.39 | 94.76 |
| kalmannet | 133.66 | 87.58 | 133.66 | 87.58 |
| small_gru | 132.49 | 89.82 | 132.49 | 89.82 |
| residual_tcn | 130.46 | 87.01 | 139.73 | 97.65 |

Force 표도 위치 파트너MLP로 고정한 대표 결과다. Class0/Masked의 힘 차이는 ID 평가 n의
효과가 아니며 독립 조합별 실제 학습 결과 차이다. Test 최저 모델로 validation 선택을 교체하지 않았다.
XYZ RMSE는3축 성분 전체의 제곱오차 평균 제곱근이며 벡터 크기 RMSE와 다르다.

**저장·검증·남은 작업**

- 분석 파일: [comparison_id-tol-2-vs-3.xlsx](../results/predict/20261006_221159/analysis_20261006_223135_id-tol-2-vs-3/comparison_id-tol-2-vs-3.xlsx).
  selected_models/body_all_models/tip_all_models/per_ID에 거리/검출 지표,
  selected_per_file에 실험별 결과, ID_confusion/class0_state_from_ID에 혼동 분포,
  force_metrics_mN에22모델의 축별RMSE/MAE, force_selected_per_file에2개tip실험별 값을 저장했다.
  body_comparison_chart에는 두 방식의 모델별 ±2/±3 막대그래프가 있다.
- 검증: 양쪽 정리의 GT/ID/행 대응/모델 정보/힘/기존 공통 지표 일치;
  22개ID모델의 모든 ±2/±3 및검출포함 행 판정·scope/macro 재계산 일치;
  22개힘모델의 축별/XYZ RMSE·MAE 재계산 및test comparison 일치;
  원본 predictions.xlsx의44개모델시트와 정리본 전수 대조 및대표checkpoint SHA256 일치.
  원본predictions SHA256 불변, 기존6개organized Excel은 이름 변경 전후SHA256 불변이다.
- 코드검증: 전체 unittest39개 통과, shell구문/organize --help/git diff --check 통과.
  새 분석 Excel도 저장 후 수치·문자열을 다시 읽어 검증했다.
- 미완료/다음 작업: 이번 요청은 완료했다. 모델·라벨·데이터 변경과 신규 학습은 하지 않았다.
  현재결과로90% 실시간 body 검출이나 tip/body 자동구별을 달성했다고 주장하지 않는다.
  운용 기본ID18의 확률정의/임계값과 제어 연결은71절의 별도 미확정 항목으로 유지한다.

## 74. 2026-10-07 — Transformer 선택 기준과 지표별 test 최고 모델 구분

- 질문: Transformer가 ID를 가장 잘 구분했던 모델인지 확인한다.
- 확인 대상은73절과 같은 train20261006_211528/test20261006_221159다.
  predict.select_comparison_rows는 먼저 validation 힘 XYZ RMSE 최저에서0.001mN 이내 조합을
  추리고, 그 안에서 validation ID별 recall 단순평균(location_macro_recall)이 높은 조합을 고른다.
  이번에는 양방식 모두 힘MLP/위치Transformer가 선택됐다. ±2/±3 test 최고 모델을 고른 것이 아니다.
- 고정 힘 파트너MLP의 대표11개 위치 모델을 비교하면 아래와 같다. 수치는%다.
  ‘정확ID’/‘조건부’는 GT유부하 전체에서 위치 후보를 비교하며 class0는 p0를 제외한다.
  마지막 두 행은 같은 GT유부하 전체에서 최종ID0을 실패로 포함한다.

| Test 평가 기준 | masked 최고 | class0 최고 |
|---|---|---|
| 전체ID1–18 정확ID 조건부 | MLP 37.11 | KalmanNet 37.42 |
| BodyID1–17 정확ID 조건부 | MLP 31.86 | Transformer 32.89 |
| Body ±2 조건부 | TCN 82.52 | Residual TCN 78.31 |
| Body ±3 조건부 | LSTM 88.41 | MLP 86.33 |
| Body 검출+±2 | 해당 없음 | Transformer 60.66 |
| Body 검출+±3 | 해당 없음 | Transformer 64.21 |

- Transformer의 전체ID1–18 정확ID 조건부는 masked30.38%/class034.30%다.
  따라서 모든ID/모든지표에서 최고라고 해석하지 않는다. Body에서 접촉 검출 누락까지 포함한
  ±2/±3 성공률은 class0 Transformer가 대표11모델 중 최고다.
- Body test는 동일녹화분할이고 tip test는 독립실험이므로 전체ID 통합 수치와 body 수치를 구분한다.
  Test 관찰 최고값으로 기존 validation 선택을 교체하지 않았다.
- 수행/검증:73절 분석 Excel의 body_all_models/all_ID_models/tip_all_models를 읽어 방식별
  각 지표의 최댓값을 다시 계산하고 train 비교표의 validation 선택 및선택코드를 확인했다.
  설명과기록만 추가했으며 학습·추론·코드/설정/기존결과 수정은 없다. 이번 질문의 남은 작업은 없다.

## 75. 2026-10-07 — 150/200mN 기준의 위치 표시 정책 제안 검토

- 요청: 향후 실시간 운용에서 150 또는 200mN 이내는 무부하 또는 기본 ID18의 힘으로
  표시하고, 그 이상에서 ID와 히트맵을 표시하는 방향을 검토한다. 근처 위치 성공률을 논문에 보고하고 싶다는 의견이다.
  이번 요청은 방향 검토이며 특정 임계값이나 상태 규칙의 구현 승인으로 간주하지 않았다.
- 현재 설정은 `force_scope: tip`이다. 힘 모델은 ID18 정답으로 학습했으므로 body 접촉에서
  출력 크기가 실제 외력 크기를 나타낸다는 검증이 없다. 출력이 작다는 이유로 body 접촉이
  없다고 판단하는 정책은 별도 평가가 필요하다. 이번에 그 검출 성능을 계산하지 않았다.
- 작은 신호에서 body 위치 판정을 보류하고 연속 힘 표시를 유지하는 정책은 검토할 수 있다.
  보류는 실제 무부하나 tip 접촉을 확인했다는 뜻이 아니다. 운용 기본 ID18을 쓰더라도 원래
  예측·확률·부하 판정과 기본값 적용 여부를 보존한다. 평가에서 예측이나 GT를 기본18로 덮어쓰지 않는다.
  Body 상태의 tip 모델 출력을 검증된 body 힘으로 해석하지 않는다.
- 확인 질문: 150/200mN을 모델이 예측한 합력 `sqrt(Fx²+Fy²+Fz²)`, 예측 각 축의 ±범위,
  실측 F/T 중 어느 값에 적용하려는지 비동기로 질문했다. 답변 전이며 임의로 확정하지 않았다.
  실시간에 F/T 정답이 없다면 실측 GT로 만든 gate의 성능을 배포 성능으로 보고할 수 없다.
  현재 YAML의 축별 범위 판정과 합력 경계는 다르며, 학습 GT 경계와 운용 표시 경계를 구분한다.
- 비교 제안: 라벨과 모델을 고정하고 실제 사용 가능한 신호로 150/200 후보 후처리를
  validation에서 비교한다. 표시 비율, GT 접촉을 표시한 재현율, 표시된 접촉의 ±2/±3 성공률,
  전체 GT 접촉에서 표시와 위치 성공을 모두 만족한 비율, 무부하 오표시율을 함께 본다.
  ID별 support와 tip/body 구별도 유지한다. 임계값 미만 body 접촉은 전체 접촉 평가에서 누락으로 남긴다.
  낮은 힘의 GT를 무부하로 바꾸면서 성공률이 개선됐다고 보고하지 않는다.
- 후처리 비교는 재학습을 요구하지 않는다. 학습의 class0 라벨 자체를 새 경계로 바꾸려면
  별도의 재학습 실험이다. 이미 반복 분석한 현 test의 추가 비교는 탐색적 결과로 구분하며,
  운용 정책을 고정한 뒤 새 독립 body 실험으로 검증하는 것이 후속 방향이다.
- 히트맵은 ID1–18 모델 확률과 예측 위치를 표시할 수 있다. 실시간에는 GT가 없으므로
  ‘정답±n 이내인지’는 계산할 수 없다. 예측 주변 확률 합과 사후 GT 거리 성공률은 다른 값이다.
  Softmax를 보정된 실제 접촉 확률로 보증하지 않는다. 표시의 깜빡임과 지연도 향후 검증 대상이다.
- 현재 논문에 쓸 수 있는 표현: ‘동일 녹화 분할 body test의 GT 유부하에서 masked
  Transformer의 위치 후보가 정답±2 이내 82.16%, ±3 이내 87.14%였다.’ 정확ID 분류나
  독립 body 검출이87%라는 뜻은 아니다. 새150/200 조건의 성능은 아직 계산하지 않았다.
- 참고한 일반 원리: [SelectiveNet, ICML2019](https://proceedings.mlr.press/v97/geifman19a.html)는
  선택적 예측에서 평가 대상 비율과 오류의 관계를 다룬다. 해당 모델로 바꾸자는 제안은 아니다.
  [Guo et al., ICML2017](https://proceedings.mlr.press/v70/guo17a.html)는 신경망 확률과
  실제 정확도의 보정 문제를 다룬다. 두 논문은 현재 HRM 성능을 검증한 자료가 아니다.
- 수행/검증: 현재 config, 힘 평가 범위 코드, 73–74절 결과와 위 두 일차 논문의 초록을 확인했다.
  문서만 갱신했으며 새 학습·추론·임계값 성능 계산·코드/라벨 변경은 하지 않았다.
  남은 확인은 판정 신호, 합력/각축 정의, 임계값, 낮은 힘의 표시 규칙이다.

## 76. 2026-10-07 — 기준 힘 이하의 기본 tip 운용 의미 확인

- 사용자 정정: 실제 제어는 tip 접촉을 중심으로 한다. 기준 힘 이하는 운용상 ID18로 취급하고,
  기준을 넘었을 때 예측ID18이면 tip, 다른 접촉 위치를 예측하면 body contact로 취급하려는 뜻이다.
  낮은 힘의 처리 의도는 이번에 확인됐으며75절의 단순 표시 보류 설명보다 이 정정이 우선한다.
- 이해한 규칙:
  1. 기준 힘 이하: ID 예측과 관계없이 운용 ID18, tip 힘으로 취급한다.
  2. 기준 힘 초과 + 예측 ID18: tip 접촉으로 취급한다.
  3. 기준 힘 초과 + 예측 ID1–17: body contact로 취급하고 해당 위치를 표시한다.
- 이는 제어에서 사용할 운용상 접촉 위치 해석이다. 연속 힘 회귀값과 원래 ID/확률을 보존하며,
  학습 GT나 기존 정량평가의 예측을 이 기본값으로 재라벨하라는 요청으로 해석하지 않는다.
  Body 판정 뒤 어드미턴스 제어의 정지/전환 규칙은 이번 대화에서 정하지 않았다.
- 남은 구현 조건: 기준 신호(실측/예측), 합력/각축 정의, 정확한 임계값은 아직 미확정이다.
  ‘그 외 위치’는 ID1–17로 이해한다. Class0의 ID0은 접촉 위치가 아니므로,
  기준 초과인데 최종ID0인 경우의 정책까지 body로 임의 확정하지 않는다.
- 수행/검증:75절 기록과 사용자 정정을 대조해 위 운용 의도를 문서에 반영했다.
  이번에는 이해 확인과 기록만 수행했으며 코드/설정/학습/추론/제어 동작은 변경하지 않았다.
