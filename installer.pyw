import sys
import subprocess
import random
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QLineEdit, QComboBox, QPushButton, QGraphicsOpacityEffect, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QPoint, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QLinearGradient, QColor, QIcon, QPainterPath

##########################################################################
# Custom TitleBar
##########################################################################
# This TitleBar class replaces the native title bar. It uses a blue gradient
# (from #003399 to #0059b3) and lets the window be moved by dragging.
# (Rounded edges and the overall border are painted by the top-level window.)
##########################################################################

class TitleBar(QWidget):
    def __init__(self, parent, title_text="PyXP Setup"):
        super().__init__(parent)
        self.parent = parent
        self.pressing = False
        self.start = QPoint(0, 0)
        self.setFixedHeight(30)
        # Use a blue gradient for the title bar.
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #003399, stop:1 #0059b3);
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Title label on the left.
        self.title = QLabel(title_text, self)

        # Check if your custom font file exists
        font_path = "windows-xp-tahoma.ttf"
        if os.path.exists(font_path):
            # If the file exists, assume you'll load and use your custom font.
            font_family = "Windows XP Tahoma"  # Or whatever family name your loaded font uses.
        else:
            # Fallback to Tahoma
            font_family = "Tahoma"

        # Build the QSS string dynamically
        style = f"color: white; font: bold 10pt '{font_family}';"

        self.title.setStyleSheet(style)
        layout.addWidget(self.title)
        layout.addStretch()
        
        # Minimize button.
        self.btn_min = QPushButton(self)
        self.btn_min.setFixedSize(20, 20)
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setIcon(QIcon("minimize.png"))
        self.btn_min.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.btn_min.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.btn_min)
        
        # Maximize/Restore button.
        self.btn_max = QPushButton(self)
        self.btn_max.setFixedSize(20, 20)
        self.btn_max.setToolTip("Maximize")
        self.btn_max.setIcon(QIcon("maximize.png"))
        self.btn_max.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.btn_max.clicked.connect(self.toggle_max_restore)
        layout.addWidget(self.btn_max)
        
        # Close button.
        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setToolTip("Close")
        self.btn_close.setIcon(QIcon("close.png"))
        self.btn_close.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.btn_close.clicked.connect(self.parent.close)
        layout.addWidget(self.btn_close)
        
        self.setLayout(layout)
    
    def toggle_max_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.btn_max.setIcon(QIcon("maximize.png"))
        else:
            self.parent.showMaximized()
            self.btn_max.setIcon(QIcon("maximize.png"))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = event.pos()
            self.pressing = True
        event.accept()
    
    def mouseMoveEvent(self, event):
        if self.pressing:
            self.parent.move(self.parent.pos() + event.pos() - self.start)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        self.pressing = False
        event.accept()

##########################################################################
# Custom XP-Style Progress Bar
##########################################################################
# This widget paints a series of segments. Only the "active" segment (based
# on the current value) is filled with a blue vertical gradient (from #0033CC
# to #0066FF) and a glow effect.
##########################################################################
class XPProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setFixedHeight(30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.black)
        segWidth = 20
        segSpacing = 4
        totalWidth = self.width()
        numSegments = (totalWidth - segSpacing) // (segWidth + segSpacing)
        if numSegments <= 0:
            return
        activeSegment = int(self.value() / self.maximum() * numSegments)
        if activeSegment >= numSegments:
            activeSegment = numSegments - 1
        segmentHeight = 20
        y = (self.height() - segmentHeight) // 2
        x = segSpacing
        for i in range(numSegments):
            rect = QRect(x, y, segWidth, segmentHeight)
            if i == activeSegment:
                gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                gradient.setColorAt(0, QColor("#0033CC"))
                gradient.setColorAt(1, QColor("#0066FF"))
                painter.fillRect(rect, gradient)
                glowColor = QColor("#0066FF")
                glowColor.setAlpha(120)
                pen = QPen(glowColor)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawRect(rect)
            else:
                painter.fillRect(rect, QColor(50, 50, 50))
            x += segWidth + segSpacing
        painter.end()

##########################################################################
# InstallerUI – Pre-Boot Installer Screen
##########################################################################
# This window uses a three-column layout:
#  - Left: Installation step checklist.
#  - Center: Installation progress (header, progress bar, buttons).
#  - Right: System tips.
# A rounded blue border is drawn in the paintEvent.
##########################################################################
class InstallerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.steps = ["Initializing", "Copying Files", "Installing Drivers",
                      "Configuring System", "Finalizing Setup"]
        self.step_thresholds = [(i+1)*20 for i in range(len(self.steps))]
        self.step_labels = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PyXP Installation")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 250)
        self.content_style = """
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #DCE8F7, stop:1 #B0C4DE);
            font-family: 'Tahoma', sans-serif;
            font-size: 10pt;
        """
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(10, 10, 10, 10)
        
        content = QWidget(self)
        content.setStyleSheet(self.content_style)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Custom TitleBar.
        self.title_bar = TitleBar(content, "PyXP Installation")
        content_layout.addWidget(self.title_bar)
        
        main_layout = QHBoxLayout()
        # Left Sidebar – Checklist.
        left_panel = QFrame(content)
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setFixedWidth(150)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(5, 5, 5, 5)
        for step in self.steps:
            label = QLabel(f"○ {step}", self)
            label.setStyleSheet("font-weight: bold;")
            left_layout.addWidget(label)
            self.step_labels.append(label)
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)
        
        # Center Panel – Installation Progress.
        center_panel = QFrame(content)
        center_panel.setFrameStyle(QFrame.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        header_label = QLabel("Welcome to PyXP Setup", self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("background-color: #003399; color: white; font: bold 12pt Tahoma; padding: 10px;")
        center_layout.addWidget(header_label)
        self.label = QLabel("Click 'Install' to begin the PyXP installation.", self)
        center_layout.addWidget(self.label)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        center_layout.addWidget(self.progress_bar)
        btn_layout = QHBoxLayout()
        self.install_button = QPushButton("Install", self)
        self.install_button.clicked.connect(self.start_installation)
        btn_layout.addWidget(self.install_button)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_button)
        center_layout.addLayout(btn_layout)
        center_panel.setLayout(center_layout)
        main_layout.addWidget(center_panel, stretch=1)
        
        # Right Panel – System Tips.
        right_panel = QFrame(content)
        right_panel.setFrameStyle(QFrame.StyledPanel)
        right_panel.setFixedWidth(200)
        right_layout = QVBoxLayout(right_panel)
        tips_label = QLabel("System Tips", self)
        tips_label.setStyleSheet("font: bold 10pt Tahoma; color: #003399;")
        tips_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(tips_label)
        tips_text = ("• Press F1 for help.\n"
                     "• Use Control Panel to adjust settings.\n"
                     "• Your hardware is auto-detected.\n"
                     "• A restart is advised after setup.\n"
                     "• Use Alt+Tab to switch application windows.")
        tips_content = QLabel(tips_text, self)
        tips_content.setWordWrap(True)
        right_layout.addWidget(tips_content)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel)
        
        content_layout.addLayout(main_layout)
        main_vlayout.addWidget(content)
        self.setLayout(main_vlayout)
        
        self.install_timer = QTimer(self)
        self.install_timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        self.pause_trigger = random.randint(20, 80)
        self.pause_duration = random.randint(500, 2000)
        self.installing = True
    
    def paintEvent(self, event):
        # Draw a rounded blue border around the entire window.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        outer_path = QPainterPath()
        outer_path.addRoundedRect(QRectF(rect), 10, 10)
        painter.fillPath(outer_path, QColor("#003399"))
        event.accept()
    
    def moveEvent(self, event):
        self.update()
        super().moveEvent(event)
    
    def start_installation(self):
        self.label.setText("Installing, please wait...")
        self.install_button.hide()
        self.install_timer.start(50)
    
    def update_progress(self):
        if self.current_progress == self.pause_trigger and self.installing:
            self.installing = False
            self.install_timer.stop()
            QTimer.singleShot(self.pause_duration, self.resume_installation)
        else:
            self.current_progress += 1
            self.progress_bar.setValue(self.current_progress)
            self.update_steps()
            if self.current_progress >= 100:
                self.install_timer.stop()
                self.label.setText("Installation Complete!")
                QTimer.singleShot(1000, self.launch_boot_screen)
    
    def resume_installation(self):
        self.installing = True
        self.current_progress += 1
        self.progress_bar.setValue(self.current_progress)
        self.update_steps()
        self.install_timer.start(50)
    
    def update_steps(self):
        for idx, threshold in enumerate(self.step_thresholds):
            if self.current_progress >= threshold:
                self.step_labels[idx].setText(f"<font color='green'>●</font> {self.steps[idx]}")
            else:
                self.step_labels[idx].setText(f"○ {self.steps[idx]}")
    
    def launch_boot_screen(self):
        self.hide()
        global boot_screen
        boot_screen = BootScreen()
        boot_screen.show()

##########################################################################
# BootScreen – The Windows XP Boot Screen
##########################################################################
# This window is frameless with a custom rounded blue border.
# Inner content (logo and progress bar) is on a black background.
##########################################################################
class BootScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("%.boot%")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 600)
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(10, 10, 10, 10)
        
        content = QWidget(self)
        content.setStyleSheet("background-color: black;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("logo.png").scaled(400, 300, Qt.KeepAspectRatio)
        self.logo_label.setPixmap(pixmap)
        content_layout.addWidget(self.logo_label)
        
        self.progress_bar = XPProgressBar(self)
        content_layout.addWidget(self.progress_bar)
        
        main_vlayout.addWidget(content)
        self.setLayout(main_vlayout)
        
        self.fade_in_widgets()
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.cycle_progress)
        self.progress_timer.start(100)
        self.transition_timer = QTimer(self)
        self.transition_timer.singleShot(15000, self.fade_out_widgets)
        self.current_progress = 0
    
    def paintEvent(self, event):
        # Draw the overall rounded blue border.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 10, 10)
        painter.fillPath(path, QColor("#003399"))
        event.accept()
    
    def moveEvent(self, event):
        self.update()
        super().moveEvent(event)
    
    def fade_in_widgets(self):
        self.logo_opacity = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.logo_opacity)
        self.logo_animation = QPropertyAnimation(self.logo_opacity, b"opacity")
        self.logo_animation.setDuration(1000)
        self.logo_animation.setStartValue(0)
        self.logo_animation.setEndValue(1)
        self.logo_animation.start()
        
        self.progress_opacity = QGraphicsOpacityEffect(self.progress_bar)
        self.progress_bar.setGraphicsEffect(self.progress_opacity)
        self.progress_animation = QPropertyAnimation(self.progress_opacity, b"opacity")
        self.progress_animation.setDuration(1000)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(1)
        self.progress_animation.start()
    
    def fade_out_widgets(self):
        self.logo_fade_out = QPropertyAnimation(self.logo_opacity, b"opacity")
        self.logo_fade_out.setDuration(1000)
        self.logo_fade_out.setStartValue(1)
        self.logo_fade_out.setEndValue(0)
        self.logo_fade_out.start()
        
        self.progress_fade_out = QPropertyAnimation(self.progress_opacity, b"opacity")
        self.progress_fade_out.setDuration(1000)
        self.progress_fade_out.setStartValue(1)
        self.progress_fade_out.setEndValue(0)
        self.progress_fade_out.finished.connect(self.complete_transition)
        self.progress_fade_out.start()
    
    def complete_transition(self):
        self.hide()
        global setup_window
        setup_window = UserSetupScreen()
        setup_window.show()
    
    def cycle_progress(self):
        self.current_progress += 10
        if self.current_progress > 100:
            self.current_progress = 0
        self.progress_bar.setValue(self.current_progress)
        self.progress_bar.update()

##########################################################################
# UserSetupScreen – Windows XP Setup Screen
##########################################################################
# This window shows a custom TitleBar and account fields,
# and also draws a rounded blue border for the entire window.
##########################################################################
class UserSetupScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PyXP Setup")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 600, 400)
        self.content_style = """
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #DCE8F7, stop:1 #B0C4DE);
            font-family: Tahoma, sans-serif;
            font-size: 10pt;
        """
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(10, 10, 10, 10)
        
        content = QWidget(self)
        content.setStyleSheet(self.content_style)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = TitleBar(content, "PyXP Setup")
        content_layout.addWidget(self.title_bar)
        
        layout = QVBoxLayout()
        self.header_label = QLabel("Welcome to PyXP Setup", self)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("background-color: #003399; color: white; font: bold 12pt Tahoma; padding: 10px;")
        layout.addWidget(self.header_label)
        self.label = QLabel("Setup PyXP Account", self)
        layout.addWidget(self.label)
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Enter Username")
        layout.addWidget(self.username_input)
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        self.language_selection = QComboBox(self)
        self.language_selection.addItems(["English", "Spanish", "French", "Japanese"])
        layout.addWidget(self.language_selection)
        self.timezone_selection = QComboBox(self)
        self.timezone_selection.addItems(["EST", "PST", "CST", "GMT"])
        layout.addWidget(self.timezone_selection)
        self.finish_button = QPushButton("Finish Setup", self)
        self.finish_button.clicked.connect(self.launch_login)
        layout.addWidget(self.finish_button)
        content_layout.addLayout(layout)
        main_vlayout.addWidget(content)
        self.setLayout(main_vlayout)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 10, 10)
        painter.fillPath(path, QColor("#003399"))
        event.accept()
    
    def moveEvent(self, event):
        self.update()
        super().moveEvent(event)
    
    def launch_login(self):
        global login_window
        login_window = LoginScreen(self.username_input.text(), self.password_input.text())
        self.hide()
        login_window.show()

##########################################################################
# LoginScreen – Windows XP Login Screen
##########################################################################
# This window uses a custom TitleBar and white inner background,
# and draws a rounded blue border around the entire window.
##########################################################################
class LoginScreen(QWidget):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PyXP Login")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 600, 400)
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(10, 10, 10, 10)
        
        content = QWidget(self)
        content.setStyleSheet("background-color: white; font-family: Tahoma, sans-serif; font-size: 10pt;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = TitleBar(content, "PyXP Login")
        content_layout.addWidget(self.title_bar)
        
        layout = QVBoxLayout()
        self.label = QLabel("Login to W{yXP", self)
        layout.addWidget(self.label)
        self.username_label = QLabel(f"Username: {self.username}", self)
        layout.addWidget(self.username_label)
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.validate_login)
        layout.addWidget(self.login_button)
        content_layout.addLayout(layout)
        main_vlayout.addWidget(content)
        self.setLayout(main_vlayout)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 10, 10)
        painter.fillPath(path, QColor("#003399"))
        event.accept()
    
    def moveEvent(self, event):
        self.update()
        super().moveEvent(event)

    def validate_login(self):
        if self.password_input.text() == self.password:
            self.label.setText("Login Successful! Launching Desktop...")
            # Launch desktop.pyw with your current Python interpreter.
            subprocess.Popen([sys.executable, "desktop.pyw"])
            # Close the login screen.
            self.close()
        else:
            self.label.setText("Incorrect password. Try again.")


##########################################################################
# Main Execution
##########################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    installer = InstallerUI()
    installer.show()
    boot_screen = None
    setup_window = None
    login_window = None
    sys.exit(app.exec_())
