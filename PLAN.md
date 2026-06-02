# Project Plan: PyTorch `module.py` 源码深度学习

> 通过 10 个 Jupyter Notebook + 交互式网页，系统性地解剖 PyTorch `torch.nn.modules.module.py` 的全部 class 和 function，深入理解 `nn.Module` 内部设计原理。

---

## 0. 网页可视化方案

除了 Jupyter Notebook，项目包含一个**静态文档网站**，通过交互式流程图展示 Module 系统的内部运作：

```
pytorch-module-deep-dive/
├── index.html                    # 🏠 首页 — 交互式流程图总览
├── css/
│   └── style.css                 # 网站样式
├── js/
│   └── main.js                   # 导航 + 交互逻辑
├── notebooks/
│   ├── html/                     # 从 .ipynb 导出的 HTML（nbconvert）
│   │   ├── 01_module_initialization.html
│   │   ├── 02_parameter_and_buffer.html
│   │   └── ...（共 10 个）
│   └── ipynb/                    # 原始 Jupyter Notebook
│       ├── 01_module_initialization.ipynb
│       └── ...
├── experiments/
├── output/
└── slides/
```

### 首页流程图设计

首页展示 **6 张 Mermaid 流程图**（可切换 Tab），覆盖 Module 系统的全部核心交互：

| Tab | 流程图 | 展示内容 |
|-----|--------|----------|
| **总览** | Module 系统全景图 | Class 依赖、核心数据流、外部接口 |
| **属性注册** | `__setattr__` 路由机制 | 如何自动将 Parameter/Module/Buffer 分类存入内部字典 |
| **Forward 调用链** | `__call__` → `_call_impl` | pre_hooks → forward → hooks 的完整执行顺序 |
| **设备/类型转换** | `_apply` 引擎 | cuda/cpu/float/half 如何递归处理参数与缓冲区 |
| **序列化** | state_dict / load_state_dict | 参数保存/加载的完整数据流，含 hook 注入点 |
| **层级导航** | DFS 遍历机制 | named_modules/named_parameters 的递归去重逻辑 |

### 导航栏

顶部固定导航栏，支持：
- 🏠 **首页** — 回到流程图总览
- **Notebook 01-10** — 下拉菜单或直接链接，跳转到对应 HTML
- **GitHub 源码链接** — 链接到 PyTorch 官方 module.py

### 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 流程图 | Mermaid.js (CDN) | 纯文本定义、渲染美观、无需构建 |
| 样式 | 纯 CSS（CSS Variables 主题） | 零依赖，支持暗色/亮色切换 |
| 交互 | 原生 JavaScript | 无框架依赖，Tab 切换、导航高亮 |
| Notebook 渲染 | nbconvert → HTML | 保留输出和样式，静态托管友好 |
| 部署 | GitHub Pages | 免费托管，自动发布 |

---

## 1. 项目概述

| 维度 | 说明 |
|------|------|
| **目标** | 学习 PyTorch `module.py` 中每一个 class 和 function 的设计与实现 |
| **范围** | `Module` + `_IncompatibleKeys` + `_WrappedHook` + 全部 50+ 方法 + 关联容器类 |
| **交付形式** | 10 个 Jupyter Notebook（.ipynb）+ Python 实验脚本 + HTML 静态导出 |
| **输入** | PyTorch 源码（`torch/nn/modules/module.py`、`container.py`） |
| **技术栈** | Python 3.9+, PyTorch 2.4+, Jupyter Lab, graphviz |
| **硬件** | CPU 即可（GPU 可选，仅 Notebook 4 设备迁移演示中有帮助） |
| **周期** | 6 周（可压缩为 2 周 MVP 或扩展为 8 周深度版） |

---

## 2. 相关参考资源

### 2.1 源码

- [PyTorch 官方 module.py](https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/module.py) — 核心学习对象，约 2000+ 行
- [PyTorch 官方 container.py](https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/container.py) — 关联容器类

### 2.2 中文源码分析文章

- [PyTorch 源码分析：Module类 (CSDN)](https://blog.csdn.net/zzxxxaa1/article/details/121037766)
- [PyTorch项目源码学习（3）——Module类初步学习 (CNBlogs)](https://www.cnblogs.com/int-me-X/p/17963848)
- [PyTorch nn.Module 常用API讲解与源码解析 (CSDN)](https://blog.csdn.net/AggressiveYu/article/details/149427664)

### 2.3 课程参考

- **Stanford CS231n** — Assignment 2 中广泛使用 `nn.Module` 构建自定义网络
- **CMU 11-785** — Deep Learning 课程中的 PyTorch Module 系统

---

## 3. `module.py` 完整内容清单

### 3.1 Classes

| 类名 | 类型 | 职责 |
|------|------|------|
| `Module` | 主类 | 所有神经网络模块的基类 |
| `_IncompatibleKeys` | namedtuple | `load_state_dict()` 不匹配时的返回值 |
| `_WrappedHook` | 内部类 | Hook 包装器（存储 hook callable + 元数据） |

### 3.2 Functions（按主题分组）

#### 组 A：初始化与属性拦截
| 方法 | 作用 |
|------|------|
| `__init__` | 初始化 `_parameters`、`_buffers`、`_modules`、hook dicts |
| `__setattr__` | 自动将 `Parameter` → `_parameters`，`Module` → `_modules` |
| `__getattr__` | 从 `_parameters`、`_buffers`、`_modules` 中查找属性 |
| `__delattr__` | 从对应内部字典中删除 |
| `register_module` | 显式注册子模块 |
| `add_module` | 添加子模块（`register_module` 的别名） |

#### 组 B：Parameter 与 Buffer
| 方法 | 作用 |
|------|------|
| `register_parameter` | 注册可学习参数 |
| `register_buffer` | 注册不可学习 Buffer（支持 persistent） |
| `parameters` | 迭代所有可学习参数 |
| `named_parameters` | 带完整路径名的参数迭代 |
| `buffers` | 迭代所有 Buffer |
| `named_buffers` | 带完整路径名的 Buffer 迭代 |
| `_named_members` | `named_parameters`/`named_buffers` 的共享引擎 |
| `get_parameter` | 按点分隔路径查找参数 |
| `get_buffer` | 按点分隔路径查找 Buffer |

#### 组 C：层级导航
| 方法 | 作用 |
|------|------|
| `children` | 迭代直接子模块（非递归） |
| `named_children` | 带名称的直接子模块迭代 |
| `modules` | 递归迭代所有子模块（DFS pre-order，去重） |
| `named_modules` | 带完整路径的递归迭代 |
| `get_submodule` | 按点分隔路径查找子模块 |

#### 组 D：设备与类型转换
| 方法 | 作用 |
|------|------|
| `_apply` | 核心：对参数/Buffer/子模块递归应用函数 |
| `apply` | 对子模块递归调用函数（bottom-up） |
| `to` | 转换设备/数据类型 |
| `cuda` / `cpu` / `xpu` / `mtia` | 设备迁移快捷方法 |
| `float` / `double` / `half` / `bfloat16` | 类型转换快捷方法 |
| `type` | 转换为指定类型 |
| `to_empty` | 迁移到设备但不初始化数据 |

#### 组 E：训练模式与梯度
| 方法 | 作用 |
|------|------|
| `train` | 设置训练模式（递归） |
| `eval` | 设置评估模式 |
| `requires_grad_` | 设置所有参数的 `requires_grad` |
| `zero_grad` | 清零所有参数梯度 |

#### 组 F：Forward 调用链与 Hook
| 方法 | 作用 |
|------|------|
| `__call__` | 入口：调用 `_call_impl` |
| `_call_impl` | 实际执行：pre_hooks → forward → hooks |
| `forward` | 用户必须覆写的核心方法 |
| `_forward_unimplemented` | 默认 forward 实现（抛 NotImplementedError） |
| `register_forward_pre_hook` | 注册前向执行前的 hook |
| `register_forward_hook` | 注册前向执行后的 hook |
| `register_full_backward_pre_hook` | 注册反向传播前的 hook |
| `register_full_backward_hook` | 注册反向传播后的 hook |
| `register_backward_hook` | 已废弃的旧版反向 hook |

#### 组 G：状态序列化
| 方法 | 作用 |
|------|------|
| `state_dict` | 导出参数/Buffer 到 OrderedDict |
| `_save_to_state_dict` | state_dict 的内部实现 |
| `load_state_dict` | 从 dict 加载参数/Buffer |
| `_load_from_state_dict` | load_state_dict 的内部实现 |
| `get_extra_state` | 获取额外自定义状态 |
| `set_extra_state` | 设置额外自定义状态 |
| `register_state_dict_pre_hook` | state_dict 导出前的 hook |
| `register_state_dict_post_hook` | state_dict 导出后的转换 hook |
| `register_load_state_dict_pre_hook` | load_state_dict 加载前的 hook |

#### 组 H：全局 Hook（模块级函数）
| 函数 | 作用 |
|------|------|
| `register_module_forward_pre_hook` | 全局前向 pre-hook（影响所有 Module） |
| `register_module_forward_hook` | 全局前向 post-hook |
| `register_module_full_backward_pre_hook` | 全局反向 pre-hook |
| `register_module_full_backward_hook` | 全局反向 hook |
| `register_module_backward_hook` | 已废弃的全局反向 hook |

#### 组 I：工具方法
| 方法 | 作用 |
|------|------|
| `__repr__` | 模块的字符串表示 |
| `__dir__` | 返回属性列表（含参数/子模块名） |
| `_get_name` | 返回类名 |
| `extra_repr` | 自定义额外 repr 信息 |
| `share_memory` | 将参数移到共享内存（多进程） |
| `_replicate_for_data_parallel` | DataParallel 复制 |
| `compile` | PyTorch 2.0+ torch.compile 接口 |

#### 组 J：关联容器类（container.py）
| 类 | 作用 |
|------|------|
| `nn.Sequential` | 顺序容器，按序执行子模块 |
| `nn.ModuleList` | 列表容器，自动注册子模块 |
| `nn.ModuleDict` | 字典容器，自动注册子模块 |
| `nn.ParameterList` | 参数列表容器 |
| `nn.ParameterDict` | 参数字典容器 |

---

## 4. Notebook 结构（10 个递进式 Notebook）

### [01] Module 初始化与属性拦截
- **覆盖**：`__init__`, `__setattr__`, `__getattr__`, `__delattr__`, `add_module`, `register_module`
- **实验**：忘记 `super().__init__()` 的后果、不同赋值类型的分类路由、`__setattr__` 调用链追踪

### [02] Parameter 与 Buffer
- **覆盖**：`register_parameter`, `register_buffer`, `parameters`, `named_parameters`, `buffers`, `named_buffers`, `_named_members`, `get_parameter`, `get_buffer`
- **实验**：Parameter vs Tensor 的行为差异、`persistent=False` buffer、`_named_members` 去重机制、共享参数

### [03] Module 层级导航
- **覆盖**：`children`, `named_children`, `modules`, `named_modules`, `get_submodule`
- **实验**：嵌套树遍历、DFS pre-order 验证、去重行为、点分隔路径查找

### [04] 设备迁移与类型转换
- **覆盖**：`_apply`, `apply`, `to`, `cuda`, `cpu`, `xpu`, `float`, `double`, `half`, `bfloat16`, `type`, `to_empty`
- **实验**：`model.cuda()` 调用链追踪、`_apply` vs `apply` 区别、Parameter gradient 的设备迁移

### [05] 训练模式与梯度管理
- **覆盖**：`train`, `eval`, `requires_grad_`, `zero_grad`, `apply`
- **实验**：Dropout/BatchNorm 在 train/eval 下的行为差异、`zero_grad(set_to_none=True)` 内存分析、权重初始化

### [06] Forward 调用链与 Hook 系统
- **覆盖**：`__call__`, `_call_impl`, `forward`, `_forward_unimplemented`, `register_forward_pre_hook`, `register_forward_hook`, `register_full_backward_pre_hook`, `register_full_backward_hook`, `register_backward_hook`
- **实验**：hook 监控每层 shape、修改输入/输出/梯度、hook 执行顺序、handle.remove()

### [07] 状态序列化
- **覆盖**：`state_dict`, `_save_to_state_dict`, `load_state_dict`, `_load_from_state_dict`, `register_state_dict_pre_hook`, `register_state_dict_post_hook`, `register_load_state_dict_pre_hook`, `get_extra_state`, `set_extra_state`, `_IncompatibleKeys`
- **实验**：strict vs non-strict 加载、自定义序列化 hook、extra_state 保存非 Tensor 数据、迁移学习场景

### [08] 全局 Hook 与高级内部机制
- **覆盖**：`register_module_forward_pre_hook`, `register_module_forward_hook`, `register_module_full_backward_hook`, `register_module_full_backward_pre_hook`, `_WrappedHook`, 全局 OrderedDict 注册表
- **实验**：简易 profiler 实现、全局 vs 局部 hook 执行顺序

### [09] 容器类（container.py）
- **覆盖**：`nn.Sequential`, `nn.ModuleList`, `nn.ModuleDict`, `nn.ParameterList`, `nn.ParameterDict`
- **实验**：ModuleList vs Python list、Sequential 索引访问、ModuleDict key 查找、容器内 named_modules 路径

### [10] 编译系统与内部细节
- **覆盖**：`compile`, `__repr__`, `__dir__`, `_get_name`, `extra_repr`, `share_memory`, `_replicate_for_data_parallel`
- **实验**：`torch.compile` 加速、自定义 repr、多进程 share_memory

---

## 5. 文件结构

```
pytorch-module-deep-dive/
├── PLAN.md                       # 本文件 — 完整项目计划
├── README.md                     # 项目说明 + 使用方法 + 学习路线
├── requirements.txt              # torch, jupyter, nbconvert, graphviz
│
├── index.html                    # 🏠 首页 — 交互式流程图总览（6 张 Mermaid 图）
├── css/
│   └── style.css                 # 网站样式（亮色/暗色主题）
├── js/
│   └── main.js                   # 导航高亮、Tab 切换、主题切换
│
├── notebooks/
│   ├── ipynb/                    # 原始 Jupyter Notebook（可运行）
│   │   ├── 01_module_initialization.ipynb
│   │   ├── 02_parameter_and_buffer.ipynb
│   │   ├── 03_module_hierarchy.ipynb
│   │   ├── 04_device_and_dtype.ipynb
│   │   ├── 05_training_mode.ipynb
│   │   ├── 06_forward_and_hooks.ipynb
│   │   ├── 07_state_serialization.ipynb
│   │   ├── 08_global_hooks_and_advanced.ipynb
│   │   ├── 09_containers.ipynb
│   │   └── 10_compilation_and_internals.ipynb
│   └── html/                     # nbconvert 导出的 HTML（网站展示用）
│       ├── 01_module_initialization.html
│       ├── 02_parameter_and_buffer.html
│       └── ...（共 10 个）
│
├── experiments/                  # 配套 Python 实验脚本
│   ├── custom_module.py
│   ├── hook_lab.py
│   └── serialization_lab.py
│
├── output/                       # 导出产物
│   └── html/                     # 整站静态导出
└── slides/                       # 可选讲解幻灯片
```

---

## 6. 每个 Notebook 内部结构模板

每个 Notebook 统一采用**四段式结构**：

```
## N. 标题

### Part A: 源码阅读
- 展示 module.py 中相关源码（带行号引用）
- 标注关键设计模式（Composite、Template Method、Observer）
- 逐行解读核心逻辑

### Part B: 机制分析
- 用流程图/示意图解释工作机制
- 对比易混淆概念（如 Parameter vs Tensor、children vs modules）
- 强调常见陷阱

### Part C: 动手实验
- 每节 ≥2 个可运行的代码单元格
- A/B 对比实验
- 故意触发错误案例

### Part D: 小结
- 要点清单
- 与其他 Notebook 的关联
- 延伸阅读链接
```

---

## 7. 项目里程碑

| 周 | 目标 | 产出 |
|---|------|------|
| 第 1 周 | 环境搭建 + Notebook 1-3 | Module 基础、参数/缓冲区、层级导航 |
| 第 2 周 | Notebook 4-5 + 实验脚本 | 设备类型转换、训练模式 |
| 第 3 周 | Notebook 6-7 | Hook 系统、序列化机制 |
| 第 4 周 | Notebook 8-10 + HTML 导出 | 全局 hook、容器类、编译系统 |
| 第 5 周 | README + 图表 + 整合 | 完整 GitHub 仓库 |
| 第 6 周 | 打磨 + 边缘 case 补充 | 最终可发布版本 |

### 版本规划

| 版本 | 时长 | 范围 |
|------|------|------|
| **MVP** | 2 周 | Notebook 1-5（Module 基础全覆盖） |
| **标准版** | 4 周 | Notebook 1-8（加 Hook 系统 + 序列化） |
| **完整版** | 6 周 | Notebook 1-10（加容器类 + 编译） |
| **研究级** | 8-12 周 | 加 JAX/Haiku 对比、自定义 Module 框架、视频教程 |

---

## 8. 实验设计

- **A/B 对比**：每个 Notebook 设计对比实验（Parameter vs Tensor、ModuleList vs list、hook vs 无 hook）
- **错误案例**：故意触发常见错误并展示错误信息（忘调 `super().__init__()`、误用 list 存 Module）
- **源码溯源**：每个函数附 PyTorch GitHub 链接和行号
- **可视化**：
  - Module 树结构图（graphviz）
  - Hook 执行流程图
  - `__call__` 调用时序图

---

## 9. 风险与备用方案

| 风险 | 概率 | 影响 | 备用方案 |
|------|------|------|----------|
| PyTorch 版本间 API 差异 | 中 | 中 | 以 PyTorch 2.4 LTS 为基准，标注版本差异说明 |
| `_call_impl` 等内部函数重构 | 中 | 低 | 记录多版本实现差异作为版本演进材料 |
| `torch.compile` 环境不稳定 | 低 | 低 | Notebook 10 标注为可选进阶内容 |

---

## 10. 最终交付物清单

- [ ] **交互式网页**（index.html + CSS + JS）— 首页流程图 + 导航栏
- [ ] 10 个 Jupyter Notebook（.ipynb）— 可运行实验
- [ ] 10 个 HTML 页面（nbconvert 导出）— 网站展示
- [ ] README.md（项目说明 + 学习路线 + 使用方法）
- [ ] requirements.txt
- [ ] 3+ Python 实验脚本
- [ ] 6 张 Mermaid 流程图（属性注册、Forward 调用链、设备转换、序列化、层级导航、全景总览）
- [ ] GitHub Pages 部署
- [ ] （可选）讲解幻灯片
