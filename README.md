# HRM Force Estimation

HRM의 케이블 길이·장력·상대각으로 aligned XYZ 힘을 추정하고 여러 경량 모델을 비교하는
독립 Python 프로젝트다. ROS나 로봇을 실행하지 않는다.

## 현재 구현

- 기본 입력26: 현재 케이블 길이4 + 장력4 + 실제 축 상대각18. 입력 그룹 선택 가능.
- 기본 정답: `fts_kalman.aligned_fx/fy/fz`, `hrm_base`, 저장 부호 유지. 기록 mN을 N으로
  변환하고 학습 정규화는 train에서만 계산한다. HRM 제어 코드 연결 시 역정규화된
  추론값에 **-1을 한 번** 곱해야 한다. 이 프로젝트에서 제어는 실행하지 않는다.
- 끝단 모드: XYZ + 보조 하중 확률. 위치는 고정18이며 위치를 학습했다고 해석하지 않는다.
- 전체 segment 모드: XYZ + 보조 하중 확률 + 유부하 조건의 위치1~18 분류.
- 표시 하중은 예측 XYZ가 모두 ±45.4/43.6/72.9mN 안이면 무부하, 아니면 유부하다.
  회귀 예측값은 보존하고 별도 display 열만 무부하에서0으로 표시한다. ID0은 위치 해당 없음.
- `model_zoo.py`: MLP, CNN, ConvMixer, ResNet, LSTM, GRU, TCN, Transformer,
  GRU96+MLP(기존 KalmanNetLite), small_gru, residual_tcn — 총11종.
- 원본을 보존하는 CSV 검사, 시간 공백 윈도우 차단, 학습/예측 CLI, CSV·PNG 결과 저장.

## trainsets / testsets 폴더 방식

새 녹화는 `datasets/trainsets/<녹화>/csv/summary.csv`, 독립 테스트는
`datasets/testsets/<녹화>/csv/summary.csv`에 배치한다. 메타데이터가 포함된 녹화 폴더 전체를
유지한다. 설정은 `configs/tip_force_folders.json` / `configs/body_force_folders.json`이며,
trainsets에서 ID별 녹화 단위 validation을 나누고 testsets는 예측에만 사용한다.

```bash
# 데이터 검사만 (학습 없음)
/home/daeyun/HRM_env/bin/python train.py --config configs/tip_force_folders.json --output results/folder_check --prepare-only
# 실제 실행할 때: 끝단 11모델 학습과 별도 testsets 평가
bash scripts/train_folders.sh tip results/tip_folder_run
bash scripts/predict_folders.sh results/tip_folder_run results/tip_folder_test
```

현재 trainsets에 있는 과거 test `sine-35deg-both_seg-id-18_right`는 testsets로 배치해야 한다.
그대로 두면 누출 방지 검사에서 중단한다. 데이터 이동/학습은 이번 구현에서 실행하지 않았다.
폴더 추가는 새 실행에만 반영하고 체크포인트의 저장 목록은 고정한다.
자세한 설정·validation 비율·출력 경로는 [폴더 사용법](docs/DATASET_FOLDERS.md)을 참조한다.

## 실행

기존 `/home/daeyun/HRM_env`에 PyTorch2.7.1+cu126 설치 및 RTX3060 GPU 검증 완료.

```bash
source /home/daeyun/HRM_env/bin/activate
python -m unittest discover -s tests -v

# 끝단 전체 모델 학습 → test 예측 → body 전체 모델 학습 → test 예측 → 집계
bash scripts/train_all.sh results/새로운_실험명

# 단일 모델
python train.py --config configs/tip_force.json --output results/tip_example --models gru
python predict.py --checkpoint results/tip_example/gru/checkpoint.pt --device cuda

# 저장된 모든 모델 재평가
bash scripts/predict_all.sh results/실험명
```

`--resume`은 완료된 모델을 건너뛰는 기능이다. 중단된 모델의 optimizer 상태를 이어가는
기능은 아니다. 기존 결과 덮어쓰기를 피하려면 새 결과 경로를 사용한다. `predict.py --session`
옵션은 `csv/summary.csv`와 관련 메타데이터가 있는 별도 폴더를 평가한다. 현재 CLI는 정답이
있는 기록의 offline 평가용이며, 센서 정답 없이 동작하는 온라인 ROS 노드는 아직 없다.

## 기존 모델로 추가 학습

```bash
bash scripts/fine_tune.sh configs/tip_force_extended.json \
  results/20260926_tip_body_v1/tip/mlp/checkpoint.pt \
  results/새로운_추가학습_실험
```

직접 실행할 때는 `train.py --init-checkpoint 기존/checkpoint.pt --models mlp`를 사용한다.
현재 설정의 데이터로 새 optimizer를 시작하며, 입력/출력/좌표/단위/정답 소스/시간창/
무부하 범위의 호환성을 검사하고 **부모 X/Y scaler를 고정**한다. 이전 test를 train으로
넣거나 이전 train/validation을 새 test로 지정하는 경우는 거부한다. 새 데이터만 넣으면
기존 데이터를 자동 재생하지 않으므로, 과거 성능을 유지하려면 기존 개발 데이터와 새
데이터를 config의 sessions 목록에 함께 지정한다. 독립 test는 계속 제외한다.

부모 checkpoint 경로·hash와 학습 이력을 저장한다. epoch0 초기 모델도 validation으로
평가하여, 추가 학습이 악화되면 부모 가중치를 유지한다. 원본 checkpoint를 덮어쓰지 않는다.
`--resume`(완료 모델 건너뛰기)와 warm-start(가중치로 새 학습 시작)는 다른 기능이다.

## 이번 실험 분할과 주의할 가정

실행 설정은 `configs/tip_force.json`, `configs/body_force.json`이다. 기존 `*.example.json`은
별도 미래 인터페이스 예시로 현재 CLI에 직접 넣지 않는다.

- 끝단 개발: `seg-id-18_left`, `seg-id-18_right_2`. 독립 test: `seg-id-18_right` 전체.
- 두 개발세션을 모두 학습에 쓰기 위해 각각 앞80% train, 뒤20% validation이며 경계
  양쪽2초를 제외한다. validation은 동일세션 시간블록이라 독립 실험 검증보다 약하다.
- body도 test를 제외한 세션에 같은 시간블록 정책을 적용한다. test는 모든 모델 동일하다.
- `right_2` 원본 라벨은1이다. 사용자가 끝단 데이터라고 지정했으므로 학습용18로
  명시 override했으며 원본 라벨을 결과에 보존한다. 실제 접촉 위치 확인이 필요하다.
- 일부 CSV의 앞 시간 열이 신호 행과 어긋나 있다. 확인된4세션에 한해 원본 angle CSV와
  모든18각도 행을 대조해 시간을 복원한다. 입력·힘·원본 CSV는 변경하지 않는다.
- 사용자 임계값은 표준편차1배 범위이며 통계적 신뢰구간이나 물리적 무접촉 보증이 아니다.

상세는 [가정·제한](docs/ASSUMPTIONS.md), [데이터 감사](docs/DATA_AUDIT.md)를 참조한다.

## 결과 구조

```text
results/실험명/
  tip/ 또는 body/
    config.json, dataset_audit.json, split_manifest.csv, scaler.json
    environment.json, pip_freeze.txt, code_snapshot/
    training_comparison.csv, test_comparison.csv
    모델명/
      checkpoint.pt, bundle_metadata.json, training_summary.json, history.csv
      test_predictions/
        predictions.csv, metrics.csv, metrics.json, summary.json
        per_id_metrics.csv, confusion.csv, conditional_confusion.csv
        error_by_force.csv, force_timeseries.png, load_timeseries.png
  combined_comparison.csv, RESULTS.md
```

`source_row`는 원래 summary의 0-based 데이터 행번호다. 결과는 N/mN 단위를 열 이름에
명시한다. 회귀 힘 임계값 기반 하중 판정과 보조 head 확률을 별도로 저장한다.
모델 선택은 validation_loss로 하며 test를 보고 하이퍼파라미터를 재조정하지 않는다.
CPU 지연 지표는 batch1 **모델 forward만** 측정하며 전체 실시간 지연 보장은 아니다.

## 다른 PC에서 이어서 작업

[AGENTS.md](AGENTS.md)의 핵심 규칙, [CODEX_HANDOFF.md](CODEX_HANDOFF.md)의 현재 요약,
[WORK_LOG](docs/WORK_LOG.md)의 요청 이력을 함께 전달한다. 가상환경 경로, Git 미추적 파일,
별도 복사할 datasets/results 및 체크포인트 경로는 [다른 PC 인계 안내](docs/MULTI_PC_HANDOFF.md)를 따른다.

## 문서

- [작업 일지](docs/WORK_LOG.md), [현재 인계](CODEX_HANDOFF.md), [작업 규칙](AGENTS.md)
- [데이터 규약](docs/DATASET_SPEC.md), [학습 계획](docs/TRAINING_PLAN.md)
- [기존 모델 검토](docs/MODEL_COMPARISON.md), [환경](docs/ENVIRONMENT.md)

모델 원본 참조는 사용자가 제공한 [model_zoo_30k.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/humble/scripts_model/model_zoo_30k.py)다.
새 PyTorch 구현은 구조를 참고한 변형이며 기존 TensorFlow 가중치와 호환되지 않는다.
원본 데이터와 results/는 Git에 넣지 않는다.

## 완료된 첫 비교 실험

[결과 보고서](results/20260926_tip_body_v1/RESULTS.md),
[한계 분석](results/20260926_tip_body_v1/DIAGNOSTICS.md),
[22모델 비교 CSV](results/20260926_tip_body_v1/combined_comparison.csv).
끝단11종 및 body11종을 학습·평가했고, 끝단 MLP의 추가180epoch도 수행했다.
검증 선택 MLP의 test RMSE150.12mN, body Transformer130.32mN이다. 그러나 body의
ID18 인식률은 약0.5%이고, 끝단 MLP 무부하 오경보84.4%로 검출·위치 정확도는 부족하다.
추가180epoch는 validation 개선이 없어 기존 가중치를 유지했다.

합성 테스트46개 통과. results의 verification.json은 공통 test5,361개 시점, 원본/
메타데이터 hash보존, 분할·임계값·오차 재계산을 확인한 결과다.

## Train/validation 위치 진단 (2026-09-27)

[재평가 보고서](results/20260926_tip_body_v1/TRAIN_VALIDATION.md)를 추가했다.
Transformer의 전체 위치 정확도는 train92.9%/validation65.2%, ID18만 비교하면
97.2%/71.8%/test0.5%다. 새 녹화로의 일반화에 큰 문제가 있다.
사용자가 right_2 ID를18로 수정한 현재파일은 그대로 두고 학습당시 데이터를 정확히
복원하여 평가했다. 과거모델 재평가는 다음처럼 실행한다.

```bash
python scripts/evaluate_train_validation.py --run results/20260926_tip_body_v1/body \
  --data-root results/20260926_tip_body_v1/data_replay
```

데이터경로를 바꾸어도 checkpoint의 원본hash 검사는 유지한다.

## 신규 front 데이터로11개 모델 일괄 추가 학습 (2026-09-27)

```bash
bash scripts/fine_tune_all.sh results/새로운_front_추가학습_실험 \
  configs/tip_front_finetune_20260927.json \
  results/20260926_tip_body_v1/tip
```

기존 체크포인트를 각각 불러와 새front1/2/3만 추가 학습한다. 각녹화 앞80% train,
뒤20% validation에2초 purge를 적용하고 front_testset_1은 최종평가에만 쓴다.
11모델 학습과 validation 선택을 모두 마친 뒤 부모/추가학습 모델을 같은 test 시점으로
비교한다. 출력이 이미 있으면 덮어쓰지 않는다. 새run layout은 다음과 같다.

- `selection.json`: test평가 전에 고정한 validation 선택 모델.
- `runs/<model>/<model>/checkpoint.pt`: 추가학습 후 validation 최적 가중치.
- `runs/<model>/<model>/test_predictions/predictions.csv`: 추가학습 모델의XYZ 예측.
- `baseline/<model>/test_predictions/predictions.csv`: 기존 모델의 동일새test 예측.
- `before_after_comparison.csv`: 모델별추가학습전후test지표.
- `training_comparison.csv`, `validation_comparison.csv`, `test_comparison.csv`: 상세비교.
- `run_manifest.json`, `verification.json`: 부모/원본hash, 분할, 같은평가시점 검증.

front_1의 CSV ID18/메타데이터0 차이는 명시된session/hash전용 설정으로 처리하며
원본은 변경하지 않는다. source timestamp 반올림 및 감사를 결과의audit폴더에 기록한다.
현재 회귀검증: `/home/daeyun/HRM_env/bin/python -m unittest discover -s tests -v` (52개 통과).


완료된 신규front실험: [RESULTS.md](results/20260927_tip_front_finetune_v1/RESULTS.md).
11종모두180epoch 추가학습했고 동일새test에서모두XYZ오차가줄었다.
validation선택LSTM98.72→92.65mN, test최저ResNet91.39→83.43mN이다.
11종중10종은새test의XYZ50–90mN범위이며 각축/다른방향 성능은별도확인해야한다.
독립검증은 `python scripts/verify_front_finetune.py results/20260927_tip_front_finetune_v1`로 재실행한다.

폴더 방식 추가 후 전체 회귀검증: 84개 통과. 재실행: `/home/daeyun/HRM_env/bin/python -m unittest discover -s tests -v`.
