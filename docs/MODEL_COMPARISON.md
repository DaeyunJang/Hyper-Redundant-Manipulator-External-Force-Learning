# 기존 모델 검토 및 비교 계획

상태 갱신: 기존9개 구조와 small_gru/residual_tcn을 새 PyTorch 코드로 구현하여
실제 학습·평가를 진행 중이다. 아래는 최초 검토 기록이며 최신 구현/결과는 README와
results 보고서를 따른다. Ridge는 후속 후보로 남아 있으며 현재11종 실행에는 없다.

## 참조

원본: [model_zoo_30k.py](https://github.com/DaeyunJang/LSTM-force-estimation/blob/humble/scripts_model/model_zoo_30k.py), humble 브랜치, 2026-09-26 조회.
조회 파일 SHA-256: `4188925a5ee609096eed16ce8a51c494144a879f110534bea17f7ffd1afdf23f`.
브랜치는 변경될 수 있으므로 구현 시 참조 revision과 라이선스를 다시 확인한다.
TensorFlow/Keras builder 함수 9개이며 클래스 기반 정의가 아니다. 원본 출력은 fx/fy 2개다.

| 모델 키 | 원본 구조 | 기본 시퀀스 길이 |
|---|---|---:|
| mlp | Dense 208→104→52 | 1 |
| cnn | 길이1이면 Dense128; 길이>1이면 Conv1D64 두 층 + 평균 pooling | 1 |
| convmixer | 길이1이면 Dense128; 길이>1이면 Conv64 + depthwise + pointwise + 평균 pooling | 1 |
| resnet | 길이1이면 Dense128; 길이>1이면 Conv64 + residual block 두 개 + 평균 pooling | 1 |
| lstm | LSTM60→LSTM30→Dense32 | 5 |
| gru | GRU72→GRU36 | 5 |
| tcn | causal Conv64 세 층, kernel3, dilation1/2/4 + 평균 pooling | 5 |
| transformer | projection32, attention 2 heads/key_dim32, FF64, residual/LayerNorm + 평균 pooling | 5 |
| kalmannet | GRU96→Dense96 (KalmanNetLite) | 5 |

## 적용 결정과 제안

- 위 9개를 이번 프로젝트의 참조 모델 목록으로 사용한다. 입력 차원은 선택 그룹에서
  계산하고 출력은 XYZ 3개 또는 force3/load1/location18로 바꾼다. 이전 가중치를
  그대로 불러오는 호환성이나 기존 실험의 정확한 재현을 약속하지 않는다.
- CNN/ConvMixer/ResNet의 기본 길이1 경로는 동일한 Dense128 구조다. 이를 서로 다른
  세 종류의 합성곱 성능으로 해석하지 않는다. 해당 경로는 legacy_dense128로 식별하고,
  본 비교용 CNN/ConvMixer/ResNet은 과거 윈도우에 실제 시간축 합성곱을 적용하는
  별도 adapted 변형으로 구현할 계획이다. 왼쪽 padding 및 마지막 시점 출력을 기본으로 한다.
- KalmanNetLite는 GRU 기반 회귀 모델이며 물리 상태/관측 모델과 Kalman update가 없다.
  비교 결과에는 GRU96+MLP (legacy KalmanNetLite)로 표시한다. Kalman 정답 선택과 별개다.
- Transformer 원본에는 위치 인코딩과 causal mask가 없다. 과거~현재만 담은 윈도우의
  마지막 정답을 예측한다면 윈도우 내 양방향 attention 자체가 미래 데이터 누수는 아니다.
  다만 시간 순서 표현이 부족하므로 adapted 모델에는 위치 인코딩, causal mask 및
  마지막 시점 readout을 적용하는 안을 사용한다. 원본 key_dim32는 head당 차원이다.
- 원본 TCN은 residual TCN이 아니며 수용영역은 15샘플이다. 기존 계획의 residual
  TCN32(블록당 convolution 2개, 수용영역29)는 별도 추가 후보로 유지한다.
- 추가 후보: Ridge force-only 선형 기준 모델, 기존 계획의 작은 MLP128/64 및 GRU64.
  Ridge는 복잡한 모델이 단순 선형 관계보다 얼마나 개선되는지 확인하기 위한 기준이다.
  더 높은 정확도는 실험 전 보장하지 않는다.
- 원본 모델 9개와 추가 후보를 목록에 포함하되, 동등 구조 중복 실행은 피한다.
  시계열 길이5/30은 별도 비교 축으로 두고 각 비교 내 길이와 평가 시점을 맞춘다.
  MLP도 시계열 모델이 예측 가능한 동일한 마지막 행 집합에서 평가한다.
- 원본의 30k 명칭은 현재 입력/출력에서 파라미터 수를 보장하지 않는다. 모델별 실제
  파라미터 수, 학습 시간, batch1 추론 지연을 기록한다. 프레임워크 이식 시 recurrent
  bias/gate 및 padding/attention 차이를 검사한다. TensorFlow 강제 설치는 하지 않는다.

## 분할 방침

8:1:1은 독립 trial이 충분할 때 가능한 초기 후보다. 예시 설정에도 반영한다.
파일을 새로 복사하거나 test만을 위해 반드시 새 실험을 수집할 필요는 없다.
기존 자료에서 trial_group_id 단위로 train/validation/test를 고정하면 된다.

- train: 가중치 학습 및 scaler 추정. validation: 모델/설정 선택과 early stopping.
- test: 비교할 설정을 고정한 후 최종 성능 보고. test를 보며 모델/임계값을 재조정하지 않는다.
- 예: 각 segment에 독립 trial 10개가 있다면 8/1/1로 배정 가능하다. segment별 힘 크기,
  방향 등의 분포도 확인한다. 같은 연속 수집을 여러 파일로 나눈 것은 독립 trial이 아니다.
- 비율은 그룹 배정 목표로, 길이가 다르면 행 수 비율은 정확히 8:1:1이 아닐 수 있다.
- 각 segment당 한 trial뿐이면 전체 위치의 독립 train/validation/test 확보가 어렵다.
  이때 추가 반복 수집 또는 제한을 밝힌 다른 평가 계획이 필요하다. 행 무작위 분할로
  해결하지 않는다. 미관측 segment 평가와 알려진 segment의 반복 실험 평가는 별개다.
- scaler와 window 생성 전에 그룹을 나눈다. 교정 및 교정 검증 자료는 최종 test와 분리한다.
  다른 날/초기 장력의 새 수집은 추후 외부 일반화 평가로 유용하다.

근거: [scikit-learn 교차 검증 및 그룹 분할](https://scikit-learn.org/stable/modules/cross_validation.html),
[Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
