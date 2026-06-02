# PyTorch `module.py` 源码深度学习

通过 10 个 Jupyter Notebook 系统性地解剖 PyTorch `torch.nn.modules.module.py` 的全部 class 和 function，深入理解 `nn.Module` 内部设计原理。

## 快速开始

```bash
pip install -r requirements.txt
jupyter lab notebooks/
```

## 学习路线

| Notebook | 主题 | 核心内容 |
|----------|------|----------|
| 01 | Module 初始化与属性拦截 | `__init__`, `__setattr__`, `__getattr__`, `add_module` |
| 02 | Parameter 与 Buffer | `register_parameter`, `register_buffer`, `named_parameters` |
| 03 | Module 层级导航 | `children`, `modules`, `named_modules`, `get_submodule` |
| 04 | 设备迁移与类型转换 | `_apply`, `to`, `cuda`, `cpu`, `float`, `half` |
| 05 | 训练模式与梯度管理 | `train`, `eval`, `zero_grad`, `requires_grad_` |
| 06 | Forward 调用链与 Hook | `__call__`, `forward`, `register_forward_hook` |
| 07 | 状态序列化 | `state_dict`, `load_state_dict`, `_IncompatibleKeys` |
| 08 | 全局 Hook 与高级机制 | `register_module_forward_hook`, `_WrappedHook` |
| 09 | 容器类 | `Sequential`, `ModuleList`, `ModuleDict`, `ParameterDict` |
| 10 | 编译系统与内部细节 | `compile`, `extra_repr`, `share_memory` |

## 项目结构

```
pytorch-module-deep-dive/
├── PLAN.md                 # 完整项目计划
├── README.md               # 本文件
├── requirements.txt        # 依赖
├── notebooks/              # 10 个 Jupyter Notebook
├── experiments/            # Python 实验脚本
├── output/html/            # HTML 导出
└── slides/                 # 讲解幻灯片（可选）
```

## 适用人群

- 有 PyTorch 使用经验，想深入框架内部机制的学习者
- 准备 PyTorch 框架面试的候选人
- 需要自定义 Module 行为的高级用户（如自定义序列化、hook 注入）
