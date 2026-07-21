"""
find_missing_help.py

Scan the SignalIntegrity App source for help keys referenced by devices
(PartPropertyHelp('device:...')) and control elements
(AddHelpElement('Control-Help:...') and similar), then report which of those
keys do NOT exist in the built help system (helpkeys file).
"""
import os
import re

APP_DIR = os.path.join(os.path.dirname(__file__), 'SignalIntegrity', 'App')
HELPKEYS = os.path.join(
    os.path.dirname(__file__), '..', 'SignalIntegrityPages',
    'SignalIntegrity', 'App', 'Help', 'site', 'helpkeys')

# Patterns that register a help key in the source.
REF_RE = re.compile(
    r"(?:AddHelpElement|PartPropertyHelp)\(\s*['\"]([^'\"]*)['\"]")

def existing_keys():
    keys = set()
    with open(HELPKEYS, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' >>> ')
            keys.add(parts[0])
    return keys

def referenced_keys():
    refs = {}  # key -> list of (file, line)
    for root, _dirs, files in os.walk(APP_DIR):
        for name in files:
            if not name.endswith('.py'):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    for i, line in enumerate(f, 1):
                        for m in REF_RE.finditer(line):
                            key = m.group(1)
                            refs.setdefault(key, []).append(
                                (os.path.relpath(path, APP_DIR), i))
            except OSError:
                continue
    return refs

def main():
    existing = existing_keys()
    refs = referenced_keys()

    missing_devices = []
    missing_controls = []
    missing_other = []
    for key, locs in sorted(refs.items()):
        if key == '' or key.endswith(':'):
            # empty / placeholder help keys
            bucket = missing_other
        elif key in existing:
            continue
        elif key.startswith('device:'):
            bucket = missing_devices
        elif key.startswith('Control-Help:'):
            bucket = missing_controls
        else:
            bucket = missing_other
        bucket.append((key, locs))

    def dump(title, items):
        print('=' * 70)
        print(title, '(%d)' % len(items))
        print('=' * 70)
        for key, locs in items:
            loc = ', '.join('%s:%d' % l for l in locs)
            print('  %-45s %s' % (repr(key), loc))
        print()

    dump('DEVICES with no help entry', missing_devices)
    dump('CONTROL ELEMENTS with no help entry', missing_controls)
    dump('OTHER / placeholder help keys', missing_other)

    print('Total referenced keys: %d' % len(refs))
    print('Total existing help keys: %d' % len(existing))

if __name__ == '__main__':
    main()
