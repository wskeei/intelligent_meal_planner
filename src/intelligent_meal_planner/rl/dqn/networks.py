"""
Dueling DQN 网络架构

将 Q 值分解为状态价值 V(s) 和动作优势 A(s,a)
Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
"""

import torch
import torch.nn as nn
from typing import List


class DuelingDQN(nn.Module):
    """
    Dueling DQN 网络

    Args:
        state_dim: 状态空间维度 (默认13)
        action_dim: 动作空间维度 (默认150)
        hidden_dims: 隐藏层维度列表
    """

    def __init__(
        self,
        state_dim: int = 13,
        action_dim: int = 150,
        hidden_dims: List[int] = None
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [256, 256, 128]

        self.state_dim = state_dim
        self.action_dim = action_dim

        # 共享特征提取层
        self.feature = nn.Sequential(
            nn.Linear(state_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
        )

        # 状态价值流 (Value Stream)
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.ReLU(),
            nn.Linear(hidden_dims[2], 1)
        )

        # 动作优势流 (Advantage Stream)
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.ReLU(),
            nn.Linear(hidden_dims[2], action_dim)
        )

        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        """使用正交初始化"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=nn.init.calculate_gain('relu'))
                nn.init.constant_(module.bias, 0.0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            state: 状态张量 [batch_size, state_dim]

        Returns:
            Q 值张量 [batch_size, action_dim]
        """
        features = self.feature(state)

        value = self.value_stream(features)           # [batch, 1]
        advantage = self.advantage_stream(features)   # [batch, action_dim]

        # Q = V + (A - mean(A))
        # 减去均值使得优势函数的期望为0，提高稳定性
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))

        return q_values

    def get_action_values(
        self,
        state: torch.Tensor,
        action_mask: torch.Tensor = None
    ) -> torch.Tensor:
        """
        获取动作 Q 值，可选择应用动作掩码

        Args:
            state: 状态张量
            action_mask: 布尔掩码，True 表示有效动作

        Returns:
            Q 值张量，无效动作的 Q 值为 -inf
        """
        q_values = self.forward(state)

        if action_mask is not None:
            # 将无效动作的 Q 值设为 -inf
            q_values = q_values.clone()
            q_values[~action_mask] = float('-inf')

        return q_values
