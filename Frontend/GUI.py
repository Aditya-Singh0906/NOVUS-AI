import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit,
    QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QFrame, QSizePolicy, QLabel,
    QMessageBox, QGroupBox, QTabWidget, QFormLayout, QComboBox, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import (
    QFont, QIcon, QPainter, QMovie, QColor, QTextFormat,
    QPixmap, QTextBlockFormat, QTextCharFormat
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from dotenv import dotenv_values, set_key
from Backend.Utils import resource_path


env_vars = dotenv_values(resource_path(".env"))
AssistantName = env_vars.get("AssistantName")
current_dir = os.getcwd()
Username = env_vars.get("Username", "User")


old_chat_message = ""
TempDirPath = resource_path(r"Frontend\Files")
GraphicsDirPath = resource_path(r"Frontend\Graphics")

EndButtonStatus = False

def GetEndButtonStatus():
    global EndButtonStatus
    return EndButtonStatus

def SetEndButtonStatus(value: bool):
    global EndButtonStatus
    EndButtonStatus = value

def ResetEndButtonStatus():
    global EndButtonStatus
    EndButtonStatus = False


def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = [
        "how", "what", "where", "when", "who", "why",
        "which", "whose", "can you", "what's", "where's", "how's"
    ]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf'{TempDirPath}\Mic.Data', "w", encoding="utf-8") as file:
        file.write(Command)

def GetMicrophoneStatus():
    try:
        with open(rf'{TempDirPath}\Mic.Data', "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "False"

def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}\Status.Data', "w", encoding="utf-8") as file:
        file.write(Status)

def GetAssistantStatus():
    try:
        with open(rf'{TempDirPath}\Status.Data', "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "Offline"

def MicButtonInitialized():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    return rf'{GraphicsDirPath}\{Filename}'

def TempDirectoryPath(Filename):
    return rf'{TempDirPath}\{Filename}'

def ShowTextToScreen(Text):
    with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
        file.write(Text)
class ChatSection(QWidget):

    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)

        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        text_color = QColor(Qt.blue)
        text_color_format = QTextCharFormat()
        text_color_format.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_format)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(420, 320))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        layout.setSpacing(-10)
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(500)
        self.chat_text_edit.viewport().installEventFilter(self)

        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: black;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read()
                if messages and messages != old_chat_message:
                    if messages.strip().startswith(f"{Username} :"):
                        self.addMessage(message=messages, color='Cyan')
                    else:
                        self.addMessage(message=messages, color='White')
                    old_chat_message = messages
        except FileNotFoundError:
            pass # File might not exist on first run


    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
                self.label.setText(messages)
        except FileNotFoundError:
            self.label.setText("Listening...")


    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('voice.png'), 60, 60)
            MicButtonInitialized()
        else:
            self.load_icon(GraphicsDirectoryPath('mic.png'), 60, 60)
            MicButtonClosed()
        self.toggled = not self.toggled

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        main_layout.addStretch(1)

        self.gif_label = QLabel()
        self.movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        self.movie.setScaledSize(QSize(650, 490))
        self.gif_label.setMovie(self.movie)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.movie.start()
        main_layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        self.icon_label = QLabel()
        pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
        new_pixmap = pixmap.scaled(60, 60)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(100, 100)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.toggled = True
        self.toggle_icon()
        self.icon_label.mousePressEvent = self.toggle_icon
        main_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label, alignment=Qt.AlignCenter)

        main_layout.addStretch(1)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedSize(screen_width, screen_height)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(500)

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
                self.label.setText(messages)
        except FileNotFoundError:
            self.label.setText("Listening...")


    def load_icon(self, path, width=100, height=100):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'))
            MicButtonInitialized()
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'))
            MicButtonClosed()
        self.toggled = not self.toggled


class MessageScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.chat_section = ChatSection()
        layout.addWidget(self.chat_section, stretch=1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #444;
                border-radius: 18px;
                padding: 12px;
                color: white;
                background-color: #1c1c1c;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00ffff;
                background-color: #111;
            }
        """)
        self.input_box.returnPressed.connect(self.handleUserQuery)
        bottom_bar.addWidget(self.input_box, stretch=1)

        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
        """)
        self.send_button.clicked.connect(self.handleUserQuery)
        bottom_bar.addWidget(self.send_button)

        self.end_button = QPushButton("End")
        self.end_button.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        self.end_button.clicked.connect(self.endTasks)
        bottom_bar.addWidget(self.end_button)

        layout.addLayout(bottom_bar)
        layout.addSpacing(103)

        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

    def handleUserQuery(self):
        query = self.input_box.text().strip()
        if not query:
            return

        self.input_box.clear()
        
        try:
            from Main import process_query
            process_query(query)
        except Exception as e:
            print(f"[handleUserQuery ERROR] {e}")


    def endTasks(self):
        SetMicrophoneStatus("False")
        SetAssistantStatus("Listening...")
        SetEndButtonStatus(True)
        self.input_box.clear()

class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.env_path = resource_path('.env')
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Left Navigation Panel ---
        nav_panel = QFrame()
        nav_panel.setFixedWidth(240)
        nav_panel.setStyleSheet("background-color: #1c1c1c; border-right: 1px solid #444;")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setAlignment(Qt.AlignTop)
        
        nav_title = QLabel("Settings")
        nav_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px; padding-left: 10px;")
        nav_layout.addWidget(nav_title)
        
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #1c1c1c;
                font-size: 16px;
            }
            QListWidget::item {
                color: #ccc;
                padding: 20px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
            }
        """)
        nav_layout.addWidget(self.nav_list)
        
        # --- Right Content Panel ---
        self.content_stack = QStackedWidget()
        
        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self.content_stack)
        
        # --- Create Pages ---
        self.api_page = QWidget()
        self.prefs_page = QWidget()
        self.about_page = QWidget()
        
        self.setup_api_page()
        self.setup_prefs_page()
        self.setup_about_page()
        
        self.content_stack.addWidget(self.api_page)
        self.content_stack.addWidget(self.prefs_page)
        self.content_stack.addWidget(self.about_page)
        
        # --- Populate Nav List ---
        self.nav_list.addItem("AI & APIs")
        self.nav_list.addItem("User Preferences")
        self.nav_list.addItem("About & Help")
        
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)
        
        self.load_settings()

    def setup_api_page(self):
        layout = QVBoxLayout(self.api_page)
        layout.setContentsMargins(40, 40, 40, 40)
        group_box = QGroupBox("API Keys Configuration")
        group_box.setStyleSheet("QGroupBox { color: #00ffff; font-size: 18px; font-weight: bold; border: 1px solid #444; border-radius: 8px; margin-top: 10px;} QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        
        form_layout = QFormLayout(group_box)
        form_layout.setSpacing(20)
        
        self.key_inputs = {
            "GroqAPIKey": self.create_key_input(form_layout, "Groq API Key"),
            "CohereAPIKey": self.create_key_input(form_layout, "Cohere API Key"),
            "OPENAI_API_KEY": self.create_key_input(form_layout, "OpenAI API Key"),
            "HuggingFaceAPIKey": self.create_key_input(form_layout, "HuggingFace API Key"),
            "NewsAPIKey": self.create_key_input(form_layout, "NewsAPI Key"),
            "AlphaVantageKey": self.create_key_input(form_layout, "AlphaVantage Key"),
            "OpenWeatherMapAPIKey": self.create_key_input(form_layout, "OpenWeatherMap Key"),
        }
        layout.addWidget(group_box)
        self.add_save_button(layout)
        layout.addStretch()

    def setup_prefs_page(self):
        layout = QVBoxLayout(self.prefs_page)
        layout.setContentsMargins(40, 40, 40, 40)
        group_box = QGroupBox("Personalization")
        group_box.setStyleSheet("QGroupBox { color: #00ffff; font-size: 18px; font-weight: bold; border: 1px solid #444; border-radius: 8px; margin-top: 10px;} QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")

        form_layout = QFormLayout(group_box)
        form_layout.setSpacing(20)

        self.username_input = QLineEdit()
        self.username_input.setToolTip("Enter the name you want Novus to call you.")
        self.username_input.setStyleSheet("color: white; background-color: #2c2c2c; padding: 10px; border-radius: 8px; border: 1px solid #444;")
        form_layout.addRow(QLabel("Your Name:", self), self.username_input)

        self.assistant_name_input = QLineEdit()
        self.assistant_name_input.setToolTip("Set a custom name for your assistant.")
        self.assistant_name_input.setStyleSheet("color: white; background-color: #2c2c2c; padding: 10px; border-radius: 8px; border: 1px solid #444;")
        form_layout.addRow(QLabel("Assistant's Name:", self), self.assistant_name_input)

        self.voice_combo = QComboBox()
        self.voice_combo.setToolTip("Select the voice for the assistant's speech output.")
        self.voice_combo.addItems([
            "en-CA-LiamNeural", "en-US-JennyNeural", "en-GB-SoniaNeural",
            "en-IN-NeerjaNeural", "en-AU-NatashaNeural"
        ])
        self.voice_combo.setStyleSheet("color: white; background-color: #2c2c2c; padding: 10px; border-radius: 8px; border: 1px solid #444;")
        form_layout.addRow(QLabel("Assistant Voice:", self), self.voice_combo)
        
        layout.addWidget(group_box)
        self.add_save_button(layout)
        layout.addStretch()

    def setup_about_page(self):
        layout = QVBoxLayout(self.about_page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        about_text = QLabel("<h2>Novus AI Assistant v1.0</h2>"
                            "<p>Your multi-modal conversational AI assistant.</p>"
                            "<hr style='border: 1px solid #444;'>"
                            "<h3>How to get API Keys:</h3>"
                            "<p>Visit the websites of the respective providers (Groq, Cohere, OpenAI, etc.) to sign up and generate your API keys. Paste them into the 'AI & APIs' tab.</p>"
                            "<br><p><i><b>Note:</b> A restart is required after saving any changes for them to take effect.</i></p>")
        about_text.setWordWrap(True)
        about_text.setTextFormat(Qt.RichText)
        about_text.setStyleSheet("color: #ccc; font-size: 14px;")
        layout.addWidget(about_text)
        layout.addStretch()

    def create_key_input(self, layout, label_text):
        label = QLabel(f"{label_text}:")
        label.setStyleSheet("color: #ccc; font-size: 14px;")

        line_edit = QLineEdit()
        line_edit.setEchoMode(QLineEdit.Password)
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #444; border-radius: 8px; padding: 10px;
                color: white; background-color: #2c2c2c; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #00ffff; }
        """)

        show_hide_btn = QPushButton("Show")
        show_hide_btn.setCheckable(True)
        show_hide_btn.setFixedSize(60, 32)
        show_hide_btn.setToolTip("Show/Hide Key")
        show_hide_btn.setStyleSheet("""
            QPushButton { 
                background-color: #333; 
                color: white;
                border-radius: 16px; 
                border: none;
            }
            QPushButton:checked {
                background-color: #555;
            }
        """)
        show_hide_btn.clicked.connect(lambda checked: self.toggle_password_visibility(line_edit, show_hide_btn, checked))

        container = QHBoxLayout()
        container.addWidget(line_edit)
        container.addWidget(show_hide_btn)

        layout.addRow(label, container)
        return line_edit

    def toggle_password_visibility(self, line_edit, button, checked):
        if checked:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setText("Hide")
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setText("Show")
    
    def add_save_button(self, layout):
        save_button = QPushButton("Save Changes")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d7, stop:1 #00ffff);
                color: white; font-weight: bold;
                border-radius: 15px; padding: 12px 30px; font-size: 16px; margin-top: 20px;
            }
            QPushButton:hover { background-color: #0099ff; }
        """)
        save_button.clicked.connect(self.save_settings)
        
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(save_button)
        hbox.addStretch()
        layout.addLayout(hbox)

    def load_settings(self):
        keys = dotenv_values(self.env_path)
        for key, line_edit in self.key_inputs.items():
            if keys.get(key):
                line_edit.setPlaceholderText("●●●●●●●● (already set)")

        self.username_input.setText(keys.get("Username", ""))
        self.assistant_name_input.setText(keys.get("AssistantName", ""))
        current_voice = keys.get("AssistantVoice", "en-CA-LiamNeural")
        index = self.voice_combo.findText(current_voice)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)

    def save_settings(self):
        try:
            for key, line_edit in self.key_inputs.items():
                value = line_edit.text().strip()
                if value:
                    set_key(self.env_path, key, value)

            set_key(self.env_path, "Username", self.username_input.text().strip())
            set_key(self.env_path, "AssistantName", self.assistant_name_input.text().strip())
            set_key(self.env_path, "AssistantVoice", self.voice_combo.currentText())

            QMessageBox.information(self, "Success", "Settings saved successfully!\nPlease restart Novus for changes to take effect.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")

class CustomTopBar(QWidget):

    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()
        self.draggable = True
        self.offset = None

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)

        home_button = QPushButton()
        home_button.setIcon(QIcon(GraphicsDirectoryPath("Home.png")))
        home_button.setText(" Home")
        home_button.setStyleSheet("height:40px; background-color: white; color: black; border-radius: 8px;")

        message_button = QPushButton()
        message_button.setIcon(QIcon(GraphicsDirectoryPath("Chats.png")))
        message_button.setText("  Chat")
        message_button.setStyleSheet("height:40px; background-color: white; color: black; border-radius: 8px;")

        settings_button = QPushButton()
        settings_button.setIcon(QIcon(GraphicsDirectoryPath("settings.png")))
        settings_button.setText(" Settings")
        settings_button.setStyleSheet("height:40px; background-color: white; color: black; border-radius: 8px;")

        minimize_button = QPushButton()
        minimize_button.setIcon(QIcon(GraphicsDirectoryPath("Minimize2.png")))
        minimize_button.setStyleSheet("background-color: white; border-radius: 8px;")
        minimize_button.clicked.connect(self.minimizeWindow)

        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png'))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white; border-radius: 8px;")
        self.maximize_button.clicked.connect(self.maximizeWindow)

        close_button = QPushButton()
        close_button.setIcon(QIcon(GraphicsDirectoryPath('Close.png')))
        close_button.setStyleSheet("background-color:white; border-radius: 8px;")
        close_button.clicked.connect(self.closeWindow)

        title_label = QLabel(f" {str(AssistantName).capitalize()} AI    ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color:white")

        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addWidget(settings_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        settings_screen = SettingsScreen()

        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        stacked_widget.addWidget(settings_screen)

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    GraphicalUserInterface()

