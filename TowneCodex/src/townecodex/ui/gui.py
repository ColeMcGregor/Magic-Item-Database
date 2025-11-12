# src/townecodex/ui/gui.py
from __future__ import annotations

# --- imports (top of file) ---
import os
from PySide6.QtGui import QIcon, QAction, QKeySequence


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QStatusBar, QToolBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListView, QTextEdit, QGroupBox, QTabWidget, QFileDialog,
    QMessageBox, QSizePolicy
)

APP_TITLE = "Towne Codex"

STYLE = """
/* ================= Towne Codex — Medieval Parchment Theme (Qt-safe) ================= */

/* Base */
QMainWindow, QWidget {
  background: #F3EEE5;                 /* parchment */
  color: #1C1713;                       /* ink */
  font-family: Georgia, "Times New Roman", Times, serif;
  font-size: 13px;
}

/* Menubar / Menus */
QMenuBar {
  background: #FFFCF4;
  border-bottom: 1px solid #D8CEBE;
}
QMenuBar::item { padding: 4px 10px; }
QMenuBar::item:selected { background: #F0E6D7; border-radius: 6px; }

QMenu {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  padding: 6px 4px;
}
QMenu::separator { height: 1px; background: #C9BFAE; margin: 6px 8px; }
QMenu::item { padding: 6px 12px; }
QMenu::item:selected { background: #F0E6D7; }

/* Toolbar */
QToolBar {
  background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FFFDF7, stop:1 #FFFCF4);
  border-bottom: 1px solid #D8CEBE;
  padding: 4px 6px;
  spacing: 6px;
}
QToolButton { padding: 4px 8px; border-radius: 8px; }
QToolButton:hover { background: #F0E6D7; }

/* Panels / Grouping */
QGroupBox, QFrame[role="panel"] {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 10px;
}
QGroupBox { margin-top: 12px; }
QGroupBox::title {
  subcontrol-origin: margin; left: 10px; padding: 0 6px;
  color: #6E5B49; letter-spacing: 0.3px;
}

/* Labels */
QLabel[role="caption"] { color: #6E5B49; }

/* Inputs */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 8px;
  padding: 5px 8px;
  selection-background-color: #F0E6D7;
}
QTextEdit, QPlainTextEdit { padding: 8px 10px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
  border: 1px solid #C7AFA0;
}
QComboBox::drop-down {
  subcontrol-origin: padding;
  subcontrol-position: top right;
  width: 26px;
  border-left: 1px solid #D8CEBE;
}

/* Buttons */
QPushButton {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 8px;
  padding: 5px 12px;
  min-height: 28px;
}
QPushButton:hover { background: #FAF6EE; }
QPushButton:pressed { background: #EFE7D8; }

/* Variants via dynamic property: primary / royal / danger / flat */
QPushButton[variant="primary"] {
  background: #7C1F24;                 /* deep crimson */
  color: #FFF7F5;
  border: 1px solid #7C1F24;
}
QPushButton[variant="royal"] {
  background: #2E5AA3;                 /* royal blue */
  color: #F7FAFF;
  border: 1px solid #2E5AA3;
}
QPushButton[variant="danger"] {
  background: #9B1B20;
  color: #FFF5F4;
  border: 1px solid #9B1B20;
}
QPushButton[variant="flat"] {
  background: transparent;
  border: none;
  color: #6E5B49;
}

/* Tabs */
QTabWidget::pane {
  border: 1px solid #D8CEBE;
  border-radius: 10px;
  background: #FFFCF4;
}
QTabBar::tab {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-bottom: none;
  padding: 6px 14px;
  margin-right: 6px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  color: #6E5B49;
}
QTabBar::tab:selected {
  background: #FBF7EE;
  color: #1C1713;
  border-bottom: 2px solid #B58A2A;    /* subtle gilded underline */
}

/* Lists / Tables */
QListWidget, QTreeView, QTableView {
  background: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 10px;
}
QListView::item { padding: 7px 9px; }
QListView::item:selected { background: #F0E6D7; color: #1C1713; border-radius: 6px; }

/* Splitter */
QSplitter::handle { background: #E8E0CF; width: 8px; }
QSplitter::handle:hover { background: #E2D8C4; }

/* Scrollbars */
QScrollBar:vertical, QScrollBar:horizontal { background: transparent; margin: 0; }
QScrollBar::handle { background: #D1C7B6; border-radius: 6px; min-height: 24px; }
QScrollBar::handle:hover { background: #C5B9A6; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }

/* Status Bar & Tooltips */
QStatusBar { background: #FFFCF4; border-top: 1px solid #D8CEBE; }
QToolTip {
  background: #FFF9ED; color: #1C1713;
  border: 1px solid #D8CEBE; padding: 6px 8px; border-radius: 8px;
}

/* Placeholders (QLineEdit supports this; QTextEdit placeholder styling varies by Qt) */
QLineEdit::placeholder { color: #9B8A78; }
"""




def _noop(*_a, **_kw):
    # Visual confirmation without wiring backends
    QMessageBox.information(None, "Stub", "This action is not wired yet.")

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 800)

        self._build_menubar()
        self._build_toolbar()
        self._build_central()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
        base_dir = os.path.dirname(__file__)                 
        icon_path = os.path.join(base_dir, "..", "..", "assets", "logo.png")
        icon_path = os.path.abspath(icon_path)
        self.setWindowIcon(QIcon(icon_path))


    # ---------- Menus ----------
    def _build_menubar(self):
        mb = self.menuBar()

        m_file = mb.addMenu("&File")
        act_new = QAction("New Inventory…", self, triggered=_noop)
        act_import = QAction("Import…", self, shortcut=QKeySequence("Ctrl+I"), triggered=self._prompt_import)
        act_export = QAction("Export…", self, shortcut=QKeySequence("Ctrl+E"), triggered=_noop)
        act_quit = QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close)
        for a in (act_new, act_import, act_export):
            m_file.addAction(a)
        m_file.addSeparator()
        m_file.addAction(act_quit)

        m_edit = mb.addMenu("&Edit")
        m_edit.addAction(QAction("Update Price…", self, triggered=_noop))
        m_edit.addAction(QAction("Edit Entry…", self, triggered=_noop))

        m_view = mb.addMenu("&View")
        m_view.addAction(QAction("Refresh", self, shortcut=QKeySequence("F5"), triggered=self._refresh))
        m_view.addAction(QAction("Toggle Sidebar", self, triggered=_noop))

        m_tools = mb.addMenu("&Tools")
        m_tools.addAction(QAction("Run Generator…", self, triggered=_noop))
        m_tools.addAction(QAction("Manage Generators…", self, triggered=_noop))

        m_help = mb.addMenu("&Help")
        m_help.addAction(QAction("About", self, triggered=lambda: QMessageBox.information(self, "About", APP_TITLE)))

    # ---------- Toolbar ----------
    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)

        btn_refresh = QAction("Refresh", self, triggered=self._refresh)
        btn_search = QAction("Search", self, triggered=_noop)
        btn_generate = QAction("Run Generator", self, triggered=_noop)
        btn_show = QAction("Show", self, triggered=_noop)
        btn_export = QAction("Export", self, triggered=_noop)

        for a in (btn_refresh, btn_search, btn_generate, btn_show, btn_export):
            tb.addAction(a)

    # ---------- Central Layout ----------
    def _build_central(self):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.setOpaqueResize(True)

        # LEFT: Sidebar — Mode tabs + Filters + List
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 8, 8, 8)
        left_layout.setSpacing(10)

        # Mode strip (Query / Generator / Import)
        mode_box = QGroupBox("Mode")
        grid = QGridLayout(mode_box)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Query", "Generator", "Import"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        grid.addWidget(QLabel("Mode:"), 0, 0)
        grid.addWidget(self.mode_combo, 0, 1)
        left_layout.addWidget(mode_box)

        # Filters (shown in Query mode)
        self.filter_box = QGroupBox("Filters")
        f = QGridLayout(self.filter_box)
        self.txt_name = QLineEdit(placeholderText="name contains…")
        self.cmb_type = QComboBox(); self.cmb_type.addItems(["Any", "Wondrous Item", "Armor", "Weapon", "Potion"])
        self.cmb_rarity = QComboBox(); self.cmb_rarity.addItems(["Any", "Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"])
        self.cmb_attune = QComboBox(); self.cmb_attune.addItems(["Any", "Requires Attunement", "No Attunement"])

        f.addWidget(QLabel("Name"), 0, 0); f.addWidget(self.txt_name, 0, 1)
        f.addWidget(QLabel("Type"), 1, 0); f.addWidget(self.cmb_type, 1, 1)
        f.addWidget(QLabel("Rarity"), 2, 0); f.addWidget(self.cmb_rarity, 2, 1)
        f.addWidget(QLabel("Attunement"), 3, 0); f.addWidget(self.cmb_attune, 3, 1)

        btn_row = QHBoxLayout()
        btn_apply = QPushButton("Apply"); btn_apply.clicked.connect(self._refresh)
        btn_clear = QPushButton("Clear"); btn_clear.clicked.connect(self._clear_filters)
        btn_row.addWidget(btn_apply); btn_row.addWidget(btn_clear); btn_row.addStretch(1)
        f.addLayout(btn_row, 4, 0, 1, 2)

        left_layout.addWidget(self.filter_box)

        # Result list
        result_box = QGroupBox("Results")
        lb = QVBoxLayout(result_box)
        self.list_view = QListView()
        self.list_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lb.addWidget(self.list_view)
        left_layout.addWidget(result_box, 1)

        # RIGHT: Detail / Preview / Log tabs
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 10, 8)
        right_layout.setSpacing(10)

        tabs = QTabWidget()
        # Detail tab
        detail = QWidget()
        dl = QGridLayout(detail)
        dl.addWidget(QLabel("Title"), 0, 0)
        self.txt_title = QLineEdit(); dl.addWidget(self.txt_title, 0, 1)
        dl.addWidget(QLabel("Type"), 1, 0)
        self.txt_type = QLineEdit(); dl.addWidget(self.txt_type, 1, 1)
        dl.addWidget(QLabel("Rarity"), 2, 0)
        self.txt_rarity = QLineEdit(); dl.addWidget(self.txt_rarity, 2, 1)
        dl.addWidget(QLabel("Attunement"), 3, 0)
        self.txt_attune = QLineEdit(); dl.addWidget(self.txt_attune, 3, 1)
        dl.addWidget(QLabel("Value"), 4, 0)
        self.txt_value = QLineEdit(); dl.addWidget(self.txt_value, 4, 1)
        dl.addWidget(QLabel("Image URL"), 5, 0)
        self.txt_image = QLineEdit(); dl.addWidget(self.txt_image, 5, 1)
        dl.addWidget(QLabel("Description (markdown)"), 6, 0, 1, 2)
        self.txt_desc = QTextEdit(); self.txt_desc.setPlaceholderText("Item description…")
        dl.addWidget(self.txt_desc, 7, 0, 1, 2)
        tabs.addTab(detail, "Details")

        # Preview tab (HTML render target later)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Preview output (HTML/text) will appear here.")
        tabs.addTab(self.preview, "Preview")

        # Log tab
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        tabs.addTab(self.log, "Log")

        right_layout.addWidget(tabs)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(splitter)
        self.setCentralWidget(container)

    # ---------- actions (stubs) ----------
    def _refresh(self):
        self.statusBar().showMessage("Refreshed (stub).", 1500)
        self._append_log("Refresh pressed.")

    def _clear_filters(self):
        self.txt_name.clear()
        self.cmb_type.setCurrentIndex(0)
        self.cmb_rarity.setCurrentIndex(0)
        self.cmb_attune.setCurrentIndex(0)
        self.statusBar().showMessage("Filters cleared.", 1500)

    def _on_mode_changed(self, idx: int):
        mode = self.mode_combo.currentText()
        self.filter_box.setVisible(mode == "Query")
        self.statusBar().showMessage(f"Mode: {mode}", 1500)

    def _prompt_import(self):
        QFileDialog.getOpenFileName(self, "Import (stub)", "", "CSV/XLSX (*.csv *.xlsx)")

    def _append_log(self, msg: str):
        self.log.append(msg)

def main() -> int:
    app = QApplication([])
    app.setStyleSheet(STYLE)
    w = MainWindow()
    w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
