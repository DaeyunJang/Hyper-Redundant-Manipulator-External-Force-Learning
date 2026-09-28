# 데이터 감사 — 2026-09-26

이번 요청의 datasets/20260926_f_ext_datasets 안의 37개 csv/summary.csv 및 각
session.json, recording_config.json, csv/manifest.json, csv/summary.schema.json을
읽기 전용으로 검사했다. 아래는 **윈도우 구성 전** 수치이며 학습 성능이 아니다.

## 핵심 결과

- 세션 37개, CSV마다 268열, 합계 206,264행이다. 기본 26입력과 Kalman aligned XYZ,
  선택 신호 matched/force validity/frame 조건을 만족하는 행은 206,232개다.
- 입력은 케이블 길이 4 + 장력 4 + 상대각 18이다. 이미지·태그·FK 등 사용하지 않는
  열의 결측은 제외 사유가 아니다. 전 세션의 상대각은 홀수 tilt / 짝수 pan과 일치한다.
- 고유 session ID 37개, 고유 summary SHA-256 37개이며 세션 시각 구간은 겹치지 않는다.
- 모든 csv/ manifest, integrity, schema는 complete이고 실제 CSV 헤더와 일치한다.
  다만 **오래된 metadata 행수와 잘못 정렬된 anchor 열이 4개 세션**에서 발견됐다.
- **seg-id-18_right_2의 CSV·snapshot·manifest·schema 라벨은 모두 1**이다.
  사용자가 이번 대화에서 이 폴더를 끝단 학습 데이터로 명시했으므로 원본 ID1을 보존하는
  실험용 ID18 override를 명시적으로 적용한다. 실제 ID18에서 측정했는지는 재확인할 가정이다.
  나머지 36개 폴더는 저장 라벨과 이름이 일치한다.

## 끝단 세션

| 역할 | 폴더 접미사 | 세션 ID | 원본 행 | 선택 열 유효 행 | 저장 ID |
|---|---|---|---:|---:|---:|
| 개발 | seg-id-18_left | 20260926_202928_638928 | 9,949 | 9,949 | 18 |
| 개발 | seg-id-18_right_2 | 20260926_194602_588445 | 6,905 | 6,905 | **1** |
| 독립 test | seg-id-18_right | 20260926_173345_163794 | 5,770 | 5,740 | 18 |

개발용 총 16,854행은 두 세션뿐이다. 두 세션 모두 train에 쓰면서 validation을 확보하기
위해 각 세션 시간 블록과 경계 purge를 사용한다. 이는 **독립 세션 validation보다 약한
검증**이다. 중첩 window를 만든 뒤 무작위 분할하지 않고 scaler는 실제 train에만 fit한다.
ID18 right 전체는 test로 고정한다. 실제 분할 수·purge 간격은 실행 manifest에서 확인한다.

끝단 모델의 ID18 출력은 고정 task 라벨이며 위치 구별 성능을 입증하지 않는다.
ID1~18 확장 모델에서 별도 위치 head를 학습하고 유부하 test의 ID18 인식을 평가해야 한다.

## 단위·정렬 근거

- 정답은 fts_kalman.aligned_fx/fy/fz, frame은 hrm_base, 부호는 저장값 그대로다.
  raw 모드는 fts.aligned_fx/fy/fz와 해당 소스 validity를 함께 전환한다.
- 37개 recording config의 notes.source_units는 모두 케이블 mm, 장력 g, 각도 rad와
  F/T의 “legacy firmware declares mN; verify calibration”을 명시한다.
- 기존 로봇 코드의 src/serial_pkg/esp32/esp32_sensor_hub/src/ft_sensor_can.cpp
  57~75행은 Force[N]=raw/1000-30, Force[mN]=raw-30000을 설명하며 후자를 구현한다.
- 같은 저장소의 src/serial_pkg/serial_pkg/serial_read.py 260~312행은 offset/filter만
  적용하고 단위 스케일을 바꾸지 않는다. 181~194행은 해당 raw/Kalman 힘을 그대로 발행한다.
- 따라서 이번 기록값의 **코드상 단위는 mN**으로 일관된다. 알려진 추로 물리 교정을
  다시 검증했다는 뜻은 아니다. 센서 이득·부착 상태의 정확도는 별도 문제다.
- left 18개 세션은 [-y,-x,-z], right/right_2 19개는 [+y,-x,+z] rotation이다.
  snapshot과 manifest의 enabled=true, units=unchanged를 기준으로 한다.
  recording_config의 시작 기본값 enabled=false는 실제 세션 설정이 아니다.
- 시작 filter snapshot은 37개 모두 LPF=false, MAF=false이다. Kalman은 별도 경로다.
  시작 snapshot만으로 실행 중 필터 상태 전체를 보증하지 않는다.
- HRM 제어 연결에서는 역정규화된 aligned XYZ에 -1을 한 번만 곱한다.
  현재 학습 정답과 추론 결과는 이 제어용 부호 변환을 미리 하지 않는다.

## 시각 열 오류와 검증형 복원

다음 네 summary는 앞쪽 anchor timestamp/receipt/elapsed와 나머지 신호가 서로
다른 위치에서 시작한다. F/T matched=True만 믿으면 드러나지 않는 문제다.
센서 source timestamp와 잘못된 anchor 차이는 아래와 같으며, 저장된
time_difference_ms의 약 ±3ms와 모순된다.

| 폴더 접미사 | schema/manifest 행 | 실제 행 | angle 원본 시작 offset | 잘못된 anchor 기준 Kalman 시각차 중앙값 |
|---|---:|---:|---:|---:|
| seg-id-15_right | 5,649 | 5,596 | 53행 | 1,767.19 ms |
| seg-id-16_right | 5,008 | 5,005 | 3행 | 100.07 ms |
| seg-id-17_right | 5,205 | 5,175 | 30행 | 1,000.38 ms |
| seg-id-18_right | 5,799 | 5,770 | 29행 | 967.32 ms |

각 폴더 원본 csv/estimated_segment_angle__*.csv의 위 offset 이후 **18개 active 상대각을
모든 행에서** summary와 비교했다. 최대 절대 차이 5.14e-16 rad로 CSV 표기 수준이며
모두 일치한다. 이 행에 해당하는 원본 angle timestamp를 쓰면 Kalman timestamp 차이는
전 네 세션에서 ±2.81ms 이내다. summary의 estimated_tip.source_time_ns도 원본 angle
stamp와 반올림 오차 약 5.34µs 이내로 일치한다. 입력/정답 pairing을 이동할 필요는 없고
앞쪽 anchor 열만 다른 행을 가리킨다는 검증 결과다.

[time_repair.py](../hrm_force/time_repair.py)는 이 네 폴더와 frozen session ID만 허용한다.
schema/manifest/실제 행수를 검사하고, 모든 angle 값을 1e-12 rad 허용오차로 재대조한 뒤
파생 자료의 source anchor를 원본 int64 angle timestamp로 복원한다. raw/Kalman sensor
stamp가 복원 anchor와 ±25.01ms 이내인지 독립적으로 확인한다. 원본 CSV, 입력, 정답,
행 순서는 변경하지 않는다. 단 하나의 angle이라도 다르면 복원을 거부한다.

반환 evidence에는 원본 angle CSV의 SHA-256, offset, 비교 수, 최대 오차, 복원 후 센서
시각차와 정확한 anchor 범위가 있다. 이 동작은 loader의 명시적 known_trimmed_exports
설정을 통해서만 실행한다. 다른 파일에 행수 차이만 보고 자동 일반화하지 않는다.

네 summary는 timestamp를 지수 표기로 저장하면서 이미 약 10µs 단위로 반올림했다.
Decimal 파싱은 저장 숫자를 추가 손실 없이 읽을 뿐 잃은 ns를 되살리지 않는다.
정확한 anchor는 검증된 원본 angle CSV에서 가져오며 sensor stamp의 반올림은 남아 있다.
과거 행 감소·열 이동의 작업 원인은 확인되지 않았다. 카메라 노출 동기화나 필터 지연을
교정한 작업으로 해석해서는 안 된다.

## 결측·공백·복구 출력

- ID2 left의 0-based row 0: Kalman XYZ 1행 누락. raw는 유효하다.
- ID12 left의 row 1: 장력 4개 1행 누락.
- ID18 right의 row 0~29: 케이블 길이 4개와 wire.matched 30행 누락.
- 누락을 0으로 채우지 않는다. 제외 행, 큰 시각 공백, 세션 경계를 window가 넘지 않는다.
- anchor 간격 중앙값은 약 33.34ms이다. 전체 >100ms 공백은 12개, 최대 약266.7ms다.
  세 끝단 세션 및 시각 복원 대상 네 세션에는 >100ms 공백이 없다.
  실제 loader는 더 엄격한 gap_factor를 적용할 수 있어 window 수는 manifest가 기준이다.
- ID18 left의 현재 csv/summary.csv는 9,949행의 완성 복구 출력이다. csv_legacy는 제외한다.
  RECOVERY.md의 과거 csv_recovered 경로와 현재 재정리 상태가 다르다.
  session.json의 postprocess=running은 과거 중단 기록이고 현재 csv manifest는 complete다.
- 복구 left의 태그 자세/crop depth 부재는 이번 숫자26개 입력을 탈락시키는 사유가 아니다.

## 무부하 판정의 해석

사용자 반폭을 aligned XYZ에 [45.4,43.6,72.9]mN으로 직접 적용한다. 세 축 모두 절댓값이
반폭 이하이면 무부하이고 하나라도 초과하면 유부하다. 이는 **사용자 제공 Kalman 후
표준편차의 1배 반폭**이며 95% 개별 샘플 범위나 평균의 신뢰구간이 아니다.

본 감사에서 새 영점/오프셋을 추정하지 않았고 무부하 행의 force 정답을 0으로 덮어쓰지
않았다. raw 모드에 Kalman 기준을 조용히 재사용해서는 안 된다. 제공된 축이 sensor-frame
기준인지 aligned 기준인지는 별도 증거가 없어 **aligned 축의 반폭으로 해석**한다.
Fx/Fy가 정렬에서 서로 바뀌므로 차후 교정 기록의 축 기준도 확인해야 한다.

## 전체 세션

표의 유효 행은 source label을 자동 변경하지 않고 계산한 숫자다.

| 폴더 접미사 | 세션 ID | 저장 ID | 행 | 유효 | >100ms 공백 |
|---|---|---:|---:|---:|---:|
| seg-id-1_left | 20260926_221939_163433 | 1 | 2,050 | 2,050 | 1 |
| seg-id-1_right | 20260926_194059_958366 | 1 | 4,702 | 4,702 | 1 |
| seg-id-2_left | 20260926_221701_537927 | 2 | 3,297 | 3,296 | 0 |
| seg-id-2_right | 20260926_193748_086603 | 2 | 4,289 | 4,289 | 0 |
| seg-id-3_left | 20260926_221349_366437 | 3 | 3,838 | 3,838 | 0 |
| seg-id-3_right | 20260926_193144_191327 | 3 | 4,247 | 4,247 | 0 |
| seg-id-4_left | 20260926_220509_041238 | 4 | 4,896 | 4,896 | 0 |
| seg-id-4_right | 20260926_192818_965271 | 4 | 4,278 | 4,278 | 0 |
| seg-id-5_left | 20260926_220049_012849 | 5 | 5,111 | 5,111 | 0 |
| seg-id-5_right | 20260926_192433_139097 | 5 | 4,457 | 4,457 | 0 |
| seg-id-6_left | 20260926_215600_442707 | 6 | 5,238 | 5,238 | 1 |
| seg-id-6_right | 20260926_192119_416060 | 6 | 4,027 | 4,027 | 0 |
| seg-id-7_left | 20260926_215126_408298 | 7 | 6,399 | 6,399 | 0 |
| seg-id-7_right | 20260926_191300_259158 | 7 | 5,226 | 5,226 | 1 |
| seg-id-8_left | 20260926_214527_689765 | 8 | 6,637 | 6,637 | 0 |
| seg-id-8_right | 20260926_190236_910623 | 8 | 5,630 | 5,630 | 1 |
| seg-id-9_left | 20260926_214002_965334 | 9 | 6,705 | 6,705 | 1 |
| seg-id-9_right | 20260926_185308_395345 | 9 | 6,217 | 6,217 | 1 |
| seg-id-10_left | 20260926_212818_284417 | 10 | 6,234 | 6,234 | 1 |
| seg-id-10_right | 20260926_184614_810131 | 10 | 6,293 | 6,293 | 0 |
| seg-id-11_left | 20260926_212239_563450 | 11 | 6,263 | 6,263 | 0 |
| seg-id-11_right | 20260926_184150_408179 | 11 | 4,996 | 4,996 | 0 |
| seg-id-12_left | 20260926_211722_313452 | 12 | 7,403 | 7,402 | 1 |
| seg-id-12_right | 20260926_183818_269347 | 12 | 4,443 | 4,443 | 1 |
| seg-id-13_left | 20260926_211213_939412 | 13 | 7,437 | 7,437 | 1 |
| seg-id-13_right | 20260926_183454_860859 | 13 | 4,479 | 4,479 | 0 |
| seg-id-14_left | 20260926_210702_185369 | 14 | 7,446 | 7,446 | 0 |
| seg-id-14_right | 20260926_182723_988066 | 14 | 4,949 | 4,949 | 0 |
| seg-id-15_left | 20260926_210126_824285 | 15 | 7,398 | 7,398 | 0 |
| seg-id-15_right | 20260926_175958_063786 | 15 | 5,596 | 5,596 | 0 |
| seg-id-16_left | 20260926_205636_364541 | 16 | 6,048 | 6,048 | 1 |
| seg-id-16_right | 20260926_174832_441013 | 16 | 5,005 | 5,005 | 0 |
| seg-id-17_left | 20260926_205108_305565 | 17 | 7,231 | 7,231 | 0 |
| seg-id-17_right | 20260926_173806_037702 | 17 | 5,175 | 5,175 | 0 |
| seg-id-18_left | 20260926_202928_638928 | 18 | 9,949 | 9,949 | 0 |
| seg-id-18_right | 20260926_173345_163794 | 18 | 5,770 | 5,740 | 0 |
| seg-id-18_right_2 | 20260926_194602_588445 | 1 | 6,905 | 6,905 | 0 |

상세 수치와 SHA-256은 [DATA_AUDIT.csv](DATA_AUDIT.csv)에 보관했다. 감사 전후 summary,
session, schema, manifest 총148개 파일의 hash가 같음을 확인했다. 원본은 수정하지 않았다.

재현 가능한 합성 테스트 5개는 [test_time_repair.py](../tests/test_time_repair.py)에 있다.
실행 명령: /home/daeyun/HRM_env/bin/python -m unittest discover -s tests -p test_time_repair.py -v

정확한 int64 복원, 원본 hash 보존, angle 불일치 거부, 잘못된 센서 시각 거부, 미등록/행수
불일치 거부, angle 제외 입력 조합의 검증을 포함하며 통과했다. 실제 네 세션도 모두 복원
성공했고 각도 하나를 변경한 메모리 dataframe은 모두 거부되는 것을 확인했다.
