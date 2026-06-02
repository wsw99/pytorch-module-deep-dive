/* ============================================================
   PyTorch module.py Deep Dive — 交互逻辑
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // 1. Tab 切换逻辑（首页流程图切换）
    // ============================================================
    const tabBar = document.getElementById('diagramTabs');
    const panels = document.querySelectorAll('.diagram-panel');

    if (tabBar) {
        tabBar.addEventListener('click', function (e) {
            const btn = e.target.closest('.tab-btn');
            if (!btn) return;

            // 更新 tab 激活状态
            tabBar.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 显示对应面板
            const targetId = 'panel-' + btn.dataset.tab;
            panels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === targetId) {
                    panel.classList.add('active');
                }
            });

            // 重新渲染 Mermaid 图（切换时可能需要）
            // Mermaid 在页面加载时已渲染，切换 display 后 SVG 仍然存在
        });
    }

    // ============================================================
    // 2. 导航栏高亮
    // ============================================================
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item[data-page]');

    navItems.forEach(item => {
        const page = item.dataset.page;
        // 首页高亮
        if (page === 'home' && (currentPath.endsWith('index.html') || currentPath.endsWith('/'))) {
            item.classList.add('active');
        }
        // Notebook 页面高亮
        if (page && currentPath.includes(page)) {
            item.classList.add('active');
        }
    });

    // ============================================================
    // 3. 主题切换（亮色 / 暗色）
    // ============================================================
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // 读取本地存储的偏好
    const savedTheme = localStorage.getItem('pytorch-module-theme');
    if (savedTheme === 'dark') {
        html.setAttribute('data-theme', 'dark');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const currentTheme = html.getAttribute('data-theme');
            if (currentTheme === 'dark') {
                html.removeAttribute('data-theme');
                localStorage.setItem('pytorch-module-theme', 'light');
            } else {
                html.setAttribute('data-theme', 'dark');
                localStorage.setItem('pytorch-module-theme', 'dark');
            }
        });
    }

    // ============================================================
    // 4. Notebook iframe 加载（可选：在新标签页中打开）
    // ============================================================
    // 默认行为：点击导航栏中的 notebook 链接会跳转到对应 .html 页面
    // 如果想在 iframe 中打开，取消下面的注释

    /*
    const notebookLinks = document.querySelectorAll('.nav-dropdown-content a[data-page]');
    const homePage = document.getElementById('homePage');
    const notebookViewer = document.getElementById('notebookViewer');
    const notebookFrame = document.getElementById('notebookFrame');

    notebookLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const href = link.getAttribute('href');
            if (homePage) homePage.style.display = 'none';
            if (notebookViewer) {
                notebookViewer.style.display = 'block';
                notebookFrame.src = href;
            }
        });
    });
    */

    // ============================================================
    // 5. 键盘快捷键
    // ============================================================
    document.addEventListener('keydown', function (e) {
        // Ctrl/Cmd + 数字键 切换 flowchart tab
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '6') {
            e.preventDefault();
            const tabs = document.querySelectorAll('#diagramTabs .tab-btn');
            const idx = parseInt(e.key) - 1;
            if (tabs[idx]) tabs[idx].click();
        }
    });

    // ============================================================
    // 6. Mermaid 图表点击放大（可选）
    // ============================================================
    document.querySelectorAll('.mermaid svg').forEach(svg => {
        svg.style.cursor = 'zoom-in';
        svg.addEventListener('click', function () {
            if (this.style.maxWidth === '100%') {
                this.style.maxWidth = '200%';
                this.style.cursor = 'zoom-out';
            } else {
                this.style.maxWidth = '100%';
                this.style.cursor = 'zoom-in';
            }
        });
    });

});
