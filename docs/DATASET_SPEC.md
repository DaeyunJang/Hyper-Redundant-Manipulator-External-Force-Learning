# 데이터 계약

기준: HRM record_pkg의 2026-09-26 summary exporter. 현재 268열이나 **열 개수와
위치로 파싱하지 않는다.** 헤더 이름, summary.schema.json, manifest.json,
session.json의 frozen snapshot을 함께 확인한다. 이 문서는 향후 로더 구현 규약이다.

## 1. 읽기 전용 원본과 실험 식별

- CSV, session.json, recording_config.json, summary.schema.json, CSV manifest를
  입력으로 받는다. 원본 DB3/CSV/이미지를 수정하지 않는다.
- 하나의 실제 연속 실험을 `trial_group_id`로 식별한다. 여러 CSV가 같은 bag/session에서
  나왔다면 같은 그룹이다. 경로 변경이나 csv_recovered로 별도 실험처럼 세지 않는다.
- 데이터셋 목록에는 정확한 summary 경로를 지정한다. `record/**/summary.csv`를 모두
  무조건 학습하면 원본/복구본/가공본 중복으로 train-test leakage가 생길 수 있다.
- 폴더명과 CSV 라벨이 다르면 자동 보정하지 않고 보고한다. 저장 ID의 기준은
  contact_segment_id와 session.json.snapshot.contact_segment_id의 일치 여부다.
- 분석 산출물에 입력 파일 SHA-256, 세션ID, 선택 열, 포함/제외 이유와 원래 행번호를 남긴다.

## 2. 입력 그룹

아래 그룹명은 새 프로젝트의 registry 이름이며 CSV 헤더 자체는 오른쪽과 같다.
인덱스는 **숫자 순서**로 확장한다. `1,10,11,...,2` 사전식 정렬을 하지 않는다.

| 그룹명 | 실제 열 (범위 포함) | 수 | 기본 |
|---|---|---:|---|
| wire_length | `wire.Cable #1 length` … `wire.Cable #4 length` | 4 | ON |
| loadcell_tension | `loadcell.Loadcell #1 tension` … `#4 tension` | 4 | ON |
| relative_angle | `relative_angle_1` … `relative_angle_18` | 18 | ON |
| motor_position | `motor.Motor #1 position [count]` … `#4 position [count]` | 4 | OFF |
| wire_velocity | `wire_velocity.Cable #1 velocity` … `#4 velocity` | 4 | OFF |
| relative_angular_velocity | `relative_angular_velocity_1_rad_s` … `_18_rad_s` | 18 | OFF |
| pan_relative | `pan_relative_01_rad` … `_18_rad` | 18 | OFF |
| tilt_relative | `tilt_relative_01_rad` … `_18_rad` | 18 | OFF |
| pan_absolute | `pan_absolute_01_rad` … `_18_rad` | 18 | OFF |
| tilt_absolute | `tilt_absolute_01_rad` … `_18_rad` | 18 | OFF |

기본 입력은 4+4+18=26. 모터 위치와 케이블 길이는 중복 정보일 수 있어 기본은 길이만
사용한다. 두 그룹 동시 사용을 금지할 필요는 없지만 명시적인 비교 실험으로 남긴다.
설정에서 그룹 순서와 on/off를 바꾸면 차원을 자동 계산하고 중복 열은 오류로 알린다.
선택하지 않은 그룹의 결측은 해당 실험의 행 탈락 사유가 아니다.

하드웨어는 고정 길이 구간 1개 + 움직이는 관절 18개. relative_angle의 실제 선택은
1-based 홀수 tilt, 짝수 pan이다. 0과 음수는 유효하며 크기/절댓값/비영값으로 축을 고르지
않는다. 원래 pan/tilt 배열은 각 18칸이지 36개 관절이 아니다. absolute 배열은 hrm_base에서
본 방향각으로, relative 각도의 단순 누적합이 아니다. 각속도도 동일한 실제 축 순서다.

`wire.*`는 **모터 피드백으로 환산한 현재 케이블 길이**다. 목표 tip → IK → 모터 명령의
목표 케이블 길이(`/kinematics/target_wire_length`)와 구분한다.

## 3. 정답 선택: 기본 Kalman, 선택 raw

기본 force target은 `kalman` + `hrm_base`:

```text
fts_kalman.aligned_fx, fts_kalman.aligned_fy, fts_kalman.aligned_fz
```

source를 `raw`로 바꾸면:

```text
fts.aligned_fx, fts.aligned_fy, fts.aligned_fz
```

2026-09-26 사용자 확정: 학습/평가 정답은 aligned XYZ의 저장된 부호를 유지한다.
기존 Kalman 기본/raw 선택 방침은 유지한다. 실제 HRM 제어 연결에서는 물리 단위로
역정규화한 추론 XYZ에 각 축 공통으로 -1을 곱한다: `F_control = -F_pred_aligned`.
이 변환은 나중에 매니퓰레이터 제어 코드에서 한 번만 적용한다. 학습 정답이나
현재 모델 출력에 미리 부호를 뒤집지 않는다. 배포 bundle에도 이 규약을 기록한다.

선택한 prefix에 대해 finite XYZ, `.matched=True`, `.aligned_force_valid=True`,
`.aligned_frame_id=hrm_base` 및 해당 세션의 좌표/단위/타이밍 조건을 검증한다.
누락되면 반대 소스나 sensor-frame 힘으로 **자동 fallback하지 않는다**.

- `raw`는 `/fts_data`(non-Kalman)라는 뜻이다. 이 신호는 이미 영점 오프셋 보정이
  있으며 설정에 따라 LPF/MAF가 적용될 수 있다. ADC 생데이터라고 부르지 않는다.
- 실제 정렬 정보는 **session.json.snapshot.force_alignment 및 CSV manifest**다.
  recording_config.json.force_alignment는 시작 기본값일 수 있어 현재 세션의 실제 선택을
  대신하지 못한다. 실제 예: 기본 enabled=false여도 snapshot enabled=true인 세션이 있다.
- 축 정렬은 단위 변환, 힘의 작용/반작용 부호 보정, 센서 교정, torque 변환이 아니다.
  이번 프로젝트의 제어 연결 부호는 위 사용자 결정(-1)을 따른다. 각 세션의 실제
  저장 규약이 이에 대응하는지는 메타데이터로 확인하며 단위 검증은 별도로 수행한다.
- `.aligned_force_valid`는 수치 계산 가능 여부, `.matched`는 시간 연결 여부다.
  CAN 미연결 등으로 들어온 숫자 0을 실제 무부하 측정이라고 보증하지 않는다.
- raw/Kalman 변경 시 force target, force validity, 무부하 교정 소스, 파생 하중 라벨 및
  보고서 소스도 일관되게 바꾼다. 비교용 결과는 서로 다른 실험 run으로 저장한다.
- sensor-frame 대안은 `fts.fx/fy/fz`, `fts_kalman.fx/fy/fz`. 별도 명시적 task/frame 설정에서만
  허용한다. 기본 hrm_base task와 섞지 않는다. registry의 expected_frame=null은
  모든 frame 허용이 아니라, 데이터셋에서 검증할 header frame을 아직 지정하지 않았다는 뜻이다.
- torque 열은 sensor-frame `tx/ty/tz`이고 CSV에서 소수점 한 자리로 표현된다.
  aligned torque가 있다고 가정하거나 힘 norm에 토크를 합치지 않는다.

## 4. 단위와 스케일

Exporter는 원본 단위를 유지한다. 확인한 세션 설명에는 모터 count, 케이블 길이 mm,
장력 g, 각도 rad, 각속도 rad/s, F/T는 legacy mN 및 mN*m(교정 확인 필요)라고 되어 있다.
다른 데이터도 자동으로 같다고 가정하지 않는다. 케이블 속도 단위도 upstream 확인 후 명시한다.

- 데이터셋 manifest에 확인한 source units, 변환 계수, source/target frame을 넣는다.
- 물리 단위 변환과 학습용 standardization은 다른 처리다.
- 50 mN = 0.05 N. 단위가 확인되지 않은 데이터에 50 또는 0.05 임계값을 적용하지 않는다.
- 축별 정규화 통계는 train에서만 구하고 model bundle에 고정한다.
- 미확인 값은 null/unknown으로 남기고 물리적인 mN 성능/임계값 보고를 중단한다.

## 5. 실험 라벨과 학습용 하중 라벨

`contact_segment_id`는 원본 실험 라벨이다. 센서값에 따라 원본을 수정하지 않는다.

| 저장 ID | 실제/유효 측정 상태 | load 정답 | location 정답/loss |
|---|---|---|---|
| 9 | 교정 기준을 넘는 부하 | 1 | ID9, 사용 |
| 9 | 검출 기준 이하 | 0 | 해당 없음, loss 제외 |
| 0 | 확인된 무부하 | 0 | 해당 없음, loss 제외 |
| 0 또는 공란 | 유효한 부하이나 위치 불명 | 1 | 위치 불명, loss 제외 |
| 임의 ID | 힘 누락/센서 비정상/경계가 불확실 | unknown 또는 ambiguity | 해당 loss 제외 |

ID0만으로 실제 무부하를 입증하지 않는다. 지정한 calibration 구간은 작업자가 실제
외력이 없음을 확인해야 한다. unknown과 below-threshold를 구분한다. 유효하지만 경계에
가까운 힘은 회귀에 계속 사용할 수 있다. 무부하 힘 정답을 임의로 0으로 덮어쓰지 않는다.

모델 입력에 force 정답/파생 norm/load label/contact ID/파일명/세션ID를 넣지 않는다.
태그/추정tip/FK/설정 등은 다른 연구와 검증용으로 보존하며 기본 force 입력에 자동 포함하지 않는다.

## 6. 시간: 모델 입력에서는 제외, 데이터 준비에서는 확인

각 행은 각도 이미지의 source timestamp를 기준으로 한 연결 결과다. 한 파일이 순서대로
저장돼도 누락, 처리 실패, 프레임 간격 변화, 필터 지연은 있을 수 있다.

- `source_time_ns`: angle anchor 시각. int64/정수 문자열로 읽고 float64로 바꾸지 않는다.
  차이를 정수로 계산한 다음 초로 변환한다. 과거 파일에 지수 표기/반올림이 있으면
  정확한 원본에서 재export하거나 손실을 보고한다. nanosecond 정밀도를 지어내지 않는다.
- `bag_receive_time_ns`: angle receipt 시각. `elapsed_s` 시작이 0이 아닐 수 있다.
- motor/loadcell/force는 source stamp로 연결된다. wire/velocity는 headerless이므로
  receipt 시각으로 연결되며 source_time_ns 공란이 정상이다.
- 기본 nearest 연결 ±25 ms는 과거/미래 샘플 모두 선택 가능하고 재사용도 가능하다.
  시계 동기화나 필터 지연 보정, causal 보장을 의미하지 않는다.
- `.time_difference_ms > 0`은 해당 기준에서 anchor 이후의 샘플이다. 실시간 적용 시
  동일한 bounded buffering을 재현할지, 원본 토픽으로 causal 정렬을 다시 할지 명시한다.
  숨겨진 미래 정보를 사용하는 전처리로 실시간 성능을 과대평가하지 않는다.

각 세션에서 증가 여부, dt 분포, 누락된 선택 열, 시간 공백, 매칭 허용차를 검사한다.
원래 row index와 연속 구간 경계를 보존한다. reject한 행을 지운 뒤 앞뒤를 붙여 연속
윈도우로 만들지 않는다. 초기 예시는 median dt의 1.5배 초과를 구간 분리 후보로 두되
실제 프레임 주기/누락에 맞게 검증해 고정하고 보고한다. 30 Hz를 무조건 가정하지 않는다.

비시계열 모델은 유효한 각 행을 쓸 수 있지만 그룹 분할/센서 매칭 검사는 필요하다.
시계열은 같은 실험·연속 구간 안에서만 과거→현재 윈도우를 만든다. 단순히 모든 CSV를
이어 붙인 뒤 windowing하지 않는다. 필요한 경우 시간에 따른 재표본화는 별도 명시 옵션이며
실시간에 재현 가능한 방식만 쓴다. timestamp 열 자체는 기본 X에 넣지 않는다.

## 7. 결측/품질 규칙

현재 exporter는 초기 motor/장력/raw F/T/wire/relative angle이 확보되기 전 행만 제외한다.
**Kalman F/T, 각속도, 케이블 속도는 기본 startup gate가 보장하지 않는다.**
시작 후 결측도 남으므로 학습 측에서 선택한 X/Y를 다시 검사한다.

0과 음수는 정상 숫자다. 빈칸/NaN/Inf/불일치 frame/센서 오류를 0으로 채우지 않는다.
CSV의 True/False는 명시적 문자열 파서로 읽는다. bool("False")처럼 일반 truthiness를
사용하지 않는다. 허용하지 않은 값/빈칸은 validity unknown으로 보고하고 True로 추측하지 않는다.
사용하지 않는 tag 열이 비었다고 행을 삭제하지 않는다. 필터 상태 초기화/워밍업 처리도
데이터 준비 규칙에 명시하고 원본 기록에서 추정할 수 없는 상태를 복원했다고 주장하지 않는다.
CSV export complete는 변환 성공이지 무결한 센서·물리교정·학습 준비 완료가 아니다.

## 8. 분할과 공정 비교

- 실제 trial 그룹을 train/validation/test로 먼저 나눈 뒤 scaler/window를 만든다.
- 입력 조합 비교는 같은 그룹 분할/정답/윈도우 및 가능하면 동일한 유효 샘플 교집합을 쓴다.
  조건별 가용 데이터로 추가 실험하면 샘플 수 차이를 별도로 보고한다.
- ID별 독립 반복 실험이 부족하면 모든 ID를 포함한 독립 평가가 불가능할 수 있다.
  이를 피하려고 한 사인 실험의 인접/중첩 윈도우를 임의로 train/test에 섞지 않는다.
- 정규화·하중 기준·하이퍼파라미터를 test 결과로 조정하지 않는다. 교정 자료는 독립 지정한다.

## 확인에 사용한 기존 코드

`../Hyper-Redundant-Manipulator/src/record_pkg/record_pkg/summary_csv.py`,
`experiment_labels.py`, `../Hyper-Redundant-Manipulator/src/record_pkg/README.md`.
공유 프로젝트 이름이 달라지면 경로를 설정으로 바꾸고 이 문서를 자동 진실로 가정하지 않는다.

## 2026-09-27 명시적 CSV 라벨 수정 예외

front_1의 사용자 수정 CSV는 contact_segment_id18, frozen 메타데이터는0이다.
사용자의 ID18 확인을 근거로 label_overrides에서 original_id(메타데이터), csv_id,
training_id를 분리했다. csv_id가 메타데이터와 다르면 session_id와 summary_sha256,
basis가 모두 명시되고 실제 입력과 일치해야만 허용한다. CSV 모든행의 동일라벨도 검증한다.
기존 original_id→training_id override의 CSV/메타데이터 일치 규칙은 유지한다.
감사 info.source_id는 frozen 메타데이터, info.csv_contact_segment_id 및 예측의
source_contact_segment_id는 실제 CSV 라벨이다. 원본 파일은 덮어쓰지 않는다.

## 2026-09-27 명시적 trainsets/testsets 탐색

폴더 모드는 지정된 trainsets/testsets 하위의 정확한 csv/summary.csv만 탐색하고 메타데이터를
검증한다. 녹화 ID·CSV hash 중복 및 보호 test를 검사한 후 명시 목록/해시를 결과에 고정한다.
이는 임의 record 전체 탐색과 다르며 원본/복구본 복사를 각각 독립 녹화로 사용하지 않는다.
trainsets에서만 녹화 단위 train/validation을 만들고 testsets는 예측 전용이다.
상세와 현재 이동이 필요한 과거 test는 [DATASET_FOLDERS.md](DATASET_FOLDERS.md) 참조.
