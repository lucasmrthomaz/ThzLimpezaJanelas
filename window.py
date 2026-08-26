from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QApplication
)
from theme import C, GLOBAL_QSS
from config import CARD_CFG, TABS
from widgets import StatCard, TabPage
from utils import fmt

BASE_KINDS = ("USER", "APPDATA")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THZ Limpeza de Janelas")
        self.resize(1100, 780)
        self.setMinimumSize(850, 600)
        self.setStyleSheet(GLOBAL_QSS)
        self._settings = QSettings("THZ", "LimpezaJanelas")
        self._pages = {}
        self._cards = {}
        self._counts = {}
        self._totals = {}
        self._build()
        self._restore_state()
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
        # Card do total (não clicável) — soma apenas categorias base, sem sobreposição
        self._card_total = StatCard("TOTAL", "📊", "Total Base", "#107C10")
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
            "Cada aba opera individualmente. F5 escaneia, Del envia selecionados à lixeira. "
            "O Total Base soma apenas Perfil + AppData (demais abas são subconjuntos)."
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

    def _restore_state(self):
        try:
            geo = self._settings.value("geometry")
            if geo is not None:
                self.restoreGeometry(geo)
            idx = self._settings.value("tab", 0, type=int)
            if 0 <= idx < self.tabs.count():
                self.tabs.setCurrentIndex(idx)
            for k, page in self._pages.items():
                state = self._settings.value(f"header/{k}")
                if state is not None:
                    page.tree.header().restoreState(state)
        except Exception:
            pass

    def _save_state(self):
        try:
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("tab", self.tabs.currentIndex())
            for k, page in self._pages.items():
                self._settings.setValue(f"header/{k}", page.tree.header().saveState())
        except Exception:
            pass

    def _on_scan(self, kind, count, total):
        self._counts[kind] = count
        self._totals[kind] = total
        c = self._cards.get(kind)
        if c:
            c.set(f"{count} itens" if count else "0",
                  fmt(total) if total else "0 B")
        # Total base: apenas Perfil + AppData (categorias não sobrepostas).
        # CACHE/DEV/LOGS/DOWNLOADS/LARGE_OLD são subconjuntos dessas árvores.
        all_n = sum(self._counts.get(k, 0) for k in BASE_KINDS)
        all_sz = sum(self._totals.get(k, 0) for k in BASE_KINDS)
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
                    page.worker.wait(2000) # Timeout evita travar o fechamento
            except Exception:
                pass

            try:
                if page._del_worker and page._del_worker.isRunning():
                    page._del_worker.abort()
                    page._del_worker.wait(2000)
            except Exception:
                pass

            try:
                if page._timer:
                    page._timer.stop()
                    page._timer = None
            except Exception:
                pass

        self._save_state()
        event.accept()
