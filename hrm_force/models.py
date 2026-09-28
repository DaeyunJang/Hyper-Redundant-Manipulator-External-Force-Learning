"""끝단 힘 및 조건부 접촉 위치 비교를 위한 작은 PyTorch model zoo.

입력은 모든 모델에서 (batch, time, feature)이고, 출력은 윈도우의 마지막 시점이다.
MLP는 마지막 입력만 사용하며 나머지 모델은 현재와 과거 입력을 사용한다.
모든 convolution은 왼쪽에만 padding한다. 시간축 통계를 섞는 BatchNorm,
양방향 RNN, 미래 입력을 사용하는 필터는 사용하지 않는다.

기존 model_zoo_30k.py의 구조 설명을 참고한 새 구현이다. TensorFlow 가중치나
과거 결과와 호환되지는 않는다. CNN/ConvMixer/ResNet은 실제 시간축 convolution,
TCN은 원본의 non-residual dilation 1/2/4, residual_tcn은 별도 32-channel 구조다.
Transformer는 d_model=32, 2 heads (각 16차원), 위치 인코딩 및 causal mask를 쓴다.
KalmanNetLite라는 기존 이름은 물리 Kalman update가 없는 GRU96+MLP를 뜻한다.
힘의 단위 변환, 영점/부호 변환 및 무부하 판정은 모델 밖에서 수행한다.
"""
from __future__ import annotations

import math
from typing import Dict

import torch
from torch import Tensor, nn
from torch.nn import functional as F


MODEL_NAMES = (
    "mlp", "cnn", "convmixer", "resnet", "lstm", "gru", "tcn",
    "transformer", "kalmannet", "small_gru", "residual_tcn",
)
MODEL_DESCRIPTIONS = {
    "mlp": "MLP208/104/52 (마지막 시점만)",
    "cnn": "Causal CNN64, kernel3 × 2",
    "convmixer": "Causal ConvMixer64, depthwise kernel5",
    "resnet": "Causal ResNet64, residual blocks × 2",
    "lstm": "LSTM60 → LSTM30 → Dense32",
    "gru": "GRU72 → GRU36",
    "tcn": "Causal TCN64, dilation1/2/4 (수용영역15)",
    "transformer": "Transformer32, heads2, FF64, causal + sinusoidal position",
    "kalmannet": "GRU96 + MLP96 (legacy KalmanNetLite; Kalman filter 아님)",
    "small_gru": "GRU64, 1 layer",
    "residual_tcn": "Residual causal TCN32, dilation1/2/4 (수용영역29)",
}


class CausalConv1d(nn.Conv1d):
    """입력 B,C,T에서 과거 값만 읽고 시간 길이를 보존한다."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int,
                 dilation: int = 1, groups: int = 1):
        super().__init__(in_channels, out_channels, kernel_size,
                         dilation=dilation, groups=groups, padding=0)
        self.left_padding = dilation * (kernel_size - 1)

    def forward(self, x: Tensor) -> Tensor:
        return super().forward(F.pad(x, (self.left_padding, 0)))


class ChannelLayerNorm(nn.Module):
    """시간 위치마다 독립적으로 channel만 정규화한다 (입력 B,C,T)."""

    def __init__(self, channels: int):
        super().__init__()
        self.norm = nn.LayerNorm(channels)

    def forward(self, x: Tensor) -> Tensor:
        return self.norm(x.transpose(1, 2)).transpose(1, 2)


class ResidualBlock(nn.Module):
    def __init__(self, channels: int, dilation: int = 1):
        super().__init__()
        self.path = nn.Sequential(
            CausalConv1d(channels, channels, 3, dilation=dilation),
            nn.ReLU(),
            CausalConv1d(channels, channels, 3, dilation=dilation),
        )

    def forward(self, x: Tensor) -> Tensor:
        return F.relu(x + self.path(x))


class ConvMixerBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.depthwise = nn.Sequential(
            CausalConv1d(channels, channels, 5, groups=channels),
            nn.GELU(), ChannelLayerNorm(channels),
        )
        self.pointwise = nn.Sequential(
            nn.Conv1d(channels, channels, 1),
            nn.GELU(), ChannelLayerNorm(channels),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.pointwise(x + self.depthwise(x))


class ConvolutionEncoder(nn.Module):
    def __init__(self, input_dim: int, kind: str):
        super().__init__()
        channels = 32 if kind == "residual_tcn" else 64
        self.output_dim = channels
        if kind == "cnn":
            layers = [CausalConv1d(input_dim, channels, 3), nn.ReLU(),
                      CausalConv1d(channels, channels, 3), nn.ReLU()]
        elif kind == "convmixer":
            layers = [CausalConv1d(input_dim, channels, 3), nn.GELU(),
                      ChannelLayerNorm(channels), ConvMixerBlock(channels)]
        elif kind == "resnet":
            layers = [CausalConv1d(input_dim, channels, 3), nn.ReLU(),
                      ResidualBlock(channels), ResidualBlock(channels)]
        elif kind == "tcn":
            layers = []
            for i, dilation in enumerate((1, 2, 4)):
                layers += [CausalConv1d(input_dim if i == 0 else channels,
                                       channels, 3, dilation=dilation), nn.ReLU()]
        elif kind == "residual_tcn":
            # 1×1 입력 projection은 수용영역을 늘리지 않는다.
            layers = [nn.Conv1d(input_dim, channels, 1), nn.ReLU()]
            layers += [ResidualBlock(channels, dilation=d) for d in (1, 2, 4)]
        else:
            raise ValueError(f"Unknown convolution encoder: {kind}")
        self.network = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.network(x.transpose(1, 2)).transpose(1, 2)


class RecurrentEncoder(nn.Module):
    def __init__(self, input_dim: int, kind: str):
        super().__init__()
        if kind == "lstm":
            self.first = nn.LSTM(input_dim, 60, batch_first=True)
            self.second = nn.LSTM(60, 30, batch_first=True)
            self.projection = nn.Sequential(nn.Linear(30, 32), nn.ReLU())
            self.output_dim = 32
        elif kind == "gru":
            self.first = nn.GRU(input_dim, 72, batch_first=True)
            self.second = nn.GRU(72, 36, batch_first=True)
            self.projection = nn.Identity()
            self.output_dim = 36
        elif kind == "kalmannet":
            self.first = nn.GRU(input_dim, 96, batch_first=True)
            self.second = None
            self.projection = nn.Sequential(nn.Linear(96, 96), nn.ReLU())
            self.output_dim = 96
        elif kind == "small_gru":
            self.first = nn.GRU(input_dim, 64, batch_first=True)
            self.second = None
            self.projection = nn.Identity()
            self.output_dim = 64
        else:
            raise ValueError(f"Unknown recurrent encoder: {kind}")

    def forward(self, x: Tensor) -> Tensor:
        # 윈도우 호출마다 hidden state를 초기화한다.
        x, _ = self.first(x)
        if self.second is not None:
            x, _ = self.second(x)
        return self.projection(x)


class TransformerEncoder(nn.Module):
    def __init__(self, input_dim: int, seq_len: int):
        super().__init__()
        self.output_dim = 32
        self.projection = nn.Linear(input_dim, self.output_dim)
        self.layer = nn.TransformerEncoderLayer(
            d_model=self.output_dim, nhead=2, dim_feedforward=64,
            dropout=0.1, activation="gelu", batch_first=True,
        )
        position = torch.arange(seq_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, self.output_dim, 2).float()
                             * (-math.log(10000.0) / self.output_dim))
        encoding = torch.zeros(seq_len, self.output_dim)
        encoding[:, 0::2] = torch.sin(position * div_term)
        encoding[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("position_encoding", encoding.unsqueeze(0))
        self.register_buffer("causal_mask", torch.triu(
            torch.ones(seq_len, seq_len, dtype=torch.bool), diagonal=1))

    def forward(self, x: Tensor) -> Tensor:
        length = x.shape[1]
        if length > self.position_encoding.shape[1]:
            raise ValueError("Transformer 입력 길이가 설정 seq_len을 초과했습니다.")
        x = self.projection(x) + self.position_encoding[:, :length].to(dtype=x.dtype)
        return self.layer(x, src_mask=self.causal_mask[:length, :length])


class ForceEstimator(nn.Module):
    """공유 encoder와 force/load/선택형 location heads.

    tip: force B,3 / load_logit B. ID18은 추론 코드에서 고정 출력한다.
    body: 위 출력과 location_logits B,18. label index 0..17 → ID1..18.
    force_only: 회귀 대조실험용 force B,3만 반환한다.
    """

    def __init__(self, name: str, input_dim: int, task: str, seq_len: int):
        super().__init__()
        self.name, self.input_dim, self.task, self.seq_len = name, input_dim, task, seq_len
        if name == "mlp":
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 208), nn.ReLU(),
                nn.Linear(208, 104), nn.ReLU(),
                nn.Linear(104, 52), nn.ReLU(),
            )
            hidden_dim = 52
        elif name in {"cnn", "convmixer", "resnet", "tcn", "residual_tcn"}:
            self.encoder = ConvolutionEncoder(input_dim, name)
            hidden_dim = self.encoder.output_dim
        elif name in {"lstm", "gru", "kalmannet", "small_gru"}:
            self.encoder = RecurrentEncoder(input_dim, name)
            hidden_dim = self.encoder.output_dim
        elif name == "transformer":
            self.encoder = TransformerEncoder(input_dim, seq_len)
            hidden_dim = self.encoder.output_dim
        else:
            raise ValueError(f"Unknown model {name!r}; choose from {MODEL_NAMES}")
        self.force_head = nn.Linear(hidden_dim, 3)
        self.load_head = None if task == "force_only" else nn.Linear(hidden_dim, 1)
        self.location_head = nn.Linear(hidden_dim, 18) if task == "body" else None

    def _validate_input(self, x: Tensor) -> None:
        if x.ndim != 3 or x.shape[-1] != self.input_dim or x.shape[1] < 1:
            raise ValueError(f"입력은 (B,T,{self.input_dim}), T>=1이어야 합니다; {tuple(x.shape)}")

    def encode_sequence(self, x: Tensor) -> Tensor:
        """각 시점의 인과적 특징 B,T,H; 진단 및 인과성 검증에 사용할 수 있다."""
        self._validate_input(x)
        return self.encoder(x)

    def forward(self, x: Tensor) -> Dict[str, Tensor]:
        self._validate_input(x)
        # MLP는 동일 평가 행 집합의 마지막 샘플만 사용하여 불필요한 계산을 피한다.
        encoded = self.encoder(x[:, -1:, :] if self.name == "mlp" else x)
        last = encoded[:, -1, :]
        outputs = {"force": self.force_head(last)}
        if self.load_head is not None:
            outputs["load_logit"] = self.load_head(last).squeeze(-1)
        if self.location_head is not None:
            outputs["location_logits"] = self.location_head(last)
        return outputs


def build_model(name: str, input_dim: int, task: str = "tip",
                seq_len: int = 30) -> ForceEstimator:
    """모델 생성. task는 tip, body, force_only 중 하나다."""
    name = name.lower()
    if name not in MODEL_NAMES:
        raise ValueError(f"Unknown model {name!r}; choose from {MODEL_NAMES}")
    if task not in {"tip", "body", "force_only"}:
        raise ValueError("task must be 'tip', 'body', or 'force_only'")
    if not isinstance(input_dim, int) or input_dim < 1:
        raise ValueError("input_dim must be a positive integer")
    if not isinstance(seq_len, int) or seq_len < 1:
        raise ValueError("seq_len must be a positive integer")
    return ForceEstimator(name, input_dim, task, seq_len)


def count_parameters(model: nn.Module) -> int:
    """학습 가능한 파라미터 수 (위치 인코딩 같은 buffer 제외)."""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
