import sys
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QDate, QRegExp
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QDateEdit, QFormLayout, QLineEdit,
    QDialog, QFileDialog, QComboBox, QTextEdit, QMessageBox, QAction)
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

        #self.setStyleSheet("""QMainWindow, QWidget { background-color: white; } QLineEdit { background: black; }""")

        # Main layout
        layout = QVBoxLayout(central)

        # Data
        self.text_ra = QLineEdit() #QTextEdit()
        self.text_dec = QLineEdit() 
        self.text_date = QDateEdit()
        self.text_date.setCalendarPopup(True)
        self.text_date.setDisplayFormat("yyyy-MM-dd")
        self.text_date.setDate(QDate.currentDate())
        self.text_site = QComboBox()
        self.text_site.addItems(["La Silla", "Paranal", "La Palma", "Mt. Graham", "Cerro Tololo", "Mauna Kea", "Cerro Pachon"])

        # Constraints
        self.max_airmass = QLineEdit("2.9")
        self.max_li = QLineEdit("1.0")
        self.max_md = QLineEdit("30")

        self.text_ra.setMaximumWidth(100)
        self.text_dec.setMaximumWidth(100)
        self.text_date.setMaximumWidth(130)
        self.text_site.setMaximumWidth(130)

        self.max_airmass.setMaximumWidth(40)
        self.max_li.setMaximumWidth(40)
        self.max_md.setMaximumWidth(40)

        regex = QRegExp(r"[+-]?\d{1,2}:\d{2}:\d{2}(\.\d+)?")
        self.text_ra.setValidator(QRegExpValidator(regex))
        self.text_dec.setValidator(QRegExpValidator(regex))

        # Buttons
        self.btn_file = QPushButton("Select file for multiple objects")
        self.style_button(self.btn_file, "#3498db", size=[220, 50])
        self.btn_file.clicked.connect(self.open_file)

        self.btn_plot = QPushButton("Plot observability!")
        self.style_button(self.btn_plot, "orange", size=[240, 50],fontsize=20)
        self.btn_plot.clicked.connect(self.generate_plot)

        self.btn_clear = QPushButton("Clear")
        self.style_button(self.btn_clear, "#e14c3c", size=[80,30],fontsize=12)
        self.btn_clear.clicked.connect(self.clear_imports)

        # Plot area
        self.figure, self.ax = plt.subplots()
        self.ax.axis('off')
        self.canvas = FigureCanvas(self.figure)
        
        # Layouts
        left_layout = QHBoxLayout()
        left_layout.setSpacing(10)
        form_left = QFormLayout()
        form_left.addRow("RA:", self.text_ra)
        form_left.addRow("Dec:", self.text_dec)
        form_central = QFormLayout()
        form_central.addRow("Site:", self.text_site)
        form_central.addRow("Date:", self.text_date)
        form_right = QFormLayout()
        form_right.addRow("Airmass:", self.max_airmass)
        form_right.addRow("Moon distance:", self.max_md)
        form_right.addRow("Lunar illumination:", self.max_li)
        left_layout.addLayout(form_left)
        left_layout.addLayout(form_central)
        left_layout.addLayout(form_right)

        right_layout = QHBoxLayout()
        #right_layout.addWidget(self.btn_file)
        right_layout.addWidget(self.btn_plot)
        right_layout.addWidget(self.btn_clear)

        upper_layout = QHBoxLayout()
        upper_layout.addStretch()
        upper_layout.addLayout(left_layout)
        upper_layout.addLayout(right_layout)
        upper_layout.addStretch()
        layout.addLayout(upper_layout, 2)
        layout.addWidget(self.canvas, 8)

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

    def style_button(self, button, color, size=[210, 50],fontsize=14):
        button.setFixedSize(size[0], size[1])
        button.setFont(QFont("Verdana", fontsize)) #, QFont.Bold
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                border: 2px solid dark{color[1:]};
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
                        MoonSeparationConstraint(min=float(self.max_md.text())*u.deg), AirmassConstraint(max=float(self.max_airmass.text()), min=1.0, boolean_constraint=True),
                        MoonIlluminationConstraint(max=float(self.max_li.text()))]
            
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
