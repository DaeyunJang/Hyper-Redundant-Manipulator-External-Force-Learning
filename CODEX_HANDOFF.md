# 학습 프로젝트 인계

마지막 갱신: 2026-09-28 (Asia/Seoul)

## 현재 요약 — 다른 PC에서는 여기부터

이 절과 루트 [AGENTS.md](AGENTS.md)가 최신 기준이다. 아래 날짜별 기록에는 당시의
미구현/진행 중 상태가 남아 있으므로 최신 상태로 오인하지 않는다. 상세 요청 이력은
[WORK_LOG](docs/WORK_LOG.md), 환경/파일 인계는 [MULTI_PC_HANDOFF](docs/MULTI_PC_HANDOFF.md).

- 구현: 11개 모델, 학습/예측/추가학습, feature_groups 선택 및 입력 차원 자동 변경,
  trainsets/testsets 폴더 탐색/고정 분할, read-only 데이터 검사, CSV/PNG 결과와 출처 저장.
- tip=XYZ+하중/고정ID18, body=XYZ+하중+조건부18ID의 공동모델. 위치/힘 분리와 세 구간
  운영 후처리는 아직 미구현이다. 분리 방향에 동의했으며 새 데이터 후 후속 작업한다.
- 최신 기본 입력은 길이4+장력4+각도18. 그룹 선택 가능하나 개별채널목록 옵션은없다.
  기본 각도18개 유지. 입력을 바꾸면 기존checkpoint추가학습과호환되지않는다.
- Kalman aligned XYZ/hrm_base, mN→N, 저장부호유지. 향후 HRM제어에서 역정규화후 -1 한 번.
- 무부하1σ상자45.4/43.6/72.9mN. 원본실험ID와연속XYZ보존, 무부하표시ID0.
  초기ID관측반응없음을무부하정답으로바꾸지않는다. 초기제외범위와세구간경계는미확정.
- 사용자: ID1–18모두수집후학습범위결정. 초기ID는각도와장력모두거의변하지않는다는관찰.
  개발자료로전체/제외모델공통ID비교하고제외데이터는한계평가로보존한다.
- set-zero 때 순간 F/T누락은 기존행제외유지에동의. 포함시계열창도제외, 정상30행연속후사용.
  누락을0/무부하로채우지않음. 이벤트인식/추가안정화/영점변화보정은아직없다.
- 신규학습설정 configs/tip_force_folders.json 및 body_force_folders.json: trainsets에서
  ID별녹화단위val, testsets예측전용. 과거명시설정의동일녹화시간분할은역사적예외다.
- 2026-09-28파일점검: train40/test1. trainsets의oldright18은과거test라학습진입이차단된다.
  배치를재확인하고테스트역할유지필요. 이번문서인계작업에서는이동하지않았다.
- right_2 CSV18/메타1 및 front_1 CSV18/메타0은사용자확인된정확SID/hash예외만허용한다.
- 실제완료: 첫tip/body각11모델비교, tipMLP추가180epoch, front1/2/3기반tip11모델각180epoch.
- front validation선택LSTM의testXYZ92.65mN, Fx119.63/Fy69.70/Fz81.14mN.
  test최저ResNet83.43mN은validation선택과별개. 모든축90mN이하달성은아니다.
- 위치Transformer세구간84.04%는같은녹화val유부하위치정확도. 독립ID18-onlytest끝단재현율61.04%.
  전체3구간/무부하까지독립80%달성으로해석하지않는다.
- 검증이력: 전체84tests통과, 이후입력차원2개/F/T누락5개재검증통과.
  다른PC에서는현지환경으로재실행한다. 원본/모델바이트는이전시에도보존한다.
- 이PC Python=/home/daeyun/HRM_env/bin/python; 다른PC는현지환경과HRM_PYTHON설정사용.
  datasets/results는Git제외. 현재AGENTS/HANDOFF/코드상당수도미추적이므로별도전달확인필요.
- 현재는새데이터후학습대기. 이문서정리로새학습/모터실행/다른PC복사/commit/push를한것은아니다.

## 2026-09-26 초기 구현 기록

2026-09-26 사용자 무인 학습 승인에 따라 실제 코드를 구현하고 끝단11모델 및
전체segment11모델의 동일 right18 독립 test 평가를 완료했다. 추가 요청에 따라
검증 선택 끝단MLP에서180epoch warm-start도 완료했다.
완료 결과는 docs/WORK_LOG.md 최신 항목 및 results/20260926_tip_body_v1/RESULTS.md를 확인한다.

- 구현: hrm_force/data.py, time_repair.py, models.py, engine.py, evaluation.py,
  model_zoo.py, train.py, predict.py, scripts/train_all.sh, scripts/predict_all.sh.
- 실제 실행 설정: configs/tip_force.json, configs/body_force.json. 기존 example 설정은
  실행용이 아니다. raw 전환은 loader가 지원하지만 현재 임계값은 Kalman 전용이다.
- PyTorch2.7.1+cu126 설치, GPU/의존성 검사 성공. 합성 테스트는 tests/에서 실행한다.
- 시험 명령: `/home/daeyun/HRM_env/bin/python -m unittest discover -s tests -v`.
- 단위는 기록 메타데이터와 upstream 펌웨어의 mN 선언을 사용. 물리 교정 검증은 별도다.
- 모든 가정은 docs/ASSUMPTIONS.md. right_2 source ID1→학습ID18 override, 동일세션
  시간블록 validation 예외, 사용자1σ 임계값, 검증된 timestamp 복원을 반드시 읽는다.
- 미구현: 별도 무부하 실측 calibration 도구, 원시 토픽 기반 온라인 causal 정렬,
  실시간 ROS 추론/제어, optimizer 단계 resume 및 별도 force-only CLI 실험.

## 2026-09-26 초기 사용자 결정 기록 (현재 요약 우선)

1. 입력 그룹 조합을 쉽게 바꿀 수 있어야 한다. 각도 포함/제외, 장력 제외, 각도만 등.
2. 힘 정답은 **Kalman F/T가 기본**, raw F/T도 쉽게 선택한다. 모두 hrm_base 기준을
   기본으로 한다. 예전 "raw를 기본으로 사용" 발언은 이번 결정으로 변경됐다.
3. 무부하 센서 기록을 분석해 Fx/Fy/Fz 오프셋·잡음 범위·임계값을 산출하는 코드가 필요하다.
   아직 무부하 실측 분석을 수행하지 않았다. ±50 mN은 대화의 예시이지 확정값이 아니다.
4. 작은 비시계열/시계열 모델을 나눠 비교한다. 후보와 크기는 TRAINING_PLAN 참조.
5. summary는 다른 실험에도 쓰인다. 선택한 열만 학습에 사용하며 원본 스키마를 줄이지 않는다.
6. timestamp를 모델 입력에 넣지 않는다는 의견은 반영한다. 단, 행 순서만으로 시간 공백을
   찾을 수 없으므로 학습 준비 단계에서 시각 검사를 한다는 이유를 설명해 두었다.

## 확정된 로봇/데이터 의미

- 형상상 고정 proximal 구간 1 + 움직이는 관절/구간 18 = 길이 구간 19.
  각 길이 4.33 mm, 총 82.27 mm. 구동 케이블·모터·로드셀 각 4채널.
- 고정 base 다음 움직이는 관절은 **tilt → pan → tilt → pan**.
  relative_angle_1..18은 홀수 tilt_relative[i], 짝수 pan_relative[i]이다.
  부호·0·rad를 보존한다. 이전 pan-first 논의는 폐기된 이력이다.
- contact_segment_id는 0..18의 사용자 지정 실험 라벨.
  0=무부하 자유운동 실험, 1..18=외력 케이블/힘을 가하는 위치. ID18은 distal 구간.
  ID9 실험 중 힘을 풀어도 원본 ID9는 유지한다. 실제 하중 유무 라벨과 다르다.
- 힘이 거의 없으면 위치 자체를 신호에서 알아낼 수 없을 수 있다. 유효한 힘이 있을 때만
  위치 loss를 적용하고, 무부하도 힘 회귀 및 하중 유무 학습에 사용한다.
- 구현된 body 출력은 force3 + load1 + conditional location18이다. tip은 force3/load1
  및 고정ID18이다. 모델 factory는 force_only도 지원하나 이번 CLI 실험은 tip/body다.
- base에 가까울수록 같은 힘의 변형이 작을 수 있다. ID별 평가와 알려진 작은 힘 검증이
  필요하며 네트워크가 관측되지 않은 정보를 복원한다고 약속하지 않는다.

## 데이터/기존 코드 위치

- 기존 로봇 프로젝트: ../Hyper-Redundant-Manipulator/
- 데이터: ../Hyper-Redundant-Manipulator/record/
- 원본 규약: src/record_pkg/README.md, record_pkg/summary_csv.py,
  record_pkg/experiment_labels.py, 각 세션의 session.json / recording_config.json /
  csv/manifest.json / summary.schema.json.
- 현재 summary 268열. 번호 대신 헤더 이름으로 매핑한다. 새 버전 열 증가를 허용하되
  선택한 열/유효성/단위/좌표계가 없거나 충돌하면 명시적으로 보고한다.
- 20260926_202928_638928 세션은 폴더명 변경 중 export 실패 후 csv_recovered/로 복구됐다.
  복구 당시 기존 csv/는 중단본이다. 회복된 summary는 9,949행/268열/ID18이며 태그 자세·crop depth는 없다.
  이는 위치/형상 이미지 재분석에는 제한이지만, 선택된 수치 힘학습 열과는 별도다.
- 사용자가 수집 폴더를 재정리하고 있다. 2026-09-26 문서 검증 시 많은 실험은
  record/20260926_f_ext_datasets/ 아래로 이동했다. 과거 경로 대신 현재 파일을 확인해
  datasets 목록에 지정하고, 이 문서의 역사적 복구 경로를 고정 학습 경로로 쓰지 않는다.
- 폴더명의 seg-id와 실제 라벨이 같다고 추측하지 않는다. 원본 column/snapshot으로 검증한다.
- 기존 LSTM 저장소 model_zoo_30k.py를 사용자가 제공하여 9개 모델을 검토했다.
  docs/MODEL_COMPARISON.md의 참조/적응 구분에 따라 구현한다. 기존 2D 출력은
  XYZ 및 선택형 다중 출력으로 변경할 계획이며 아직 이식하지 않았다.

## 다음 연구 작업

1. right_2의 실제 접촉 위치가18인지 확인한다(원본 기록ID1). 다르면 해당override를
   제거하고 끝단 실험을 재구성한다. 현재 원본은 변경하지 않았다.
2. segment/힘 방향/초기 장력별 독립 반복 녹화를 확보하고 세션 전체를 나누는
   validation/test 평가를 설계한다. 같은 녹화의 시간 분할 성능을 일반화로 오인하지 않는다.
3. Fx 피크 추종 실패, 힘 bias 및 무부하 오경보, ID18 위치 식별 실패 원인을 분석한다.
   현재 test에 맞춰 임계값이나 모델을 재튜닝하지 않는다.
4. 독립 무부하 실측 calibration 및 작은 알려진 힘 검증. 필요 시 raw/Kalman,
   입력 조합/시간창 비교를 새 실험으로 수행한다.
5. 새로운 개발 데이터를 configs에 추가하고 기존 checkpoint로 warm-start한다.
   부모scaler와 역할 이력을 보존하며 기존test는 학습에 넣지 않는다.
6. 향후 온라인 causal 정렬/ROS 추론/제어 연결 검증. 제어부 -1 변환은 아직 미적용이다.

## 아직 확인해야 하는 값

- 실제 데이터별 force 단위와 저장 규약 일치 여부. 학습은 aligned 저장 부호를
  유지하고 HRM 제어 시 -1을 곱한다는 사용자 결정은 확정됐다.
- 무부하로 확인된 세션/시간 구간, sensor/filter 설정별 교정과 기준값.
- 각 ID/힘 방향/초기 장력에 대해 독립된 반복 실험 수 및 유효한 train/val/test 그룹.
- 기대 추론 장치, 허용 지연/최소 검출 힘/필요 정확도. 문서의 수치는 초기 후보일 뿐이다.

긴 원본 대화가 새 Codex에 자동 전달된다고 가정하지 않는다. 이 문서와 DATASET_SPEC,
TRAINING_PLAN이 현재 인계의 기준이다. 미구현 항목을 완료된 기능처럼 보고하지 않는다.

## 이번 준비 작업의 검증

- 독립 Git 저장소(main) 초기화. 커밋/remote/push 없음.
- JSON 예시 3개 파싱, 실제 268열 summary 헤더와 입력 그룹 10개/force source-frame
  조합 4개 대조, 입력 ablation 차원 26/8/22/18/4/48 검증.
- 상대 문서 링크와 공백 형식 확인. 데이터 규약 및 모델 계획 독립 검토 완료.
- 원본 데이터 수정/학습 실행/센서 분석/모터 명령 없음. 확인은 문서·설정 수준이다.

## 2026-09-26 환경 점검 및 기록 규칙 추가

- 기본 인터프리터: `/home/daeyun/HRM_env/bin/python` (기존 Python 3.10.12).
- 분석 패키지 import 및 pip check 성공. PyTorch는 미설치로 학습 환경 준비는
  미완료이며 GPU는 아직 검사하지 못했다. 패키지 설치/변경은 하지 않았다.
- 상세 결과: `docs/ENVIRONMENT.md`. 매 사용자 요청의 작업은
  `docs/WORK_LOG.md`에 누적 기록한다.
- 문서 검토 완료: configs/ JSON 3개 및 docs/ 문서 4개를 모두 읽었다.
- 위 문서검토 단계 당시에는 구현/설치/학습을 수행하지 않았다. 이후 실제 실행은
  현재 구현 상태 및 아래 최신 완료 항목을 따른다.

## 최신 추가 결정 — aligned 부호 및 기존 모델 참조

- 학습/평가: aligned fx/fy/fz 그대로, Kalman 기본. HRM 제어에서는 역정규화된
  추론 XYZ에 -1을 한 번 곱한다. 이번에는 규약만 기록했으며 제어 코드는 미변경.
- 기존 모델 파일의 9개 builder를 기반으로 계획을 확장했다. CNN/ConvMixer/ResNet의
  길이1 경로는 동일 Dense128이며 KalmanNetLite는 GRU 회귀다. 상세 및 추가 후보는
  docs/MODEL_COMPARISON.md. 모델 구현/프레임워크 설치/학습은 아직 하지 않았다.
- split 예시는 8:1:1로 변경. trial 그룹 기준이며 실제 반복 수 검증 후 확정한다.

## 2026-09-26 첫 실제 학습 완료 및 추가 학습 지원

- 결과 루트: results/20260926_tip_body_v1. RESULTS.md 및 DIAGNOSTICS.md 참조.
- tip validation선택MLP: testXYZ RMSE150.12mN, 무부하 오경보84.4%.
- body validation선택Transformer: testXYZ RMSE130.32mN, 유부하 ID18 인식약0.5%.
  끝단고정ID18과 학습된 위치분류를 혼동하지 않는다. 위치인식 성공으로 보고하지 않는다.
- tip_extended: 부모MLP에서 추가180epoch 실행, validation개선없음. epoch0 부모가중치
  유지 및 scaler/예측값 동일성 검증. history는 epoch0포함181행이다.
- --init-checkpoint 및 scripts/fine_tune.sh 구현. frozen parent scaler/새optimizer/
  입력·정답계약검사/과거train-test누수거부/부모hash와역할이력/기존가중치보존 지원.
- 테스트46개 통과. 공통test5361개 행·22모델지표 재계산·원본hash보존 검증 통과.
- 우선 확인: right_2의 실제접촉위치(기록ID1 vs 사용자ID18), 독립반복세션 확보,
  Fx추종오류/무부하오경보 원인. 제공1σ범위는 실제접촉정답이 아닌 파생라벨이다.
- 사용자 추가 승인이 없다고 중단한 작업은 없다. 이번 요청의 학습·평가·정리는 완료했으며
  원본데이터/ROS/제어코드는 변경하지 않았다.

## 2026-09-27 train/validation 진단 및 데이터 재현

- 결과: results/20260926_tip_body_v1/TRAIN_VALIDATION.md. bodyTransformer 전체
  조건부위치 train92.91%/val65.21%. ID18만97.19%/71.80%/test0.50%.
  학습자체불능이 아니라 녹화간 일반화실패와 일치하는 결과다. 원인은 미확정.
- 사용자 확인: right_2 CSV ID18 수정 완료. 역사적 session/schema/manifest는1,
  저장표기도변경되어 원래학습파일hash와 다르다. 과거학습은이미ID18을썼다.
- 학습당시summary를 토픽CSV로 byte-exact 복원하여 data_replay에 보존했다.
  재평가에는 --data-root results/20260926_tip_body_v1/data_replay를 지정한다.
  기존hash검사를 해제하지 않는다. 미래신규학습은 현재CSV/메타데이터불일치를 명시처리해야한다.
- 재평가 CLI: scripts/evaluate_train_validation.py. 원본·가중치변경없이 11모델의
  train/validation 예측·혼동행렬·지표를 저장했다.

## 2026-09-27 최신 우선순위

- 끝단 force 정확도(사용자 목표 RMSE 50–90 mN) → 접촉 위치 → body force 순서.
  목표는 달성 보장이 아니며 XYZ 통합/축별 성능을 모두 추적한다.
- 접촉 위치 단독 학습 및 18 ID→3구간 매핑과 직접3구간 분류는 후속 비교 후보.
  후보 범위1–9 / 10–15 / 16–18은 미확정. 수집은 정확한 원래 ID를 보존하도록 권고.
- 기존 Transformer test에서 ID18 0.50%, 후보 tip부근 61.04%이나 ID18-only test라
  전체3구간 성능을 입증하지 못한다. candidate_region_diagnostic.json에 재집계 저장.
- 이번에는 새 학습/설정 변경 없이 계획을 기록했다. docs/TRAINING_PLAN.md 최신절 참조.

## 2026-09-27 — 최신 위치 출력 방향 및 파라미터 확인

- 사용자 선택 방향: ID1–18 학습 유지 → 나중에 3구간 후처리 표시. 직접3클래스는 대안.
  구간 경계/매핑 vs 확률합은 미확정이며 후처리 코드 아직 미구현.
- 실제 모델 크기 tip9,540–54,724 / body10,134–55,894 trainable parameters.
  results/20260926_tip_body_v1/model_parameter_counts.csv에 재계산 및22개 기록 일치 확인.
- 용량 증가의 효과는 미검증. 끝단 force에서 구조별 크기 비교는 후속 제안이다.
  현재 학습/모델/데이터 변경 없음. 세부 논의는 TRAINING_PLAN 최신절 참조.

## 2026-09-27 front 신규 데이터 추가 학습 진행 중

- 요청: datasets/20260927_f_ext_datasets/front1/2/3으로 기존tip11개 warm-start,
  front_testset_1은 테스트 전용. configs/tip_front_finetune_20260927.json 준비.
- 결과 루트 results/20260927_tip_front_finetune_v1. 계획/독립감사는 해당폴더 참조.
- train25367/val6115/test2572윈도우. 원본 무변경. front1 CSV18 vsmetadata0은
  사용자 확인에 근거한 session/hash 제한 override 구현. 관련회귀 포함49tests통과.
- 실행완료/성능은 아직 미확인. 이후 완료항목을 우선한다.

## 2026-09-27 front 추가 학습 완료 (위 진행 중 기록 대체)

- 결과 results/20260927_tip_front_finetune_v1/RESULTS.md. 기존tip11개→각180epoch 추가학습.
- train25367/val6115/test2572. 신규front1/2/3만학습, front_testset_1 격리, 부모scaler동결.
- validation 선택LSTM(epoch34): 새test XYZ98.72→92.65mN, Fx119.63/Fy69.70/Fz81.14mN.
- test최저ResNet83.43mN(대표선택변경없음), MLP88.33mN. 11종중10종 XYZ50–90mN.
  같은새test에서전후비교한수치다. 전날다른test의150mN와직접개선율비교하지않는다.
- 선택LSTM 기존right18 재평가156.47→155.68mN; old_right_retention/에증거.
- 체크포인트 runs/<model>/<model>/checkpoint.pt, 예측 같은폴더/test_predictions/predictions.csv.
- 실행기 scripts/fine_tune_all.py/.sh. 원본및부모보존;52tests통과;독립44CSV검증통과.
- front1 metadata0/CSV18 explicitoverride는새config에 정확session+hash로명시.
- 다음은 Fx/오경보와독립녹화일반화 개선. 이번요청의학습/테스트/비교/기록은완료.

## 2026-09-27 위치3구간/추가수집 검토

- 초기추천 아래1–9/중간10–15/끝단부근16–18, 정확ID학습/기록유지. 경계미확정.
- 기존bodyTransformer구간재집계: train96.93%/같은녹화val84.04%,
  val재현율 아래87.12/중간83.22/끝단79.04%. 독립ID18-onlytest끝단재현율61.04%.
  새front학습모델은ID18고정force모델이라위치분류와별개다.
- 90%목표권고는독립test각구간precision/recall기준. 모델softmax0.9와다르다.
- 세구간여러ID에서방향/크기/자세를분산한독립반복과아래/중간test추가필요.
  원본ID보존. 자세한수집제안/지표는TRAINING_PLAN최신절과three_region_review/참조.
- 이번에는저장예측재집계/계획기록만수행. 새로운학습/구간설정적용없음.

## 2026-09-27 위치/힘 분리 모델 제안과11모델 구간 평가

- 사용자는위치인식과힘추정을각각잘하는모델로분리사용하는방안을제안했다.
  병렬추론/개별scaler/시점일치후결합을후속방향으로검토. 아직코드구현/전용학습없음.
- 같은val유부하세구간정확도상위 Transformer84.04/ConvMixer81.89/ResNet80.23%.
  하중오판포함순위는다르므로분리조합전체평가필요. ALL_MODELS.md참조.
- 현재tipforce는ID18전용. body및16/17위치에확장하려면해당접촉force학습/검증필요.
  위치와힘모델선택은각목표validation지표기준으로진행한다.

## 2026-09-27 최신 결정 — 분리 모델과 수집 부담

- 사용자가위치/힘별도모델방향에동의. 아직분리모델학습/결합추론미구현, 우위미검증.
- 데이터수집이어렵다는사용자제약. 모든ID일괄추가수집보다기존데이터위치전용학습과
  녹화단위validation으로취약조건을찾고필요부분만추가하는방향을우선한다.
- 기존body37녹화20.6만행이나ID1–17각2독립녹화. 부족의핵심후보는행수보다
  반복/조건다양성및독립평가. 신규4녹화는ID18뿐. 90%달성가능성/필요수집량미확정.
- 앞선각ID3–5회수집은필수최소개수가아니다. 사용자에게현재데이터로더실험가능함을설명.
- 이번에는상태확인/계획기록만수행. 다음학습시groupval을본기존weights로검증하지않는다.

## 2026-09-27 수집 방식 최신 설명

- 사용자: ID1–18재수집가능, 기존방식은사인운동중힘on/off. 고정자세수집도검토.
- 권고: 기존동적데이터유지+모든ID에같은공통정지자세를적용한비교데이터보완.
  정지는목표명령유지/외력변형허용, 서로다른ID마다다른자세만사용하지않음.
- 동적추가수집은여러사인위상에서하중on/off; 외력없는운동기준도기록.
  정지데이터만으로운동중위치인식90%를약속하지않는다. 자세/모드/ID/반복별녹화구분.
- 접촉위치고정의뜻이면한녹화ID일정유지. 이번에는조언/기록만했고로봇명령미실행.

## 2026-09-27 3×3 정지 자세 수집안

- 사용자제안: 모든ID1–18에서pan/tilt각0/15/30°의9조합, 여러방향힘수집.
- 권고: 공통9조합교차수집. 양/음운용이면-30/0/+30°후보검토. 각도미확정.
- 162조건+반복규모. 명령자세와실제측정각도구분, 녹화단위분할/정지·운동별평가.
- 세부 docs/STATIC_POSE_COLLECTION.md. 수집설계기록만수행, 제어/학습미실행.

## 2026-09-27 ID1–4 저변형 제외 검토

- 사용자관찰: ID1–4하중시거의변형없음. 원본보존/학습제외여부미확정.
- 권고: 5–18주요수집우선, 1–4공통자세소량진단으로각도+장력무부하대비변화확인.
  제외전후동일5–18검증과1–4별도실패평가. 제외시전체1–18성능으로보고금지.
- 라벨1–4녹화와입력각도1–4는별개. 입력18각도유지. 미지원접촉을무부하로바꾸지않음.
- 실행설정/원본변경없이논의만기록했다.

## 2026-09-27 초기 구간 제외 근거 분석 방향

- 입력18각도모두유지확정. 사용자는접촉ID1–4/6제외전변형추이분석과논문근거를검토.
- 권고: 초기1–6+비교8/12/18공통조건예비실험, 무부하대비18각도/장력반응·반복성검증.
  각도변화작음만으로하중검출/위치식별불가능을단정하지않음. 경계아직미확정.
- 논문에는제외기준·결정시점·ID/표본수·측정조건·적용범위와포함/제외비교를기록.
  최종test로제외경계선택금지. 아직실측분석/학습제외실행없음.

## 2026-09-27 최신 방침 — 전체 ID 수집 후 범위 결정, 하중·위치 처리

- 사용자 정정: 초기 ID는 각도뿐 아니라 장력 변화도 거의 없다. ID1–18 모두 수집할
  계획이며 새 데이터 제공 전에는 학습하지 않는다. 입력 18각도는 계속 유지한다.
- 전체 보존 → 개발 자료에서 전체/초기 구간 제외 비교 → 지원 범위 결정.
  공통 ID validation 비교와 제외 구간 한계 보고. 실제 유부하를 무부하로 바꾸지 않는다.
  미지원 접촉을 자동 unknown으로 검출할 수 있다고 보장하지 않는다.
- 추천 설계: 위치 모델=하중 확률+조건부 ID, 별도 힘 모델=연속 XYZ.
  무부하는 검출/힘 학습에 쓰고 위치 loss만 제외. 실측 XYZ는 0으로 덮어쓰지 않는다.
  상태 정답은 실제 외력 제거 기록/실측 F/T로 정의하며 입력 반응으로 만들지 않는다.
- 출력은 세 구간 우선, 원본/조건부 ID 보존. 무부하 표시 ID0/구간 없음, raw XYZ 유지.
  위치 불확실과 무부하 구분. 제외 ID/구간 경계/최종 판정 방식은 아직 미확정이다.
- 현재 ID18 force만으로 몸체 전체 무부하 판정 금지. 검출기/지원 범위가 맞는
  force-box/결합은 validation 비교 후 선택. 추천 구조의 성능 우위는 미검증이다.
- 기존 84.04%는 같은 녹화 val 유부하 위치 성능, 독립 ID18 test 구간 재현율 61.04%.
  전체 구간+무부하 독립 성능 80%로 표현하지 않는다.
- 상세: docs/NEXT_DATA_TRAINING_POLICY.md. 이번에는 문서만 작성했으며 분리 모델
  구현/라벨 변경/원본 변경/새 학습 없음. 새 데이터 제공을 기다린다.

## 2026-09-27 최신 구현 — trainsets/testsets 폴더 지원

- 사용자 요청: 최종 ID/XYZ 출력 확인, 현재 train/test 설정 위치 질문 및 datasets 아래
  trainsets/testsets로 녹화 폴더를 모아 summary.csv를 자동 확보하는 구조 제안.
- 신규 configs/tip_force_folders.json 및 body_force_folders.json 구현. train.py가 최초에
  목록/출처를 고정하고 trainsets에서 ID별 녹화 단위 validation을 선택한다. testsets는
  세션/해시 보호 검사만 수행하고 학습/scaler에는 넣지 않는다. 빈 testsets도 학습 가능.
- tip은ID18만, body는1–18전체. 기존 body 공동모델이며 위치/힘 분리 모델 구현은 별도다.
  fraction0.2는녹화수기준 ceil/min1, ID별2녹화이면50%val. ID별1녹화는오류.
- 새 hrm_force/folder_datasets.py, folder_prediction.py 및 CLI --prepare-only /
  --test-root/--output, scripts/train_folders.sh / predict_folders.sh 추가.
- 새 예측은 각모델/ predictions.csv에 전체test합산, test_comparison.csv 및 provenance저장.
  체크포인트scaler유지, 과거train/val SID/hash거절, 결과새경로필수. 기존명시config보존.
- warm-start protected test와누적학습/검증hash이력보호. 부모가본새groupval은거절.
  옛조상checkpoint에서없었던해시이력은복원됐다고주장하지않는다.
- 현재실제배치 train40/test1. train40 읽기전용검사통과(선택열유효238332행). 다만
  trainsets/sine-35deg-both_seg-id-18_right는과거test라준비단계가의도적으로차단됨.
  이녹화를testsets로배치해야새설정학습가능. 이번에는원본폴더를이동하지않았다.
- right_2 사용자수정CSV18/메타1 예외를새config에정확SID/hash로명시. front_1예외유지.
- 합성테스트84개전부통과, CLI도움말/셸문법검사통과. 실제녹화학습/새성능평가는없음.
- 상세사용법 docs/DATASET_FOLDERS.md, README. 다음은사용자의새데이터제공후분석/학습.

## 2026-09-27 입력 선택 확인

- feature_groups로 입력 그룹 선택, 11모델 input_dim 자동 구성 지원 확인. 기본26차원.
  그룹 단위이며 개별채널목록 옵션 없음. 은닉층 폭/깊이는 모델별 고정이다.
- warm-start/predict는 checkpoint 입력 열 및 순서 동일 조건. 입력 변경은 새 학습.
- 관련 기존 테스트2개 통과(11모델 4/8/18/22/48차원forward 포함). 기본입력/모델변경없음.
- DATASET_FOLDERS에 사용법 추가, feature_catalog의 낡은 status만 현재구현에맞게정정.

## 2026-09-28 F/T 누락과 영점 재설정 확인

- 사용자: 수집중set zero때F/T누락. 현코드는선택Kalman/입력invalid행및포함30행창제외,
  0대체/보간없음. 정상30행연속후사용하며이는필터안정화검증과다르다.
- set-zero이벤트검출/추가안정화구간/영점변화보정은아직없다. 정상숫자/flag면통과가능.
- 실제41녹화241002행,Kalman-invalid38행4구간,그행을포함한유효창0. front_3두18행구간.
  이벤트시각이없어원인을setzero로확정하지않음. 분석 docs/analysis/ft_missing_20260928/.
- 관련기존테스트5개통과. 실제학습/원본/모델/로더동작변경없음.

- 2026-09-28 사용자 추가 동의: 순간적인 F/T 누락은 행 제외로 처리. 기존 invalid행 및
  해당행포함시계열창제외 유지, 보간/0대체/앞뒤이어붙이기없음. 추가코드/학습변경없음.
