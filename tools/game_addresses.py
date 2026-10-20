"""Read the 1.0.0 patch-address table also included by the C/C++ runtime.

The header is the authoritative data; no generated copy or Python address list
needs updating alongside it. Runtime-only constants are kept in a separate header
so adding one does not invalidate generated code. Game-version selection remains unchanged.

Entries are GA(offset) / GA_SDK(offset), relative to the guest base (runtime/guest_base.h);
LARECOMP_GUEST_BASE overrides the default base, as -DLARECOMP_GUEST_BASE does for the runtime.
"""
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace

GUEST_BASE = int(os.environ.get('LARECOMP_GUEST_BASE', '0x7000000000'), 0)
MAIN_BASE = GUEST_BASE
SDK_BASE = GUEST_BASE + 0x0004000000


def load_table(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.startswith('#define GA_'):
            continue
        match = re.fullmatch(r'#define GA_([A-Z][A-Z0-9_]*)\s+(GA|GA_SDK|UINT64_C)\((0x[0-9a-f]+)\)', line)
        if not match or match[1] in values:
            raise ValueError(f'Invalid or duplicate game-address definition: {line}')
        base = MAIN_BASE if match[2] == 'GA' else SDK_BASE if match[2] == 'GA_SDK' else 0
        values[match[1]] = base + int(match[3], 16)
    if not values:
        raise ValueError('Empty game-address table')
    return values


_root = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(__file__).resolve().parent.parent
TABLE_PATH = _root / 'runtime/game_addresses/patches_v1_0_0.h'
ADDRESS = SimpleNamespace(**load_table(TABLE_PATH))


def addr_text(code):
    """Expand @NAME@ as hex digits inside generated-C addresses, symbols or labels."""
    return re.sub(r'@([A-Z][A-Z0-9_]*)@', lambda m: f'{getattr(ADDRESS, m[1]):x}', code)
