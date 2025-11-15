# townecodex/ui/gui.py
from __future__ import annotations
import tempfile, webbrowser, os
from sqlalchemy import inspect
import html

from PySide6.QtCore import Qt, QThreadPool, QStringListModel, QModelIndex
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QStatusBar, QToolBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListView, QTextEdit, QGroupBox, QTabWidget, QFileDialog,
    QMessageBox, QSizePolicy, QTableWidget, QTableWidgetItem
)

from townecodex.renderers.html import HTMLCardRenderer
from townecodex.dto import CardDTO
from townecodex.db import init_db, engine
from townecodex.models import Base
from townecodex.ui.styles import APP_TITLE, build_stylesheet
from townecodex.ui.backend import Backend, QueryParams
from townecodex.ui.workers import ImportWorker, ScrapeWorker, AutoPriceWorker


ABOUT_TEXT = f"""
<p><strong>{APP_TITLE}</strong> v1.0.0</p>
<p>A tool for managing your inventory of items for the game <a href="https://www.dndbeyond.com/sources/basic-rules">D&amp;D 5e</a>.</p>
<p>© 2025 <a href="https://github.com/cole-mcgregor">Cole McGregor, for Liam Towne</a></p>
"""

def _noop(*_a, **_kw):
    QMessageBox.information(None, "Stub", "This action is not wired yet.")

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 800)

        self.backend = Backend()
        self.pool = QThreadPool.globalInstance()

        self.basket: list[CardDTO] = []

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

        # --- File ---
        m_file = mb.addMenu("&File")
        m_file.addAction(QAction("Import Entries…", self,
                                shortcut=QKeySequence("Ctrl+I"),
                                triggered=self._prompt_import))
        m_file.addAction(QAction("Export Basket…", self,
                                shortcut=QKeySequence("Ctrl+E"),
                                triggered=self._export_basket))
        m_file.addSeparator()
        m_file.addAction(QAction("Quit", self,
                                shortcut=QKeySequence("Ctrl+Q"),
                                triggered=self.close))

        # --- View ---
        m_view = mb.addMenu("&View")
        m_view.addAction(QAction("Refresh", self,
                                shortcut=QKeySequence("F5"),
                                triggered=self._refresh))

        # --- Admin ---
        m_admin = mb.addMenu("&Admin")
        m_admin.addAction(QAction("Create DB", self,
                                triggered=self._admin_create_db))
        m_admin.addAction(QAction("Delete DB", self,
                                triggered=self._admin_delete_db))
        m_admin.addAction(QAction("Reset DB", self,
                                triggered=self._admin_reset_db))

        # --- Help ---
        m_help = mb.addMenu("&Help")
        m_help.addAction(QAction("About", self,
                                triggered=lambda: QMessageBox.information(self, "About", ABOUT_TEXT)))


    # ---------- Toolbar ----------
    def _build_toolbar(self):
        tb = QToolBar("Main"); tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)
        for a in (
            QAction("Refresh", self, triggered=self._refresh),
            QAction("Run Generator", self, triggered=_noop),
            QAction("Export Basket", self, triggered=self._export_basket),
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
        btn_run_import = QPushButton("Run Import")
        btn_run_import.setProperty("variant", "primary")
        btn_run_import.clicked.connect(self._run_import)

        # new: tools for bulk operations
        btn_auto_price = QPushButton("Set All Missing Prices")
        btn_auto_price.setProperty("variant", "primary")
        btn_auto_price.clicked.connect(self._run_auto_price)

        btn_scrape_existing = QPushButton("Scrape Existing Entries")
        btn_scrape_existing.setProperty("variant", "primary")
        btn_scrape_existing.clicked.connect(self._run_scrape_existing)

        r = 0
        ig.addWidget(QLabel("File"), r, 0); ig.addWidget(self.txt_import_path, r, 1); ig.addWidget(btn_browse, r, 2); r += 1
        ig.addWidget(QLabel("Default image"), r, 0); ig.addWidget(self.txt_default_img, r, 1, 1, 2); r += 1
        ig.addWidget(QLabel("Scraping"), r, 0); ig.addWidget(self.chk_scrape, r, 1, 1, 2); r += 1
        ig.addWidget(btn_run_import, r, 0, 1, 3); r += 1

        tools_row = QHBoxLayout()
        tools_row.addWidget(btn_auto_price)
        tools_row.addWidget(btn_scrape_existing)
        tools_row.addStretch(1)
        ig.addLayout(tools_row, r, 0, 1, 3)

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

        # --- GENERATOR LIST PANEL ---
        self.generator_list_box = QGroupBox("Generators")
        gl = QVBoxLayout(self.generator_list_box)

        self.generator_list = QListView()
        self.generator_model = QStandardItemModel(self.generator_list)
        self.generator_list.setModel(self.generator_model)
        self.generator_list.clicked.connect(self._on_generator_selected)

        gl.addWidget(self.generator_list)
        left_layout.addWidget(self.generator_list_box)

        # Default: hide it until Generator mode is selected
        self.generator_list_box.hide()


        # Results list (Query mode)
        self.result_box = QGroupBox("Results")
        lb = QVBoxLayout(self.result_box)

        self.list_view = QListView()
        self.list_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.clicked.connect(self._on_result_clicked)

        self.list_model = QStringListModel()
        self.list_view.setModel(self.list_model)

        lb.addWidget(self.list_view)

        # Button to push current selection into the basket
        self.btn_add_to_basket = QPushButton("Add Selected to Basket")
        self.btn_add_to_basket.setProperty("variant", "primary")
        self.btn_add_to_basket.clicked.connect(self._add_selected_to_basket)
        lb.addWidget(self.btn_add_to_basket)

        left_layout.addWidget(self.result_box, 1)


        # RIGHT
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 10, 8)
        right_layout.setSpacing(10)

        # Use an instance attribute so other methods can switch tabs
        self.tabs = QTabWidget()

        # --- Item Details tab ---
        detail = QWidget()
        dl = QGridLayout(detail)

        dl.addWidget(QLabel("Title"), 0, 0)
        self.txt_title = QLineEdit()
        dl.addWidget(self.txt_title, 0, 1)

        dl.addWidget(QLabel("Type"), 1, 0)
        self.txt_type = QLineEdit()
        dl.addWidget(self.txt_type, 1, 1)

        dl.addWidget(QLabel("Rarity"), 2, 0)
        self.txt_rarity = QLineEdit()
        dl.addWidget(self.txt_rarity, 2, 1)

        dl.addWidget(QLabel("Attunement"), 3, 0)
        self.txt_attune = QLineEdit()
        dl.addWidget(self.txt_attune, 3, 1)

        dl.addWidget(QLabel("Value"), 4, 0)
        self.txt_value = QLineEdit()
        dl.addWidget(self.txt_value, 4, 1)

        dl.addWidget(QLabel("Image URL"), 5, 0)
        self.txt_image = QLineEdit()
        dl.addWidget(self.txt_image, 5, 1)

        dl.addWidget(QLabel("Description (markdown)"), 6, 0, 1, 2)
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Item description…")
        dl.addWidget(self.txt_desc, 7, 0, 1, 2)

        self.tabs.addTab(detail, "Details")

        # --- Preview tab ---
        preview_tab = QWidget()
        pl = QVBoxLayout(preview_tab)
        pl.setContentsMargins(4, 4, 4, 4)
        pl.setSpacing(6)

        toolbar = QHBoxLayout()
        self.btn_preview_selected = QPushButton("Render from selected")
        self.btn_preview_selected.setProperty("variant", "royal")
        self.btn_open_browser = QPushButton("Open in browser…")
        self.btn_open_browser.setProperty("variant", "primary")

        toolbar.addWidget(self.btn_preview_selected)
        toolbar.addWidget(self.btn_open_browser)
        toolbar.addStretch(1)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Preview output (HTML) will appear here.")

        pl.addLayout(toolbar)
        pl.addWidget(self.preview)

        self.tabs.addTab(preview_tab, "Preview")

        # --- Generator Details tab ---
        self.tab_generator_details = QWidget()
        gl = QGridLayout(self.tab_generator_details)

        self.gen_name = QLineEdit()
        gl.addWidget(QLabel("Name"), 0, 0)
        gl.addWidget(self.gen_name, 0, 1)

        self.gen_context = QLineEdit()
        gl.addWidget(QLabel("Context"), 1, 0)
        gl.addWidget(self.gen_context, 1, 1)

        self.gen_min_items = QLineEdit()
        gl.addWidget(QLabel("Min Items"), 2, 0)
        gl.addWidget(self.gen_min_items, 2, 1)

        self.gen_max_items = QLineEdit()
        gl.addWidget(QLabel("Max Items"), 3, 0)
        gl.addWidget(self.gen_max_items, 3, 1)

        self.gen_budget = QLineEdit()
        gl.addWidget(QLabel("Budget"), 4, 0)
        gl.addWidget(self.gen_budget, 4, 1)

        # For buckets you’ll later replace with a structured widget
        self.gen_buckets = QTextEdit()
        gl.addWidget(QLabel("Buckets"), 5, 0, 1, 2)
        gl.addWidget(self.gen_buckets, 6, 0, 1, 2)

        self.tabs.addTab(self.tab_generator_details, "Generator Details")

        # --- Basket tab ---
        self.basket_tab = QWidget()
        bl = QVBoxLayout(self.basket_tab)

        # Table: Name | Rarity | Type | Value | [Remove button]
        self.basket_table = QTableWidget(0, 5)
        self.basket_table.setHorizontalHeaderLabels(
            ["Name", "Rarity", "Type", "Value", ""]
        )
        self.basket_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.basket_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.basket_table.setColumnWidth(0, 320)   # Name
        self.basket_table.setColumnWidth(1, 90)    # Rarity
        self.basket_table.setColumnWidth(2, 160)   # Type
        self.basket_table.setColumnWidth(3, 100)    # Value
        self.basket_table.setColumnWidth(4, 100)    # Remove

        bl.addWidget(self.basket_table)

        basket_buttons = QHBoxLayout()
        self.btn_clear_basket = QPushButton("Clear Basket")
        self.btn_clear_basket.setProperty("variant", "flat")
        self.btn_clear_basket.clicked.connect(self._clear_basket)

        self.btn_export_basket = QPushButton("Export Basket…")
        self.btn_export_basket.setProperty("variant", "primary")
        self.btn_export_basket.clicked.connect(self._export_basket)

        self.lbl_basket_total = QLabel("Total value: 0")
        self.lbl_basket_total.setStyleSheet("font-weight: bold;")

        basket_buttons.addWidget(self.btn_clear_basket)
        basket_buttons.addWidget(self.btn_export_basket)
        basket_buttons.addStretch(1)
        basket_buttons.addWidget(self.lbl_basket_total)

        bl.addLayout(basket_buttons)

        self.tabs.addTab(self.basket_tab, "Basket")

        
        # --- Log tab ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.tabs.addTab(self.log, "Log")

        right_layout.addWidget(self.tabs)


        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 2)

        container = QWidget(); lay = QVBoxLayout(container); lay.setContentsMargins(0, 0, 0, 0); lay.addWidget(splitter)
        self.setCentralWidget(container)

        self.btn_preview_selected.clicked.connect(self._preview_selected_card)
        self.btn_open_browser.clicked.connect(self._open_selected_card)

        self._on_mode_changed(self.mode_combo.currentIndex())
        # self._refresh()


    # ---------- actions ----------
    def _refresh(self):
        # gather filters only when in Query mode
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

        is_query = (mode == "Query")
        is_import = (mode == "Import")
        is_generator = (mode == "Generator")

        # Left-side modes
        self.filter_box.setVisible(is_query)
        self.import_box.setVisible(is_import)
        self.generator_list_box.setVisible(is_generator)

        # Show Query results only in Query mode
        self.result_box.setVisible(is_query)

        # Right-side tabs
        self.tab_generator_details.setVisible(is_generator)

        if is_generator:
            self.tabs.setCurrentWidget(self.tab_generator_details)
            self._load_generators()

        self.statusBar().showMessage(f"Mode: {mode}", 1500)

        # ---------- Admin helpers ----------

    def _db_exists(self) -> bool:
        """
        Heuristic: DB 'exists' if the core table (entries) exists.
        """
        inspector = inspect(engine)
        return inspector.has_table("entries")

    def _admin_create_db(self) -> None:
        """
        Create DB schema if it does not exist yet.
        """
        if self._db_exists():
            QMessageBox.information(
                self,
                "Create DB",
                "The database schema already exists. Nothing to do.",
            )
            return

        resp = QMessageBox.question(
            self,
            "Create DB",
            "Create a new Towne Codex database schema?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        init_db()
        self._append_log("Admin: created DB schema.")
        self.statusBar().showMessage("Database created.", 3000)

    def _admin_delete_db(self) -> None:
        """
        Drop all tables if the DB exists.
        """
        if not self._db_exists():
            QMessageBox.information(
                self,
                "Delete DB",
                "No Towne Codex database schema was found.",
            )
            return

        resp = QMessageBox.question(
            self,
            "Delete DB",
            "This will DROP all Towne Codex tables and permanently delete all items.\n\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        # Drop all tables
        Base.metadata.drop_all(bind=engine)

        self._append_log("Admin: dropped DB schema.")
        self.statusBar().showMessage("Database deleted.", 3000)

    def _admin_reset_db(self) -> None:
        """
        Drop all tables (if present) and recreate the schema.
        """
        msg = (
            "This will DELETE all existing Towne Codex data and recreate an empty schema.\n\n"
            "Are you absolutely sure?"
        )
        resp = QMessageBox.question(
            self,
            "Reset DB",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        if self._db_exists():
            Base.metadata.drop_all(bind=engine)
            self._append_log("Admin: reset DB (dropped existing schema).")

        init_db()
        self._append_log("Admin: reset DB (created new schema).")
        self.statusBar().showMessage("Database reset.", 3000)



    def _load_generators(self) -> None:
        """
        Populate the generator list on the left from the backend.
        Expects Backend to provide list_generators() -> list[GeneratorDef].
        """
        self.generator_model.clear()

        try:
            generators = self.backend.list_generators()
        except Exception as exc:
            self._append_log(f"GEN LOAD ERROR: {exc}")
            QMessageBox.critical(self, "Generators", f"Failed to load generators:\n{exc}")
            return

        for g in generators:
            item = QStandardItem(g.name or f"Generator {getattr(g, 'id', '?')}")
            item.setEditable(False)
            # stash id for _on_generator_selected
            item.setData(getattr(g, "id", None), Qt.UserRole)
            self.generator_model.appendRow(item)

        self._append_log(f"Loaded {len(generators)} generator(s).")



    def _on_generator_selected(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        gen_id = index.data(Qt.UserRole)
        if gen_id is None:
            return

        g = self.backend.get_generator(int(gen_id))
        if not g:
            return

        # Basic fields
        self.gen_name.setText(g.name or "")
        self.gen_context.setText(getattr(g, "context", "") or "")
        self.gen_min_items.setText("" if getattr(g, "min_items", None) is None else str(g.min_items))
        self.gen_max_items.setText("" if getattr(g, "max_items", None) is None else str(g.max_items))
        self.gen_budget.setText("" if getattr(g, "budget", None) is None else str(g.budget))

        # Buckets – only if/when you actually add them to the model
        if hasattr(g, "buckets") and g.buckets:
            lines = []
            for b in g.buckets:
                line = f"- {b.name}: {b.min_items}-{b.max_items}, rarity ≤ {b.max_rarity}"
                lines.append(line)
            self.gen_buckets.setPlainText("\n".join(lines))
        else:
            self.gen_buckets.clear()

        # Switch tab automatically
        self.tabs.setCurrentWidget(self.tab_generator_details)




    def _run_auto_price(self) -> None:
        """
        Start background worker to fill missing prices from the chart.
        """
        self._append_log("Auto-price: starting bulk update of missing values…")
        self.statusBar().showMessage("Auto-pricing missing values…", 3000)

        worker = AutoPriceWorker(self.backend)
        worker.signals.done.connect(self._on_auto_price_done)
        worker.signals.error.connect(self._on_auto_price_error)
        self.pool.start(worker)

    def _on_auto_price_done(self, count: int) -> None:
        self._append_log(f"Auto-price: updated {count} entr{'y' if count == 1 else 'ies'}.")
        self.statusBar().showMessage(f"Auto-price complete ({count} updated).", 3000)
        self._refresh()

    def _on_auto_price_error(self, msg: str) -> None:
        self._append_log(f"AUTO-PRICE ERROR: {msg}")
        QMessageBox.critical(self, "Auto-price failed", msg)
        self.statusBar().showMessage("Auto-price failed.", 3000)

    def _run_scrape_existing(self) -> None:
        """
        Start background worker to scrape Reddit for existing entries
        that have links but missing description/image.
        """
        self._append_log("Scrape: starting pass over existing entries…")
        self.statusBar().showMessage("Scraping existing entries…", 3000)

        worker = ScrapeWorker(self.backend, throttle_seconds=1.0)
        worker.signals.done.connect(self._on_scrape_done)
        worker.signals.error.connect(self._on_scrape_error)
        self.pool.start(worker)

    def _on_scrape_done(self, count: int) -> None:
        self._append_log(f"Scrape: updated {count} entr{'y' if count == 1 else 'ies'}.")
        self.statusBar().showMessage(f"Scrape complete ({count} updated).", 3000)
        self._refresh()

    def _on_scrape_error(self, msg: str) -> None:
        self._append_log(f"SCRAPE ERROR: {msg}")
        QMessageBox.critical(self, "Scrape failed", msg)
        self.statusBar().showMessage("Scrape failed.", 3000)


    def _browse_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file to import", "", "Data Files (*.csv *.xlsx)")
        if path: self.txt_import_path.setText(path)

    def _toggle_import_ui(self, enabled: bool):
        for w in (self.txt_import_path, self.txt_default_img, self.chk_scrape):
            w.setEnabled(enabled)

    def _clear_details(self) -> None:
        self.txt_title.clear()
        self.txt_type.clear()
        self.txt_rarity.clear()
        self.txt_attune.clear()
        self.txt_value.clear()
        self.txt_image.clear()
        self.txt_desc.clear()
        self.preview.clear()

    def _format_attunement(self, card) -> str:
        if not card.attunement_required:
            return "None"
        if card.attunement_criteria:
            return f"Requires Attunement ({card.attunement_criteria})"
        return "Requires Attunement"

    def _run_import(self):
        path = self.txt_import_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Import", "Choose a CSV/XLSX file."); return
        default_img = self.txt_default_img.text().strip() or None
        scrape = self.chk_scrape.currentIndex() == 1
        self._append_log(f"Import starting: {path} (scrape={scrape}, default_image={'yes' if default_img else 'no'})")
        self.statusBar().showMessage("Import running…"); self._toggle_import_ui(False)

        #time the import

        worker = ImportWorker(self.backend, path, scrape=scrape, default_image=default_img)
        worker.signals.done.connect(self._on_import_done)
        worker.signals.error.connect(self._on_import_error)
        self.pool.start(worker)

    def _on_import_done(self, count: int):
        self._append_log(f"Import complete. Upserted {count} entries.")
        self.statusBar().showMessage(f"Import complete ({count}).", 3000)
        self._toggle_import_ui(True)
        self._refresh()

    def _on_result_clicked(self, index):
        item = self.list_model.itemFromIndex(index)
        if not item:
            return

        # we stored the ID in the item’s UserRole
        entry_id = item.data(Qt.UserRole)
        if not entry_id:
            return

        detail = self.backend.get_item(entry_id)
        if not detail:
            return

        # Fill the fields
        self.txt_title.setText(detail.title)
        self.txt_type.setText(detail.type)
        self.txt_rarity.setText(detail.rarity)

        att = "Requires Attunement"
        if detail.attunement_required and detail.attunement_criteria:
            att += f" ({detail.attunement_criteria})"
        elif not detail.attunement_required:
            att = "None"

        self.txt_attune.setText(att)

        self.txt_value.setText(str(detail.value) if detail.value != "" else "")
        self.txt_image.setText(detail.image_url)
        self.txt_desc.setPlainText(detail.description)

    def _on_import_error(self, msg: str):
        self._append_log(f"ERROR: {msg}")
        QMessageBox.critical(self, "Import failed", msg)
        self.statusBar().showMessage("Import failed.", 3000)
        self._toggle_import_ui(True)

    def _prompt_import(self):
        self.mode_combo.setCurrentText("Import"); self._browse_import()


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

    def _preview_selected_card(self):
        dto = self._build_dto_for_selected()
        if dto is None:
            return
        renderer = HTMLCardRenderer(enable_markdown=True)
        html_snippet = renderer.render_card(dto)
        self.preview.setHtml(html_snippet)


    def _open_selected_card(self):
        dto = self._build_dto_for_selected()
        if dto is None:
            return

        renderer = HTMLCardRenderer(enable_markdown=True)
        html_page = renderer.render_page([dto], page_title=dto.title or "Towne Codex — Item")

        fd, path = tempfile.mkstemp(suffix=".html", prefix="townecodex_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_page)

        webbrowser.open_new_tab(path)


    def _selected_entry_id(self) -> int | None:
        idx = self.list_view.currentIndex()
        if not idx.isValid():
            return None
        entry_id = idx.data(Qt.UserRole)
        return int(entry_id) if entry_id is not None else None


    def _build_dto_for_selected(self) -> CardDTO | None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            QMessageBox.information(self, "Preview", "Select an item in the Results list first.")
            return None

        data = self.backend.get_item(entry_id)
        if not data:
            QMessageBox.warning(self, "Preview", f"Entry {entry_id} not found.")
            return None

        #  CardDTO
        return data

    def _add_selected_to_basket(self) -> None:
        """
        Take the currently selected entry in the Results list, build a CardDTO,
        and push it into the basket.
        """
        dto = self._build_dto_for_selected()
        if dto is None:
            return

        self.basket.append(dto)
        self._rebuild_basket_view()
        self._recompute_basket_total()
        self.statusBar().showMessage(f"Added '{dto.title}' to basket.", 2000)
        self._append_log(f"Basket: added {dto.id} / {dto.title!r}")

    def _rebuild_basket_view(self) -> None:
        """
        Rebuild the basket table from self.basket.
        """
        self.basket_table.setRowCount(0)

        for row_idx, dto in enumerate(self.basket):
            self.basket_table.insertRow(row_idx)

            # Name
            self.basket_table.setItem(row_idx, 0, QTableWidgetItem(dto.title or ""))

            # Rarity
            self.basket_table.setItem(row_idx, 1, QTableWidgetItem(dto.rarity or ""))

            # Type
            self.basket_table.setItem(row_idx, 2, QTableWidgetItem(dto.type or ""))

            # Value
            val_str = "" if dto.value is None else str(dto.value)
            self.basket_table.setItem(row_idx, 3, QTableWidgetItem(val_str))

            # Remove button
            btn = QPushButton("Remove")
            btn.setProperty("variant", "flat")
            btn.clicked.connect(self._remove_basket_row_for_button)
            self.basket_table.setCellWidget(row_idx, 4, btn)

    def _remove_basket_row_for_button(self) -> None:
        """
        Slot for 'Remove' button clicks inside the basket table.
        Finds the row for the sender button and removes it from both the
        table and the underlying self.basket list.
        """
        btn = self.sender()
        if btn is None:
            return

        # Find which row this button is in
        for row in range(self.basket_table.rowCount()):
            cell_widget = self.basket_table.cellWidget(row, 4)
            if cell_widget is btn:
                # Remove from data and table
                if 0 <= row < len(self.basket):
                    removed = self.basket.pop(row)
                    self._append_log(f"Basket: removed {removed.id} / {removed.title!r}")
                self.basket_table.removeRow(row)
                self._recompute_basket_total()
                self.statusBar().showMessage("Removed item from basket.", 2000)
                return

    def _clear_basket(self) -> None:
        """
        Clear all items from the basket.
        """
        if not self.basket:
            return
        self.basket.clear()
        self.basket_table.setRowCount(0)
        self._recompute_basket_total()
        self.statusBar().showMessage("Basket cleared.", 2000)
        self._append_log("Basket: cleared")

    def _recompute_basket_total(self) -> None:
        """
        Sum up the values of entries currently in the in-memory basket
        and update the total label.
        """
        total = 0
        for dto in self.basket:
            if dto.value is not None:
                try:
                    total += int(dto.value)
                except (TypeError, ValueError):
                    # If something weird sneaks in, just skip it
                    continue

        self.lbl_basket_total.setText(f"Total value: {total}")

    def _export_basket(self) -> None:
        """
        Export the current basket to an HTML file using HTMLCardRenderer.
        """
        if not self.basket:
            QMessageBox.information(self, "Export Basket", "Basket is empty; nothing to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Basket to HTML",
            "",
            "HTML Files (*.html);;All Files (*)",
        )
        if not path:
            return

        try:
            renderer = HTMLCardRenderer(enable_markdown=True)
            # renderer.write_page expects a list[CardDTO]
            renderer.write_page(self.basket, path, page_title="Towne Codex — Basket")
        except Exception as exc:
            self._append_log(f"EXPORT ERROR: {exc}")
            QMessageBox.critical(self, "Export failed", f"Failed to export basket:\n{exc}")
            return

        self._append_log(f"Basket: exported {len(self.basket)} item(s) to {path}")
        self.statusBar().showMessage(f"Basket exported to {path}", 4000)


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
