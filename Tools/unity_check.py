"""Recompile a connected Unity Editor and fail on errors or an unavailable verdict.

Usage: python Tools/unity_check.py [--project-path PATH] [--no-recompile] [--warnings]
The default project is the repository containing this tool.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-path', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--no-recompile', action='store_true')
    parser.add_argument('--warnings', action='store_true')
    options = parser.parse_args()
    unity = shutil.which('unity')
    if not unity:
        raise RuntimeError('Unity CLI is not installed or is not on PATH.')

    def command(name, *arguments):
        result = subprocess.run([unity, 'command', name, '--result-only', '--project-path', options.project_path,
                                 '--', *arguments], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=75)
        try:
            data = json.loads(result.stdout)
        except ValueError as error:
            raise RuntimeError(f'{name}: Unity returned no JSON verdict: {result.stderr[:400]}') from error
        if result.returncode != 0 or (isinstance(data, dict) and data.get('success') is False):
            raise RuntimeError(f'{name}: {json.dumps(data, ensure_ascii=False)[:1000]}')
        return data

    if not options.no_recompile:
        command('clear_console')
        command('recompile')
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            status = command('recompile_status')
            if status.get('failed') or status.get('compilationFailed') or status.get('status') == 'failed':
                raise RuntimeError('Unity compilation failed: ' + json.dumps(status, ensure_ascii=False))
            if status.get('status') in ('completed', 'up_to_date', 'idle'):
                break
            time.sleep(3)
        else:
            raise RuntimeError('Unity did not finish compiling within 240 seconds.')

    # Pipeline may have no ground-truth sample immediately after reloading. Missing evidence must never pass.
    for attempt in range(10):
        console = command('console', '--tail', '200')
        truth = console.get('groundTruth') or {}
        if 'compilationFailed' in truth:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Unity did not return a compilation ground-truth sample.')
    errors = [entry for entry in console.get('entries', []) if entry.get('level') == 'error']
    warnings = [entry for entry in console.get('entries', []) if entry.get('level') in ('warning', 'warn')]
    seen = set()
    for entry in errors + (warnings if options.warnings else []):
        message = entry.get('message', '').strip()
        if message not in seen:
            seen.add(message)
            print(f"[{entry.get('level')}] {message[:600]}")
    print(f"compilationFailed={truth['compilationFailed']} errors={len(errors)} warnings={len(warnings)}")
    return 1 if truth['compilationFailed'] or errors or truth.get('consoleErrors', 0) else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
