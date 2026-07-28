import os
import time
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from utils import dir_size
from config import (
    HOME, APPD, SKIP_DIRS, CACHE_PATTERNS, KNOWN_CACHE, BIG, CUTOFF
)

class Cancelled(Exception):
    pass


class _SizeWorker(QThread):
    result = Signal(str, object)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        self.result.emit(self.path, dir_size(self.path))


class ScanWorker(QThread):
    item = Signal(str, object, str)
    status = Signal(str)
    progress = Signal(int, int)
    done = Signal()

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self._abort = False

    def abort(self):
        self._abort = True

    def _check(self):
        if self._abort:
            raise Cancelled()

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
        except Cancelled:
            self.status.emit("Cancelado.")
            return
        self.done.emit()

    # USER / APPDATA — top-level entries, parallel dir sizes
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
        subs = []
        for i, e in enumerate(items):
            self._check()
            if e.is_dir(follow_symlinks=False):
                w = _SizeWorker(e.path)
                w.result.connect(lambda p, s: self.item.emit(p, s, ""))
                subs.append(w)
                w.start()
            elif e.is_file(follow_symlinks=False):
                self.item.emit(e.path, e.stat().st_size, "")
            self.progress.emit(i + 1, total)
        for w in subs:
            w.wait()
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
                                if n in SKIP_DIRS:
                                    continue
                                empty = False
                                if e.is_dir(follow_symlinks=False):
                                    stack.append(e.path)
                        if empty:
                            self.item.emit(cur, 0, "Vazia")
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

    # CACHE
    def _scan_cache(self):
        self.status.emit("Verificando caches conhecidos...")
        base = Path(APPD)
        for rel in KNOWN_CACHE:
            self._check()
            t = base / rel
            if t.exists():
                sz = dir_size(str(t))
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
                        sz = dir_size(e.path)
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
                            elif e.is_dir(follow_symlinks=False) and n not in SKIP_DIRS:
                                stack.append(e.path)
                        except (PermissionError, OSError):
                            pass
            except PermissionError:
                pass
