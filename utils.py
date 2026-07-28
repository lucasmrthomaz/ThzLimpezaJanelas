import os

def fmt(n):
    if n >= 1 << 40: return f"{n/(1<<40):.2f} TB"
    if n >= 1 << 30: return f"{n/(1<<30):.2f} GB"
    if n >= 1 << 20: return f"{n/(1<<20):.2f} MB"
    if n >= 1 << 10: return f"{n/(1<<10):.1f} KB"
    return f"{n} B"


def parse_size(text):
    t = text.replace(",", ".")
    if "TB" in t: return float(t.replace(" TB", "")) * (1 << 40)
    if "GB" in t: return float(t.replace(" GB", "")) * (1 << 30)
    if "MB" in t: return float(t.replace(" MB", "")) * (1 << 20)
    if "KB" in t: return float(t.replace(" KB", "")) * (1 << 10)
    v = t.replace(" B", "").strip()
    return float(v) if v else 0


def dir_size(root):
    total = 0
    try:
        stack = [root]
        while stack:
            cur = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for e in it:
                        try:
                            if e.is_dir(follow_symlinks=False):
                                stack.append(e.path)
                            elif e.is_file(follow_symlinks=False):
                                total += e.stat().st_size
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError):
                pass
    except Exception:
        pass
    return total
