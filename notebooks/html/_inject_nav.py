"""将网站导航栏 + 公共样式注入到 nbconvert 生成的 HTML 中"""
import sys
from pathlib import Path

# 注入到 </head> 之后（CSS link）
HEADER_INJECT = '''
<link rel="stylesheet" href="../../css/style.css">
'''

# 注入到 <body> 之后（导航栏 + 内容包裹 div）
BODY_INJECT = '''
<nav class="navbar">
    <div class="nav-brand">
        <a href="../../index.html" class="nav-logo">🧠 PyTorch Module Deep Dive</a>
    </div>
    <div class="nav-links">
        <a href="../../index.html" class="nav-item">🏠 首页流程图</a>
        <div class="nav-dropdown">
            <button class="nav-dropbtn">📓 Notebooks ▾</button>
            <div class="nav-dropdown-content">
                <a href="01_module_initialization.html" class="nav-item">01 · Module 初始化与属性拦截</a>
                <a href="02_parameter_and_buffer.html" class="nav-item">02 · Parameter 与 Buffer</a>
                <a href="03_module_hierarchy.html" class="nav-item">03 · Module 层级导航</a>
                <a href="04_device_and_dtype.html" class="nav-item">04 · 设备迁移与类型转换</a>
                <a href="05_training_mode.html" class="nav-item">05 · 训练模式与梯度管理</a>
                <a href="06_forward_and_hooks.html" class="nav-item">06 · Forward 调用链与 Hook</a>
                <a href="07_state_serialization.html" class="nav-item">07 · 状态序列化</a>
                <a href="08_global_hooks_and_advanced.html" class="nav-item">08 · 全局 Hook 与高级机制</a>
                <a href="09_containers.html" class="nav-item">09 · 容器类</a>
                <a href="10_compilation_and_internals.html" class="nav-item">10 · 编译系统与内部细节</a>
            </div>
        </div>
        <a href="https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/module.py"
           target="_blank" class="nav-item nav-source">📄 module.py ↗</a>
        <button id="themeToggle" class="nav-item theme-btn" title="切换主题">🌓</button>
    </div>
</nav>
<div class="main-content">
'''

# 注入到 </body> 之前（关闭 div + footer + JS）
FOOTER_INJECT = '''
</div>
<footer>
    <p>PyTorch module.py Deep Dive · <a href="../../index.html">Home</a> · <a href="https://github.com/pytorch/pytorch" target="_blank">PyTorch GitHub</a></p>
</footer>
<script src="../../js/main.js"></script>
'''


def inject_nav(html_path: Path) -> None:
    content = html_path.read_text(encoding='utf-8')

    # 1. 在 </head> 后注入 CSS link
    content = content.replace('</head>', '</head>' + HEADER_INJECT, 1)

    # 2. 在 <body ...> 后注入导航栏（body 可能带属性）
    import re
    content = re.sub(r'(<body[^>]*>)', r'\1' + BODY_INJECT, content, count=1)

    # 3. 在 </body> 前注入 footer + JS
    content = content.replace('</body>', FOOTER_INJECT + '</body>', 1)

    html_path.write_text(content, encoding='utf-8')
    print(f'✅ 已注入导航栏: {html_path.name}')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        inject_nav(Path(sys.argv[1]))
    else:
        print('Usage: python _inject_nav.py <notebook.html>')
