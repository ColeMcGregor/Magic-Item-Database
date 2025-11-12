# townecodex/ui/gui.py
from __future__ import annotations
import os

from PySide6.QtCore import Qt, QThreadPool, QStringListModel
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QStatusBar, QToolBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListView, QTextEdit, QGroupBox, QTabWidget, QFileDialog,
    QMessageBox, QSizePolicy
)
from PySide6.QtGui import QFontDatabase, QFont

from townecodex.db import init_db, engine
from townecodex.ui.styles import APP_TITLE, build_stylesheet
from townecodex.ui.backend import Backend, QueryParams
from townecodex.ui.workers import ImportWorker, QueryWorker

def _noop(*_a, **_kw):
    QMessageBox.information(None, "Stub", "This action is not wired yet.")

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 800)

        self.backend = Backend()
        self.pool = QThreadPool.globalInstance()

        self._build_menubar()
        self._build_toolbar()
        self._build_central()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        base_dir = os.path.dirname(__file__)
        icon_path = os.path.abspath(os.path.join(base_dir, "..", "..", "assets", "logo.png"))
        self.setWindowIcon(QIcon(icon_path))

    # ---------- Menus ----------
    def _build_menubar(self):
        mb = self.menuBar()

        m_file = mb.addMenu("&File")
        m_file.addAction(QAction("New Inventory…", self, triggered=_noop))
        m_file.addAction(QAction("Import…", self, shortcut=QKeySequence("Ctrl+I"), triggered=self._prompt_import))
        m_file.addAction(QAction("Export…", self, shortcut=QKeySequence("Ctrl+E"), triggered=_noop))
        m_file.addSeparator()
        m_file.addAction(QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))

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
        tb = QToolBar("Main"); tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)
        for a in (
            QAction("Refresh", self, triggered=self._refresh),
            QAction("Search", self, triggered=_noop),
            QAction("Run Generator", self, triggered=_noop),
            QAction("Show", self, triggered=_noop),
            QAction("Export", self, triggered=_noop),
        ):
            tb.addAction(a)

    # ---------- Central ----------
    def _build_central(self):
        splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False); splitter.setHandleWidth(8); splitter.setOpaqueResize(True)

        # LEFT
        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.setContentsMargins(10, 8, 8, 8); left_layout.setSpacing(10)

        mode_box = QGroupBox("Mode"); grid = QGridLayout(mode_box)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["Query", "Generator", "Import"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        grid.addWidget(QLabel("Mode:"), 0, 0); grid.addWidget(self.mode_combo, 0, 1)
        left_layout.addWidget(mode_box)

        self.list_view = QListView()
        self.list_model = QStandardItemModel(self.list_view)
        self.list_view.setModel(self.list_model)

        # Import panel
        self.import_box = QGroupBox("Import"); ig = QGridLayout(self.import_box)
        self.txt_import_path = QLineEdit(placeholderText="Select CSV/XLSX file…")
        btn_browse = QPushButton("Browse…"); btn_browse.clicked.connect(self._browse_import)
        self.txt_default_img = QLineEdit(placeholderText="Optional default image URL…")
        self.chk_scrape = QComboBox(); self.chk_scrape.addItems(["Don't scrape Reddit", "Scrape Reddit"])
        btn_run_import = QPushButton("Run Import"); btn_run_import.setProperty("variant", "primary"); btn_run_import.clicked.connect(self._run_import)
        r = 0
        ig.addWidget(QLabel("File"), r, 0); ig.addWidget(self.txt_import_path, r, 1); ig.addWidget(btn_browse, r, 2); r += 1
        ig.addWidget(QLabel("Default image"), r, 0); ig.addWidget(self.txt_default_img, r, 1, 1, 2); r += 1
        ig.addWidget(QLabel("Scraping"), r, 0); ig.addWidget(self.chk_scrape, r, 1, 1, 2); r += 1
        ig.addWidget(btn_run_import, r, 0, 1, 3)
        left_layout.addWidget(self.import_box)

        # Filters
        self.filter_box = QGroupBox("Filters"); f = QGridLayout(self.filter_box)
        self.txt_name = QLineEdit(placeholderText="name contains…")
        self.cmb_type = QComboBox(); self.cmb_type.addItems(["Any", "Wondrous Item", "Armor", "Weapon", "Potion"])
        self.cmb_rarity = QComboBox(); self.cmb_rarity.addItems(["Any", "Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"])
        self.cmb_attune = QComboBox(); self.cmb_attune.addItems(["Any", "Requires Attunement", "No Attunement"])
        f.addWidget(QLabel("Name"), 0, 0); f.addWidget(self.txt_name, 0, 1)
        f.addWidget(QLabel("Type"), 1, 0); f.addWidget(self.cmb_type, 1, 1)
        f.addWidget(QLabel("Rarity"), 2, 0); f.addWidget(self.cmb_rarity, 2, 1)
        f.addWidget(QLabel("Attunement"), 3, 0); f.addWidget(self.cmb_attune, 3, 1)
        btn_row = QHBoxLayout()
        btn_apply = QPushButton("Apply"); btn_apply.setProperty("variant", "primary"); btn_apply.clicked.connect(self._refresh)
        btn_clear = QPushButton("Clear"); btn_clear.setProperty("variant", "flat"); btn_clear.clicked.connect(self._clear_filters)
        btn_row.addWidget(btn_apply); btn_row.addWidget(btn_clear); btn_row.addStretch(1)
        f.addLayout(btn_row, 4, 0, 1, 2)
        left_layout.addWidget(self.filter_box)

        # Results list
        result_box = QGroupBox("Results"); lb = QVBoxLayout(result_box)
        self.list_view = QListView(); self.list_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_model = QStringListModel(); self.list_view.setModel(self.list_model)
        lb.addWidget(self.list_view); left_layout.addWidget(result_box, 1)

        # RIGHT
        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(8, 8, 10, 8); right_layout.setSpacing(10)
        tabs = QTabWidget()
        detail = QWidget(); dl = QGridLayout(detail)
        dl.addWidget(QLabel("Title"), 0, 0); self.txt_title = QLineEdit(); dl.addWidget(self.txt_title, 0, 1)
        dl.addWidget(QLabel("Type"), 1, 0); self.txt_type = QLineEdit(); dl.addWidget(self.txt_type, 1, 1)
        dl.addWidget(QLabel("Rarity"), 2, 0); self.txt_rarity = QLineEdit(); dl.addWidget(self.txt_rarity, 2, 1)
        dl.addWidget(QLabel("Attunement"), 3, 0); self.txt_attune = QLineEdit(); dl.addWidget(self.txt_attune, 3, 1)
        dl.addWidget(QLabel("Value"), 4, 0); self.txt_value = QLineEdit(); dl.addWidget(self.txt_value, 4, 1)
        dl.addWidget(QLabel("Image URL"), 5, 0); self.txt_image = QLineEdit(); dl.addWidget(self.txt_image, 5, 1)
        dl.addWidget(QLabel("Description (markdown)"), 6, 0, 1, 2)
        self.txt_desc = QTextEdit(); self.txt_desc.setPlaceholderText("Item description…"); dl.addWidget(self.txt_desc, 7, 0, 1, 2)
        tabs.addTab(detail, "Details")

        self.preview = QTextEdit(); self.preview.setReadOnly(True); self.preview.setPlaceholderText("Preview output (HTML/text) will appear here.")
        tabs.addTab(self.preview, "Preview")

        self.log = QTextEdit(); self.log.setReadOnly(True); tabs.addTab(self.log, "Log")
        right_layout.addWidget(tabs)

        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 2)

        container = QWidget(); lay = QVBoxLayout(container); lay.setContentsMargins(0, 0, 0, 0); lay.addWidget(splitter)
        self.setCentralWidget(container)

        self._on_mode_changed(self.mode_combo.currentIndex())
        # self._refresh()


    # ---------- actions ----------
    def _refresh(self):
        # gather filters only when in Query mode
        if self.mode_combo.currentText() != "Query":
            self.statusBar().showMessage("Not in Query mode.", 1500)
            return
        name = self.txt_name.text()
        type_ = self.cmb_type.currentText()
        rarity = self.cmb_rarity.currentText()
        attune_txt = self.cmb_attune.currentText()
        attune_required = None
        if attune_txt == "Requires Attunement":
            attune_required = True
        elif attune_txt == "No Attunement":
            attune_required = False

        items = self.backend.list_items(
            name_contains=name,
            type_equals=type_,
            rarities=[rarity] if rarity and rarity != "Any" else None,
            attunement_required=attune_required,
        )

        # populate list
        self.list_model.removeRows(0, self.list_model.rowCount())
        if not isinstance(self.list_model, QStandardItemModel):
          self.list_model = QStandardItemModel(self.list_view)
          self.list_view.setModel(self.list_model)
        for it in items:
            row = QStandardItem(it.name)
            row.setEditable(False)
            row.setData(it.id, Qt.UserRole)  # stash 
            
            self.list_model.appendRow(row)

        self.statusBar().showMessage(f"{len(items)} result(s).", 2000)

    def _clear_filters(self):
        self.txt_name.clear(); self.cmb_type.setCurrentIndex(0); self.cmb_rarity.setCurrentIndex(0); self.cmb_attune.setCurrentIndex(0)
        self.statusBar().showMessage("Filters cleared.", 1500)

    def _on_mode_changed(self, _idx: int):
        mode = self.mode_combo.currentText()
        self.filter_box.setVisible(mode == "Query"); self.import_box.setVisible(mode == "Import")
        self.statusBar().showMessage(f"Mode: {mode}", 1500)

    def _browse_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file to import", "", "Data Files (*.csv *.xlsx)")
        if path: self.txt_import_path.setText(path)

    def _toggle_import_ui(self, enabled: bool):
        for w in (self.txt_import_path, self.txt_default_img, self.chk_scrape):
            w.setEnabled(enabled)

    def _run_import(self):
        path = self.txt_import_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Import", "Choose a CSV/XLSX file."); return
        default_img = self.txt_default_img.text().strip() or None
        scrape = self.chk_scrape.currentIndex() == 1
        self._append_log(f"Import starting: {path} (scrape={scrape}, default_image={'yes' if default_img else 'no'})")
        self.statusBar().showMessage("Import running…"); self._toggle_import_ui(False)

        worker = ImportWorker(self.backend, path, scrape=scrape, default_image=default_img)
        worker.signals.done.connect(self._on_import_done)
        worker.signals.error.connect(self._on_import_error)
        self.pool.start(worker)

    def _on_import_done(self, count: int):
        self._append_log(f"Import complete. Upserted {count} entries.")
        self.statusBar().showMessage(f"Import complete ({count}).", 3000)
        self._toggle_import_ui(True)
        self._refresh()

    def _on_import_error(self, msg: str):
        self._append_log(f"ERROR: {msg}")
        QMessageBox.critical(self, "Import failed", msg)
        self.statusBar().showMessage("Import failed.", 3000)
        self._toggle_import_ui(True)

    def _prompt_import(self):
        self.mode_combo.setCurrentText("Import"); self._browse_import()

    def _gather_query_filters(self):
        name_contains = self.txt_name.text().strip() or None
        type_equals = self.cmb_type.currentText()
        rar = self.cmb_rarity.currentText()
        rarities = None if rar == "Any" else [rar]
        att_txt = self.cmb_attune.currentText()
        if att_txt == "Any":
            att = None
        elif att_txt == "Requires Attunement":
            att = True
        else:
            att = False
        return dict(
            name_contains=name_contains,
            type_equals=type_equals,
            rarities=rarities,
            attunement_required=att,
        )

    def _on_row_changed(self, current, _previous):
        if not current or not current.isValid():
            return
        idx = current
        entry_id = idx.data(Qt.UserRole)
        if entry_id is None:
            return
        data = self.backend.get_item(int(entry_id))
        if not data:
            return
        # fill the right-hand fields
        self.txt_title.setText(data["name"])
        self.txt_type.setText(data["type"])
        self.txt_rarity.setText(data["rarity"])
        attune = "Requires Attunement" if data["attunement_required"] else "None"
        if data["attunement_criteria"]:
            attune += f" ({data['attunement_criteria']})"
        self.txt_attune.setText(attune)
        self.txt_value.setText("" if data["value"] == "" else str(data["value"]))
        self.txt_image.setText(data["image_url"])
        self.txt_desc.setPlainText(data["description"])

    def _on_query_done(self, items):
        # items is list[ListItem]
        if not isinstance(self.list_model, QStandardItemModel):
          self.list_model = QStandardItemModel(self.list_view)
          self.list_view.setModel(self.list_model)

        if isinstance(self.list_model, QStandardItemModel):
            self.list_model.clear()
        for itm in items:
            sitem = QStandardItem(itm.name)
            sitem.setEditable(False)
            # stash the id for later detail loading
            sitem.setData(itm.id, Qt.UserRole + 1)
            if not isinstance(self.list_model, QStandardItemModel):
                      self.list_model = QStandardItemModel(self.list_view)
                      self.list_view.setModel(self.list_model)
            self.list_model.appendRow(sitem)
        self.statusBar().showMessage(f"Loaded {len(items)} items.", 2000)
        self._append_log(f"Query: {len(items)} rows")

    def _on_query_error(self, msg: str):
        self._append_log(f"QUERY ERROR: {msg}")
        QMessageBox.critical(self, "Query failed", msg)
        self.statusBar().showMessage("Query failed.", 3000)

    def _append_log(self, msg: str):
        self.log.append(msg)


def main() -> int:
    app = QApplication([])

    app.setStyleSheet(build_stylesheet())          

    init_db(); print("DB URL:", engine.url)
    w = MainWindow(); w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
