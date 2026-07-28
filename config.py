import os
import time
from pathlib import Path

# General Clean Up Paths and Configuration
HOME = os.environ.get("USERPROFILE", str(Path.home()))
APPD = os.path.join(HOME, "AppData")
CUTOFF = time.time() - 365 * 24 * 3600
BIG = 100 * 1024 * 1024

SKIP_DIRS = frozenset({
    'windows', 'program files', 'program files (x86)', '$recycle.bin',
    'system volume information', 'perflogs', 'recovery', 'winnt',
    'all users', 'default user', 'public', 'default',
})

CACHE_PATTERNS = [
    'cache', 'temp', 'tmp', 'logs', 'log', 'crash', 'dumps',
    'thumbnails', 'iconcache', 'recent', 'history',
    'installer', 'installcache', '.npm', '.yarn', '.gradle', '.m2',
    '.cache', '.cargo', '__pycache__', 'node_modules',
    'code cache', 'serviceworker', 'session storage', 'local storage',
    'blob_storage', 'webfonts', '.git'
]

KNOWN_CACHE = [
    r'Local\Temp',
    r'Local\Microsoft\Windows\INetCache',
    r'Local\Microsoft\Windows\Temporary Internet Files',
    r'Local\CrashDumps',
    r'Local\Microsoft\Terminal Server Client\Cache',
    r'LocalLow',
    r'Local\Google\Chrome\User Data\Default\Cache',
    r'Local\Google\Chrome\User Data\Default\Code Cache',
    r'Local\Google\Chrome\User Data\Default\Service Worker',
    r'Local\Microsoft\Edge\User Data\Default\Cache',
    r'Local\Microsoft\Edge\User Data\Default\Code Cache',
    r'Local\Microsoft\Edge\User Data\Default\Service Worker',
    r'Local\npm-cache', r'Local\pip\cache', r'Local\Yarn\Cache',
    r'Local\Microsoft\Windows\AppCache',
    r'Roaming\Mozilla\Firefox\Profiles',
    r'Local\Discord\Cache', r'Local\Discord\Code Cache',
    r'Local\Slack\Cache', r'Local\Slack\Service Worker',
    r'Local\Spotify\Data', r'Local\Microsoft\Teams\old_scripts',
    r'Roaming\Spotify\Browser\Cache',
    r'Local\Microsoft\OneDrive\logs',
    r'Local\Microsoft\Windows\WER',
]

CARD_CFG = [
    ("USER",     "📁", "Perfil do Usuário",     "#0078D4"),
    ("APPDATA",  "📂", "AppData",               "#0078D4"),
    ("EMPTY",    "📭", "Pastas Vazias",         "#5C2D91"),
    ("CACHE",    "🗑️", "Cache/Temporários",     "#D83B01"),
    ("LARGE_OLD","⚠️", "Arquivos +1 ano",       "#E81123"),
]

TABS = [
    ("USER",     "📁 Perfil do Usuário"),
    ("APPDATA",  "📂 AppData"),
    ("EMPTY",    "📭 Pastas Vazias"),
    ("CACHE",    "🗑️ Cache e Temporários"),
    ("LARGE_OLD","⚠️  Arquivos +1 ano (100MB+)"),
]
