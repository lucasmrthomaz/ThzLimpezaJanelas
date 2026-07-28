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

        # Cabeçalho com Título e Descrição
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        
        h = QLabel("🧹  THZ Limpeza de Janelas")
        h.setStyleSheet(f'font-size:18px;font-weight:700;color:{C["text"]};border:none')
        desc = QLabel("Ferramenta de limpeza rápida e otimização de espaço para o Windows")
        desc.setStyleSheet(f'font-size:11px;color:{C["dim"]};border:none')
        
        header_layout.addWidget(h)
        header_layout.addWidget(desc)
        lo.addLayout(header_layout)

        dash = QHBoxLayout()
        dash.setSpacing(6)
        for k, icon, label, color in CARD_CFG:
            c = StatCard(k, icon, label, color)
            c.clicked.connect(self._on_card_clicked)
            self._cards[k] = c
            dash.addWidget(c)
        # Card do total (não clicável)
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
            "💡 Clique em qualquer card indicador no topo para alternar rapidamente entre abas. "
            "Cada aba opera individualmente."
        )
        self._status.setStyleSheet(f'color:{C["dim"]};font-size:11px;padding:2px 0;border:none')
        lo.addWidget(self._status)

        self.setCentralWidget(cw)

    def _on_card_clicked(self, key):
        # Alterna para a aba correspondente ao card clicado
        for index, (k, _) in enumerate(TABS):
            if k == key:
                self.tabs.setCurrentIndex(index)
                break

    def _on_scan(self, kind, count, total):
        c = self._cards.get(kind)
        if c:
            c.set(f"{count} itens" if count else "0",
                  fmt(total) if total else "0 B")
        # Recalcular somatório total de todas as abas
        all_n = 0
        all_sz = 0
        for k, p in self._pages.items():
            t = p.tree
            for i in range(t.topLevelItemCount()):
                item = t.topLevelItem(i)
                if item:
                    try:
                        sz_txt = item.text(1)
                        all_n += 1
                        all_sz += parse_size(sz_txt)
                    except Exception:
                        pass
        self._card_total.set(fmt(all_sz) if all_sz else "0 B",
                             f"{all_n} itens")

    def closeEvent(self, event):
        # Para todas as threads e timers em execução antes de fechar a janela
        self._status.setText("⏳ Finalizando tarefas de forma segura...")
        QApplication.processEvents()
        
        for k, page in self._pages.items():
            try:
                if page.worker and page.worker.isRunning():
                    page.worker.abort()
                    page.worker.wait() # Aguarda a thread fechar de forma limpa
            except Exception:
                pass
                
            try:
                if page._timer:
                    page._timer.stop()
                    page._timer = None
            except Exception:
                pass
                
        event.accept()
