import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QThread, Signal
import send2trash
from utils import dir_size
from config import (
    HOME, APPD, SKIP_DIRS, CACHE_PATTERNS, KNOWN_CACHE, BIG, CUTOFF,
    DEV_PATTERNS, LOG_PATTERNS
)

class Cancelled(Exception):
    pass


class ScanWorker(QThread):
    item = Signal(str, object, str)
    status = Signal(str)
    progress = Signal(int, int)
    done = Signal()

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self._abort = False
        self._emitted = set()

    def abort(self):
        self._abort = True

    def _check(self):
        if self._abort:
            raise Cancelled()

    def _already_covered(self, path):
        p = os.path.normcase(os.path.normpath(path))
        cur = p
        while True:
            parent = os.path.dirname(cur)
            if cur in self._emitted:
                return True
            if parent == cur:
                break
            cur = parent
        self._emitted.add(p)
        return False

    def run(self):
        try:
            if self.kind == "USER":
                self._scan_root(HOME, skip_appdata=True)
            elif self.kind == "APPDATA":
                self._scan_root(APPD, skip_appdata=False)
            elif self.kind == "EMPTY":
                self._scan_empty()
            elif self.kind == "CACHE":
                self._scan_cache()
            elif self.kind == "LARGE_OLD":
                self._scan_old()
            elif self.kind == "DEV":
                self._scan_dev()
            elif self.kind == "DOWNLOADS":
                self._scan_downloads()
            elif self.kind == "LOGS":
                self._scan_logs()
        except Cancelled:
            self.status.emit("Cancelado pelo usuário.")
        finally:
            self.done.emit()

    # USER / APPDATA — top-level entries calculated sequentially in the background
    def _scan_root(self, root, skip_appdata):
        self.status.emit("Analisando diretórios...")
        self._check()
        if not os.path.isdir(root):
            return

        items = []
        try:
            with os.scandir(root) as it:
                for e in it:
                    self._check()
                    n = e.name.lower()
                    if skip_appdata and 'appdata' in n:
                        continue
                    if n in SKIP_DIRS:
                        continue
                    items.append(e)
        except PermissionError:
            pass

        total = len(items)
        self.progress.emit(0, total)
        
        for i, e in enumerate(items):
            self._check()
            try:
                if e.is_dir(follow_symlinks=False):
                    # Calcula sequencialmente (evita sobrecarga de threads concurrentes e I/O thrashing)
                    sz = dir_size(e.path, self._check)
                    self.item.emit(e.path, sz, "")
                elif e.is_file(follow_symlinks=False):
                    self.item.emit(e.path, e.stat().st_size, "")
            except (PermissionError, OSError):
                pass
            self.progress.emit(i + 1, total)
        self.progress.emit(total, total)

    # EMPTY
    def _scan_empty(self):
        self.status.emit("Procurando pastas vazias...")
        for base in (HOME, APPD):
            if not os.path.isdir(base):
                continue
            try:
                stack = [base]
                while stack:
                    self._check()
                    cur = stack.pop()
                    try:
                        empty = True
                        with os.scandir(cur) as it:
                            for e in it:
                                n = e.name.lower()
                                if e.is_dir(follow_symlinks=False):
                                    if n not in SKIP_DIRS:
                                        stack.append(e.path)
                                empty = False
                        if empty:
                            self.item.emit(cur, 0, "Vazia")
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

    # CACHE
    def _scan_cache(self):
        self.status.emit("Verificando caches conhecidos...")
        self._emitted = set()
        base = Path(APPD)
        for rel in KNOWN_CACHE:
            self._check()
            t = base / rel
            if t.exists():
                if self._already_covered(str(t)):
                    continue
                sz = dir_size(str(t), self._check)
                self.item.emit(str(t), sz, f"Cache: {t.name}")

        self.status.emit("Buscando pastas de cache por nome...")
        self._find_caches(APPD, 0)

    def _find_caches(self, path, depth):
        if depth > 3 or not os.path.isdir(path):
            return
        try:
            with os.scandir(path) as it:
                for e in it:
                    self._check()
                    if not e.is_dir(follow_symlinks=False):
                        continue
                    n = e.name.lower()
                    if any(p in n for p in CACHE_PATTERNS):
                        if self._already_covered(e.path):
                            continue
                        sz = dir_size(e.path, self._check)
                        self.item.emit(e.path, sz, "Cache/Temp")
                    else:
                        self._find_caches(e.path, depth + 1)
        except PermissionError:
            pass

    # LARGE OLD
    def _scan_old(self):
        self.status.emit("Buscando >100MB sem mod. +1 ano...")
        stack = [HOME]
        while stack:
            self._check()
            cur = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for e in it:
                        self._check()
                        n = e.name.lower()
                        if n in SKIP_DIRS:
                            continue
                        try:
                            if e.is_file(follow_symlinks=False):
                                st = e.stat()
                                if st.st_size >= BIG and st.st_mtime < CUTOFF:
                                    d = datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y")
                                    self.item.emit(e.path, st.st_size, f"Mod: {d}")
                            elif e.is_dir(follow_symlinks=False):
                                stack.append(e.path)
                        except (PermissionError, OSError):
                            pass
            except PermissionError:
                pass

    # DEV JUNK
    def _scan_dev(self):
        self.status.emit("Procurando lixo de desenvolvimento...")
        for base in (HOME, APPD):
            if not os.path.isdir(base):
                continue
            try:
                stack = [base]
                while stack:
                    self._check()
                    cur = stack.pop()
                    try:
                        with os.scandir(cur) as it:
                            for e in it:
                                self._check()
                                n = e.name.lower()
                                if e.is_dir(follow_symlinks=False):
                                    if n in SKIP_DIRS:
                                        continue
                                    if any(p in n for p in DEV_PATTERNS):
                                        sz = dir_size(e.path, self._check)
                                        self.item.emit(e.path, sz, "Dev Junk")
                                    else:
                                        stack.append(e.path)
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

    # DOWNLOADS
    def _scan_downloads(self):
        self.status.emit("Verificando Downloads antigos (>30 dias)...")
        downloads = os.path.join(HOME, "Downloads")
        if not os.path.isdir(downloads):
            return
        now = time.time()
        cutoff_downloads = now - 30 * 24 * 3600  # 30 dias
        try:
            stack = [downloads]
            while stack:
                self._check()
                cur = stack.pop()
                try:
                    with os.scandir(cur) as it:
                        for e in it:
                            self._check()
                            try:
                                if e.is_file(follow_symlinks=False):
                                    st = e.stat()
                                    if st.st_mtime < cutoff_downloads:
                                        days = int((now - st.st_mtime) / 86400)
                                        self.item.emit(e.path, st.st_size, f"Antigo: {days}d")
                                elif e.is_dir(follow_symlinks=False):
                                    stack.append(e.path)
                            except (PermissionError, OSError):
                                pass
                except PermissionError:
                    pass
        except (PermissionError, OSError):
            pass

    # LOGS
    def _scan_logs(self):
        self.status.emit("Procurando logs do sistema e aplicativos...")
        for base in (HOME, APPD):
            if not os.path.isdir(base):
                continue
            try:
                stack = [base]
                while stack:
                    self._check()
                    cur = stack.pop()
                    try:
                        with os.scandir(cur) as it:
                            for e in it:
                                self._check()
                                n = e.name.lower()
                                if e.is_dir(follow_symlinks=False):
                                    if n in SKIP_DIRS:
                                        continue
                                    if any(p in n for p in LOG_PATTERNS):
                                        sz = dir_size(e.path, self._check)
                                        self.item.emit(e.path, sz, "Logs")
                                    else:
                                        stack.append(e.path)
                                elif e.is_file(follow_symlinks=False):
                                    if n.endswith('.log'):
                                        self.item.emit(e.path, e.stat().st_size, "Log")
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass


class DeleteWorker(QThread):
    progress = Signal(int, int)
    done_phase = Signal(int, list)

    def __init__(self, paths, permanent=False):
        super().__init__()
        self._paths = paths
        self._permanent = permanent
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        ok = 0
        failed = []
        total = len(self._paths)
        for i, p in enumerate(self._paths):
            if self._abort:
                break
            try:
                if self._permanent:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                    if os.path.exists(p):
                        raise OSError("item bloqueado")
                else:
                    send2trash.send2trash(p)
                ok += 1
            except Exception:
                failed.append(p)
            self.progress.emit(i + 1, total)
        self.done_phase.emit(ok, failed)
