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
    'cache', 'temp', 'tmp', 'logs', 'crash', 'dumps',
    'thumbnails', 'iconcache',
    'installcache', '.npm', '.yarn', '.gradle', '.m2',
    '.cache', '.cargo', '__pycache__', 'node_modules',
    'code cache', 'serviceworker',
    'blob_storage', 'webfonts',
    'thumbcache', 'fontcache', 'shadercache',
    'dxcache', 'gpucache', 'cef_cache', 'grcache',
    'crashpad', 'crash-reports', 'crashdumps',
    'update-cache', 'squirrel-temp', 'nuget',
    '.pytest_cache', '.mypy_cache', '.tox',
    '.eggs', 'egg-info', '.parcel-cache',
]

LOG_PATTERNS = [
    'logs', 'crash', 'crashpad', 'crash-reports',
    'diagnostics', 'logfiles', 'eventlog',
]

DEV_PATTERNS = [
    'node_modules', '__pycache__',
    'dist', 'build', 'out', 'target',
    '.venv', 'venv',
    '__snapshot__', 'coverage', '.nyc_output',
    '.cache', '.parcel-cache',
    '.next', '.nuxt', '.output', '.vercel', '.svelte-kit',
    '.dart_tool', '.gradle', '.m2',
    '.tox', '.eggs', '.pytest_cache', '.mypy_cache',
    'bower_components', 'jspm_packages',
    '.sass-cache', 'composer',
    'carthage', '.build', '.swiftpm',
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
    r'Local\Google\Chrome\User Data\Default\GPUCache',
    r'Local\Google\Chrome\User Data\Default\ShaderCache',
    r'Local\Microsoft\Edge\User Data\Default\Cache',
    r'Local\Microsoft\Edge\User Data\Default\Code Cache',
    r'Local\Microsoft\Edge\User Data\Default\Service Worker',
    r'Local\Microsoft\Edge\User Data\Default\GPUCache',
    r'Local\npm-cache', r'Local\pip\cache', r'Local\Yarn\Cache',
    r'Local\Microsoft\Windows\AppCache',
    r'Roaming\Mozilla\Firefox\Profiles',
    r'Local\Discord\Cache', r'Local\Discord\Code Cache',
    r'Local\Discord\Video Cache', r'Local\Discord\GPUCache',
    r'Local\Slack\Cache', r'Local\Slack\Service Worker',
    r'Local\Slack\Code Cache', r'Local\Slack\GPUCache',
    r'Local\Spotify\Data', r'Local\Microsoft\Teams\old_scripts',
    r'Local\Microsoft\Teams\Cache', r'Local\Microsoft\Teams\Code Cache',
    r'Local\Microsoft\Teams\GPUCache',
    r'Roaming\Spotify\Browser\Cache',
    r'Local\Microsoft\OneDrive\logs',
    r'Local\Microsoft\Windows\WER',
    r'Local\Zoom\logs', r'Local\Zoom\cache',
    r'Local\Microsoft\VisualStudio\17.0\scoped_cache',
    r'Local\Microsoft\VisualStudio\17.0\ComponentModelCache',
    r'Local\JetBrains\Roaming\cache',
    r'Local\JetBrains\Roaming\indexCache',
    r'Local\JetBrains\Roaming\log',
    r'Local\JetBrains\Roaming\threadIndex',
    r'Roaming\Code\Cache', r'Roaming\Code\logs',
    r'Roaming\Code\CachedData', r'Roaming\Code\CachedExtensionVSIXs',
    r'Roaming\Code\CachedExtensions',
    r'Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\TempState',
    r'Local\Microsoft\Windows\INetCookies',
    r'Local\Microsoft\Windows\History',
    r'Local\Microsoft\Windows\PrivacIE',
    r'Local\PeerDistRepub',
    r'Local\Microsoft\Windows\Explorer\ExplicitCache',
    r'Local\Microsoft\Windows\WER\ReportQueue',
    r'Local\Microsoft\Windows\WER\ReportArchive',
    r'Local\Microsoft\TokenBroker\Cache',
    r'Local\Microsoft\Windows\CloudStore',
    r'Local\Microsoft\Windows\Notifications',
    r'Local\Packages\MicrosoftEdge_8wekyb3d8bbwe\AC\MicrosoftEdge\Cache',
    r'Local\Packages\MicrosoftEdge_8wekyb3d8bbwe\AC\MicrosoftEdge\Code Cache',
    r'Local\Packages\MicrosoftEdge_8wekyb3d8bbwe\AC\MicrosoftEdge\GPUCache',
    r'Local\Packages\MicrosoftEdge_8wekyb3d8bbwe\AC\MicrosoftEdge\Service Worker',
    r'Local\Packages\MicrosoftEdge_8wekyb3d8bbwe\TempState',
    r'Local\Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\LocalCache',
    r'Local\Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\TempState',
    r'Local\Packages\Microsoft.SkypeApp_kzf8qxf38zg5c\LocalCache',
    r'Local\Packages\Microsoft.SkypeApp_kzf8qxf38zg5c\TempState',
    r'Local\Microsoft\WindowsApps',
    r'Local\Microsoft\GameDVR',
    r'Local\Microsoft\Windows\GameExplorer',
    r'Local\Microsoft\DirectX',
    r'Local\D3DSCache',
    r'Local\NVIDIA\DXCache',
    r'Local\NVIDIA\GLCache',
    r'Local\AMD\DxCache',
    r'Local\Intel\ShaderCache',
]

CARD_CFG = [
    ("USER",     "📁", "Perfil do Usuário",     "#0078D4"),
    ("APPDATA",  "📂", "AppData",               "#0078D4"),
    ("EMPTY",    "📭", "Pastas Vazias",         "#5C2D91"),
    ("CACHE",    "🗑️", "Cache/Temporários",     "#D83B01"),
    ("LARGE_OLD","⚠️", "Arquivos +1 ano",       "#E81123"),
    ("DEV",      "🔧", "Dev Junk",              "#6B3FA0"),
    ("DOWNLOADS","📥", "Downloads Antigos",      "#00B294"),
    ("LOGS",     "📋", "Logs",                   "#FF8C00"),
]

TABS = [
    ("USER",     "📁 Perfil do Usuário"),
    ("APPDATA",  "📂 AppData"),
    ("EMPTY",    "📭 Pastas Vazias"),
    ("CACHE",    "🗑️ Cache e Temporários"),
    ("LARGE_OLD","⚠️  Arquivos +1 ano (100MB+)"),
    ("DEV",      "🔧 Dev Junk"),
    ("DOWNLOADS","📥 Downloads Antigos"),
    ("LOGS",     "📋 Logs"),
]
