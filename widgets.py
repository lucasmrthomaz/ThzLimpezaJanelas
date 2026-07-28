import os
import shutil
import send2trash
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QProgressBar, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QColor
from theme import C, BTN, BTN_GRAY, BTN_RED, BTN_OUT
from utils import fmt, parse_size
from workers import ScanWorker


class StatCard(QFrame):
    def __init__(self, key, icon, label, color, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setMinimumWidth(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(
            f'StatCard{{background:{C["card"]};border:1px solid {C["border"]};'
            f'border-radius:6px;border-top:3px solid {color}}}'
        )
        lo = QVBoxLayout(self)
        lo.setContentsMargins(10, 6, 10, 6)
        lo.setSpacing(1)
        t = QLabel(f"{icon}  {label}")
        t.setStyleSheet(f'color:{C["dim"]};font-size:10px;font-weight:700;border:none')
        self.val = QLabel("—")
        self.val.setStyleSheet(f'color:{C["text"]};font-size:18px;font-weight:800;border:none')
        self.sub = QLabel("")
        self.sub.setStyleSheet(f'color:{C["dim"]};font-size:10px;border:none')
        lo.addWidget(t)
        lo.addWidget(self.val)
        lo.addWidget(self.sub)

    def set(self, v, sub=""):
        self.val.setText(str(v))
        self.sub.setText(sub)


class TabPage(QWidget):
    scanned = Signal(str, int, object)

    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.worker = None
        self._setup()

    def _setup(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(6, 6, 6, 6)
        lo.setSpacing(6)

        bar = QHBoxLayout()
        bar.setSpacing(5)
        self.b_scan = QPushButton("▶ Escanear")
        self.b_scan.setStyleSheet(BTN)
        self.b_scan.clicked.connect(self.start)
        self.b_cancel = QPushButton("⏹ Cancelar")
        self.b_cancel.setStyleSheet(BTN_GRAY)
        self.b_cancel.setEnabled(False)
        self.b_cancel.clicked.connect(self._cancel)
        self.b_sel = QPushButton("☑ Selecionar")
        self.b_sel.setStyleSheet(BTN_OUT)
        self.b_sel.clicked.connect(self._sel_all)
        self.b_desel = QPushButton("☐ Desmarcar")
        self.b_desel.setStyleSheet(BTN_OUT)
        self.b_desel.clicked.connect(self._desel_all)
        self.b_del = QPushButton("🗑 Lixeira")
        self.b_del.setStyleSheet(BTN_RED)
        self.b_del.setEnabled(False)
        self.b_del.clicked.connect(self._delete)
        bar.addWidget(self.b_scan)
        bar.addWidget(self.b_cancel)
        bar.addSpacing(10)
        bar.addWidget(self.b_sel)
        bar.addWidget(self.b_desel)
        bar.addSpacing(10)
        bar.addWidget(self.b_del)
        bar.addStretch()
        lo.addLayout(bar)

        row = QHBoxLayout()
        self.lbl = QLabel("💡 Clique em qualquer coluna para marcar/desmarcar o item.")
        self.lbl.setStyleSheet(f'color:{C["dim"]};font-size:11px;border:none')
        self.prog = QProgressBar()
        self.prog.setRange(0, 0)
        self.prog.setFixedHeight(8)
        self.prog.hide()
        row.addWidget(self.lbl, 1)
        row.addWidget(self.prog, 2)
        lo.addLayout(row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Item", "Tamanho", "Info"])
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 100)
        self.tree.setSortingEnabled(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.setStyleSheet(
            "QTreeWidget::indicator { width: 18px; height: 18px; }"
            "QTreeWidget::indicator:checked { background: #0078D4;"
            " border: 1px solid #0078D4; border-radius: 3px; }"
            f"QTreeWidget::indicator:unchecked {{ background: {C['indicator_bg']};"
            f" border: 1px solid {C['indicator_border']}; border-radius: 3px; }}"
            f"QTreeWidget {{ border: none; alternate-background-color: {C['tree_alt']}; }}"
            f"QTreeWidget::item:hover {{ background: {C['tree_hover']}; }}"
            f"QHeaderView::section {{ background: {C['tree_header']};"
            f" color: {C['tree_header_text']};"
            " padding: 4px 6px; border: none;"
            f" border-bottom: 2px solid {C['tree_header_border']};"
            " font-weight: 700; font-size: 11px; }"
        )
        self.tree.itemClicked.connect(self._toggle_item)
        lo.addWidget(self.tree, 1)

    # ── API ───────────────────────────────────────────────────────

    def _enable(self, busy):
        self.b_scan.setEnabled(not busy)
        self.b_cancel.setEnabled(busy)
        self.b_sel.setEnabled(not busy)
        self.b_desel.setEnabled(not busy)
        self.b_del.setEnabled(not busy and self.tree.topLevelItemCount() > 0)

    def start(self):
        if self.worker and self.worker.isRunning():
            return
        self.tree.clear()
        self.prog.setRange(0, 0)
        self.prog.show()
        self._enable(True)
        self.lbl.setText("🔍 Escaneando...")
        self.worker = ScanWorker(self.kind)
        self.worker.item.connect(self._add)
        self.worker.status.connect(self.lbl.setText)
        self.worker.progress.connect(lambda c, t: (
            self.prog.setRange(0, 0) if t == 0 else
            self.prog.setRange(0, t) or self.prog.setValue(c)
        ))
        self.worker.done.connect(self._done)
        self.worker.start()

    def _cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.b_cancel.setEnabled(False)
            self.lbl.setText("⏳ Cancelando...")

    def _toggle_item(self, item, column):
        if column > 0:
            state = item.checkState(0)
            item.setCheckState(0, Qt.Unchecked if state == Qt.Checked else Qt.Checked)

    def _add(self, path, size, info):
        item = QTreeWidgetItem()
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(0, Qt.Unchecked)
        item.setText(0, path)
        item.setText(1, fmt(size) if size else "0 B")
        item.setText(2, info)
        item.setData(0, Qt.UserRole, path)
        item.setToolTip(0, path)
        if size > 1 << 30:
            item.setForeground(1, QColor("#E81123"))
        elif size > 500 << 20:
            item.setForeground(1, QColor("#D83B01"))
        self.tree.addTopLevelItem(item)

    def _done(self):
        self.prog.hide()
        self._enable(False)
        c = self.tree.topLevelItemCount()
        total = sum(parse_size(self.tree.topLevelItem(i).text(1))
                    for i in range(c))
        self.lbl.setText(f"✅ {c} itens | {fmt(total)}")
        self.scanned.emit(self.kind, c, total)

    def _sel_all(self):
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.Checked)

    def _desel_all(self):
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.Unchecked)

    def _delete(self):
        paths = []
        total = 0
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                paths.append(item.data(0, Qt.UserRole))
                total += parse_size(item.text(1))
        if not paths:
            QMessageBox.information(self, "Vazio", "Nada selecionado.")
            return
        if QMessageBox.question(self, "Confirmar",
                f"Enviar {len(paths)} item(ns) para Lixeira?\n"
                f"Espaço: {fmt(total)}",
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        ok = 0
        erros = []
        for p in paths:
            try:
                send2trash.send2trash(p)
                ok += 1
            except Exception:
                if QMessageBox.question(self, "Não foi para Lixeira",
                        f"{p}\n\nO Windows não permite enviar este item para a Lixeira.\n\n"
                        "Deseja deletar permanentemente?",
                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            os.remove(p)
                        ok += 1
                    except Exception as e2:
                        erros.append(f"{p}\n{e2}")
                else:
                    erros.append(f"{p}\n(Pulado pelo usuário)")
        if erros:
            QMessageBox.warning(self, "Erros",
                f"{len(erros)} item(ns) não puderam ser removidos:\n\n"
                + "\n---\n".join(erros[:5])
                + ("\n..." if len(erros) > 5 else ""))
        QMessageBox.information(self, "Concluído", f"{ok}/{len(paths)} enviados.")
        self.start()
