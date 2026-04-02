"""
带动作掩码的 Dueling Double DQN Agent

核心功能：
- 动作掩码支持
- Double DQN 目标计算
- 优先经验回放
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path

from .networks import DuelingDQN
from .replay_buffer import PrioritizedReplayBuffer
from .utils import EpsilonScheduler, LinearScheduler


class MaskableDQNAgent:
    """
    带动作掩码的 Dueling Double DQN Agent

    Args:
        state_dim: 状态维度
        action_dim: 动作维度
        config: 配置字典
    """

    def __init__(
        self,
        state_dim: int = 13,
        action_dim: int = 150,
        config: Dict = None
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config or self._default_config()

        # 设备
        self.device = torch.device(
            self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        )

        # 网络
        hidden_dims = self.config.get('hidden_dims', [256, 256, 128])
        self.q_network = DuelingDQN(state_dim, action_dim, hidden_dims).to(self.device)
        self.target_network = DuelingDQN(state_dim, action_dim, hidden_dims).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()

        # 优化器
        self.optimizer = optim.Adam(
            self.q_network.parameters(),
            lr=self.config.get('learning_rate', 1e-4)
        )

        # 经验回放
        self.buffer = PrioritizedReplayBuffer(
            capacity=self.config.get('buffer_size', 100000),
            alpha=self.config.get('per_alpha', 0.6),
            beta_start=self.config.get('per_beta_start', 0.4),
            beta_end=self.config.get('per_beta_end', 1.0),
            beta_steps=self.config.get('per_beta_steps', 400000)
        )

        # 调度器
        self.epsilon_scheduler = EpsilonScheduler(
            self.config.get('epsilon_schedule')
        )
        self.lr_scheduler = LinearScheduler(
            self.config.get('learning_rate', 1e-4),
            self.config.get('learning_rate_end', 1e-5),
            self.config.get('total_timesteps', 500000)
        )

        # 超参数
        self.gamma = self.config.get('gamma', 0.99)
        self.target_update_freq = self.config.get('target_update_freq', 1000)
        self.grad_clip = self.config.get('grad_clip', 10.0)

        # 计数器
        self.train_step = 0

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'hidden_dims': [256, 256, 128],
            'gamma': 0.99,
            'learning_rate': 1e-4,
            'learning_rate_end': 1e-5,
            'buffer_size': 100000,
            'batch_size': 256,
            'target_update_freq': 1000,
            'grad_clip': 10.0,
            'per_alpha': 0.6,
            'per_beta_start': 0.4,
            'per_beta_end': 1.0,
            'per_beta_steps': 400000,
            'total_timesteps': 500000,
            'epsilon_schedule': None,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        }

    def select_action(
        self,
        state: np.ndarray,
        action_mask: np.ndarray,
        step: int,
        deterministic: bool = False
    ) -> int:
        """
        选择动作 (带掩码的 epsilon-greedy)

        Args:
            state: 状态
            action_mask: 动作掩码 (True=有效)
            step: 当前步数
            deterministic: 是否确定性选择

        Returns:
            选择的动作索引
        """
        valid_actions = np.where(action_mask)[0]

        if len(valid_actions) == 0:
            return 0  # 安全回退

        epsilon = 0.0 if deterministic else self.epsilon_scheduler.get_epsilon(step)

        if np.random.random() < epsilon:
            # 探索：从有效动作中随机选择
            return np.random.choice(valid_actions)
        else:
            # 利用：选择有效动作中 Q 值最大的
            with torch.no_grad():
                state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                mask_t = torch.BoolTensor(action_mask).unsqueeze(0).to(self.device)

                q_values = self.q_network.get_action_values(state_t, mask_t)
                return q_values.argmax(dim=1).item()

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        action_mask: np.ndarray,
        next_action_mask: np.ndarray
    ):
        """存储经验"""
        self.buffer.add(
            state, action, reward, next_state, done,
            action_mask, next_action_mask
        )

    def train_step_fn(self, batch_size: int = None) -> Optional[Dict]:
        """
        执行一步训练

        Returns:
            训练指标字典，或 None (如果缓冲区不足)
        """
        batch_size = batch_size or self.config.get('batch_size', 256)
        min_buffer = self.config.get('min_buffer_size', 10000)

        if len(self.buffer) < min_buffer:
            return None

        # 采样
        batch, indices, weights = self.buffer.sample(batch_size)

        # 转换为张量
        states = torch.FloatTensor(batch['states']).to(self.device)
        actions = torch.LongTensor(batch['actions']).to(self.device)
        rewards = torch.FloatTensor(batch['rewards']).to(self.device)
        next_states = torch.FloatTensor(batch['next_states']).to(self.device)
        dones = torch.FloatTensor(batch['dones']).to(self.device)
        next_masks = torch.BoolTensor(batch['next_action_masks']).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        # 计算当前 Q 值
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # 计算目标 Q 值 (Double DQN)
        with torch.no_grad():
            # 用 online 网络选择动作 (带掩码)
            next_q_online = self.q_network(next_states)
            next_q_online[~next_masks] = float('-inf')
            best_actions = next_q_online.argmax(dim=1)

            # 用 target 网络评估
            next_q_target = self.target_network(next_states)
            next_q = next_q_target.gather(1, best_actions.unsqueeze(1)).squeeze(1)

            # 目标值
            target_q = rewards + (1 - dones) * self.gamma * next_q

        # 计算 TD 误差
        td_errors = (current_q - target_q).detach().cpu().numpy()

        # 加权损失
        loss = (weights * (current_q - target_q) ** 2).mean()

        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q_network.parameters(), self.grad_clip)
        self.optimizer.step()

        # 更新优先级
        self.buffer.update_priorities(indices, td_errors)

        # 更新目标网络
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.update_target_network()

        # 更新学习率
        new_lr = self.lr_scheduler.get_value(self.train_step)
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = new_lr

        return {
            'loss': loss.item(),
            'q_mean': current_q.mean().item(),
            'q_max': current_q.max().item(),
            'td_error_mean': np.abs(td_errors).mean(),
            'learning_rate': new_lr,
        }

    def update_target_network(self):
        """硬更新目标网络"""
        self.target_network.load_state_dict(self.q_network.state_dict())

    def save(self, path: str):
        """保存模型"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'train_step': self.train_step,
            'config': self.config,
        }, path)

    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)

        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.train_step = checkpoint['train_step']

    @classmethod
    def from_pretrained(cls, path: str, device: str = None):
        """从预训练模型加载"""
        checkpoint = torch.load(path, map_location='cpu')
        config = checkpoint['config']

        if device:
            config['device'] = device

        agent = cls(config=config)
        agent.load(path)
        return agent
