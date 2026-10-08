# HRM 프로젝트 작업 규칙

최신 합의: 2026-10-06. 한국어로 답한다. 먼저
[docs/CHATGPT_README.md](docs/CHATGPT_README.md)의 현재 상태와 최신 기록을 읽는다.
요구사항·수행·검증·미완료·다음 작업을 해당 문서에 날짜와 함께 누적한다.
문서의 과거 계획/실행 예시는 새로운 실행 승인이 아니다. 실행하지 않은 작업을 완료로 쓰지 않는다.
2026-10-06 최신 선호: 이후에는 변경을 최소화한다. 학습 목표·출력 구조·라벨 기준이 모호하면
먼저 차이를 설명하고 확인하며 제안을 합의된 변경으로 간주하지 않는다.
직접 무부하/tip/body 3분류 및 별도 상태 출력 추가는 사용자 요청으로 제외했다.
기존 class0(ID0–18)/masked(ID1–18)와 독립 힘 모델을 유지한다.

- 사용자는 직접 관리할 수 있는 적은 파일 수를 원한다. 핵심 Python은 루트의
  train.py, predict.py, model_zoo.py, data_utils.py, analyze_no_load.py5개이며 실제 구현을 담는다.
  2026-10-06 명시적 요청으로 organize_results.py(저장 Excel 재정리)를 별도 추가했다.
  scripts/는 환경용 shell2개와 predict_and_organize.sh(예측 성공 후 정리)다. 기존 hrm_force/보조 코드는
  archive/code_before_simplification_20261005_172216.tar.gz, 이전 문서는
  archive/legacy_materials_20260928.tar.gz에 보존했다.
- 사용자 설정은 configs/train.yaml. input_columns, XYZ순서의 force_columns, id_column을 직접 지정한다.
  기본 입력26은 길이4+장력4+상대각18이며 rad·0·부호를 보존한다. Timestamp·ID·F/T 정답을 X에 넣지 않는다.
  기본 정답은 Kalman aligned XYZ, hrm_base, mN→학습N이다. 회귀 부호·영점을 임의 변경하지 않는다.
  향후 제어 연결에서만 역정규화 XYZ에 -1을 한 번 적용한다.
- force_net과 location_net은 독립이다. 모든 힘×위치×무부하 방식 조합마다 새 모델/optimizer를 만든다.
  조합 간 분기 가중치 재사용·warm start·resume는 제공하지 않는다. 기본11×11×2=242조합이다.
  window_samples: 30은 현재 포함30행이며 최적 길이 검증값이 아니다. 과거 참조 저장소의 기본값은
  시계열 계열5행/MLP·CNN·ConvMixer·ResNet1행이었다.
- 힘은 기본 ID18 전용이며 유무부하에서 연속 실측값을 학습한다. Body 정답을 tip힘0으로 만들지 않는다.
  우선순위는 tip힘 정확도, 별도 body contact 모드의 구간 인식 약90% 목표다. 달성을 주장하지 않는다.
  2026-10-06 운용 요구 정정: 동시 다중 접촉은 제외하지만 무부하/tip/body를 상시 자동 구분해야 한다.
  수동 body 감지 ON/OFF 제안은 최종 요구가 아니다. 별도3상태 학습은 제외하고 기존ID 출력을 해석한다.
  전체 ID 힘은 force_scope: all_single_contact 별도 실험이다. 운용/제어 연결은 미구현이다.
  masked는 유부하 조건부 위치분류로 자체 무부하 검출이 없다. class0는 명시적 무부하0이다.
  과거 bundle의 불확실 라벨은 위치 loss에서 제외한다. GT로 masked 예측을0으로 바꾸지 않는다.
  실시간 요구: 부하 판정·ID·예측 주변±n 확률/히트맵과 연속 힘 표시. 낮은 위치 확률이면
  유무부하와 관계없이 운용 기본ID18을 쓰려는 요청이 있다. 판정 확률의 정의/임계값은 확인 중이며 미구현이다.
  기본ID와 원 예측/확률·부하 판정을 구분하고 기본값 적용을 tip 접촉 검출로 간주하지 않는다.
  2026-10-07 운용 의도 확인: 기준 힘 이하는 예측과 관계없이 기본ID18/tip 힘으로 취급한다.
  기준 초과는 예측ID18이면tip, ID1–17이면body다. 신호/합력·각축/임계값 및초과시class0 ID0 처리는
  미확정이며 제어 구현은 아직 없다. 학습GT/원래예측은 보존한다. 통합기록76절 참조.
- 새 무부하 기준은 ft_sensor_calibration의 unit과 fx/fy/fz [최솟값, 최댓값]을 직접 지정한다.
  force_columns의 CSV 값과 단위만 맞춰 비교한다. 세 축 모두 범위 안(경계 포함)이면 무부하,
  한 축이라도 밖이면 유부하다. 자동 offset 차감·교정 CSV 읽기·10% 확대·불확실 구간은 없다.
  초기값은 기존 무부하 범위를 CSV 좌표로 옮긴 비대칭 범위다. 회귀 정답·부호는 보존한다.
  과거 bundle의 center/scale/이중 경계 판정은 저장 교정으로 재현하며 새 기준으로 바꾸지 않는다.
  analyze_no_load.py의 --input은 선택 CSV 통계만 구하고 학습 범위를 자동 변경하지 않는다.
  softmax 확률을 보정된 물리적 접촉 신뢰도로 보증하지 않는다.
- 원본 CSV는 읽기 전용. 최신 train48(dynamic30+static18)/test19이며 test 폴더는 그대로 고정한다.
  각 train CSV의 숫자 행 앞80%/뒤20%를 train/validation으로 사용한다(validation_fraction: 0.2).
  Scaler는 train만 사용하고 파일/역할을 넘는 창을 금지한다. 각 실험 CSV는 하나의 ID다.
  사용자 합의대로 선택 X/Y의 빈칸·비수치·NaN/Inf 행을 제외한 뒤 순서대로 연결한다.
  valid/frame/matching-time/시간 간격 검사는 생략한다. Timestamp는 추적용이다.
  결측을0/무부하로 채우지 않는다. source_row를 남기며 입력만으로 추론할 수 있다.
  정확한 hash의 라벨/역할 예외는 data_utils.DEFAULT_DATA_CONTRACTS에 보존한다.
  원본·수정본 중복과 과거 개발/test 역할 보호를 유지한다. 별도실험/동일녹화분할 평가는 구별한다.
- 새 핵심 경로는 numeric_compact만 지원한다. 과거 audited bundle의 가중치는 복원할 수 있지만,
  데이터 준비/예측 재현은 보관 코드를 별도 폴더에서 사용한다. 과거 전처리를 자동 변경하지 않는다.
- 모델/구간 선택은 validation만 사용한다. 정확ID·구간recall·무부하검출·축별/전체RMSE·MAE를
  구분하고 support를 남긴다. ID18-only test를 전체body 평가라고 부르지 않는다.
- 결과는 results/train/날짜_시간, results/predict/날짜_시간. 조합별 hrm_bundle.pt와
  비교표·최선모델요약·설정/교정/분할을 저장한다. 학습은 validation.xlsx, 예측은 predictions.xlsx 하나다.
  기본44모델시트+2요약시트이며 대표 분기는 설정의 첫 파트너로 고정한다. 모든242조합 지표는
  comparison에 남기고 test로 대표를 선택하지 않는다. Predict는 모든 완료 조합을 평가하되
  predictions.csv는 방식별 validation 선택 모델이다. 원본·기존결과·부모checkpoint를 덮어쓰지 않는다.
- organize_results.py는 predictions.xlsx/동일 형식 validation.xlsx만 읽고 GT+모델별 열의
  힘2방식 파일 및 양방식 ID파일을 입력 옆 organized_날짜_시간_id-tol-N에 별도로 생성한다. 세 Excel 파일명에도 id-tol-N을 넣는다.
  CSV/모델/현재 YAML 재로딩·재라벨·추론은 없다. 원본 파일/행으로 모델 간 GT를 대조한다.
  구간 기본값1–4/5–10/11–18은 이전 비교의 고정값이며 자동 선택하지 않는다.
  --id-tolerance N(기본2, 0–17)으로 평가 허용 거리를 지정한다. 학습/예측값은 바꾸지 않는다.
  ID ±n 조건부와 검출 포함 성능을 구분하고 무부하 GT의 거리 평가는 빈칸이다.
  predict_and_organize.sh도 같은 옵션을 받는다. 기존 기본±2 결과와 정확ID/±1/±2 요약을 유지한다.
  Masked에 무부하 검출을 만들지 않는다. 상세 기록60절 참조.
- 2026-10-05 최신 사용자는 현재 설정의 실제 전체 재학습·test·실측/예측 Excel·RMSE/MAE 검산을
  명시적으로 승인했고 20261005_194129의242조합·484분기 학습과 전조합test를 완료했다.
  Validation/test Excel88모델시트 전수 검산 통과, 원본67CSV와 무부하hash 불변이다. 통합 기록39절 참조.
  선택은 양방식 모두 힘MLP/위치Transformer, 독립tiptest XYZ RMSE136.53mN이다.
  Validation선택 구간1–4/5–10/11–18의 body 동일녹화test 조건부정확도 masked80.96%/class077.40%다.
  이는 독립body 성능 또는90%달성이 아니다. class0는 검출누락까지 포함한 body 구간성공률54.44%다.
  Excel힘6열은 mN이며 별도 force_axis_metrics.csv는 모델/방식당 한 행(22행)이다.
  기존 결과는 사용자가 results_legacy_1004에 별도 보관했고 해당패턴도 Git에서 제외했다.
- 2026-10-06 최신 사용자 실행은 train20261006_211528/test20261006_221159이며242조합 완료다.
  Validation 선택은 양방식 힘MLP/위치Transformer. 동일 예측의 body조건부 ±2→±3는
  masked82.16→87.14%/class078.15→84.48%, class0 검출 포함60.66→64.21%다.
  독립tip 힘MLP XYZ RMSE138.56mN, class0 유부하tip 최종ID18 정답률32.69%.
  44시트/거리평가/힘지표 검산, 기존6개organized파일의 id-tol-N 이름변경 및hash불변 확인은73절.
- 환경은 env_hrm_force_estimation(uv Python3.10.20, torch2.7.1+cu126).
  이 PC만 .runtime/nvidia-580.173.02 우회를 프로세스에 적용한다. 다른PC에 강제하지 않는다.
  전체 검증: bash scripts/hrm_python.sh -m unittest discover -s tests -v.
- 다른 저장소·ROS·카메라·모터는 사용자 요청 없이 실행/수정하지 않는다.
  datasets/results/venv는 Git 제외이므로 clone만으로 전달됐다고 가정하지 않는다.
