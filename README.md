# HRM 외력·접촉 위치 추정

CSV의 지정한 입력으로 연속 Fx/Fy/Fz와 접촉 ID를 추정한다. 힘과 위치 네트워크는 독립이며,
기본 설정은 힘11종 × 위치11종 × `masked`/`class0`의 **242조합**을 새로 학습한다.

설정은 **[configs/train.yaml](configs/train.yaml)**, 요구사항·작업·실험 이력은
**[docs/CHATGPT_README.md](docs/CHATGPT_README.md)** 한 곳에서 관리한다.

## 수정할 파일

| 파일 | 실제 구현과 수정할 내용 |
|---|---|
| [train.py](train.py) | 조합 반복, 정규화, loss/optimizer, early stopping, 모델 저장 |
| [model_zoo.py](model_zoo.py) | 실제11종 모델 정의, 모델 크기, 독립 힘/위치 네트워크 구성 |
| [predict.py](predict.py) | 모델 복원, test 예측/평가, 비교표·요약·모델별 Excel |
| [data_utils.py](data_utils.py) | CSV 열 선택/결측 제거, 분할, 시간창의 범위, 공통 평가식 |
| [analyze_no_load.py](analyze_no_load.py) | 수동 무부하 범위·부하 라벨, 선택한 CSV의 범위 내/외 통계 |
| [organize_results.py](organize_results.py) | 저장된 Excel을 읽어 GT + 모델별 열로 재정리; 학습·추론 없음 |

학습 흐름은 `train.py`의 `train_experiment()`, 학습 루프는 `train_branch()`부터 보면 된다.
`model_zoo.py`를 수정하면 실제 사용하는 모델이 바뀐다.
`scripts/`에는 환경 설치·Python 실행용 shell 2개와 예측→정리 실행용 `predict_and_organize.sh`가 있다.

`predict.py`가 긴 이유는 단일 모델 예측 외에 전체 조합 평가, validation 기준 모델 선택,
모델별 Excel 저장과 학습 후 validation Excel 내보내기까지 함께 들어 있기 때문이다.
신경망 추론은 `predict_trials()`, 전체 조합 실행은 `select_and_evaluate()`를 보면 된다.
비교 Excel의 열 구성은 `organize_results.py`의 `force_tables()`/`id_tables()`에서 수정한다.

## 설정

- `input_columns`: 원하는 입력 열을 순서대로 지정. 기본은 길이4+장력4+상대각18.
- `force_columns`: 정답 Fx/Fy/Fz 열3개. `id_column`: 정답 ID 열.
- `source_force_unit`: CSV 힘 단위 mN 또는 N. 내부 학습은 N, Excel은 mN.
- `ft_sensor_calibration`: 무부하로 볼 Fx/Fy/Fz의 `[최솟값, 최댓값]`과 범위 단위 `unit`.
- `force_candidates`, `location_candidates`, `no_load_modes`: 비교할 모델/방식 목록.
- `force_params`, `location_params`: 모델별 너비·층수. 지원 항목은 `model_zoo.DEFAULT_PARAMS` 참고.
- `window_samples`: 현재 행을 포함한 이력 길이. 현재30은 최적화된 값이 아니다.
- `validation_fraction`: 각 train CSV의 뒷부분을 validation으로 남길 비율. 기본0.2.

기본 힘 모델은 **ID18 전용**이며 무부하에서도 연속 실측 힘을 학습한다. 위치는 ID1–18을 사용한다.
`masked`는 무부하의 위치 손실을 제외하고, `class0`는 무부하를 ID0으로 학습한다.
`ft_sensor_calibration`의 세 축 범위 안(양끝 포함)이면 무부하, 하나라도 밖이면 유부하다.
CSV의 `force_columns` 값과 직접 비교하며 자동 offset 차감·범위 확대·중간 불확실 구간은 없다.
기본 범위는 기존 무부하 판정을 유지하도록 CSV 좌표로 옮긴 비대칭 범위다.
0 중심 ±150mN으로 바꾸려면 해당 축을 `[-150, 150]`으로 지정하면 된다.
이 설정은 위치 정답 라벨에만 쓰며 힘 회귀의 원래 값과 부호는 보존한다.
새 모델에 적용하려면 새로 학습한다. 기존 모델 예측은 bundle에 저장된 당시 기준을 그대로 사용한다.

`datasets/train/*.csv` 각 파일의 숫자 행 앞80%가 train, 뒤20%가 validation이다.
`datasets/test/*.csv`는 사용자가 분리한 그대로 고정한다. 선택 X/Y의 빈칸·비수치·NaN/Inf 행을
제외하고 남은 행을 이어붙인다. Valid flag와 timestamp 간격으로 추가 제외하지 않는다.
창은 파일/분할 경계를 넘지 않으며 scaler는 train만으로 계산한다.
같은 녹화에서 잘라낸 test 성능과 별도 실험의 성능은 구별한다.

## 실행

```bash
# 최초 환경 설치: uv가 PATH에 있어야 한다.
bash scripts/setup_environment.sh

# 데이터 준비만 확인 (학습하지 않음)
bash scripts/hrm_python.sh train.py --config configs/train.yaml --check-data

# 학습: results/train/날짜_시간 생성
bash scripts/hrm_python.sh train.py --config configs/train.yaml

# 위 학습의 실제 날짜 폴더를 지정: 모든 조합의 test 평가
bash scripts/hrm_python.sh predict.py --train-dir results/train/학습날짜_시간

# 저장된 predictions.xlsx만 GT + 모델별 열로 정리 (모델 실행 없음)
bash scripts/hrm_python.sh organize_results.py results/predict/예측날짜_시간/predictions.xlsx

# 또는 전체 조합 test 예측부터 위 정리까지 한 번에 실행 (재학습 없음)
bash scripts/predict_and_organize.sh results/train/학습날짜_시간 --id-tolerance 2

# 저장 결과를 ±3 ID 기준으로 다시 정리 (학습/추론 없음)
bash scripts/hrm_python.sh organize_results.py results/predict/예측날짜_시간/predictions.xlsx --id-tolerance 3

# 수동 무부하 기준 확인/저장 (교정 CSV를 읽지 않음)
bash scripts/hrm_python.sh analyze_no_load.py --config configs/train.yaml

# 선택: 기존 센서 기록이 지정 범위 안에 얼마나 들어오는지 분석 (경계 변경 없음)
bash scripts/hrm_python.sh analyze_no_load.py --config configs/train.yaml --input datasets/aidin_FT_sensor_validation_2/csv/summary.csv

# 코드 검증
bash scripts/hrm_python.sh -m unittest discover -s tests -v
```

가상환경 활성화 후 일반 `python train.py ...`도 가능하다.
현재 PC의 GPU 라이브러리 우회는 실행 프로세스에만 적용한다.

## 결과

| 위치 | 주요 파일 |
|---|---|
| `results/train/날짜_시간/` | `comparison.csv`, `summary.json`, `validation.xlsx`, 설정·분할·교정·환경 기록 |
| 위 폴더의 `models/방식__force_모델__location_모델/` | `hrm_bundle.pt`, 학습 이력, validation 예측 배열 |
| `results/predict/날짜_시간/` | `comparison.csv`, `predictions.csv`, `summary.json`, `predictions.xlsx`, 상세 지표·출처 |

`hrm_bundle.pt`는 두 네트워크 가중치와 입력 순서·scaler·무부하 기준 등을 함께 저장한다.
최선 모델은 validation으로 선택하며 test 점수로 바꾸지 않는다. Predict 비교표의 `test_` 열은
모든 조합의 test 지표이고, `predictions.csv`는 방식별 validation 선택 모델의 행별 결과다.

Excel은 실행마다 하나이며 힘/ID/방식/모델별 시트로 나뉜다. 힘 시트 첫6열은
`gt_fx_mN`, `gt_fy_mN`, `gt_fz_mN`, `pred_fx_mN`, `pred_fy_mN`, `pred_fz_mN`이다.
파일·원본 행·시간·부하 상태도 남긴다. 학습 폴더의 Excel은 **validation 결과**다.
기본 구성은 모델 시트44개와 `_comparison`/`_models` 시트2개다. 행별 시트는 각 모델의
파트너를 설정 목록의 첫 모델로 고정한다. 모든242조합의 지표는 비교표에 보존하며,
대표 시트의 정확한 checkpoint와 파트너는 `_models`에 기록한다.

`organize_results.py`를 별도로 실행하면 입력 Excel 옆에 `organized_날짜_시간_id-tol-N/`을 만들고,
입력에 포함된 방식에 따라 다음 비교 파일을 저장한다. `predict.py`만 실행하면 원래의
`predictions.xlsx`까지 생성하며, 정리까지 자동 실행하려면 위 shell 명령을 사용한다.

- `force-estimation_loss-mask_id-tol-N_results.xlsx`: fx/fy/fz 시트, 첫 열 GT(mN), 다음 열 모델별 예측.
- `force-estimation_class0_id-tol-N_results.xlsx`: 같은 구성의 class0 힘 결과.
- `id-estimation_all-models_id-tol-N_results.xlsx`: 양방식 ID, 조건부 ID 오차/±n 성공, class0 부하 판정,
  검출 포함 ±n 성공과 구간 결과. GT 무부하 행의 ID 오차/±n 평가는 빈칸이다.

파일명과 기본 폴더명의 `N`에는 실제 `--id-tolerance` 값(예: 2, 3)이 들어간다. 힘값은 n과 무관하며 파일명은 같은 정리 실행을 구별하기 위한 표시다.

각 파일의 `_summary`는 힘 RMSE/MAE 또는 위치 정확도·검출 지표이고, `_rows`는 원본 행 대응이다.
모델 개수와 이름은 입력 시트를 따르며 원래 GT·예측값·부하 라벨을 보존한다.
정리에는 이 프로젝트의 Excel만 필요하며 CSV·checkpoint·현재 YAML을 다시 읽지 않는다.
`--id-tolerance N`은 정답 ID와 예측 위치 후보의 절대 차이가 N 이하인지를 계산하는
**평가 전용 옵션**이다. 기본2, 허용0–17이며0은 정확ID 일치다. 학습 loss나 예측값을 바꾸지 않는다.
예를 들어 N=3이면 `loss-mask_within3`, `class0_within3_conditional`,
`class0_within3_detected` 시트가 생성된다. 성공1/실패0/GT무부하 빈칸이다.
Class0 조건부 평가는 p0를 제외한 위치 후보를 사용하고, 검출 포함 평가는 최종ID0이면 실패다.
`_summary`에는 선택한 n과 그 지표를 기록하고 기존 정확ID/±1/±2 요약도 유지한다.
이 옵션은 정리된 Excel에만 적용하며 원본 predict 비교표나 validation 모델 선택을 변경하지 않는다.
`validation.xlsx`도 같은 옵션으로 정리할 수 있다. n을 바꿔 비교할 때 재학습/재예측은 필요 없다.
구간은 이전 비교와 같은 `1–4 / 5–10 / 11–18`로 고정된다. 필요하면
`--regions 1-8,9-17,18`처럼 명시할 수 있지만 test로 최선 경계를 고르는 기능은 없다.
단독 정리의 `--output 새폴더` 또는 shell의 두 번째 인자로 저장 위치를 지정할 수 있다.
기존 폴더·파일은 덮어쓰지 않는다. `validation.xlsx`도 같은 시트 형식이면 정리할 수 있다.

2026-10-05 추가 승인으로 **242조합 학습·test를 완료**했고 두 Excel의88모델시트를 전수 검산했다.
최신 [validation Excel](results/train/20261005_194129/validation.xlsx),
[test Excel](results/predict/20261005_194129/predictions.xlsx),
[모델별 test RMSE·MAE](results/predict/20261005_194129/force_axis_metrics.csv),
[선택 모델 범위별 요약](results/predict/20261005_194129/selected_model_summary.csv)을 참고한다.
Validation 선택은 힘MLP/위치Transformer이고 독립 ID18 test XYZ RMSE136.53mN이다.
Validation Excel은 약1,038MiB, test는171MiB이므로 MATLAB에서 필요한 시트만 읽을 수 있다.
자세한 성능·분할 해석·검증은 통합 기록39절에 있다. 기존 데이터·모델·결과는 보존했다.
이전 코드는 [정리 전 압축본](archive/code_before_simplification_20261005_172216.tar.gz)에 있다.
과거 `audited` 전처리/JSON 실행 재현에는 별도 폴더에서 보관 코드를 사용한다.
새 코드가 과거 모델의 전처리를 임의로 변경하지 않는다.

`datasets/`, `results/`, 가상환경, 로컬 GPU 보조 라이브러리는 Git 제외 대상이다.
다른 PC에서는 데이터·결과를 별도로 옮기고 환경을 설치한다.
