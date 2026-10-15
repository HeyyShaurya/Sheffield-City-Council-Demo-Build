"""Quick automated smoke and regression verification. Never touches current demo database."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
checks = [
 ('Python backend syntax', [sys.executable, '-m', 'py_compile', str(root/'app'/'main.py'), str(root/'run.py')]),
 ('32+ isolated end-to-end/API workflow tests', [sys.executable, '-m', 'pytest', '-q', str(root/'tests'/'test_workflows.py')]),
]
try:
    found = subprocess.run(['node', '--version'], capture_output=True, check=False).returncode == 0
except FileNotFoundError:
    found = False
if found:
    checks.insert(1, ('Frontend JavaScript syntax', ['node', '--check', str(root/'app'/'static'/'app.js')]))
else:
    print('NOTE: Node.js not present, skipping optional JavaScript syntax command.')

for title, argv in checks:
    print('\n=== '+title+' ===', flush=True)
    result = subprocess.run(argv, cwd=root, check=False)
    if result.returncode != 0:
        print('FAIL: '+title+' (exit '+str(result.returncode)+')', flush=True)
        sys.exit(result.returncode)
    print('PASS: '+title, flush=True)
print('\nALL CHECKS PASSED. Browser tests: optional `python tests/browser_navigation.py` and `python tests/browser_journeys.py` (playwright and Chromium required).')
