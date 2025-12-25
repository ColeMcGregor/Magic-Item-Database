# townecodex/ui/styles.py
import os
from PySide6.QtGui import QFontDatabase, QFont


APP_TITLE = "Towne Codex"

STYLE = """
/* === Towne Codex — Parchment Theme (Qt-safe) === */

/* Base */
QMainWindow, QWidget {
  background: #F3EEE5;
  color: #1C1713;
  font-family: "__SERIF__", Georgia, "Times New Roman", Times, serif;
  font-size: 15px;
}

/* Menubar / Menus */
QMenuBar {
  background-color: #FFFCF4;
  border-bottom: 1px solid #D8CEBE;
}
QMenuBar::item { padding: 4px 10px; }
QMenuBar::item:selected { background-color: #F0E6D7; border-radius: 6px; }

QMenu {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  padding: 6px 4px;
}
QMenu::separator { height: 1px; background-color: #C9BFAE; margin: 6px 8px; }
QMenu::item { padding: 6px 12px; }
QMenu::item:selected { background-color: #F0E6D7; }

/* Toolbar */
QToolBar {
  background-color: #FFFDF7;
  border-bottom: 1px solid #D8CEBE;
  padding: 4px 6px;
}
QToolButton { padding: 4px 8px; border-radius: 8px; }
QToolButton:hover { background-color: #F0E6D7; }

/* Panels / Grouping */
QGroupBox, QFrame[role="panel"] {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 10px;
}
QGroupBox { margin-top: 12px; }
QGroupBox::title {
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 6px;
  color: #6E5B49;
}

/* Labels */
QLabel[role="caption"] { color: #6E5B49; }

/* Inputs */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 8px;
  padding: 5px 8px;
  selection-background-color: #F0E6D7;
}
QTextEdit, QPlainTextEdit { padding: 8px 10px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #C7AFA0; }

/* --- Fix QComboBox arrow --- */
QComboBox { padding-right: 30px; }
QComboBox::drop-down {
  subcontrol-origin: padding;
  subcontrol-position: top right;
  width: 26px;
  border-left: 1px solid #D8CEBE;
}
QComboBox::down-arrow {
  width: 12px; height: 12px; margin-right: 6px;
}

/* Buttons */
QPushButton {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 8px;
  padding: 4px 8px;
  min-height: 18px;
}
QPushButton:hover {
    background-color: #FAF6EE;
    border: 2px solid #B6B1A7;
    padding-top: 7px;    /* shift text down 1px */
    padding-left: 9px;   /* shift text right 1px */
    padding-bottom: 5px; /* adjust to keep height stable */
    padding-right: 11px;
}
QPushButton:pressed { background-color: #EFE7D8; }

QPushButton[variant="primary"] {
  background-color: #7C1F24; color: #FFF7F5; border: 1px solid #7C1F24;
}
QPushButton[variant="royal"] {
  background-color: #2E5AA3; color: #F7FAFF; border: 1px solid #2E5AA3;
}
QPushButton[variant="danger"] {
  background-color: #9B1B20; color: #FFF5F4; border: 1px solid #9B1B20;
}
QPushButton[variant="bulbasaur"] {
  background-color: #26854c; color: #FFF5F4; border: 1px solid #26854c;
}
QPushButton[variant="flat"] {
  background-color: transparent; border: none; color: #6E5B49;
}

/* Tabs */
QTabWidget::pane {
  border: 1px solid #D8CEBE;
  border-radius: 10px;
  background-color: #FFFCF4;
}
QTabBar::tab {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-bottom: none;
  padding: 6px 14px;
  margin-right: 6px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  color: #6E5B49;
}
QTabBar::tab:selected {
  background-color: #FBF7EE;
  color: #1C1713;
  border-bottom: 2px solid #B58A2A;
}

/* Lists / Tables */
QListWidget, QTreeView, QTableView {
  background-color: #FFFCF4;
  border: 1px solid #D8CEBE;
  border-radius: 10px;
}
QListView::item { padding: 6px 8px; }
QListView::item:selected { background-color: #F0E6D7; color: #1C1713; border-radius: 6px; }

/* Splitter */
QSplitter::handle { background-color: #E8E0CF; width: 8px; }
QSplitter::handle:hover { background-color: #E2D8C4; }

/* Scrollbars */
QScrollBar:vertical, QScrollBar:horizontal { background: transparent; margin: 0; }
QScrollBar::handle { background-color: #D1C7B6; border-radius: 6px; min-height: 24px; }
QScrollBar::handle:hover { background-color: #C5B9A6; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }

/* Status Bar & Tooltips */
QStatusBar { background-color: #FFFCF4; border-top: 1px solid #D8CEBE; }
QToolTip {
  background-color: #FFF9ED; color: #1C1713;
  border: 1px solid #D8CEBE; padding: 6px 8px; border-radius: 8px;
}

/* Placeholders */
QLineEdit::placeholder { color: #9B8A78; }
"""


def build_stylesheet() -> str:
    """
    Registers IM Fell English if present and returns the final stylesheet
    with the correct font-family injected. If the font is missing, the
    token resolves to Georgia fallback.
    """
    base_dir = os.path.dirname(__file__)
    font_path = os.path.abspath(os.path.join(
        base_dir, "..", "..", "assets", "fonts", "IMFellEnglish-Regular.ttf"
    ))

    family = "Georgia"
    if os.path.exists(font_path):
        fid = QFontDatabase.addApplicationFont(font_path)
        fams = QFontDatabase.applicationFontFamilies(fid)
        if fams:
            family = fams[0]
            # print("Loaded font:", family)
    else:
        print("IMFellEnglish-Regular.ttf not found; using fallback:", family)

    return STYLE.replace("__SERIF__", family)