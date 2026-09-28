# HRM 외력 추정 프로젝트 작업 규칙

최신 합의 반영: 2026-09-28 (Asia/Seoul). 다른 PC에서도 이 파일을 저장소 루트에 유지한다.

## 대화와 작업 기록

- 한국어로 답한다. 새 작업은 [CODEX_HANDOFF.md](CODEX_HANDOFF.md)의 **현재 요약**과
  [docs/WORK_LOG.md](docs/WORK_LOG.md)의 최신 요청부터 확인한다. 긴 과거 대화가 다른
  PC/새 세션에 자동 전달된다고 가정하지 않는다.
- 매 사용자 요청마다 WORK_LOG에 날짜·요청·수행·검증·미완료/다음을 누적 기록한다.
  실패나 미실행을 완료로 기록하지 않는다. 중요한 결정은 이 파일과 HANDOFF도 갱신한다.
- 과거 일지는 보존한다. 현재 합의/구현과 이전 제안이 다르면 최신 사용자 지시와 현재
  요약을 우선하고, 미구현 계획을 완료된 기능처럼 설명하지 않는다.
- 데이터 작업은 [DATASET_SPEC](docs/DATASET_SPEC.md), 학습 설계는
  [TRAINING_PLAN](docs/TRAINING_PLAN.md), 다른 PC 인계는
  [MULTI_PC_HANDOFF](docs/MULTI_PC_HANDOFF.md)를 필요한 범위에서 읽는다.

## 연구 방향과 현재 범위

- 우선순위: 끝단 힘 정확도 → 접촉 위치/세 구간 인식 → 몸체 접촉 힘 추정.
  끝단 목표는 축별 RMSE 약50–90mN이며 달성을 보장하지 않는다.
- 위치와 힘을 별도 모델로 운용하는 방향에 합의했다. **분리 모델은 아직 미구현**이다.
  현재 tip은 XYZ+보조 하중 확률, 위치는 고정18. body는 XYZ+하중+조건부 ID1–18 공동 모델.
- 향후 위치는 정확 ID를 보존하며 우선 아래/중간/끝단 부근 세 구간으로 표시한다.
  후보1–9/10–15/16–18의 경계는 미확정. 세 구간 운영 후처리/분리 모델 학습을
  이미 적용했다고 말하지 않는다. 기존 세 구간 수치는 저장 예측을 재집계한 진단이다.
- 사용자는 ID1–18 전부 수집할 계획이다. 초기 ID는 각도와 장력 모두 거의 변하지 않는다는
  관찰이 있다. 제외 ID는 개발 자료의 반응/구분 가능성과 포함·제외 모델 비교 후 결정한다.
  실제 유부하를 무부하로 바꾸지 않고 원본/한계 평가를 보존한다. 입력18각도는 유지한다.
- 같은 공통 ID validation에서 포함/제외 모델을 비교한다. 최종 test로 제외 경계를 고르거나
  지원 범위 축소를 전체 ID 성능 향상으로 표현하지 않는다. 관측되지 않는 접촉을 자동으로
  unknown/무부하와 구별할 수 있다고 약속하지 않는다.
- 수집 제안은 [STATIC_POSE_COLLECTION](docs/STATIC_POSE_COLLECTION.md), 후속 학습 설계는
  [NEXT_DATA_TRAINING_POLICY](docs/NEXT_DATA_TRAINING_POLICY.md). 고정 자세+동적 녹화 병행,
  모든 ID의 공통 자세/힘 조건을 검토했으나 자세값/수집량은 성능 보장 조건이 아니다.
- 현재는 새 데이터 제공 후 후속 분석·학습을 진행하기로 한 상태다. 환경 확인/문서 질문을
  실제 새 학습 요청으로 해석하지 않는다. 이미 승인된 작업은 중복 허락을 요구하지 않는다.

## 입력·정답·출력 계약

- 기본 입력26: wire_length4 + loadcell_tension4 + relative_angle18. 실제 축은 홀수 tilt,
  짝수 pan, rad의 부호와0을 보존한다. timestamp/실험ID/F/T 정답은 기본 X에 넣지 않는다.
- config의 feature_groups로 **그룹 단위** 선택, 11모델 입력 차원 자동 변경. 개별 채널
  목록 옵션은 없다. 은닉층 폭/층 수는 모델별 고정이다. 기본18각도 유지 방침을 임의 변경하지 않는다.
- 기본 정답: fts_kalman.aligned_fx/fy/fz, hrm_base. 기록 mN→학습 N, 저장 부호 유지.
  raw 선택도 가능하지만 센서 frame으로 자동 대체하지 않으며 Kalman 임계값을 raw에
  그대로 유효한 교정값이라고 주장하지 않는다.
- 실제 HRM 제어 코드에서는 **역정규화된 추론 XYZ에 -1을 한 번** 곱해야 한다.
  학습 정답을 미리 뒤집지 않는다. ROS 제어 연결은 아직 미구현이다.
- 원본 contact_segment_id는 실험 라벨이다. 무부하에서도 원본 ID를 덮어쓰지 않는다.
  현재 body 위치 loss는 유부하에만 적용하고, 힘 회귀는 무부하 실측값도 그대로 사용한다.
- 최종 사용자 출력은 ID/XYZ이며 무부하 표시 ID는0. 현재 표시 하중은 예측 XYZ가 모두
  ±45.4/43.6/72.9mN 이내인지로 판정한다. 사용자 제공1σ 범위이지 신뢰구간/물리적 무접촉 보증이 아니다.
- raw 연속 XYZ 예측과 실측 정답은 보존한다. 현재 별도 display 힘 열만 무부하에서0이며
  이것을 raw 회귀값과 혼동하지 않는다. 향후 구조는 위치+하중 모델/별도 힘 모델을 비교한다.
- 위치 불확실과 무부하는 다르다. ID18 전용 힘 모델을 body/ID16·17까지 검증 없이 적용하지 않는다.

## 데이터 폴더·분할·누락

- 원본 CSV/bag/이미지/메타데이터는 읽기 전용. 파일을 자동 수정/이동하지 않는다.
  단위·영점·실험 라벨·무부하 구간을 추측하지 않는다. 선택한 열만 유효성 검사한다.
- 신규 설정은 configs/tip_force_folders.json / body_force_folders.json.
  datasets/trainsets/<녹화>/csv/summary.csv를 탐색하되 **메타데이터 포함 녹화 폴더 전체**가 필요하다.
  testsets는 예측 전용이며 학습/scaler/모델 선택에 사용하지 않는다.
- trainsets에서 ID별 녹화 단위 validation. 기본 비율0.2지만 ID당2녹화면1개씩 분할된다.
  ID당1녹화는 오류이며 자동 시간 분할로 바꾸지 않는다. 같은 물리 세션/CSV 복사본은 중복 거절.
- 실행 시작에 목록·역할·hash를 고정하고 모든 모델이 같은 분할을 사용한다. scaler는 train만 사용한다.
  체크포인트의 고정 목록에는 나중에 추가된 폴더가 자동 편입되지 않는다.
- 과거 test의 train 편입/과거 train·val의 test 편입을 금지한다. 2026-09-28 확인 시
  trainsets/sine-35deg-both_seg-id-18_right가 과거 test여서 준비 단계가 차단된다.
  다른 PC에서는 현재 배치를 재확인하고 이 기록의 보호 역할을 유지한다.
- right_2는 사용자 수정 CSV18/메타데이터1, front_1은 CSV18/메타데이터0 예외다.
  새 설정의 정확한 session/hash/basis만 허용하며 다른 파일에 자동 확대하지 않는다.
  알려진4개 trim 세션은 원본 angle CSV로 검증된 시간 복원만 허용한다.
- **set zero 등으로 생긴 짧은 F/T 누락은 사용자의 합의대로 학습에서 제외한다.** 빈칸/NaN/
  Inf/비수치, 필요한 유효성 flag 실패, 허용 매칭 시간차 초과 등을0이나 무부하로 채우지 않는다.
- invalid 행을 포함하거나 가로지르는 시계열 창도 제외한다. 기본30행이 다시 연속 유효해야
  사용한다. 원래 행/시간 공백을 유지하고 누락 전후를 이어 붙이지 않는다. 비증가 timestamp나
  간격 중앙값×1.5 초과도 창 경계다. 사용 소스는 현재 Kalman이며 raw만 누락되면 별도로 판단한다.
- set-zero 이벤트 검출/추가 안정화 시간/영점 변화 보정은 미구현이다. 정상 숫자·flag로 저장된
  값까지 자동 제외되는 것은 아니다. 30행 조건을 물리적 필터 안정화 보장으로 표현하지 않는다.
  분석: [F/T 누락 점검](docs/analysis/ft_missing_20260928/README.md).

## 학습·예측·재사용

- 실행법: [DATASET_FOLDERS](docs/DATASET_FOLDERS.md). train.py --prepare-only는 데이터 준비만,
  scripts/train_folders.sh는11모델 학습, predict.py --test-root ... --output 새경로는 별도 평가다.
- 새 결과는 results/의 날짜·실험별 경로에 저장한다. 모델별 predictions.csv, 지표, 설정,
  split_manifest와 hash를 보존하고 기존 결과/부모 체크포인트를 덮어쓰지 않는다.
- --init-checkpoint는 부모 가중치+고정 X/Y scaler로 새 optimizer를 시작한다. 입력 열/순서,
  정답 계약/시간창/하중 기준이 같아야 한다. 입력 조합 변경은 새 학습이다.
  --resume은 완료 모델 건너뛰기이며 optimizer 단계 복원이 아니다.
- 새 녹화 단위 validation을 부모가 이미 본 경우 거절한다. 부모/과거 test 역할 이력을 보존한다.
  옛 체크포인트에 없는 조상 hash를 복원했다고 주장하지 않는다.
- 과거 configs/tip_force.json, body_force.json, tip_front_finetune_20260927.json은 명시 목록 및
  같은 녹화 앞80%/뒤20%+양쪽2초 purge의 승인된 역사적 예외다. 신규 폴더 설정과 혼동하지 않는다.

## 결과 해석과 확인 위치

- 기존 두 실험: results/20260926_tip_body_v1/, results/20260927_tip_front_finetune_v1/.
  각 RESULTS.md와 CODEX_HANDOFF의 현재 요약을 확인한다. 다른 PC에 없으면 별도 복사가 필요하다.
- front 추가학습 validation 선택 LSTM: test XYZ92.65mN, 축별119.63/69.70/81.14mN.
  **모든 축90mN 이하를 달성한 것은 아니다.** test 최저모델을 validation 선택모델로 바꾸지 않는다.
- 위치 Transformer 세 구간84.04%는 같은 녹화 val의 유부하 위치 정확도다.
  독립 ID18-only test의 끝단 구간 재현율61.04%와 구분한다. 전체3구간+무부하 독립80%로 말하지 않는다.

## 다른 PC 환경과 검증

- 현재 PC의 Python은 /home/daeyun/HRM_env/bin/python. 다른 PC에서 이 경로를 강제하지 말고
  현지 가상환경을 확인한 뒤 HRM_PYTHON으로 셸 스크립트 인터프리터를 지정한다.
  Python3.10.12 / PyTorch2.7.1+cu126은 이 PC의 검증 이력이며 다른 PC 호환 보장이 아니다.
- 저장소 루트에서 현지 Python으로 `python -m unittest discover -s tests -v`.
  최근 전체84개 통과, 이후 입력 차원2개/F/T 누락5개 관련 재검증 통과. 코드 수정 시 적절한
  회귀검증을 수행하고 README/WORK_LOG에 실제 결과를 기록한다.
- 의존성은 requirements.txt, 검증 이력은 docs/ENVIRONMENT.md 및 각 실험 pip_freeze.txt.
  환경이 없으면 현지 환경을 준비하고 import/GPU/테스트를 확인한다. 가상환경 폴더 자체를
  다른 PC에서 바로 실행 가능하다고 가정하지 않는다.
- 코드·configs·문서는 함께 전달해야 한다. datasets/와 results/는 .gitignore 대상이라
  Git clone만으로 오지 않는다. 2026-09-28 현재 AGENTS/HANDOFF/대부분 코드도 Git 미추적이며
  인계 전 파일 포함 여부를 확인한다. 실제 다른 PC 복사/commit/push 완료를 추측하지 않는다.
- 이 저장소는 비-ROS 학습 프로젝트다. 사용자 요청 없이 다른 저장소를 수정하거나
  ROS/카메라/모터를 실행하지 않는다. 이 PC의 sandbox/도구 오류를 다른 PC의 영구 제한으로 쓰지 않는다.
