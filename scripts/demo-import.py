#!/usr/bin/env python3
"""Run a complete import/update example using only temporary local Git repos."""
import difflib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*args, cwd):
    result = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main():
    with tempfile.TemporaryDirectory(prefix='plugin-import-demo-') as dirname:
        root = Path(dirname)
        upstream, consumer = root / 'upstream', root / 'consumer'
        skill = upstream / 'skills' / 'example'
        skill.mkdir(parents=True)
        text = '---\nname: example\ndescription: A synthetic import demonstration.\n---\n\nSummarize the supplied text.\n'
        (skill / 'SKILL.md').write_text(text)
        run('git', 'init', '-b', 'main', cwd=upstream)
        run('git', 'config', 'user.name', 'Local example', cwd=upstream)
        run('git', 'config', 'user.email', 'example@example.invalid', cwd=upstream)
        run('git', 'config', 'commit.gpgSign', 'false', cwd=upstream)
        run('git', 'add', '.', cwd=upstream)
        run('git', 'commit', '-m', 'Initial skill', cwd=upstream)
        (consumer / 'scripts').mkdir(parents=True)
        shutil.copy2(Path(__file__).with_name('skills.py'), consumer / 'scripts/skills.py')
        for path, data in [('.claude-plugin/marketplace.json', {'name': 'example', 'plugins': []}),
                           ('.agents/plugins/marketplace.json', {'name': 'example', 'plugins': []}),
                           ('sources.json', {'sources': []}), ('sources.lock.json', {'sources': {}})]:
            dest = consumer / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(data))
        def cli(*args):
            return run(sys.executable, 'scripts/skills.py', *args, cwd=consumer)
        print('$ skills.py add <local-upstream> --path skills/example --plugin demo-bundle')
        print(cli('add', str(upstream), '--path', 'skills/example', '--plugin', 'demo-bundle'))
        plugin = consumer / 'plugins/demo-bundle'
        installed = plugin / 'skills/example/SKILL.md'
        before = installed.read_text()
        assert before == text
        print('Generated: provider manifests, bundled SKILL.md, source registration and revision lock.')
        version = lambda: json.loads((plugin / '.claude-plugin/plugin.json').read_text())['version']
        assert version() == '0.1.0'
        updated = text + '\nInclude a short list of unresolved questions.\n'
        (skill / 'SKILL.md').write_text(updated)
        run('git', 'add', '.', cwd=upstream)
        run('git', 'commit', '-m', 'Add unresolved questions', cwd=upstream)
        print('\n$ skills.py sync --check')
        print(cli('sync', '--check'))
        assert installed.read_text() == before, 'Dry run modified installed files'
        print('\n$ skills.py sync --apply')
        print(cli('sync', '--apply'))
        assert installed.read_text() == updated
        assert version() == '0.1.1'
        locked = json.loads((consumer / 'sources.lock.json').read_text())['sources']['demo-bundle']['skills']['example']
        assert locked['commit'] == run('git', 'rev-parse', 'HEAD', cwd=upstream)
        print(''.join(difflib.unified_diff(before.splitlines(True), installed.read_text().splitlines(True),
              fromfile='before/SKILL.md', tofile='after/SKILL.md')))
        print('Verified version: 0.1.0 -> 0.1.1; revision lock matches upstream.')
        print(cli('sync', '--apply'))
        assert version() == '0.1.1', 'Unchanged sync bumped version'
        print('Example complete; temporary repositories removed on exit.')


if __name__ == '__main__':
    main()
