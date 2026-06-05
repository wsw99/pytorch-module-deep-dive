#!/usr/bin/env python3
"""
Convert a standard Jupyter .ipynb (JSON) to the custom XML .ipynb format
used by _build_notebook.py.

Usage:
    python _convert_json_to_xml.py ../ipynb/05_training_mode.ipynb
"""

import json
import sys
from pathlib import Path
from collections import OrderedDict


def extract_text_from_output(output):
    """Extract text representation from a Jupyter output cell."""
    output_type = output.get('output_type', '')

    if output_type == 'stream':
        # stdout/stderr
        text = ''.join(output.get('text', []))
        return text.strip('\n')

    elif output_type == 'execute_result':
        # Result of the last expression
        data = output.get('data', {})
        text = data.get('text/plain', '')
        if isinstance(text, list):
            text = ''.join(text)
        return text.strip('\n')

    elif output_type == 'error':
        # Traceback
        traceback = output.get('traceback', [])
        return '\n'.join(traceback).strip('\n')

    elif output_type == 'display_data':
        data = output.get('data', {})
        text = data.get('text/plain', '')
        if isinstance(text, list):
            text = ''.join(text)
        return text.strip('\n')

    return ''


def convert_notebook(input_path: str) -> str:
    """Convert a Jupyter JSON .ipynb to custom XML format string."""
    with open(input_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cell_count = sum(1 for c in nb['cells'] if c['cell_type'] in ('markdown', 'code'))

    lines = []
    cell_index = 0

    for c in nb['cells']:
        cell_type = c.get('cell_type', '')

        if cell_type == 'markdown':
            # Join source lines
            source = ''.join(c.get('source', []))
            # Strip leading/trailing whitespace while preserving internal structure
            source = source.rstrip('\n').rstrip()

            cell_id = f'cell-{cell_index}'
            lines.append(f'<cell id="{cell_id}"><cell_type>markdown</cell_type>{source}</cell id="{cell_id}">')
            lines.append('')
            cell_index += 1

        elif cell_type == 'code':
            # Join source lines
            source = ''.join(c.get('source', []))
            source = source.rstrip('\n').rstrip()

            cell_id = f'cell-{cell_index}'
            lines.append(f'<cell id="{cell_id}">{source}</cell id="{cell_id}">')

            # Collect outputs
            outputs = c.get('outputs', [])
            if outputs:
                for out in outputs:
                    text = extract_text_from_output(out)
                    if text:
                        lines.append('')
                        lines.append(text)

            lines.append('')
            cell_index += 1

        elif cell_type == 'raw':
            # Skip raw cells
            pass

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <notebook.ipynb>")
        print(f"       python {sys.argv[0]} <notebook1.ipynb> <notebook2.ipynb> ...")
        sys.exit(1)

    for path in sys.argv[1:]:
        ipynb_path = Path(path).resolve()
        if not ipynb_path.exists():
            print(f"Error: file not found: {ipynb_path}")
            continue

        print(f"Converting: {ipynb_path.name}")
        result = convert_notebook(str(ipynb_path))

        with open(ipynb_path, 'w', encoding='utf-8') as f:
            f.write(result)

        # Count cells
        import re
        cells = len(re.findall(r'<cell id="[^"]+">', result))
        md = len(re.findall(r'<cell_type>markdown</cell_type>', result))
        code = cells - md
        print(f"  → {cells} cells ({md} markdown + {code} code), {len(result):,} chars")


if __name__ == '__main__':
    main()
