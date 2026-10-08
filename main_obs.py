import sys
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QDate, QRegExp
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QDateEdit, QFormLayout, QLineEdit,
    QDialog, QFileDialog, QComboBox, QTextEdit, QMessageBox, QAction, QGridLayout, QLabel, QDoubleSpinBox)
from PyQt5.QtGui import QFont, QIcon, QRegExpValidator, QKeySequence, QColor, QPalette
import astropy.units as u
from astroplan import AtNightConstraint, AltitudeConstraint, MoonSeparationConstraint, AirmassConstraint, MoonIlluminationConstraint
import funcs_obs as fo
import warnings
warnings.filterwarnings("ignore")

def apply_theme(app):
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, Qt.white)
    pal.setColor(QPalette.WindowText, QColor(30, 34, 45))
    pal.setColor(QPalette.Base, Qt.white)
    pal.setColor(QPalette.Text, QColor(20, 23, 31))
    pal.setColor(QPalette.Button, Qt.white)
    pal.setColor(QPalette.ButtonText, QColor(45, 50, 65)) 
    app.setPalette(pal)

class MainWindow(QMainWindow): #QWidget
    def __init__(self):
        super().__init__()
        central = QWidget()
        self.setCentralWidget(central)
        self.setWindowTitle("Observability")
        self.resize(1200, 600)
        self.setMinimumSize(900, 550)

        #self.setStyleSheet("""QMainWindow, QWidget { background-color: white; } QLineEdit { background: black; }""")

        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Data
        self.text_ra = QLineEdit()
        self.text_dec = QLineEdit()
        self.text_date = QDateEdit()
        self.text_date.setCalendarPopup(True)
        self.text_date.setDisplayFormat("yyyy-MM-dd")
        self.text_date.setDate(QDate.currentDate())
        self.text_site = QComboBox()
        self.text_site.addItems(["La Silla", "Paranal", "La Palma", "Mt. Graham", "Cerro Tololo", "Mauna Kea", "Cerro Pachon"])

        # Constraints
        self.max_airmass = QDoubleSpinBox()
        self.max_airmass.setRange(1.0, 5.0)
        self.max_airmass.setSingleStep(0.1)
        self.max_airmass.setValue(2.9)

        self.min_md = QDoubleSpinBox()
        self.min_md.setRange(0, 180)
        self.min_md.setSingleStep(1)
        self.min_md.setSuffix(" °")
        self.min_md.setValue(30)

        self.max_li = QDoubleSpinBox()
        self.max_li.setRange(0, 1)
        self.max_li.setSingleStep(0.05)
        self.max_li.setValue(1.0)

        for w in (self.text_ra, self.text_dec):
            w.setFixedWidth(100)
        for w in (self.text_site, self.text_date):
            w.setFixedWidth(130)
        for w in (self.max_airmass, self.min_md, self.max_li):
            w.setFixedWidth(80)
            w.setKeyboardTracking(True)

        regex = QRegExp(r"[+-]?\d{1,2}:\d{2}:\d{2}(\.\d+)?")
        self.text_ra.setValidator(QRegExpValidator(regex))
        self.text_dec.setValidator(QRegExpValidator(regex))

        # Buttons
        self.btn_file = QPushButton("Select file for multiple objects")
        self.style_button(self.btn_file, "#3498db", size=[220, 50])
        self.btn_file.clicked.connect(self.open_file)

        self.btn_plot = QPushButton("Plot observability")
        self.style_button(self.btn_plot, "orange", size=[240, 50],fontsize=20)
        self.btn_plot.clicked.connect(self.generate_plot)
        self.btn_plot.setDefault(True)
        self.btn_plot.setShortcut("Ctrl+Return")

        self.btn_clear = QPushButton("Clear")
        self.style_button(self.btn_clear, "#e14c3c", size=[80,30],fontsize=12, border_px=1)
        self.btn_clear.clicked.connect(self.clear_imports)

        # Plot area
        self.figure, self.ax = plt.subplots()
        self.ax.axis('off')
        self.canvas = FigureCanvas(self.figure)
        
        # Layouts
        left_layout = QHBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(2, 24)
        grid.setColumnMinimumWidth(5, 24)
        self._add_in_grid(0, 0, "RA:", self.text_ra, grid);          self._add_in_grid(0, 3, "Site:", self.text_site, grid);    self._add_in_grid(0, 6, "Max airmass:", self.max_airmass, grid)
        self._add_in_grid(1, 0, "Dec:", self.text_dec, grid);        self._add_in_grid(1, 3, "Date:", self.text_date, grid);    self._add_in_grid(1, 6, "Min moon distance:", self.min_md, grid)
        self._add_in_grid(2, 6, "Max lunar illumination:", self.max_li, grid)
        grid.setColumnStretch(9, 1)
        self.text_ra.setPlaceholderText("hh:mm:ss")
        self.text_dec.setPlaceholderText("dd:mm:ss")
        self.min_md.setToolTip("[deg]")
        self.max_li.setToolTip("0 (new) to 1 (full)")
        left_layout.addLayout(grid)

        right_layout = QVBoxLayout()
        #right_layout.addWidget(self.btn_file)
        right_layout.addWidget(self.btn_plot, alignment=Qt.AlignRight | Qt.AlignVCenter)
        right_layout.addWidget(self.btn_clear, alignment=Qt.AlignRight | Qt.AlignVCenter)

        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(24)
        upper_layout.addStretch()
        upper_layout.addLayout(left_layout)
        upper_layout.addLayout(right_layout)
        upper_layout.addStretch()
        layout.addLayout(upper_layout, 2)
        layout.addWidget(self.canvas, 8)

        QWidget.setTabOrder(self.text_ra, self.text_dec)
        QWidget.setTabOrder(self.text_dec, self.text_site)
        QWidget.setTabOrder(self.text_site, self.text_date)
        QWidget.setTabOrder(self.text_date, self.max_airmass)
        QWidget.setTabOrder(self.max_airmass, self.min_md)
        QWidget.setTabOrder(self.min_md, self.max_li)
        QWidget.setTabOrder(self.max_li, self.btn_plot)
        QWidget.setTabOrder(self.btn_plot, self.btn_clear)

        self.setLayout(layout)

        # Variables
        self.selected_file = None
        self._build_menu_and_shortcuts()

    def _build_menu_and_shortcuts(self):
        m = self.menuBar().addMenu("File")
        for text, key, slot in (
            ("Load file", "Ctrl+O", self.open_file),
            ("Save plot", "Ctrl+S", self.save_plot),
        ):
            a = QAction(text, self)
            a.setShortcut(QKeySequence(key))
            a.triggered.connect(slot)
            m.addAction(a)

    def style_button(self, button, color, size=[210, 50],fontsize=14, border_px=2):
        button.setFixedSize(size[0], size[1])
        button.setFont(QFont("Verdana", fontsize)) #, QFont.Bold
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                border: {int(border_px)}px solid dark{color[1:]};
            }}
            QPushButton:hover {{
                background-color: dark{color[1:]};
            }}
            QPushButton:pressed {{
                background-color: black;
            }}
        """)

    def style_textedit(self, textedit):
        textedit.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #D0D7DE;
                border-radius: 6px;
            }
        """)

    def _add_in_grid(self, row, col, text, widget, grid):
        lbl = QLabel(text)
        grid.addWidget(lbl, row, col, alignment=Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(widget, row, col + 1)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose data file", "", "Data Files (*.csv *.txt *.dat);;All Files (*)")
        if file_name:
            self.selected_file = file_name
            print(f"Selected file: {file_name}")
        else:
            return
    
    def save_plot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save plot", "observability.png", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if not path:
            return
        self.ax.figure.savefig(path, dpi=200, bbox_inches='tight')

    def clear_imports(self):
        self.selected_file = None

    def on_pick(self, event):
        print("Pick:", event.artist.get_label())
        #event.artist.set_visible(False)
        picked_line = event.artist
        gid = picked_line.get_gid()
        if not gid:
            return

        if event.mouseevent is getattr(self, '_last_mouse_event', None):
            return
        self._last_mouse_event = event.mouseevent
        group = self.moon_degs.get(gid, []) #[ln for ln in self.ax.get_lines() if ln.get_gid() == gid]
        if not group:
            return

        # Hide/show toggle on every lines with the same gid
        new_visible = not group[0].get_visible()
        for art in group:
            art.set_visible(new_visible)

        # target_line = None
        # for line in self.ax.get_lines():
        #     if line.get_gid() == gid:
        #         target_line = line
        #         break
        
        # if target_line is None:
        #     return

        # 
        # new_visible = not target_line.get_visible()
        # target_line.set_visible(new_visible)
        # # for line in ax.get_lines():
        # #     if line.get_gid() == gid:
        # #         line.set_visible(not line.get_visible())

        for md in self.moon_degs.get(gid, []):
            md.set_visible(new_visible)

        legend = self.ax.get_legend()
        if legend:
            handles = getattr(legend, 'legend_handles', None) or getattr(legend, 'legendHandles', [])
            for leg_line, leg_text in zip(handles, legend.get_texts()):
                if leg_text.get_text() == gid:
                    leg_line.set_alpha(1.0 if new_visible else 0.2)

        self.canvas.draw_idle()


    def generate_plot(self):

        self.ax.clear()

        if hasattr(self, 'cid_pick'):
            self.figure.canvas.mpl_disconnect(self.cid_pick)

        if self.selected_file:
            try:
                target_names, ra, dec = np.genfromtxt(self.selected_file,unpack=True, dtype=str)
                if len(ra) == 0 or len(dec) == 0 or len(ra) != len(dec):
                    QMessageBox.warning(self, "Invalid selection", f"Invalid RA, Dec provided!")
                    return
            except:
                QMessageBox.warning(self, "Invalid selection", f"Invalid data in file. Please check...")
                self.ax.axis('off')
                return

            if self.text_ra.text().strip() != '' and self.text_dec.text().strip() != '':
                ra = np.append(ra, self.text_ra.text().strip())
                dec = np.append(dec, self.text_dec.text().strip())
                target_names = np.append(target_names,'User target')

        else:
            ra = [self.text_ra.text().strip()]
            dec = [self.text_dec.text().strip()]
            target_names = ['']
            if ra==[''] or dec==['']:
                QMessageBox.warning(self, "Invalid selection", f"Invalid RA, Dec provided!")
                return

        site = self.text_site.currentText()
        date_str = self.text_date.date().toString("yyyy-MM-dd")

        if not date_str:
            date_str = 'today'

        try:
            constraints = [AtNightConstraint.twilight_astronomical(), AltitudeConstraint(min=20*u.deg), 
                        MoonSeparationConstraint(min=float(self.min_md.value())*u.deg), 
                        AirmassConstraint(max=float(self.max_airmass.value()), min=1.0024, boolean_constraint=True),
                        MoonIlluminationConstraint(max=float(self.max_li.value()))]

            self.moon_degs = fo.plot_observability(self.ax,site,ra,dec, date=date_str,target_names=target_names, constraints=constraints)
            self.cid_pick = self.canvas.mpl_connect("pick_event", self.on_pick)

            legend = self.ax.get_legend()
            if legend:
                handles = getattr(legend, 'legend_handles', None) or getattr(legend, 'legendHandles', [])
                for leg_line, leg_text in zip(handles, legend.get_texts()):
                    leg_line.set_picker(5)
                    leg_line.set_gid(leg_text.get_text())

        except Exception as e:
            QMessageBox.warning(self,"Exception", f"Error in plotting: {e}")
            return

        self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    app.setWindowIcon(QIcon("obs_logo.png"))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
