from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QApplication
)
from theme import C, GLOBAL_QSS
from config import CARD_CFG, TABS
from widgets import StatCard, TabPage
from utils import fmt, parse_size


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THZ Limpeza de Janelas")
        self.resize(1100, 780)
        self.setMinimumSize(850, 600)
        self.setStyleSheet(GLOBAL_QSS)
        self._pages = {}
        self._cards = {}
        self._build()
        QApplication.processEvents()

    def _build(self):
        cw = QWidget()
        lo = QVBoxLayout(cw)
        lo.setContentsMargins(12, 12, 12, 12)
        lo.setSpacing(8)

        h = QLabel("🧹  THZ Limpeza de Janelas")
        h.setStyleSheet(f'font-size:18px;font-weight:700;color:{C["text"]};padding:2px 0;border:none')
        lo.addWidget(h)

        dash = QHBoxLayout()
        dash.setSpacing(6)
        for k, icon, label, color in CARD_CFG:
            c = StatCard(k, icon, label, color)
            self._cards[k] = c
            dash.addWidget(c)
        # Total card
        self._card_total = StatCard("TOTAL", "📊", "Total Geral", "#107C10")
        dash.addWidget(self._card_total)
        lo.addLayout(dash)

        self.tabs = QTabWidget()
        for k, lbl in TABS:
            page = TabPage(k)
            page.scanned.connect(self._on_scan)
            self.tabs.addTab(page, lbl)
            self._pages[k] = page
        lo.addWidget(self.tabs, 1)

        self._status = QLabel(
            "💡 Cada aba tem seu próprio botão 'Escanear'. "
            "Escaneie cada categoria individualmente."
        )
        self._status.setStyleSheet(f'color:{C["dim"]};font-size:11px;padding:2px 0;border:none')
        lo.addWidget(self._status)

        self.setCentralWidget(cw)

    def _on_scan(self, kind, count, total):
        c = self._cards.get(kind)
        if c:
            c.set(f"{count} itens" if count else "0",
                  fmt(total) if total else "0 B")
        # Recalc total
        all_n = 0
        all_sz = 0
        for k, p in self._pages.items():
            t = p.tree
            for i in range(t.topLevelItemCount()):
                all_n += 1
                all_sz += parse_size(t.topLevelItem(i).text(1))
        self._card_total.set(fmt(all_sz) if all_sz else "0 B",
                             f"{all_n} itens")
