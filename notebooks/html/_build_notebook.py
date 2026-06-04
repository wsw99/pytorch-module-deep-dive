#!/usr/bin/env python3
"""
Build a standalone notebook HTML page from the custom .ipynb format.

Usage:
    python _build_notebook.py ../ipynb/07_state_serialization.ipynb 07_state_serialization.html
"""

import sys
import re
import html
from pathlib import Path
from collections import OrderedDict

from pygments import highlight
from pygments.lexers import PythonLexer, PythonConsoleLexer
from pygments.formatters import HtmlFormatter

# ---------------------------------------------------------------------------
# Parse the custom .ipynb format
# ---------------------------------------------------------------------------

# Match any tag: <cell id="...">, </cell id="...">, <cell_type>, </cell_type>
TAG_RE = re.compile(r'</?cell[^>]*>')

# For extracting the id attribute from <cell id="..."> or </cell id="...">
ID_RE = re.compile(r'id="([^"]+)"')

def parse_ipynb(path: str) -> list[dict]:
    """Parse a custom .ipynb file into a list of cell dicts.

    Strategy: split the entire file on every <cell...> or </cell...> tag.
    Then walk the parts to reconstruct cells.

    For markdown cells:
      <cell id="X"><cell_type>markdown</cell_type>CONTENT</cell id="X">
      → parts: '', '', 'markdown', 'CONTENT'

    For code cells:
      <cell id="X">CODE</cell id="X">
      → parts: '', 'CODE'
      Followed by output text until next <cell> tag.

    Actually: the split produces alternating tag-content-tag-content...
    Each open tag <cell id="X"> is followed by either:
      - <cell_type>markdown</cell_type> (so parts go: open_tag, '', cell_type_tag, 'markdown',
        close_cell_type_tag, 'CONTENT', close_cell_tag)
      - directly by code: open_tag, '', 'CODE', close_cell_tag
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on every cell-related tag
    parts = TAG_RE.split(content)

    cells = []
    i = 0
    # parts[0] is always '' (before first <cell> tag)
    i = 1

    while i < len(parts):
        # We expect to find cell content here
        # Skip empty parts between adjacent tags
        if i >= len(parts):
            break

        # The pattern after a <cell id="..."> tag:
        # If markdown: <cell_type> → 'markdown' → </cell_type> → CONTENT → </cell id="...">
        #   parts: part[i]='' (between <cell> and <cell_type>)
        #          part[i+1]='markdown' (between <cell_type> and </cell_type>)
        #          part[i+2]=CONTENT (between </cell_type> and </cell>)
        # If code: CODE → </cell id="...">
        #   parts: part[i]=CODE (between <cell> and </cell>)

        part = parts[i]
        i += 1

        # Skip empty parts
        if not part:
            continue

        # If part is 'markdown' or 'code', this was a <cell_type> value
        if part.strip() == 'markdown':
            # Next part is the markdown content (between </cell_type> and </cell>)
            if i < len(parts):
                source = parts[i].strip('\n')
                cells.append({
                    'id': f'md-{len(cells)}',
                    'cell_type': 'markdown',
                    'source': source,
                    'output': None,
                })
                i += 1
            continue

        if part.strip() == 'code':
            # Next part is the code
            if i < len(parts):
                source = parts[i].strip('\n')
                cells.append({
                    'id': f'code-{len(cells)}',
                    'cell_type': 'code',
                    'source': source,
                    'output': None,
                })
                i += 1
            continue

        # If we get here, part is either code source or output.
        # Structural rule: output ALWAYS immediately follows its code cell
        # in the split. So if the previous cell is a code cell without output,
        # this part IS its output. Otherwise, it's a new code cell.
        stripped = part.strip()
        if stripped:
            if cells and cells[-1]['cell_type'] == 'code' and cells[-1].get('output') is None:
                # Output following a code cell
                cells[-1]['output'] = stripped
            else:
                # New code cell
                cells.append({
                    'id': f'code-{len(cells)}',
                    'cell_type': 'code',
                    'source': stripped,
                    'output': None,
                })

    return cells


# ---------------------------------------------------------------------------
# Markdown → HTML (lightweight)
# ---------------------------------------------------------------------------

def markdown_to_html(md: str) -> str:
    """Convert basic markdown to HTML. Handles headings, code, lists, tables, etc."""
    out = []
    in_code_block = False
    code_fence_lang = ''
    code_block_lines = []

    in_table = False
    table_lines = []

    lines = md.split('\n')

    def flush_code_block():
        nonlocal in_code_block, code_block_lines, code_fence_lang
        if code_block_lines:
            joined = '\n'.join(code_block_lines)
            escaped = html.escape(joined)
            out.append(f'<pre><code>{escaped}</code></pre>')
        code_block_lines = []
        in_code_block = False
        code_fence_lang = ''

    def flush_table():
        nonlocal in_table, table_lines
        if table_lines:
            out.append('<table>')
            header = True
            for row in table_lines:
                cells = [c.strip() for c in row.split('|') if c.strip() != '']
                # Filter alignment-only rows
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    header = False
                    continue
                tag = 'th' if header else 'td'
                out.append('<tr>')
                for c in cells:
                    out.append(f'<{tag}>{_inline_format(c)}</{tag}>')
                out.append('</tr>')
                header = False
            out.append('</table>')
        table_lines = []
        in_table = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code fences
        if line.startswith('```'):
            if in_code_block:
                flush_code_block()
            else:
                code_fence_lang = line[3:].strip()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Table detection
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                flush_code_block()
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Headings
        h3_match = re.match(r'^### (.+)$', line)
        h2_match = re.match(r'^## (.+)$', line)
        h1_match = re.match(r'^# (.+)$', line)

        if h3_match:
            flush_code_block()
            out.append(f'<h3>{_inline_format(h3_match.group(1))}</h3>')
        elif h2_match:
            flush_code_block()
            out.append(f'<h2>{_inline_format(h2_match.group(1))}</h2>')
        elif h1_match:
            flush_code_block()
            out.append(f'<h1>{_inline_format(h1_match.group(1))}</h1>')

        # Horizontal rule
        elif line.strip() in ('---', '***', '___'):
            out.append('<hr>')

        # Blockquote
        elif line.startswith('> '):
            flush_code_block()
            # Collect all blockquote lines
            bq_lines = []
            while i < len(lines) and lines[i].startswith('> '):
                prefix = '> '
                # Handle tip/warning blockquotes
                stripped = lines[i][2:]  # remove '> '
                if stripped.startswith('**'):
                    prefix += '**'
                bq_lines.append(stripped)
                i += 1

            bq_content = _inline_format('\n'.join(bq_lines))
            # Detect tip/warning
            cls = ''
            if '⚠️' in bq_content or 'warning' in bq_content.lower():
                cls = ' warning'
            elif '💡' in bq_content or 'tip' in bq_content.lower() or '✅' in bq_content:
                cls = ' tip'
            cls_attr = f' class="{cls.strip()}"' if cls.strip() else ''
            out.append(f'<blockquote{cls_attr}>{bq_content}</blockquote>')
            continue

        # Unordered list
        elif re.match(r'^[\*\-\+]\s+', line):
            flush_code_block()
            out.append('<ul>')
            while i < len(lines) and re.match(r'^[\*\-\+]\s+', lines[i]):
                item = re.sub(r'^[\*\-\+]\s+', '', lines[i])
                out.append(f'<li>{_inline_format(item)}</li>')
                i += 1
            out.append('</ul>')
            continue

        # Ordered list
        elif re.match(r'^\d+\.\s+', line):
            flush_code_block()
            out.append('<ol>')
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                item = re.sub(r'^\d+\.\s+', '', lines[i])
                out.append(f'<li>{_inline_format(item)}</li>')
                i += 1
            out.append('</ol>')
            continue

        # Empty line → paragraph break
        elif line.strip() == '':
            flush_code_block()
            out.append('')

        # Regular paragraph
        else:
            flush_code_block()
            out.append(f'<p>{_inline_format(line)}</p>')

        i += 1

    flush_code_block()
    flush_table()
    return '\n'.join(out)


def _inline_format(text: str) -> str:
    """Handle inline formatting: bold, italic, inline code, links, images."""
    # Inline code (backticks)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold + italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # Images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    # Checkboxes
    text = re.sub(r'\[x\]', '<input type="checkbox" checked disabled>', text, flags=re.IGNORECASE)
    text = re.sub(r'\[ \]', '<input type="checkbox" disabled>', text)
    return text


# ---------------------------------------------------------------------------
# Pygments highlighting
# ---------------------------------------------------------------------------

def highlight_python(code: str) -> str:
    """Highlight Python code with pygments, using CSS classes that map to CSS variables."""
    lexer = PythonLexer()
    # Strip common leading whitespace for cleaner display
    code = code.strip()
    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)


def highlight_output(text: str) -> str:
    """Highlight output text (plain or Python console style)."""
    text = text.strip()
    if not text:
        return ''
    # Use PythonConsoleLexer for traceback-style output, fallback to plain
    try:
        lexer = PythonConsoleLexer()
        formatter = HtmlFormatter(nowrap=True)
        return highlight(text, lexer, formatter)
    except Exception:
        return html.escape(text)


# ---------------------------------------------------------------------------
# HTML page template
# ---------------------------------------------------------------------------

def build_html(cells: list[dict], title: str = '07 · 状态序列化', subtitle: str = '') -> str:
    """Build the full HTML page from parsed cells."""
    # Get pygments CSS
    pygments_css = HtmlFormatter(style='default').get_style_defs('.highlight')

    body_parts = []
    counter = 0

    for cell in cells:
        if cell['cell_type'] == 'markdown':
            body_parts.append('<div class="notebook-cell markdown">')
            body_parts.append(markdown_to_html(cell['source']))
            body_parts.append('</div>')

        elif cell['cell_type'] == 'code':
            counter += 1
            code_html = highlight_python(cell['source'])
            body_parts.append('<div class="notebook-cell code">')
            body_parts.append('<div class="input-area">')
            body_parts.append(f'<div class="in-prompt">In [{counter}]:</div>')
            body_parts.append(f'<div class="highlight"><pre>{code_html}</pre></div>')
            body_parts.append('</div>')  # input-area

            if cell.get('output'):
                out_html = highlight_output(cell['output'])
                body_parts.append('<div class="output-area">')
                body_parts.append(f'<pre>{out_html}</pre>')
                body_parts.append('</div>')

            body_parts.append('</div>')  # notebook-cell

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — PyTorch module.py Deep Dive</title>
    <link rel="stylesheet" href="../../css/style.css">
    <style>
        /* ============================================================
           Pygments syntax highlighting — uses site CSS variables
           ============================================================ */
        {pygments_css}

        /* Override pygments colors with site theme variables */
        .highlight {{ background: var(--code-bg); }}
        .highlight .k, .highlight .kn, .highlight .kd, .highlight .kc, .highlight .kr, .highlight .kt {{ color: #d73a49; font-weight: bold; }}
        .highlight .n, .highlight .nb, .highlight .bp, .highlight .fm {{ color: #24292e; }}
        .highlight .s, .highlight .s1, .highlight .s2, .highlight .sa, .highlight .sb, .highlight .sc, .highlight .sd, .highlight .se, .highlight .sh, .highlight .si, .highlight .sx {{ color: #032f62; }}
        .highlight .mi, .highlight .mf, .highlight .mh, .highlight .mo, .highlight .il, .highlight .m {{ color: #005cc5; }}
        .highlight .c, .highlight .c1, .highlight .cm, .highlight .cp, .highlight .cs, .highlight .ch {{ color: #6a737d; font-style: italic; }}
        .highlight .o, .highlight .ow, .highlight .p {{ color: #24292e; }}
        .highlight .nf, .highlight .nc, .highlight .ne {{ color: #6f42c1; }}
        .highlight .nn, .highlight .no {{ color: #005cc5; }}
        .highlight .nd {{ color: #6f42c1; }}
        .highlight .vm, .highlight .nb {{ color: #005cc5; }}
        .highlight .err {{ color: #cb2431; }}

        /* Dark mode overrides */
        [data-theme="dark"] .highlight .k, [data-theme="dark"] .highlight .kn,
        [data-theme="dark"] .highlight .kd, [data-theme="dark"] .highlight .kc,
        [data-theme="dark"] .highlight .kr, [data-theme="dark"] .highlight .kt {{ color: #ff7b72; font-weight: bold; }}
        [data-theme="dark"] .highlight .n, [data-theme="dark"] .highlight .nb,
        [data-theme="dark"] .highlight .bp, [data-theme="dark"] .highlight .fm {{ color: #c9d1d9; }}
        [data-theme="dark"] .highlight .s, [data-theme="dark"] .highlight .s1,
        [data-theme="dark"] .highlight .s2, [data-theme="dark"] .highlight .sa,
        [data-theme="dark"] .highlight .sb, [data-theme="dark"] .highlight .sc,
        [data-theme="dark"] .highlight .sd, [data-theme="dark"] .highlight .se,
        [data-theme="dark"] .highlight .sh, [data-theme="dark"] .highlight .si,
        [data-theme="dark"] .highlight .sx {{ color: #a5d6ff; }}
        [data-theme="dark"] .highlight .mi, [data-theme="dark"] .highlight .mf,
        [data-theme="dark"] .highlight .mh, [data-theme="dark"] .highlight .mo,
        [data-theme="dark"] .highlight .il, [data-theme="dark"] .highlight .m {{ color: #79c0ff; }}
        [data-theme="dark"] .highlight .c, [data-theme="dark"] .highlight .c1,
        [data-theme="dark"] .highlight .cm, [data-theme="dark"] .highlight .cp,
        [data-theme="dark"] .highlight .cs, [data-theme="dark"] .highlight .ch {{ color: #8b949e; font-style: italic; }}
        [data-theme="dark"] .highlight .o, [data-theme="dark"] .highlight .ow,
        [data-theme="dark"] .highlight .p {{ color: #c9d1d9; }}
        [data-theme="dark"] .highlight .nf, [data-theme="dark"] .highlight .nc,
        [data-theme="dark"] .highlight .ne {{ color: #d2a8ff; }}
        [data-theme="dark"] .highlight .nn, [data-theme="dark"] .highlight .no {{ color: #79c0ff; }}
        [data-theme="dark"] .highlight .nd {{ color: #d2a8ff; }}
        [data-theme="dark"] .highlight .vm {{ color: #79c0ff; }}
        [data-theme="dark"] .highlight .err {{ color: #f85149; }}

        /* Notebook cell styling */
        .notebook-cell {{ margin: 1.5em 0; padding: 0 1em; }}
        .notebook-cell.markdown {{ line-height: 1.8; }}
        .notebook-cell.markdown h2 {{ border-bottom: 2px solid #e74c3c; padding-bottom: 0.3em; margin-top: 1.5em; }}
        .notebook-cell.markdown h3 {{ margin-top: 1.5em; color: #c0392b; }}
        .notebook-cell.markdown table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        .notebook-cell.markdown th, .notebook-cell.markdown td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        .notebook-cell.markdown th {{ background: #f5f5f5; font-weight: 600; }}
        .notebook-cell.markdown code {{ background: var(--code-bg); color: var(--code-text); padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
        .notebook-cell.markdown pre {{ background: var(--code-bg); padding: 1em; border-radius: 6px; overflow-x: auto; border: 1px solid var(--border-color); line-height: 1.5; }}
        .notebook-cell.markdown pre code {{ background: none; padding: 0; color: inherit; }}
        .notebook-cell.code {{ background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }}
        .notebook-cell.code .input-area {{ padding: 1em; border-bottom: 1px solid var(--border-color); }}
        .notebook-cell.code .input-area .highlight {{ background: var(--code-bg); padding: 0.8em 1em; border-radius: 6px; overflow-x: auto; }}
        .notebook-cell.code .input-area .highlight pre {{ margin: 0; white-space: pre-wrap; font-family: 'SF Mono','Menlo','Monaco','Courier New',monospace; font-size: 0.88em; line-height: 1.5; }}
        .notebook-cell.code .input-area .in-prompt {{ color: #3498db; font-weight: bold; margin-bottom: 0.5em; }}
        .notebook-cell.code .output-area {{ padding: 0.8em 1em; }}
        .notebook-cell.code .output-area pre {{ margin: 0; white-space: pre-wrap; font-family: 'SF Mono','Menlo','Monaco','Courier New',monospace; font-size: 0.85em; line-height: 1.4; color: var(--text-secondary); }}
        blockquote.tip {{ border-left: 4px solid #27ae60; padding: 0.5em 1em; margin: 1em 0; background: #f0fff4; border-radius: 0 6px 6px 0; }}
        blockquote.warning {{ border-left: 4px solid #f39c12; padding: 0.5em 1em; margin: 1em 0; background: #fffdf0; border-radius: 0 6px 6px 0; }}

        /* Dark mode overrides for notebook cells */
        [data-theme="dark"] .notebook-cell.markdown h2 {{ border-bottom-color: #e74c3c; }}
        [data-theme="dark"] .notebook-cell.markdown h3 {{ color: #e74c3c; }}
        [data-theme="dark"] .notebook-cell.markdown th {{ background: var(--bg-tertiary); }}
        [data-theme="dark"] .notebook-cell.markdown th, [data-theme="dark"] .notebook-cell.markdown td {{ border-color: var(--border-color); }}
        [data-theme="dark"] .notebook-cell.code {{ background: var(--bg-secondary); border-color: var(--border-color); }}
        [data-theme="dark"] .notebook-cell.code .input-area {{ border-bottom-color: var(--border-color); }}
        [data-theme="dark"] .notebook-cell.code .input-area .in-prompt {{ color: #60a5fa; }}
        [data-theme="dark"] blockquote.tip {{ background: #064e3b; color: #d1fae5; }}
        [data-theme="dark"] blockquote.warning {{ background: #78350f; color: #fef3c7; }}
    </style>
</head>
<body>
<nav class="navbar">
    <div class="nav-brand"><a href="../../index.html" class="nav-logo">🧠 PyTorch Module Deep Dive</a></div>
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
                <a href="07_state_serialization.html" class="nav-item active">07 · 状态序列化</a>
                <a href="08_global_hooks_and_advanced.html" class="nav-item">08 · 全局 Hook 与高级机制</a>
                <a href="09_containers.html" class="nav-item">09 · 容器类</a>
                <a href="10_compilation_and_internals.html" class="nav-item">10 · 编译系统与内部细节</a>
            </div>
        </div>
        <a href="https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/module.py" target="_blank" class="nav-item nav-source">📄 module.py ↗</a>
        <button id="themeToggle" class="nav-item theme-btn" title="切换主题">🌓</button>
    </div>
</nav>
<main class="main-content">
    <header class="page-header">
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
    </header>
    <div class="diagram-container">

{chr(10).join(body_parts)}

    </div>
</main>
<footer><p>PyTorch module.py Deep Dive · <a href="../../index.html">Home</a> · <a href="https://github.com/pytorch/pytorch" target="_blank">PyTorch GitHub</a></p></footer>
<script src="../../js/main.js"></script>
</body>
</html>'''

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <input.ipynb> <output.html>")
        print(f"       python {sys.argv[0]} <input.ipynb> <output.html> --title '...' --subtitle '...'")
        sys.exit(1)

    ipynb_path = sys.argv[1]
    output_path = sys.argv[2]

    # Parse optional flags
    title = '07 · 状态序列化'
    subtitle = '覆盖：state_dict, load_state_dict, _IncompatibleKeys, 序列化 Hook, extra_state'

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--subtitle' and i + 1 < len(sys.argv):
            subtitle = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Resolve paths
    base = Path(__file__).resolve().parent
    ipynb_full = (base / ipynb_path).resolve()
    output_full = (base / output_path).resolve()

    if not ipynb_full.exists():
        print(f"Error: file not found: {ipynb_full}")
        sys.exit(1)

    print(f"Parsing: {ipynb_full}")
    cells = parse_ipynb(str(ipynb_full))
    print(f"  Found {len(cells)} cells")

    code_count = sum(1 for c in cells if c['cell_type'] == 'code')
    md_count = sum(1 for c in cells if c['cell_type'] == 'markdown')
    print(f"  Code cells: {code_count}, Markdown cells: {md_count}")

    print(f"Building HTML...")
    html_content = build_html(cells, title=title, subtitle=subtitle)

    print(f"Writing: {output_full}")
    with open(output_full, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Done! Output: {len(html_content):,} bytes")


if __name__ == '__main__':
    main()
