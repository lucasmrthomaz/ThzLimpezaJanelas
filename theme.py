def _detect_dark():
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        winreg.CloseKey(k)
        return v == 0
    except Exception:
        return False


def _build_theme(dark):
    C = {
        "bg":       "#1E1E1E" if dark else "#F5F5F5",
        "card":     "#2D2D30" if dark else "#FFFFFF",
        "border":   "#3E3E42" if dark else "#E0E0E0",
        "text":     "#CCCCCC" if dark else "#1A1A1A",
        "dim":      "#999999" if dark else "#666666",
        "blue":     "#0078D4",
        "tree_alt": "#252526" if dark else "#F8F8F8",
        "tree_hover": "#2A2D2E" if dark else "#E8F4FD",
        "tree_header": "#2D2D30" if dark else "#F8F8F8",
        "tree_header_text": "#999999" if dark else "#666666",
        "tree_header_border": "#3E3E42" if dark else "#E0E0E0",
        "indicator_bg": "#2D2D30" if dark else "white",
        "indicator_border": "#999999",
    }

    BTN = (
        'QPushButton{background:#0078D4;color:white;border:none;'
        'padding:5px 14px;border-radius:4px;font-weight:bold;font-size:12px;}'
        'QPushButton:hover{background:#106EBE}'
        'QPushButton:disabled{background:#555555;color:#888888}'
    )
    BTN_GRAY = (
        'QPushButton{background:#6C757D;color:white;border:none;'
        'padding:5px 14px;border-radius:4px;font-weight:bold;font-size:12px;}'
        'QPushButton:hover{background:#5A6268}'
        'QPushButton:disabled{background:#555555;color:#888888}'
    )
    BTN_RED = (
        'QPushButton{background:#D9534F;color:white;border:none;'
        'padding:5px 14px;border-radius:4px;font-weight:bold;font-size:12px;}'
        'QPushButton:hover{background:#C9302C}'
        'QPushButton:disabled{background:#553333;color:#888888}'
    )

    if dark:
        BTN_OUT = (
            'QPushButton{background:#2D2D30;color:#CCCCCC;border:1px solid #3E3E42;'
            'padding:5px 12px;border-radius:4px;font-size:12px;}'
            'QPushButton:hover{background:#3E3E42}'
            'QPushButton:disabled{color:#555555;border:1px solid #333333}'
        )
    else:
        BTN_OUT = (
            'QPushButton{background:white;color:#333;border:1px solid #CCC;'
            'padding:5px 12px;border-radius:4px;font-size:12px;}'
            'QPushButton:hover{background:#F0F0F0}'
            'QPushButton:disabled{color:#B0B0B0;border:1px solid #E0E0E0}'
        )

    tab_hover = "#2A2D2E" if dark else "#E8F4FD"
    qs_progress_bg = "#333333" if dark else "#E8E8E8"

    GLOBAL_QSS = (
        'QMainWindow{background:%s}'
        'QWidget{font-family:"Segoe UI","Arial",sans-serif;font-size:13px;color:%s}'
        'QTabWidget::pane{border:1px solid %s;border-radius:5px;background:%s}'
        'QTabBar::tab{background:transparent;color:%s;padding:6px 12px;'
        'margin-right:1px;border-top-left-radius:4px;border-top-right-radius:4px;'
        'font-weight:600;font-size:11px}'
        'QTabBar::tab:selected{background:%s;color:%s;'
        'border:1px solid %s;border-bottom:2px solid %s}'
        'QTabBar::tab:hover:!selected{background:%s;color:%s}'
        'QScrollBar:vertical{background:transparent;width:6px}'
        'QScrollBar::handle:vertical{background:#555555;border-radius:3px;min-height:20px}'
        'QScrollBar::handle:vertical:hover{background:#777777}'
        'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}'
        'QProgressBar{border:none;border-radius:4px;background:%s;'
        'height:8px;text-align:center;font-size:9px}'
        'QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,'
        'stop:0 %s,stop:1 #00A2E8);border-radius:4px}'
    ) % (C["bg"], C["text"], C["border"], C["card"],
         C["dim"], C["card"], C["blue"], C["border"], C["blue"],
         tab_hover, C["blue"],
         qs_progress_bg, C["blue"])

    return C, BTN, BTN_GRAY, BTN_RED, BTN_OUT, GLOBAL_QSS


_DARK = _detect_dark()
C, BTN, BTN_GRAY, BTN_RED, BTN_OUT, GLOBAL_QSS = _build_theme(_DARK)
