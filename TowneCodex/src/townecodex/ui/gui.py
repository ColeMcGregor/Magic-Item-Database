# townecodex/ui/gui.py
from __future__ import annotations
import tempfile, webbrowser, os
from sqlalchemy import inspect
import html

from PySide6.QtCore import Qt, QThreadPool, QStringListModel, QModelIndex
from PySide6.QtGui import QIcon, QAction, QKeySequence, QActionGroup
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QStatusBar, QToolBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListView, QTextEdit, QGroupBox, QTabWidget, QFileDialog,
    QMessageBox, QSizePolicy, QTableWidget, QTableWidgetItem, QDialog,
    QDialogButtonBox, QFormLayout, QCheckBox
)

from townecodex.renderers.html import HTMLCardRenderer
from townecodex.dto import CardDTO
from townecodex.db import init_db, engine
from townecodex.models import Base
from townecodex.ui.styles import APP_TITLE, build_stylesheet
from townecodex.ui.backend import Backend
from townecodex.ui.workers import ImportWorker, ScrapeWorker, AutoPriceWorker
from townecodex import admin_ops
from townecodex.admin_ops import AdminScope, AdminAction, perform_admin_action
from townecodex.generation.schema import (
    GeneratorConfig,
    BucketConfig,
    config_from_json,
)


ABOUT_TEXT = f"""
<p><strong>{APP_TITLE}</strong> v1.0.0</p>
<p>A tool for managing your inventory of items for the game <a href="https://www.dndbeyond.com/sources/basic-rules">D&amp;D 5e</a>.</p>
<p>© 2025 <a href="https://github.com/cole-mcgregor">Cole McGregor, for Liam Towne</a></p>
"""

def _noop(*_a, **_kw):
    QMessageBox.information(None, "Stub", "This action is not wired yet.")


class BucketDialog(QDialog):
    """
    Full dialog to create/edit a BucketConfig.
    """

    def __init__(self, parent: QWidget | None = None, bucket: BucketConfig | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bucket")
        self.setMinimumWidth(500)

        self._result_bucket: BucketConfig | None = None

        form = QFormLayout(self)

        # -------- Name --------
        self.name_edit = QLineEdit()
        form.addRow("Name", self.name_edit)

        # -------- Item count range --------
        self.min_count_edit = QLineEdit()
        self.min_count_edit.setPlaceholderText("0")
        form.addRow("Min items", self.min_count_edit)

        self.max_count_edit = QLineEdit()
        self.max_count_edit.setPlaceholderText("leave blank for no max")
        form.addRow("Max items", self.max_count_edit)

        # -------- Allowed rarities --------
        # User enters comma-separated list (e.g. "Common, Uncommon, Rare")
        self.rarities_edit = QLineEdit()
        self.rarities_edit.setPlaceholderText("Comma-separated (optional)")
        form.addRow("Allowed rarities", self.rarities_edit)

        # -------- Type substring filters --------
        # Again comma-separated ("weapon, armor", etc.)
        self.type_contains_edit = QLineEdit()
        self.type_contains_edit.setPlaceholderText("Comma-separated substrings (optional)")
        form.addRow("Type contains any", self.type_contains_edit)

        # -------- Price range --------
        self.min_value_edit = QLineEdit()
        self.min_value_edit.setPlaceholderText("leave blank for no minimum")
        form.addRow("Min price (gp)", self.min_value_edit)

        self.max_value_edit = QLineEdit()
        self.max_value_edit.setPlaceholderText("leave blank for no maximum")
        form.addRow("Max price (gp)", self.max_value_edit)

        # -------- Attunement (tri-state) --------
        #   Ignore     = None
        #   Required   = True
        #   Forbidden  = False
        self.attune_combo = QComboBox()
        self.attune_combo.addItem("Ignore")       # -> None
        self.attune_combo.addItem("Required")     # -> True
        self.attune_combo.addItem("Forbidden")    # -> False
        form.addRow("Attunement", self.attune_combo)

        # -------- Prefer unique --------
        self.unique_check = QCheckBox("Prefer unique items")
        self.unique_check.setChecked(True)
        form.addRow(self.unique_check)

        # -------- Buttons --------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        if bucket is not None:
            self._prefill(bucket)

    # ------------------------------------------------------------------

    def _prefill(self, bucket: BucketConfig) -> None:
        self.name_edit.setText(bucket.name or "")
        self.min_count_edit.setText(str(bucket.min_count))

        if bucket.max_count is not None and bucket.max_count >= 0:
            self.max_count_edit.setText(str(bucket.max_count))
        else:
            self.max_count_edit.clear()

        # Rarities
        if bucket.allowed_rarities:
            self.rarities_edit.setText(", ".join(bucket.allowed_rarities))

        # Type filters
        if bucket.type_contains_any:
            self.type_contains_edit.setText(", ".join(bucket.type_contains_any))

        # Values
        if bucket.min_value is not None:
            self.min_value_edit.setText(str(bucket.min_value))
        if bucket.max_value is not None:
            self.max_value_edit.setText(str(bucket.max_value))

        # Attunement
        if bucket.attunement_required is None:
            self.attune_combo.setCurrentIndex(0)
        elif bucket.attunement_required is True:
            self.attune_combo.setCurrentIndex(1)
        else:
            self.attune_combo.setCurrentIndex(2)

        # Unique
        self.unique_check.setChecked(bucket.prefer_unique)

    # ------------------------------------------------------------------

    def _parse_optional_int(self, text: str) -> int | None:
        t = text.strip()
        if not t:
            return None
        return int(t)

    # ------------------------------------------------------------------

    def accept(self) -> None:
        name = (self.name_edit.text() or "").strip()
        if not name:
            QMessageBox.warning(self, "Bucket", "Bucket name is required.")
            return

        # Min count
        try:
            min_count_text = self.min_count_edit.text().strip()
            min_count = int(min_count_text) if min_count_text else 0
        except ValueError:
            QMessageBox.warning(self, "Bucket", "Min items must be an integer.")
            return

        if min_count < 0:
            QMessageBox.warning(self, "Bucket", "Min items cannot be negative.")
            return

        # Max count
        try:
            max_count_opt = self._parse_optional_int(self.max_count_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Bucket", "Max items must be an integer or blank.")
            return

        if max_count_opt is not None and max_count_opt < min_count:
            QMessageBox.warning(
                self, "Bucket",
                "Max items cannot be less than min items."
            )
            return

        max_count = max_count_opt if max_count_opt is not None else -1

        # Rarities
        rarities_raw = self.rarities_edit.text().strip()
        allowed_rarities = (
            [r.strip() for r in rarities_raw.split(",") if r.strip()]
            if rarities_raw else None
        )

        # Type filters
        type_raw = self.type_contains_edit.text().strip()
        type_contains_any = (
            [t.strip() for t in type_raw.split(",") if t.strip()]
            if type_raw else None
        )

        # Value range
        try:
            min_val_opt = self._parse_optional_int(self.min_value_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Bucket", "Min price must be an integer or blank.")
            return

        try:
            max_val_opt = self._parse_optional_int(self.max_value_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Bucket", "Max price must be an integer or blank.")
            return

        if (min_val_opt is not None and max_val_opt is not None
                and max_val_opt < min_val_opt):
            QMessageBox.warning(
                self, "Bucket",
                "Max price cannot be less than min price."
            )
            return

        # Attunement tri-state
        attune_idx = self.attune_combo.currentIndex()
        if attune_idx == 0:
            attunement = None
        elif attune_idx == 1:
            attunement = True
        else:
            attunement = False

        # Prefer unique
        prefer_unique = self.unique_check.isChecked()

        # Construct result
        self._result_bucket = BucketConfig(
            name=name,
            min_count=min_count,
            max_count=max_count,
            allowed_rarities=allowed_rarities,
            type_contains_any=type_contains_any,
            min_value=min_val_opt,
            max_value=max_val_opt,
            attunement_required=attunement,
            prefer_unique=prefer_unique,
        )

        super().accept()

    # ------------------------------------------------------------------

    def result(self) -> BucketConfig | None:
        return self._result_bucket



class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 800)

        self.admin = admin_ops
        self.backend = Backend()
        self.pool = QThreadPool.globalInstance()    

        self._admin_scope: str = "WHOLE_DB"
        self.basket: list[CardDTO] = []

        self.current_generator_def = None
        self.current_generator_config = None
        self.current_bucket_config = None

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

        # Status / ping
        act_status = QAction("DB Status…", self, triggered=self._admin_show_status)
        m_admin.addAction(act_status)
        m_admin.addSeparator()

        # Nested drop-downs for actions
        menu_create = m_admin.addMenu("Create")
        menu_drop   = m_admin.addMenu("Drop")
        menu_reset  = m_admin.addMenu("Reset")
        menu_clear  = m_admin.addMenu("Clear")

        # Helper to wire menu items to perform_admin_action
        def _add_admin_item(menu, label, scope, action):
            act = QAction(label, self)
            act.triggered.connect(
                lambda _checked=False, sc=scope, ac=action: self._admin_perform(sc, ac)
            )
            menu.addAction(act)

        # Labels for scopes
        label_all        = "All (whole DB)"
        label_entries    = "Entries + Inventories + Types"
        label_inventories = "Inventories only"
        label_generators = "Generators only"
        label_types      = "Type catalog only"

        # CREATE
        _add_admin_item(menu_create, label_all,        AdminScope.WHOLE_DB,               AdminAction.CREATE)
        _add_admin_item(menu_create, label_entries,    AdminScope.ENTRIES_AND_DEPENDENTS, AdminAction.CREATE)
        _add_admin_item(menu_create, label_inventories,AdminScope.INVENTORIES,           AdminAction.CREATE)
        _add_admin_item(menu_create, label_generators, AdminScope.GENERATORS,             AdminAction.CREATE)
        _add_admin_item(menu_create, label_types,      AdminScope.TYPE_CATALOG,           AdminAction.CREATE)

        # DROP
        _add_admin_item(menu_drop, label_all,        AdminScope.WHOLE_DB,               AdminAction.DROP)
        _add_admin_item(menu_drop, label_entries,    AdminScope.ENTRIES_AND_DEPENDENTS, AdminAction.DROP)
        _add_admin_item(menu_drop, label_inventories,AdminScope.INVENTORIES,           AdminAction.DROP)
        _add_admin_item(menu_drop, label_generators, AdminScope.GENERATORS,             AdminAction.DROP)
        _add_admin_item(menu_drop, label_types,      AdminScope.TYPE_CATALOG,           AdminAction.DROP)

        # RESET
        _add_admin_item(menu_reset, label_all,        AdminScope.WHOLE_DB,               AdminAction.RESET)
        _add_admin_item(menu_reset, label_entries,    AdminScope.ENTRIES_AND_DEPENDENTS, AdminAction.RESET)
        _add_admin_item(menu_reset, label_inventories,AdminScope.INVENTORIES,           AdminAction.RESET)
        _add_admin_item(menu_reset, label_generators, AdminScope.GENERATORS,             AdminAction.RESET)
        _add_admin_item(menu_reset, label_types,      AdminScope.TYPE_CATALOG,           AdminAction.RESET)

        # CLEAR
        _add_admin_item(menu_clear, label_all,        AdminScope.WHOLE_DB,               AdminAction.CLEAR)
        _add_admin_item(menu_clear, label_entries,    AdminScope.ENTRIES_AND_DEPENDENTS, AdminAction.CLEAR)
        _add_admin_item(menu_clear, label_inventories,AdminScope.INVENTORIES,           AdminAction.CLEAR)
        _add_admin_item(menu_clear, label_generators, AdminScope.GENERATORS,             AdminAction.CLEAR)
        _add_admin_item(menu_clear, label_types,      AdminScope.TYPE_CATALOG,           AdminAction.CLEAR)



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
        btn_run_import = QPushButton("Run Import")
        btn_run_import.setProperty("variant", "primary")
        btn_run_import.clicked.connect(self._run_import)


        r = 0
        ig.addWidget(QLabel("File"), r, 0); ig.addWidget(self.txt_import_path, r, 1); ig.addWidget(btn_browse, r, 2); r += 1
        ig.addWidget(QLabel("Default image"), r, 0); ig.addWidget(self.txt_default_img, r, 1, 1, 2); r += 1
        ig.addWidget(btn_run_import, r, 0, 1, 3); r += 1

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
        self.detail = QWidget()
        dl = QGridLayout(self.detail)

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

        self.tabs.addTab(self.detail, "Details")

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

        self.tab_generator_details = QWidget()
        gl = QGridLayout(self.tab_generator_details)

        # --- Generator toolbar (buttons) ---
        generator_toolbar_row = QHBoxLayout()
        self.btn_gen_new = QPushButton("New Generator")
        self.btn_gen_new.setProperty("variant", "bulbasaur")

        self.btn_gen_save = QPushButton("Save Generator")
        self.btn_gen_save.setProperty("variant", "royal")

        self.btn_gen_delete = QPushButton("Delete Generator")
        self.btn_gen_delete.setProperty("variant", "danger")

        generator_toolbar_row.addWidget(self.btn_gen_new)
        generator_toolbar_row.addWidget(self.btn_gen_save)
        generator_toolbar_row.addWidget(self.btn_gen_delete)
        generator_toolbar_row.addStretch(1)

        generator_toolbar_container = QWidget()
        generator_toolbar_container.setLayout(generator_toolbar_row)
        gl.addWidget(generator_toolbar_container, 0, 0, 1, 2)

        # --- Generator fields ---
        self.gen_name = QLineEdit()
        gl.addWidget(QLabel("Name"), 1, 0)
        gl.addWidget(self.gen_name, 1, 1)

        self.gen_purpose = QLineEdit()
        gl.addWidget(QLabel("Purpose"), 2, 0)
        gl.addWidget(self.gen_purpose, 2, 1)

        self.gen_min_items = QLineEdit()
        gl.addWidget(QLabel("Min Items"), 3, 0)
        gl.addWidget(self.gen_min_items, 3, 1)

        self.gen_max_items = QLineEdit()
        gl.addWidget(QLabel("Max Items"), 4, 0)
        gl.addWidget(self.gen_max_items, 4, 1)

        self.gen_budget = QLineEdit()
        gl.addWidget(QLabel("Budget"), 5, 0)
        gl.addWidget(self.gen_budget, 5, 1)

        # BUCKET TOOLBAR BUTTONS----------------------------------

        # --- Bucket toolbar (buttons) ---
        bucket_toolbar_row = QHBoxLayout()

        self.btn_bucket_add = QPushButton("Add Bucket")
        self.btn_bucket_add.setProperty("variant", "bulbasaur")
        self.btn_bucket_add.clicked.connect(self._on_add_bucket_clicked)

        self.btn_bucket_edit = QPushButton("Edit Bucket")
        self.btn_bucket_edit.setProperty("variant", "royal")

        self.btn_bucket_remove = QPushButton("Remove Selected")
        self.btn_bucket_remove.setProperty("variant", "danger")

        self.btn_bucket_move_up = QPushButton("Move Up")
        self.btn_bucket_move_up.setProperty("variant", "flat")

        self.btn_bucket_move_down = QPushButton("Move Down")
        self.btn_bucket_move_down.setProperty("variant", "flat")

        bucket_toolbar_row.addWidget(self.btn_bucket_add)
        bucket_toolbar_row.addWidget(self.btn_bucket_edit)
        bucket_toolbar_row.addWidget(self.btn_bucket_remove)
        bucket_toolbar_row.addWidget(self.btn_bucket_move_up)
        bucket_toolbar_row.addWidget(self.btn_bucket_move_down)
        bucket_toolbar_row.addStretch(1)

        bucket_toolbar_container = QWidget()
        bucket_toolbar_container.setLayout(bucket_toolbar_row)

        # IMPORTANT: use the correct row index depending on your layout
        gl.addWidget(bucket_toolbar_container, 6, 0, 1, 2)

        #------------------------------------------------------
        # --- Buckets section  ---
        buckets_label = QLabel("Buckets")
        gl.addWidget(buckets_label, 7, 0)

        # bucket control buttons (Add/Edit/Delete/Move)
        buckets_controls_row = QHBoxLayout()
        buckets_controls_container = QWidget()
        buckets_controls_container.setLayout(buckets_controls_row)
        gl.addWidget(buckets_controls_container, 7, 1)

        # Bucket table: Name | Items | Price (per item)
        self.bucket_table = QTableWidget(0, 3)
        self.bucket_table.setHorizontalHeaderLabels(
            ["Name", "Items", "Price (per item)", ""]
        )
        self.bucket_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bucket_table.setSelectionMode(QTableWidget.SingleSelection)
        self.bucket_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.bucket_table.setColumnWidth(0, 420)   # Name
        self.bucket_table.setRowHeight
        self.bucket_table.setColumnWidth(1, 90)    # Item count
        self.bucket_table.setColumnWidth(2, 200)   # Price per item
        self.bucket_table.setColumnWidth(3, 90)    # Remove

        self.bucket_table.setAlternatingRowColors(True)

        gl.addWidget(self.bucket_table, 8, 0, 1, 2)

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
        self.basket_table.setColumnWidth(3, 100)   # Value
        self.basket_table.setColumnWidth(4, 100)   # Remove

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

    # ---------- actions ----------
    def _refresh(self):
        # gather filters only when in Query mode
        name = self.txt_name.text()
        type_ = self.cmb_type.currentText()
        type_filter = None if type_ == "Any" else type_
        rarity = self.cmb_rarity.currentText()
        attune_txt = self.cmb_attune.currentText()
        attune_required = None
        if attune_txt == "Requires Attunement":
            attune_required = True
        elif attune_txt == "No Attunement":
            attune_required = False

        items = self.backend.list_items(
            name_contains=name,
            type_contains = type_filter,
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
        self._append_log(f"Loaded {len(items)} items from Entries Table(s).")

    def _clear_filters(self):
        self.txt_name.clear(); self.cmb_type.setCurrentIndex(0); self.cmb_rarity.setCurrentIndex(0); self.cmb_attune.setCurrentIndex(0)
        self.statusBar().showMessage("Filters cleared.", 1500)

    def _on_mode_changed(self, _idx: int):
        mode = self.mode_combo.currentIndex()

        is_query = (mode == 0)
        is_generator = (mode == 1)
        is_import = (mode == 2)

        # Left-side modes
        self.filter_box.setVisible(is_query)
        self.import_box.setVisible(is_import)
        self.generator_list_box.setVisible(is_generator)

        if is_generator:
            self.tabs.setCurrentWidget(self.tab_generator_details)
            self._load_generators()

        if is_import:
            self.tabs.setCurrentWidget(self.detail)

        if is_query:
            self.tabs.setCurrentWidget(self.detail)
            self._refresh()

        self.statusBar().showMessage(f"Mode: {mode}", 1500)

    # ---------- Admin helpers ----------

    def _set_admin_scope(self, scope: str) -> None:
        self._admin_scope = scope
        label = self._admin_scope_label(scope)
        self.statusBar().showMessage(f"Admin scope set to: {label}", 2500)
        self._append_log(f"Admin: scope changed to {scope} ({label})")

    def _admin_scope_label(self, scope: str) -> str:
        return {
            "WHOLE_DB": "Whole database (all tables)",
            "ENTRIES_AND_DEPENDENTS": "Entries + inventories + items + type catalog",
            "INVENTORIES": "Inventories only",
            "TYPE_CATALOG": "Type catalog (general & specific types)",
            "GENERATORS": "Generators only",
        }.get(scope, scope)

    def _admin_scope_enum(self, key: str) -> AdminScope:
        if key == "WHOLE_DB":
            return AdminScope.WHOLE_DB
        if key == "ENTRIES_AND_DEPENDENTS":
            return AdminScope.ENTRIES_AND_DEPENDENTS
        if key == "INVENTORIES":
            return AdminScope.INVENTORIES
        if key == "GENERATORS":
            return AdminScope.GENERATORS
        if key == "TYPE_CATALOG":
            return AdminScope.TYPE_CATALOG
        raise ValueError(f"Unknown scope {key}")


    # Convenience wrappers for “current scope” operations ---------------

    def _admin_create_scope_current(self) -> None:
        self._admin_create_scope(self._admin_scope)

    def _admin_drop_scope_current(self) -> None:
        self._admin_drop_scope(self._admin_scope)

    def _admin_clear_scope_current(self) -> None:
        self._admin_clear_scope(self._admin_scope)

    def _admin_ping_status_current(self) -> None:
        self._admin_ping_status(self._admin_scope)

    # ------------------------------------------------------------------ #
    # Scope-specific operations      #
    # ------------------------------------------------------------------ #

    def _admin_create_scope(self, scope_key: str) -> None:
        scope_enum = self._admin_scope_enum(scope_key)
        result = perform_admin_action(scope_enum, AdminAction.CREATE)

        if result.success:
            self._append_log(result.message)
        else:
            QMessageBox.warning(self, "Admin Error", result.message)
            self._append_log(f"ERROR: {result.message}")


    def _admin_drop_scope(self, scope_key: str) -> None:
        """
        Drop tables for the given scope using admin_ops.

        WHOLE_DB:
            - Drop the entire schema (all tables in metadata).
        Other scopes:
            - Drop only the tables mapped to that scope.
        """
        label = self._admin_scope_label(scope_key)
        try:
            scope_enum = self._admin_scope_enum(scope_key)
        except ValueError as exc:
            QMessageBox.critical(self, "Admin error", str(exc))
            self._append_log(f"ADMIN ERROR: {exc}")
            return

        # Confirmation
        msg = (
            "This will DROP all tables in the selected scope.\n\n"
            f"Scope: {label}\n\n"
            "All data in those tables will be permanently deleted and the schema "
            "for those tables removed.\n\n"
            "Are you sure?"
        )
        resp = QMessageBox.question(
            self,
            "Admin — Drop Tables",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            self._append_log(f"Admin: drop scope={scope_key} cancelled by user.")
            return

        result = perform_admin_action(scope_enum, AdminAction.DROP)

        if result.success:
            self._append_log(result.message)
            self.statusBar().showMessage(result.message, 4000)
            QMessageBox.information(self, "Admin — Drop Tables", result.message)
        else:
            self._append_log(f"ADMIN DROP ERROR: {result.message}")
            QMessageBox.critical(self, "Admin — Drop Failed", result.message)

    def _admin_clear_scope(self, scope_key: str) -> None:
        """
        Clear (truncate) all rows in the tables for this scope but keep schema,
        using admin_ops.clear_scope / perform_admin_action.
        """
        label = self._admin_scope_label(scope_key)
        try:
            scope_enum = self._admin_scope_enum(scope_key)
        except ValueError as exc:
            QMessageBox.critical(self, "Admin error", str(exc))
            self._append_log(f"ADMIN ERROR: {exc}")
            return

        msg = (
            "This will DELETE all rows in the tables for the selected scope, "
            "but keep the table definitions (schema) intact.\n\n"
            f"Scope: {label}\n\n"
            "Cascades:\n"
            "  • ENTRIES_AND_DEPENDENTS: entries, inventories, inventory_items,\n"
            "    and type catalog will all be cleared. Generators remain.\n"
            "  • INVENTORIES: inventories and inventory_items will be cleared.\n"
            "  • TYPE_CATALOG: general_types and specific_types will be cleared.\n"
            "  • WHOLE_DB: all known tables will be cleared.\n\n"
            "Are you sure?"
        )
        resp = QMessageBox.question(
            self,
            "Admin — Clear Data",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            self._append_log(f"Admin: clear scope={scope_key} cancelled by user.")
            return

        result = perform_admin_action(scope_enum, AdminAction.CLEAR)

        if result.success:
            self._append_log(result.message)
            self.statusBar().showMessage(result.message, 4000)
            QMessageBox.information(self, "Admin — Clear Data", result.message)
        else:
            self._append_log(f"ADMIN CLEAR ERROR: {result.message}")
            QMessageBox.critical(self, "Admin — Clear Failed", result.message)

    def _admin_ping_status(self, scope: str) -> None:
        """
        Stage 1: placeholder DB status ping.

        Later, this will call admin_ops.get_db_status() and show table
        existence + row counts. For now, just a stub.
        """
        label = self._admin_scope_label(scope)
        msg = (
            f"[Stage 1] Ping DB status for scope:\n\n{label}\n\n"
            "In the next stage, this will display table existence and row counts "
            "using admin_ops.get_db_status()."
        )
        QMessageBox.information(self, "DB Status (stub)", msg)
        self._append_log(f"[STUB] Admin ping status scope={scope} ({label})")


    def _admin_show_status(self) -> None:
        """
        Ping the DB and show which tables exist and how many rows they have.
        """
        try:
            status = self.admin.get_db_status()
        except Exception as exc:
            msg = f"DB status check failed: {exc}"
            self._append_log(f"Admin: {msg}")
            QMessageBox.critical(self, "DB Status", msg)
            self.statusBar().showMessage("DB status check failed.", 3000)
            return

        lines = []
        for label in sorted(status.keys()):
            ts = status[label]
            if ts.exists:
                lines.append(
                    f"{label}: {ts.row_count} row(s) in '{ts.table_name}'"
                )
            else:
                lines.append(
                    f"{label}: [missing] (no table '{ts.table_name}')"
                )

        text = "Database status:\n\n" + "\n".join(lines)

        # Log a compact version
        self._append_log(
            "Admin: DB status -> " + " | ".join(l.replace("\n", " ") for l in lines)
        )

        QMessageBox.information(self, "DB Status", text)
        self.statusBar().showMessage("DB status loaded.", 3000)

    def _confirm_admin_action(self, scope: AdminScope, action: AdminAction) -> bool:
        """
        Centralized confirmation dialog for destructive admin actions.
        """
        # CREATE is non-destructive
        if action is AdminAction.CREATE:
            return True

        scope_label = {
            AdminScope.WHOLE_DB: "the ENTIRE Towne Codex database",
            AdminScope.ENTRIES_AND_DEPENDENTS: "Entries + Inventories + Type catalog",
            AdminScope.INVENTORIES: "Inventories (and their items)",
            AdminScope.GENERATORS: "Generators",
            AdminScope.TYPE_CATALOG: "Type catalog (general/specific types)",
        }.get(scope, str(scope))

        if action is AdminAction.CLEAR:
            verb = "clear ALL rows from"
        elif action is AdminAction.DROP:
            verb = "DROP the tables for"
        elif action is AdminAction.RESET:
            verb = "RESET (DROP + CREATE) the tables for"
        else:
            verb = f"perform {action.name} on"

        msg = (
            f"This will {verb} {scope_label}.\n\n"
            "Are you absolutely sure?"
        )

        resp = QMessageBox.question(
            self,
            "Confirm admin operation",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return resp == QMessageBox.Yes


    def _admin_perform(self, scope: AdminScope, action: AdminAction) -> None:
        """
        Execute an admin_ops action for a given scope and wire it into the UI:
        - confirmation
        - log
        - status bar message
        - refresh when appropriate
        """
        # 1. Confirm action
        if not self._confirm_admin_action(scope, action):
            self._append_log(f"Admin: {action.name} {scope.name} cancelled.")
            return

        # 2. Run admin operation
        try:
            result = self.admin.perform_admin_action(scope, action)
        except Exception as exc:
            msg = f"Admin {action.name} on {scope.name} failed: {exc}"
            self._append_log("Admin ERROR: " + msg)
            QMessageBox.critical(self, "Admin error", msg)
            self.statusBar().showMessage("Admin operation failed.", 4000)
            return

        # 3. Log result
        log_msg = f"Admin: [{result.action.name}] {result.message}"
        self._append_log(log_msg)

        # 4. UI feedback
        if result.success:
            self.statusBar().showMessage(result.message, 5000)

            # Refresh item list if entries or whole DB affected
            if scope in (AdminScope.WHOLE_DB, AdminScope.ENTRIES_AND_DEPENDENTS):
                try:
                    self._refresh()
                except Exception as exc:
                    self._append_log(f"Admin: refresh after {action.name} failed: {exc}")
        else:
            QMessageBox.critical(self, "Admin error", result.message)
            self.statusBar().showMessage("Admin operation failed.", 5000)






    # ------------------------------------------------------------------ #
    # bucket level operations
    # ------------------------------------------------------------------ #


    def _refresh_bucket_table(self) -> None:
        """
        Rebuild the bucket table from self.current_generator_config.
        """
        self.bucket_table.setRowCount(0)

        cfg = self.current_generator_config
        if cfg is None or not cfg.buckets:
            return

        for row_idx, bucket in enumerate(cfg.buckets):
            self.bucket_table.insertRow(row_idx)

            # Name
            self.bucket_table.setItem(row_idx, 0, QTableWidgetItem(bucket.name or ""))

            # Items: min_count–max_count, with -1 meaning "no upper bound"
            if bucket.max_count is None or bucket.max_count < 0:
                items_str = f"{bucket.min_count}–∞"
            else:
                items_str = f"{bucket.min_count}–{bucket.max_count}"
            self.bucket_table.setItem(row_idx, 1, QTableWidgetItem(items_str))

            # Price (per item)
            if bucket.min_value is None and bucket.max_value is None:
                price_str = "Any"
            elif bucket.min_value is not None and bucket.max_value is None:
                price_str = f"≥ {bucket.min_value} gp"
            elif bucket.min_value is None and bucket.max_value is not None:
                price_str = f"≤ {bucket.max_value} gp"
            else:
                price_str = f"{bucket.min_value}–{bucket.max_value} gp"
            self.bucket_table.setItem(row_idx, 2, QTableWidgetItem(price_str))

            # Remove button
            btn = QPushButton("Remove")
            btn.setProperty("variant", "flat")
            btn.clicked.connect(self._remove_bucket_row_for_button)
            self.bucket_table.setCellWidget(row_idx, 3, btn)

    def _remove_bucket_row_for_button(self) -> None:
        """
        Slot for 'Remove' button clicks inside the bucket table.
        Finds the row for the sender button and removes it from both the
        table and the underlying current_generator_config.buckets list.
        """
        btn = self.sender()
        if btn is None:
            return

        # Find which row this button is in
        for row in range(self.bucket_table.rowCount()):
            cell_widget = self.bucket_table.cellWidget(row, 3)
            if cell_widget is btn:
                cfg = self.current_generator_config
                if cfg is not None and 0 <= row < len(cfg.buckets):
                    removed = cfg.buckets.pop(row)
                    self._append_log(f"Generator: removed bucket {removed.name!r}")
                # Remove from table either way
                self.bucket_table.removeRow(row)
                self.statusBar().showMessage("Removed bucket.", 2000)
                return

    def _on_add_bucket_clicked(self) -> None:
        """
        Handle 'Add Bucket' from the bucket toolbar.

        Opens a BucketDialog, and if accepted, appends a new BucketConfig
        to self.current_generator_config.buckets and refreshes the table.
        """
        # Ensure we have a config object to attach buckets to
        if self.current_generator_config is None:
            self.current_generator_config = GeneratorConfig()

        dlg = BucketDialog(self)

        if dlg.exec() != QDialog.Accepted:
            return

        bucket = dlg.result()
        if bucket is None:
            return

        self.current_generator_config.buckets.append(bucket)
        self._append_log(f"Generator: added bucket {bucket.name!r}")
        self._refresh_bucket_table()

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
        """
        Load a generator from the backend, parse its config_json into a
        GeneratorConfig, and populate the Generator Details tab.
        """
        if not index.isValid():
            return

        gen_id = index.data(Qt.UserRole)
        if gen_id is None:
            return

        g = self.backend.get_generator(int(gen_id))
        if not g:
            return

        # Keep the model object around
        self.current_generator_def = g

        # Parse config_json into a GeneratorConfig
        cfg: GeneratorConfig
        raw_cfg = getattr(g, "config_json", None)
        if raw_cfg:
            try:
                cfg = config_from_json(raw_cfg)
            except Exception as exc:
                # Fallback to an empty config and log
                self._append_log(f"GEN CONFIG PARSE ERROR for id={g.id}: {exc}")
                cfg = GeneratorConfig()
        else:
            cfg = GeneratorConfig()

        self.current_generator_config = cfg

        # Basic fields
        self.gen_name.setText(g.name or "")
        # For now, map gen_purpose to GeneratorDef.context
        self.gen_purpose.setText(g.context or "")

        # Global bounds from GeneratorConfig
        self.gen_min_items.setText("" if cfg.min_items is None else str(cfg.min_items))
        self.gen_max_items.setText("" if cfg.max_items is None else str(cfg.max_items))
        # Treat "Budget" as max_total_value for now
        self.gen_budget.setText("" if cfg.max_total_value is None else str(cfg.max_total_value))

        # Buckets: read-only table projection
        self._refresh_bucket_table()

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
        for w in (self.txt_import_path, self.txt_default_img):
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

    def _clear_generator_details(self) -> None:
        """
        Clear the Generator Details tab and reset current generator state.
        """
        self.current_generator_def = None
        self.current_generator_config = None

        self.gen_name.clear()
        self.gen_purpose.clear()
        self.gen_min_items.clear()
        self.gen_max_items.clear()
        self.gen_budget.clear()

        self.bucket_table.setRowCount(0)

    def _format_attunement(self, card) -> str:
        if not card.attunement_required:
            return "None"
        if card.attunement_criteria:
            return f"Requires Attunement ({card.attunement_criteria})"
        return "Requires Attunement"

    def _run_import(self):
        path = self.txt_import_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Import", "Choose a CSV/XLSX file.")
            return

        default_img = self.txt_default_img.text().strip() or None

        self._append_log(
            f"Import starting: {path} (default_image={'yes' if default_img else 'no'})"
        )
        self.statusBar().showMessage("Import running…")
        self._toggle_import_ui(False)

        worker = ImportWorker(
            self.backend,
            path,
            default_image=default_img,
            batch_size=10,
            batch_sleep_seconds=5.0,
        )
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
            sitem.setData(itm.id, Qt.UserRole)
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

        # CardDTO
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
