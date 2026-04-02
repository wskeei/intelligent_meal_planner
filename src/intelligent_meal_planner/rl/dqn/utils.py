"""
DQN 训练工具函数

包含 epsilon 调度器和学习率调度器
"""

from typing import List, Tuple


class EpsilonScheduler:
    """
    分段线性 epsilon 调度器

    与课程学习阶段对齐的探索率调度
    """

    def __init__(self, schedules: List[Tuple[int, int, float, float]] = None):
        """
        Args:
            schedules: [(start_step, end_step, start_eps, end_eps), ...]
        """
        if schedules is None:
            # 默认调度：与课程学习阶段对齐
            schedules = [
                (0, 100_000, 1.0, 0.3),       # Stage 1: 高探索
                (100_000, 300_000, 0.3, 0.1), # Stage 2: 中等探索
                (300_000, 500_000, 0.1, 0.02) # Stage 3: 低探索
            ]
        self.schedules = schedules

    def get_epsilon(self, step: int) -> float:
        """获取当前 epsilon 值"""
        for start, end, eps_start, eps_end in self.schedules:
            if start <= step < end:
                progress = (step - start) / (end - start)
                return eps_start - progress * (eps_start - eps_end)

        # 超出所有阶段，返回最终值
        return self.schedules[-1][3]


class LinearScheduler:
    """线性调度器，用于学习率等参数"""

    def __init__(self, start_value: float, end_value: float, total_steps: int):
        self.start_value = start_value
        self.end_value = end_value
        self.total_steps = total_steps

    def get_value(self, step: int) -> float:
        """获取当前值"""
        progress = min(1.0, step / self.total_steps)
        return self.start_value + progress * (self.end_value - self.start_value)
