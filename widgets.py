import os
import shutil
import send2trash
import subprocess
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QProgressBar, QMessageBox, QFrame, QSizePolicy,
    QStyle, QApplication, QMenu
)
from PySide6.QtGui import QColor, QAction
from theme import C, BTN, BTN_GRAY, BTN_RED, BTN_OUT
from utils import fmt, parse_size
from workers import ScanWorker


class SizeWidgetItem(QTreeWidgetItem):
    """
    Subclasse de QTreeWidgetItem que permite ordenação numérica correta na coluna de tamanhos
    com contramedidas absolutas contra falhas de ciclo de vida de objetos C++.
    """
    def __lt__(self, other):
        try:
            # Proteção preventiva: se other for nulo ou inválido, evita chamar C++
            if not other or not isinstance(other, QTreeWidgetItem):
                return False
                
            tw = self.treeWidget()
            if tw is None:
                return False
                
            column = tw.sortColumn()
            
            if column == 1:
                # Obtém o tamanho numérico bruto (em bytes)
                size_self = self.data(1, Qt.UserRole)
                size_other = other.data(1, Qt.UserRole)
                
                val_self = float(size_self) if size_self is not None else 0.0
                val_other = float(size_other) if size_other is not None else 0.0
                
                return val_self < val_other
            else:
                # Compara texto em Python direto para evitar chamar 'super().__lt__'
                # Isso impede que o C++ faça desreferenciamento de ponteiro deletado directamente
                text_self = self.text(column)
                text_other = other.text(column)
                return text_self < text_other
        except Exception:
            # Qualquer objeto deletado do C++ levanta um RuntimeError no Python,
            # que é capturado de forma silenciosa e segura aqui.
            return False


class StatCard(QFrame):
    clicked = Signal(str)

    def __init__(self, key, icon, label, color, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedHeight(80)
        self.setMinimumWidth(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Cursor indicador de interatividade (exceto para o total)
        if key != "TOTAL":
            self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet(
            f'StatCard{{background:{C["card"]};border:1px solid {C["border"]};'
            f'border-radius:6px;border-top:3px solid {color}}}'
            f'StatCard:hover{{background:{C["tree_hover"]};border-color:{C["blue"]}}}'
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

    def mousePressEvent(self, event):
        if self.key != "TOTAL" and event.button() == Qt.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class TabPage(QWidget):
    scanned = Signal(str, int, object)

    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.worker = None
        self._item_buffer = []
        self._timer = None
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
        self.lbl = QLabel("💡 Clique duplo em um item abre seu local. Botão direito exibe opções.")
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
            "QTreeWidget { border: none; alternate-background-color: " + C['tree_alt'] + "; outline: none; }"
            "QTreeWidget::item { padding: 6px; min-height: 28px; border-bottom: 1px solid " + C['border'] + "; }"
            "QTreeWidget::item:hover { background-color: " + C['tree_hover'] + "; }"
            "QTreeWidget::item:selected { background-color: " + C['blue'] + "; color: white; }"
            "QTreeWidget::indicator { width: 18px; height: 18px; }"
            "QTreeWidget::indicator:checked { background: #0078D4; border: 1px solid #0078D4; border-radius: 3px; }"
            f"QTreeWidget::indicator:unchecked {{ background: {C['indicator_bg']}; border: 1px solid {C['indicator_border']}; border-radius: 3px; }}"
            f"QHeaderView::section {{ background: {C['tree_header']}; color: {C['tree_header_text']}; padding: 6px 8px; border: none; border-bottom: 2px solid {C['tree_header_border']}; font-weight: 700; font-size: 11px; }}"
        )
        self.tree.itemClicked.connect(self._toggle_item)
        self.tree.itemDoubleClicked.connect(self._open_item_location)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
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
        
        # Limpa temporizador antigo se houver ativo
        if self._timer:
            try:
                self._timer.stop()
            except Exception:
                pass
            self._timer = None

        self.tree.clear()
        self.prog.setRange(0, 0)
        self.prog.show()
        self._enable(True)
        self.lbl.setText("🔍 Escaneando...")
        
        self._item_buffer.clear()
        
        # Desativa a ordenação durante a inserção de dados para performance rápida
        self.tree.setSortingEnabled(False)
        
        # Inicia o timer para descarregar o buffer lote a lote a cada 100ms
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._flush_buffer)
        self._timer.start()

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
        if not item:
            return
        try:
            if item.treeWidget() is None:
                return
        except RuntimeError:
            return # Objeto C++ destruído

        if column > 0:
            try:
                state = item.checkState(0)
                item.setCheckState(0, Qt.Unchecked if state == Qt.Checked else Qt.Checked)
            except Exception:
                pass

    def _add(self, path, size, info):
        # Apenas joga no buffer para descarregar lote a lote na thread principal
        self._item_buffer.append((path, size, info))

    def _flush_buffer(self):
        if not self._item_buffer:
            return
        
        chunk = self._item_buffer
        self._item_buffer = []
        
        style = QApplication.style()
        dir_icon = style.standardIcon(QStyle.SP_DirIcon)
        file_icon = style.standardIcon(QStyle.SP_FileIcon)
        
        widget_items = []
        for path, size, info in chunk:
            item = SizeWidgetItem() # Subclasse com ordenação correta por bytes
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(0, Qt.Unchecked)
            item.setText(0, path)
            item.setText(1, fmt(size) if size else "0 B")
            item.setText(2, info)
            
            # Armazena o tamanho bruto (bytes) na coluna 1 para comparação na ordenação
            item.setData(1, Qt.UserRole, size)
            item.setData(0, Qt.UserRole, path)
            item.setToolTip(0, path)
            
            # Alinhamento à direita para tamanho
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            
            # Definição de ícones nativos
            if os.path.isdir(path):
                item.setIcon(0, dir_icon)
            else:
                item.setIcon(0, file_icon)

            if size > 1 << 30:
                item.setForeground(1, QColor("#E81123"))
            elif size > 500 << 20:
                item.setForeground(1, QColor("#D83B01"))
            widget_items.append(item)
            
        self.tree.addTopLevelItems(widget_items)

    def _done(self):
        # Para o temporizador e esvazia o buffer final
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._flush_buffer()

        self.prog.hide()
        self._enable(False)
        
        # Reativa ordenação estruturada
        self.tree.setSortingEnabled(True)
        # Força ordenação inicial decrescente por tamanho de arquivo (Coluna 1)
        self.tree.sortByColumn(1, Qt.DescendingOrder)

        c = self.tree.topLevelItemCount()
        total = sum(parse_size(self.tree.topLevelItem(i).text(1))
                    for i in range(c) if self.tree.topLevelItem(i) is not None)
                    
        # Exibe status condicional ao cancelamento
        if self.worker and self.worker._abort:
            self.lbl.setText("⏹️ Escaneamento cancelado pelo usuário.")
        else:
            self.lbl.setText(f"✅ {c} itens encontrados | total {fmt(total)}")
            
        self.scanned.emit(self.kind, c, total)

    def _sel_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item:
                item.setCheckState(0, Qt.Checked)

    def _desel_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item:
                item.setCheckState(0, Qt.Unchecked)

    def _delete(self):
        paths = []
        total = 0
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item:
                if item.checkState(0) == Qt.Checked:
                    paths.append(item.data(0, Qt.UserRole))
                    total += parse_size(item.text(1))
        
        if not paths:
            QMessageBox.information(self, "Vazio", "Nada selecionado.")
            return

        if QMessageBox.question(self, "Confirmar exclusão",
                f"Enviar {len(paths)} item(ns) para a Lixeira?\n"
                f"Espaço total liberado estimado: {fmt(total)}",
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        ok = 0
        failed_trash = []
        
        # 1. Enviar para lixeira
        for p in paths:
            try:
                send2trash.send2trash(p)
                ok += 1
            except Exception:
                failed_trash.append(p)

        # 2. Perguntar exclusão permanente sob os que falharam (uma única vez)
        if failed_trash:
            res = QMessageBox.question(self, "Limpeza de itens bloqueados",
                f"{len(failed_trash)} item(ns) não puderam ser enviados para a lixeira (provavelmente em uso ou pastas de sistema protegidas).\n\n"
                "Deseja tentar excluí-los permanentemente de forma direta?",
                QMessageBox.Yes | QMessageBox.No)
            
            if res == QMessageBox.Yes:
                erros = []
                for p in failed_trash:
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            os.remove(p)
                        if not os.path.exists(p):
                            ok += 1
                        else:
                            erros.append(f"{p}\nMotivo: restaurado/enquanto bloqueado")
                    except Exception as e:
                        erros.append(f"{p}\nMotivo: {e}")
                if erros:
                    QMessageBox.warning(self, "Falha na exclusão permanente",
                        f"{len(erros)} item(ns) ainda continuam protegidos e não puderam ser excluídos:\n\n"
                        + "\n---\n".join(erros[:5])
                        + ("\n..." if len(erros) > 5 else ""))

        QMessageBox.information(self, "Limpeza concluída", f"{ok} de {len(paths)} itens removidos com sucesso.")
        self.start()

    # ── Context Menu e Ações ──────────────────────────────────────

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        
        path = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {C['card']}; color: {C['text']}; border: 1px solid {C['border']}; border-radius: 4px; padding: 4px; }}"
            f"QMenu::item {{ padding: 6px 22px 6px 10px; border-radius: 3px; font-size: 12px; }}"
            f"QMenu::item:selected {{ background-color: {C['tree_hover']}; color: {C['blue']}; }}"
        )
        
        act_open = QAction("📁 Abrir na Pasta", self)
        act_open.triggered.connect(lambda: self._open_in_explorer(path))
        menu.addAction(act_open)
        
        act_copy = QAction("📋 Copiar Caminho", self)
        act_copy.triggered.connect(lambda: self._copy_path_to_clipboard(path))
        menu.addAction(act_copy)
        
        menu.addSeparator()
        
        act_del = QAction("🗑 Excluir este item", self)
        act_del.triggered.connect(lambda: self._delete_single_item(item))
        menu.addAction(act_del)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _open_item_location(self, item, column):
        if item:
            path = item.data(0, Qt.UserRole)
            self._open_in_explorer(path)

    def _open_in_explorer(self, path):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Caminho inexistente", "O item de destino não existe mais.")
            return
        try:
            if os.path.isdir(path):
                os.startfile(path)
            else:
                subprocess.run(['explorer', '/select,', os.path.normpath(path)], shell=True)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir: {e}")

    def _copy_path_to_clipboard(self, path):
        QApplication.clipboard().setText(path)
        self.lbl.setText("📋 Caminho copiado para a área de transferência!")

    def _delete_single_item(self, item):
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        res = QMessageBox.question(self, "Deletar item",
            f"Deseja enviar este item para a Lixeira?\n\n{path}",
            QMessageBox.Yes | QMessageBox.No)
        
        if res == QMessageBox.Yes:
            try:
                send2trash.send2trash(path)
                index = self.tree.indexOfTopLevelItem(item)
                if index != -1:
                    self.tree.takeTopLevelItem(index)
                self.lbl.setText("🗑️ Item enviado para a lixeira.")
                self._recalc_and_emit()
            except Exception:
                res2 = QMessageBox.question(self, "Impossível enviar para lixeira",
                    "Falha ao enviar para a lixeira. Deseja deletar permanentemente?",
                    QMessageBox.Yes | QMessageBox.No)
                if res2 == QMessageBox.Yes:
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            os.remove(path)
                        if not os.path.exists(path):
                            index = self.tree.indexOfTopLevelItem(item)
                            if index != -1:
                                self.tree.takeTopLevelItem(index)
                            self.lbl.setText("🗑️ Item excluído permanentemente.")
                            self._recalc_and_emit()
                        else:
                            QMessageBox.warning(self, "Falha de exclusão", f"Não foi possível apagar: {path}")
                    except Exception as e:
                        QMessageBox.warning(self, "Falha de exclusão", f"Não foi possível apagar: {e}")

    def _recalc_and_emit(self):
        c = self.tree.topLevelItemCount()
        total = sum(parse_size(self.tree.topLevelItem(i).text(1)) for i in range(c) if self.tree.topLevelItem(i) is not None)
        self.scanned.emit(self.kind, c, total)
