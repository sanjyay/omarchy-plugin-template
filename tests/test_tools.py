import argparse
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from repo_checks import inspect_tree, validate, TOKEN


class ToolTests(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / '.test-tmp'
        temporary.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='plugin tests ', dir=temporary)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / 'checkout with spaces'
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(
            '.git', '.test-tmp', '__pycache__', '.source-baseline.json', '.init-transaction'))
        # After personalization, initializer fixtures no longer exist. Synthesize
        # them from a tiny explicit contract, not by undoing user metadata.
        if json.loads((self.repo / '.template.json').read_text())['initialized']:
            self.restore_template_fixture()
        (self.repo / '.git').mkdir()
        (self.repo / '.git' / 'sentinel').write_bytes(b'never change\0')

    def restore_template_fixture(self):
        manifest = {'schemaVersion': 1, 'id': '@@ID@@', 'name': '@@NAME@@',
                    'author': '@@AUTHOR@@', 'description': '@@DESCRIPTION@@',
                    'license': 'MIT', 'version': '0.1.0', 'kinds': ['bar-widget'],
                    'entryPoints': {'barWidget': 'Main.qml'}}
        (self.repo / 'manifest.json').write_text(json.dumps(manifest))
        (self.repo / 'Main.qml').write_text('import QtQuick\nItem { property string name: "@@NAME@@"; property string moduleName: "@@ID@@" }\n')
        (self.repo / 'README.md').write_text('# @@NAME@@\n@@DESCRIPTION@@\n@@ID@@\n@@AUTHOR@@\n')
        (self.repo / 'LICENSE').write_text('@@YEAR@@ @@AUTHOR@@\n')
        (self.repo / '.template.json').write_text('{"schemaVersion":1,"initialized":false}\n')

    def invoke(self, tool, *args):
        return subprocess.run([sys.executable, str(self.repo / 'tools' / tool), *args],
                              cwd=self.base, capture_output=True, text=True, timeout=20,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def init(self, **overrides):
        values = {'name': 'PeekBar', 'id': 'sanjyay.peekbar',
                  'description': 'Reveal the bar', **overrides}
        argv = [item for k, v in values.items() for item in ('--' + k, v)]
        return self.invoke('init-plugin', *argv)

    def snapshot(self):
        return {p.relative_to(self.repo).as_posix(): (p.read_bytes(), p.stat().st_mode)
                for p in self.repo.rglob('*') if p.is_file()}

    def test_help_has_no_mutation(self):
        before = self.snapshot()
        for tool in ('init-plugin', 'check'):
            result = self.invoke(tool, '--help')
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_init_updates_all_contexts_and_preserves_git(self):
        result = self.init(name='Café "bar" $() `x` \\ done', author='A & B',
                           description='An <example> with "quotes"')
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.repo / 'manifest.json').read_text())
        self.assertEqual(manifest['name'], 'Café "bar" $() `x` \\ done')
        self.assertEqual(manifest['author'], 'A & B')
        self.assertIn('A & B', (self.repo / 'LICENSE').read_text())
        self.assertEqual((self.repo / '.git/sentinel').read_bytes(), b'never change\0')
        errors, files = inspect_tree(self.repo)
        self.assertEqual(errors + validate(self.repo, files, template=False), [])
        for rel, data in files.items():
            if not rel.startswith(('tools/', 'tests/')):
                self.assertFalse(TOKEN.search(data.decode(errors='replace')), rel)
        result = self.invoke('check', '--portable')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repeat_refused_unchanged(self):
        self.assertEqual(self.init().returncode, 0)
        before = self.snapshot()
        self.assertNotEqual(self.init().returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_bad_values_never_write(self):
        before = self.snapshot()
        cases = [('id', 'peekbar'), ('id', 'omarchy.foo'), ('id', '../oops'),
                 ('id', 'a..b'), ('id', 'a.b/c'), ('id', 'a.B'), ('name', ''),
                 ('name', ' white'), ('name', 'bad\nvalue'), ('name', 'x' * 81),
                 ('description', '@@NAME@@'), ('author', '\x1b[31m')]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.assertNotEqual(self.init(**{key: value}).returncode, 0)
                self.assertEqual(before, self.snapshot())

    def test_missing_and_unknown_options(self):
        before = self.snapshot()
        for args in [[], ['--wat'], ['--na', 'foo']]:
            self.assertNotEqual(self.invoke('init-plugin', *args).returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_unknown_placeholder_refused(self):
        (self.repo / 'extra.md').write_text('@@FORGOTTEN@@')
        before = self.snapshot()
        self.assertNotEqual(self.init().returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_symlink_and_fifo_refused_without_touching_target(self):
        target = self.base / 'outside'
        target.write_text('foreign')
        path = self.repo / 'README.md'
        path.unlink()
        path.symlink_to(target)
        self.assertNotEqual(self.init().returncode, 0)
        self.assertEqual(target.read_text(), 'foreign')
        path.unlink()
        os.mkfifo(path)
        self.assertNotEqual(self.init().returncode, 0)

    def test_intermediate_link_and_hardlink(self):
        target = self.base / 'foreign'
        target.mkdir()
        (self.repo / 'linked-directory').symlink_to(target, target_is_directory=True)
        self.assertNotEqual(self.init().returncode, 0)
        (self.repo / 'linked-directory').unlink()
        os.link(self.repo / 'README.md', self.repo / 'hardlinked.md')
        self.assertNotEqual(self.init().returncode, 0)

    def test_failed_replace_rolls_back(self):
        loader = importlib.machinery.SourceFileLoader('initializer', str(self.repo / 'tools/init-plugin'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        before = self.snapshot()
        replace = os.replace
        calls = 0
        def fail_second(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected write failure')
            return replace(src, dst)
        args = argparse.Namespace(name='Example', id='acme.example', description='Example', author='Acme')
        with patch.object(module.os, 'replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                module.initialize(self.repo, args)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.repo / '.init-transaction').exists())

    def test_interrupted_transaction_refused(self):
        (self.repo / '.init-transaction').mkdir()
        self.assertNotEqual(self.init().returncode, 0)

    def test_check_template_and_initialized_modes(self):
        self.assertEqual(self.invoke('check', '--template', '--portable').returncode, 0)
        self.assertNotEqual(self.invoke('check', '--portable').returncode, 0)
        self.assertEqual(self.init().returncode, 0)
        self.assertNotEqual(self.invoke('check', '--template', '--portable').returncode, 0)

    def test_check_rejects_real_packaging_errors(self):
        self.assertEqual(self.init().returncode, 0)
        original = (self.repo / 'manifest.json').read_text()
        cases = [('schemaVersion', True), ('kinds', ['overlay']),
                 ('entryPoints', {'barWidget': '../Main.qml'}),
                 ('barWidget', {'defaultSection': 'top'}), ('version', 'banana')]
        for field, val in cases:
            with self.subTest(field=field):
                manifest = json.loads(original)
                manifest[field] = val
                (self.repo / 'manifest.json').write_text(json.dumps(manifest))
                self.assertNotEqual(self.invoke('check', '--portable').returncode, 0)
        (self.repo / 'manifest.json').write_text(original)
        for rel, text in [('bad.md', '[broken](missing.qml)'),
                          ('bad.qml', 'import "missing.js" as Missing'),
                          ('bad.py', 'invalid syntax !'),
                          ('bad.sh', '#!/bin/bash\neval "$INPUT"\n')]:
            path = self.repo / rel
            path.write_text(text)
            path.chmod(0o755)
            self.assertNotEqual(self.invoke('check', '--portable').returncode, 0)
            path.unlink()
        (self.repo / 'tools/init-plugin').chmod(0o644)
        self.assertNotEqual(self.invoke('check', '--portable').returncode, 0)

    def test_check_duplicate_json_and_missing_file(self):
        (self.repo / 'manifest.json').write_text('{"schemaVersion":1,"schemaVersion":1}')
        self.assertNotEqual(self.invoke('check', '--template', '--portable').returncode, 0)
        (self.repo / 'manifest.json').unlink()
        self.assertNotEqual(self.init().returncode, 0)

    def test_optional_helper_can_be_removed(self):
        (self.repo / 'scripts/bounded_process.py').unlink()
        (self.repo / 'tests/test_process.py').unlink()
        self.assertEqual(self.init().returncode, 0)
        result = self.invoke('check', '--portable')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shell_syntax_is_actually_checked(self):
        self.assertEqual(self.init().returncode, 0)
        script = self.repo / 'scripts/example.sh'
        script.write_text('#!/bin/bash\nif then\n')
        script.chmod(0o755)
        self.assertNotEqual(self.invoke('check', '--portable').returncode, 0)
        script.write_text("#!/bin/bash\nprintf '%s\\n' \"hello world\"\n")
        result = self.invoke('check', '--portable')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_state_is_rejected(self):
        (self.repo / '.template.json').write_text('{"schemaVersion":true,"initialized":false}')
        before = self.snapshot()
        self.assertNotEqual(self.init().returncode, 0)
        self.assertEqual(before, self.snapshot())
