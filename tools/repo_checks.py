"""Portable repository checks shared by check and initializer preflight."""
import ast
import json
import os
from pathlib import Path
import re
import stat

TOKEN = re.compile(r'@@([A-Z][A-Z0-9_]*)@@')
REQUIRED = ('manifest.json', 'README.md', 'LICENSE', 'AGENTS.md', 'ARCHITECTURE.md',
            'tools/check', 'tools/init-plugin', 'tools/repo_checks.py', '.template.json')
PLACEHOLDERS = {
    'manifest.json': {'ID', 'NAME', 'AUTHOR', 'DESCRIPTION'},
    'Main.qml': {'ID', 'NAME'},
    'README.md': {'ID', 'NAME', 'DESCRIPTION', 'AUTHOR'},
    'LICENSE': {'YEAR', 'AUTHOR'},
}
KIND_KEYS = {'bar-widget': 'barWidget', 'bar': 'bar', 'overlay': 'overlay',
             'panel': 'panel', 'menu': 'menu', 'service': 'service'}
TEXT_SUFFIXES = {'.qml', '.js', '.mjs', '.py', '.sh', '.json', '.md', '.yml', '.yaml'}


def inspect_tree(root):
    errors, files = [], {}
    def walk(directory):
        for p in sorted(directory.iterdir()):
            rel = p.relative_to(root).as_posix()
            if p.name == '.git':
                continue
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode):
                errors.append(f'{rel}: symlinks are not allowed')
            elif stat.S_ISDIR(mode):
                if rel == '.test-tmp':
                    continue
                if p.name in {'__pycache__', 'node_modules', '.venv', '.init-transaction'}:
                    errors.append(f'{rel}: generated or unfinished content in package; remove it')
                else:
                    walk(p)
            elif not stat.S_ISREG(mode):
                errors.append(f'{rel}: special file is not allowed')
            elif p.stat().st_nlink != 1:
                errors.append(f'{rel}: hardlinked files are not supported')
            elif p.stat().st_size > 8 * 1024 * 1024:
                errors.append(f'{rel}: exceeds 8 MiB packaging budget; review before raising limit')
            else:
                files[rel] = p.read_bytes()
                if mode & (stat.S_ISUID | stat.S_ISGID | stat.S_IWOTH):
                    errors.append(f'{rel}: unsafe permissions')
    walk(root)
    return errors, files


def json_object(data):
    def unique(pairs):
        result = {}
        for key, val in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key {key}')
            result[key] = val
        return result
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def safe_path(path):
    return (isinstance(path, str) and bool(path) and not path.startswith('/')
            and '..' not in path and '\\' not in path
            and all(c.isprintable() for c in path)
            and all(p not in ('', '.') for p in path.split('/')))


def validate(root, files, *, template):
    errors = []
    for rel in REQUIRED:
        if rel not in files:
            errors.append(f'missing required file: {rel}')
    try:
        state = json_object(files.get('.template.json', b'{}'))
        if (type(state) is not dict or type(state.get('schemaVersion')) is not int or state.get('schemaVersion') != 1
                or type(state.get('initialized')) is not bool):
            errors.append('.template.json: invalid initialization state')
        elif state['initialized'] == template:
            errors.append('use --template only before initialization; otherwise initialize first')
        manifest = json_object(files.get('manifest.json', b'{}'))
        if type(manifest) is not dict:
            raise ValueError('manifest must be an object')
    except (ValueError, UnicodeError) as exc:
        return errors + [f'invalid JSON metadata: {exc}']
    if type(manifest.get('schemaVersion')) is not int or manifest['schemaVersion'] != 1:
        errors.append('manifest: schemaVersion must be the number 1')
    for field in ('id', 'name', 'version', 'author', 'description', 'license'):
        val = manifest.get(field)
        if not isinstance(val, str) or not val.strip() or any(not c.isprintable() for c in val):
            errors.append(f'manifest: {field} must be nonempty printable text')
    for field, limit in {'id': 128, 'name': 80, 'version': 64, 'author': 100,
                         'description': 300}.items():
        if isinstance(manifest.get(field), str) and len(manifest[field]) > limit:
            errors.append(f'manifest: {field} exceeds {limit} characters')
    plugin_id = manifest.get('id', '')
    if isinstance(plugin_id, str) and not (template and plugin_id == '@@ID@@'):
        if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', plugin_id)
                or '..' in plugin_id or plugin_id.startswith('omarchy.')):
            errors.append('manifest: invalid or reserved id')
    version = manifest.get('version', '')
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?', version):
        errors.append('manifest: use a semantic version, e.g. 0.1.0')
    kinds, entries = manifest.get('kinds'), manifest.get('entryPoints')
    if (not isinstance(kinds, list) or not kinds
            or any(not isinstance(k, str) or k not in KIND_KEYS for k in kinds)):
        errors.append('manifest: kinds must contain supported plugin kinds')
        kinds = []
    elif len(set(kinds)) != len(kinds):
        errors.append('manifest: duplicate kinds')
    if not isinstance(entries, dict):
        errors.append('manifest: entryPoints must be an object')
        entries = {}
    for kind in kinds:
        if KIND_KEYS[kind] not in entries:
            errors.append(f'manifest: {kind} requires entryPoints.{KIND_KEYS[kind]}')
    for key, path in entries.items():
        if not safe_path(path) or path not in files or not path.endswith('.qml'):
            errors.append(f'manifest: unsafe, missing or non-QML entry point {key}')
    if 'keepLoaded' in manifest and type(manifest['keepLoaded']) is not bool:
        errors.append('manifest: keepLoaded must be boolean')
    if 'bar-widget' in kinds:
        widget = manifest.get('barWidget', {})
        if not isinstance(widget, dict):
            errors.append('manifest: barWidget must be an object')
        else:
            if widget.get('defaultSection', 'right') not in ('left', 'center', 'right'):
                errors.append('manifest: invalid defaultSection')
            if 'allowMultiple' in widget and type(widget['allowMultiple']) is not bool:
                errors.append('manifest: allowMultiple must be boolean')
    for rel, data in files.items():
        p = Path(rel)
        if p.name in {'.DS_Store', '.env'} or p.suffix in {'.pyc', '.swp', '.bak'}:
            errors.append(f'{rel}: unwanted package artifact')
        try:
            text = data.decode('utf-8')
        except UnicodeError:
            if p.suffix in TEXT_SUFFIXES:
                errors.append(f'{rel}: expected UTF-8')
            continue
        tokens = set(TOKEN.findall(text))
        # Only these exact infrastructure files contain intentional literals.
        literal_sources = {'tools/repo_checks.py', 'tools/init-plugin', 'tests/test_tools.py'}
        if rel in literal_sources:
            if tokens - {'ID', 'NAME', 'AUTHOR', 'DESCRIPTION', 'YEAR', 'FORGOTTEN'}:
                errors.append(f'{rel}: unknown tooling placeholder')
        else:
            expected = PLACEHOLDERS.get(rel, set()) if template else set()
            if tokens != expected:
                errors.append(f'{rel}: unexpected or missing template placeholders {sorted(tokens ^ expected)}')
            if '@@' in TOKEN.sub('', text):
                errors.append(f'{rel}: malformed template delimiter')
        if re.search(r'^(?:<{7}|={7}|>{7})(?: |$)', text, re.M):
            errors.append(f'{rel}: possible merge-conflict marker')
        if p.suffix == '.py' or text.startswith('#!/usr/bin/env python3'):
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as exc:
                errors.append(f'{rel}: {exc}')
        if text.startswith('#!') and not os.access(root / rel, os.X_OK):
            errors.append(f'{rel}: shebang script must be executable')
        if p.suffix == '.qml':
            for target in re.findall(r'(?:Qt\.resolvedUrl\(|\bsource\s*:)\s*["\']([^"\']+)["\']', text):
                if ':' not in target and target and not (p.parent / target).as_posix() in files:
                    errors.append(f'{rel}: missing local asset {target}')
            for target in re.findall(r'^import\s+["\']([^"\']+)["\']', text, re.M):
                local = os.path.normpath(str(p.parent / target))
                if local != '.' and local not in files and not any(f.startswith(local.rstrip('/') + '/') for f in files):
                    errors.append(f'{rel}: missing local import {target}')
        if p.suffix == '.md':
            for target in re.findall(r'\]\(([^\s)]+)\)', text):
                if ':' in target or target.startswith('#'):
                    continue
                local = os.path.normpath(str(p.parent / target.split('#')[0]))
                if local not in files and not any(f.startswith(local.rstrip('/') + '/') for f in files):
                    errors.append(f'{rel}: broken local link {target}')
    return errors
