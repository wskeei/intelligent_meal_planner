"""
优先经验回放 (Prioritized Experience Replay)

使用 SumTree 数据结构实现 O(log n) 的优先采样
"""

import numpy as np
from typing import Tuple, Dict, Any


class SumTree:
    """
    SumTree 数据结构，用于高效的优先采样

    叶子节点存储优先级，内部节点存储子节点优先级之和
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1)
        self.data = np.zeros(capacity, dtype=object)
        self.data_pointer = 0
        self.n_entries = 0

    def add(self, priority: float, data: Any):
        """添加数据和对应的优先级"""
        tree_idx = self.data_pointer + self.capacity - 1
        self.data[self.data_pointer] = data
        self.update(tree_idx, priority)

        self.data_pointer = (self.data_pointer + 1) % self.capacity
        self.n_entries = min(self.n_entries + 1, self.capacity)

    def update(self, tree_idx: int, priority: float):
        """更新优先级"""
        change = priority - self.tree[tree_idx]
        self.tree[tree_idx] = priority

        while tree_idx != 0:
            tree_idx = (tree_idx - 1) // 2
            self.tree[tree_idx] += change

    def get(self, s: float) -> Tuple[int, float, Any]:
        """根据累积优先级采样"""
        parent_idx = 0

        while True:
            left_child_idx = 2 * parent_idx + 1
            right_child_idx = left_child_idx + 1

            if left_child_idx >= len(self.tree):
                leaf_idx = parent_idx
                break

            if s <= self.tree[left_child_idx]:
                parent_idx = left_child_idx
            else:
                s -= self.tree[left_child_idx]
                parent_idx = right_child_idx

        data_idx = leaf_idx - self.capacity + 1
        return leaf_idx, self.tree[leaf_idx], self.data[data_idx]

    @property
    def total_priority(self) -> float:
        return self.tree[0]


class PrioritizedReplayBuffer:
    """
    优先经验回放缓冲区

    Args:
        capacity: 缓冲区容量
        alpha: 优先级指数 (0=均匀采样, 1=完全优先)
        beta_start: 重要性采样初始值
        beta_end: 重要性采样最终值
        beta_steps: beta 退火步数
    """

    def __init__(
        self,
        capacity: int = 100000,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_steps: int = 400000
    ):
        self.tree = SumTree(capacity)
        self.capacity = capacity
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.beta_steps = beta_steps
        self.current_step = 0

        self.epsilon = 1e-6  # 防止优先级为0
        self.max_priority = 1.0

    def add(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        action_mask: np.ndarray,
        next_action_mask: np.ndarray
    ):
        """添加经验"""
        experience = (state, action, reward, next_state, done, action_mask, next_action_mask)
        priority = self.max_priority ** self.alpha
        self.tree.add(priority, experience)

    def sample(self, batch_size: int) -> Tuple[Dict[str, np.ndarray], np.ndarray, np.ndarray]:
        """
        采样一批经验

        Returns:
            batch: 经验字典
            indices: 树索引 (用于更新优先级)
            weights: 重要性采样权重
        """
        batch = {
            'states': [], 'actions': [], 'rewards': [],
            'next_states': [], 'dones': [],
            'action_masks': [], 'next_action_masks': []
        }
        indices = np.zeros(batch_size, dtype=np.int32)
        priorities = np.zeros(batch_size)

        # 分段采样
        segment = self.tree.total_priority / batch_size

        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            s = np.random.uniform(a, b)

            idx, priority, data = self.tree.get(s)
            indices[i] = idx
            priorities[i] = priority

            state, action, reward, next_state, done, mask, next_mask = data
            batch['states'].append(state)
            batch['actions'].append(action)
            batch['rewards'].append(reward)
            batch['next_states'].append(next_state)
            batch['dones'].append(done)
            batch['action_masks'].append(mask)
            batch['next_action_masks'].append(next_mask)

        # 转换为 numpy 数组
        for key in batch:
            batch[key] = np.array(batch[key])

        # 计算重要性采样权重
        beta = self._get_beta()
        min_prob = priorities.min() / self.tree.total_priority
        max_weight = (self.tree.n_entries * min_prob) ** (-beta)

        probs = priorities / self.tree.total_priority
        weights = (self.tree.n_entries * probs) ** (-beta)
        weights = weights / max_weight  # 归一化

        self.current_step += 1

        return batch, indices, weights.astype(np.float32)

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """更新优先级"""
        priorities = (np.abs(td_errors) + self.epsilon) ** self.alpha

        for idx, priority in zip(indices, priorities):
            self.tree.update(idx, priority)
            self.max_priority = max(self.max_priority, priority)

    def _get_beta(self) -> float:
        """获取当前 beta 值"""
        progress = min(1.0, self.current_step / self.beta_steps)
        return self.beta_start + progress * (self.beta_end - self.beta_start)

    def __len__(self) -> int:
        return self.tree.n_entries
