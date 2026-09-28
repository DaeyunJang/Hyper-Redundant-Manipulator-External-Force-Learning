# trainsets / testsets 사용 방법

2026-09-27 구현. 새 폴더 방식은 기존 실험 설정과 별도로 제공한다.
현재 분리 위치/힘 네트워크를 구현한 것이 아니라 기존 tip/body 모델의 데이터 입구를 확장했다.

## 폴더 배치

```text
datasets/
  trainsets/
    녹화폴더_seg-id-18_.../
      session.json
      recording_config.json
      csv/
        summary.csv
        manifest.json
        summary.schema.json
        (기존 원본 토픽 CSV들도 유지)
  testsets/
    별도녹화폴더_seg-id-18_.../
      session.json
      recording_config.json
      csv/summary.csv
      csv/manifest.json
      csv/summary.schema.json
```

**CSV 하나가 아니라 녹화 폴더 전체**를 넣는다. 날짜별 중간 폴더를 둬도 재귀 탐색한다.
탐색 대상은 정확히 `<녹화>/csv/summary.csv`이며 녹화 안의 이미지/원시 bag을 재탐색하지 않는다.
폴더명은 기존 `seg-id-숫자` 부분을 유지한다. 이름에서 ID를 자동 정답으로 추측하지 않고
CSV와 메타데이터를 교차 검증한다. 중복 이름은 예외 설정이 모호해지므로 거절한다.

## 어느 파일을 수정하는가

| 용도 | 설정 파일 | 선택 범위 |
| --- | --- | --- |
| 새 폴더의 끝단 힘 학습 | `configs/tip_force_folders.json` | trainsets 중 ID18 |
| 새 폴더의 기존 body 공동 모델 학습 | `configs/body_force_folders.json` | trainsets 중 ID1–18 전체 |
| 과거 끝단/몸체 실험 재현 | `configs/tip_force.json`, `configs/body_force.json` | 기존 명시 sessions/test_sessions |
| 과거 front 추가 학습 재현 | `configs/tip_front_finetune_20260927.json` | 기존 front 명시 목록 |

새 설정의 `data_root`, `train_directory`, `test_directory`가 폴더 위치다.
`include_contact_ids`로 명시적 ID 선택이 가능하며 기본 body에서 초기 ID를 자동 제외하지 않는다.
끝단은 ID18 고정 출력이고 body 모델이 접촉 ID를 학습한다. 향후 위치/힘 분리는 별도 작업이다.

## 입력 그룹 선택과 네트워크 차원

학습 설정의 `feature_groups`를 바꾸면 선택된 열만 입력으로 사용하고, 11개 모델의
입력 차원과 새 학습의 scaler 크기가 자동으로 맞춰진다. 기본은 다음26차원이다.

```json
"feature_groups": ["wire_length", "loadcell_tension", "relative_angle"]
```

예를 들어 `["loadcell_tension", "relative_angle"]`은 장력4+각도18=22차원,
`["relative_angle"]`은18차원이다. 실제 입력 배열은 `[batch, window_samples, 입력차원]`이며
MLP는 마지막 시점만 사용한다. 입력 그룹 정의는 `configs/feature_catalog.json`에 있다.

현재 선택은 그룹 단위이며 임의 개별 채널 목록 옵션은 없다. 은닉층 폭/층 수는 모델별
정의를 유지하고 자동 확대하지 않는다. 입력층 관련 가중치 수는 차원에 따라 달라진다.
새 입력 조합은 새 모델 학습에 적용하며 기존 체크포인트 추가 학습/예측은 입력 열과
순서가 모두 같아야 한다. 기본 설정과 입력18각도 유지 방침은 이번 확인에서 변경하지 않았다.

## 데이터 준비와 학습

```bash
source /home/daeyun/HRM_env/bin/activate

# 검사와 분할·scaler·출처 저장만, 모델 학습 없음
python train.py --config configs/tip_force_folders.json \
  --output results/tip_folder_check --prepare-only

# 끝단 11모델 학습 (새 결과 폴더 사용)
bash scripts/train_folders.sh tip results/tip_folder_run

# 단일 모델 학습
python train.py --config configs/tip_force_folders.json \
  --output results/tip_folder_single --models lstm
```

- `trainsets`에서만 train/validation을 구성한다. `testsets`는 학습·정규화·모델 선택에
  쓰지 않는다. 학습 단계에서는 test 폴더의 세션 ID/파일 해시를 중복 및 예약 검사에만 쓴다.
  testsets는 빈 폴더여도 학습할 수 있다.
- 기본 validation은 **ID별 녹화 단위**이며 `validation_fraction: 0.2`, `seed: 42`다.
  각 ID에서 ceil(녹화수×비율), 최소1개를 validation으로 남기되 train에도 최소1개를 둔다.
  따라서 ID별 녹화가2개면1개씩 나뉘고 실제 validation 비율은50%다.
  한 ID에 녹화가1개뿐이면 중단하며 임의로 같은 녹화를 train/validation에 섞지 않는다.
- 세션 경계와 시간 공백을 넘는 입력창을 만들지 않는다. scaler는 train만으로 계산한다.
- 모든 모델에 동일하게 쓸 명시 목록을 실행 처음에 고정한다. 결과의 `config.json`,
  `dataset_audit.json`, `split_manifest.csv`, `scaler.json`에 목록·역할·해시가 남는다.
  저장된 config/체크포인트는 나중에 추가된 폴더를 자동으로 포함하지 않는다.
- 동일 녹화 ID 또는 동일 CSV 해시의 복사본을 train/test로 나눠 넣으면 중단한다.
  잘못된 라벨/메타데이터는 자동 수정하지 않는다.
- 새 학습은 새 output을 권장한다. 같은 실험의 `--resume`은 저장 목록/분할이 같아야 한다.
  저장 config를 지정하면 새 폴더가 있어도 해당 고정 목록만 재사용한다.
- warm-start는 기존 `--init-checkpoint ... --models 모델명`을 사용할 수 있다. 새
  녹화 단위 validation을 부모가 이미 본 경우에는 독립 검증으로 간주하지 않고 중단한다.
  기존 가중치를 쓰려면 부모가 보지 않은 validation 녹화가 필요하다.
- 과거 날짜별 datasets 폴더를 옮겼다면 옛 config의 경로가 더는 맞지 않는다. 옛 config는
  과거 기록으로 남겨 두고 새 학습에 위 폴더 설정을 사용한다.

## testsets 일괄 예측

```bash
# 앞서 학습한 모든 모델에 같은 testsets 적용
bash scripts/predict_folders.sh results/tip_folder_run results/tip_folder_test

# 특정 체크포인트 한 개
python predict.py --checkpoint results/tip_folder_run/lstm/checkpoint.pt \
  --test-root datasets/testsets --output results/lstm_folder_test --device cpu
```

`--run`은 `<run>/<model>/checkpoint.pt` 구조를 읽는다. 기존 front 결과처럼
`runs/<model>/<model>/checkpoint.pt` 구조이면 위 `--checkpoint`에 정확한 파일을 지정한다.
기존 `--data-root`는 동일한 과거 자료의 위치 변경용이며 새 testsets 평가 옵션과 다르다.
새 출력 경로를 사용해야 하며 기존 결과를 덮어쓰지 않는다.

```text
results/tip_folder_test/
  evaluation_config.json
  test_comparison.csv
  lstm/ (각 모델별)
    predictions.csv
    metrics.csv, metrics.json, summary.json
    dataset_audit.json, evaluation_provenance.json
    기타 기존 평가 CSV/PNG
```

모델마다 testsets 전체를 합친 predictions.csv를 저장하며 session_id/source_row로 녹화를
구분한다. 원본과 체크포인트를 변경하지 않고 checkpoint scaler를 그대로 사용한다.
과거 train/validation에 사용한 녹화를 testsets에 넣으면 오류를 낸다. 새 checkpoint는
누적 학습/검증 hash 이력도 보존한다. 옛 checkpoint에서 조상 hash를 보존하지 않았던
부분은 복원했다고 주장하지 않으며 남아 있는 세션 이력과 hash까지 확인한다.
현재 CLI는 정답 F/T가 있는 녹화의 offline 평가용이다.

## 현재 배치에서 발견한 항목

- trainsets40개, testsets1개. trainsets40개를 읽기 전용 검사했고 현재 선택 열 기준
  유효238,332행이다. 유효 행수와 학습창 수는 다르다.
- **`trainsets/sine-35deg-both_seg-id-18_right`는 과거 독립 테스트 녹화다.**
  새 설정은 이 녹화가 trainsets에 있으면 학습을 중단한다. 테스트를 계속 보존하려면
  이 녹화 폴더를 testsets로 배치해야 한다. 이번 작업에서는 원본을 이동하지 않았다.
- 과거 front_testset_1도 보호 목록에 포함했다. 보호 목록은
  `protected_test_session_ids` 및 `protected_test_hashes`에 기록한다.
- 사용자 수정 right_2 CSV18/메타데이터1과 front_1 CSV18/메타데이터0은 새 설정의
  정확한 session/hash 예외로 처리한다. 다른 파일로 자동 확대하지 않는다.
- 이 작업에서 실제 데이터로 모델을 학습하거나 새 성능 결과를 만들지 않았다.

검증 명령: `/home/daeyun/HRM_env/bin/python -m unittest discover -s tests -v`.
