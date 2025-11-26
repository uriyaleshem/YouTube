import math
import socket
import os
import threading
import datetime
from socket import errorTab
import hashlib
from YouTube_server import dp_helman
from  tcp_by_size import send_with_size ,recv_by_size
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt5 import QtWidgets, uic
import sys
from AES_e import encrypt_message, decrypt_message, get_aes_key
import time
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
import os
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QBuffer, QByteArray, QIODevice
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtGui import QIcon
from datetime import datetime
from DH import DH_client
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QRect


from PyQt5.QtWebEngineWidgets import QWebEngineSettings

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QUrl
import sys
#==========================================================================
#========================================================================== imports end
#==========================================================================

manager = None



#========================================================================== class DragDropLabel
#========================================================================== handles the drop area in the upload screen
#========================================================================== START
class DragDropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("Drag Your File Here")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px dashed gray;")
        self.file_path = ""


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.setText(f"Selected: {file_path}")
            self.file_path = file_path

    def get_path(self):
        return self.file_path
#========================================================================== class DragDropLabel
#========================================================================== handles the drop area in the upload screen
#========================================================================== END





#========================================================================== class AppManager
#========================================================================== handles the jump between screens. only at the home page! not login/sign up
#========================================================================== START
class AppManager(QtWidgets.QMainWindow):
    def __init__(self, key, sock):
        super().__init__()
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomeWindow(key, sock)
        self.upload = UploadWindow(key, sock)
        self.watch = WatchWindow(key, sock)
        self.settings = SettingsWindow(key, sock)


        self.stack.addWidget(self.home)
        self.stack.addWidget(self.upload)
        self.stack.addWidget(self.watch)
        self.stack.addWidget(self.settings)

        self.resize(1500, 850)

        self.stack.setCurrentWidget(self.home)
        self.show()

    def show_home(self):
        self.stack.setCurrentWidget(self.home)
        self.home.load_videos_noserch()

    def show_upload(self):
        self.stack.setCurrentWidget(self.upload)
        self.upload.uploadProgressBar.setValue(0)

    def show_watch(self):
        self.stack.setCurrentWidget(self.watch)
        self.watch.get_paremters()

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings)
        self.settings.request_data()

#========================================================================== class AppManager
#========================================================================== handles the jump between screens. only at the home page! not login/sign up
#========================================================================== END




#========================================================================== class UploadThread
#========================================================================== handles the upload process
#========================================================================== START
class UploadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, path, sock, key):
        super().__init__()
        self.path = path
        self.sock = sock
        self.key = key

    def run(self):
        try:
            size = os.path.getsize(self.path)
            chunk_size = 1048576
            sent = 0

            with open(self.path, "rb") as f:
                while chunk := f.read(chunk_size):
                    sent += len(chunk)
                    percent = int((sent / size) * 100)
                    chunk = encrypt_message(self.key, chunk)
                    send_with_size(self.sock, chunk)
                    self.progress.emit(percent)

            msg = recv_by_size(self.sock)
            msg = decrypt_message(self.key, msg).decode()
            if msg != "UPLS":
                self.error.emit("couldn't upload")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
# ========================================================================== class UploadThread
# ========================================================================== handles the upload process
# ========================================================================== END


# ========================================================================== class WatchWindow
# ========================================================================== handles the watch video screen
# ========================================================================== START
class WatchWindow(QtWidgets.QMainWindow):
    def __init__(self,key,sock):
        super().__init__()
        uic.loadUi("youtube_c/watch.ui", self)
        self.key = key
        self.sock = sock
        self.title = ""
        self.home_button.clicked.connect(self.send_to_home)
        self.like_button.clicked.connect(self.like_pressed)
        self.dislike_button.clicked.connect(self.dislike_pressed)
        self.resume_button.clicked.connect(self.resume_vid)
        self.pause_button.clicked.connect(self.pause_vid)
        self.Logout_button.clicked.connect(self.log_out)



        self.upload_button.clicked.connect(self.send_to_upload)
        self.volume_slider = self.findChild(QtWidgets.QSlider, "volume_slider")
        self.volume_percentage = self.findChild(QtWidgets.QLabel, "volume_percentage")
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        self.volume_percentage.setText(f"1%")

        self.liked = False
        self.disliked = False
        geom = self.videowidget.geometry()

        self.video_browser = QWebEngineView(self)
        self.video_browser.setGeometry(QRect(geom.x(), geom.y(), geom.width(), geom.height()))
        self.video_browser.show()

        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        global manager

    def play_video(self, title):
        video_url = f"http://10.68.121.85:5000/video/{title}.webm"
        html_path = os.path.abspath("youtube_c/video_player.html")
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read().replace("{VIDEO_URL}", video_url)
            self.video_browser.setHtml(html)
            print(f"Loaded player for: {video_url}")
            self.video_browser.page().runJavaScript("document.getElementById('player').muted = false;")
            self.video_browser.page().runJavaScript(f"document.getElementById('player').volume = {self.volume_slider.value() / 100.0};")

        except Exception as e:
            print(f"Failed to load HTML video player: {e}")


    def send_perm_update(self,code, delta):
        msg = code + self.title + "~" + str(delta)
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)

    def get_paremters(self):

        msg = "PERM" + self.title
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)

        msg = recv_by_size(self.sock)
        msg = decrypt_message(self.key, msg).decode()
        print(msg)

        splitted = msg.split("~")
        creator = splitted[0]
        date = splitted[1]
        views = splitted[2]
        likes = splitted[3]
        dislikes = splitted[4]
        description = splitted[5]

        date = datetime.fromisoformat(date)
        date =  date.strftime("%d/%m/%Y %H:%M")

        self.title_label.setText(self.title)
        self.creator_label.setText(creator)
        self.date_label.setText(date)
        self.views_label.setText(views)
        self.like_label.setText(likes)
        self.dislike_label.setText(dislikes)

        self.description_label.setText(description)


        self.send_perm_update("UPDV" , 1)

        self.play_video(self.title)



        icon = QIcon("youtube_c/empty_like.png")
        self.liked = False
        self.like_button.setIcon(icon)
        icon = QIcon("youtube_c/empty_dislike.png")
        self.disliked = False
        self.dislike_button.setIcon(icon)

    def log_out(self):
        msg = "EXIT"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.sock.close()
        exit()

    def like_pressed(self):
        if self.liked:
            icon = QIcon("youtube_c/empty_like.png")
            self.liked = False

            current = int(self.like_label.text())
            current -= 1
            self.like_label.setText(str(current))
            self.send_perm_update("UPDL", -1)


        else:
            self.send_perm_update("UPDL", 1)
            icon = QIcon("youtube_c/full_like.png")
            self.liked = True
            current = int(self.like_label.text())
            current += 1
            self.like_label.setText(str(current))
            if self.disliked:
                self.dislike_pressed()

        self.like_button.setIcon(icon)

    def dislike_pressed(self):
        if self.disliked:
            self.send_perm_update("UPDD", -1)
            icon = QIcon("youtube_c/empty_dislike.png")
            self.disliked = False

            current = int(self.dislike_label.text())
            current -= 1
            self.dislike_label.setText(str(current))

        else:
            self.send_perm_update("UPDD", 1)
            icon = QIcon("youtube_c/full_dislike.png")
            self.disliked = True
            current = int(self.dislike_label.text())
            current += 1
            self.dislike_label.setText(str(current))
            if self.liked:
                self.like_pressed()

        self.dislike_button.setIcon(icon)


    def update_volume_label(self, value):
        self.volume_percentage.setText(f"{value}%")
        js_code = f"document.getElementById('player').volume = {value / 100.0};"
        self.video_browser.page().runJavaScript(js_code)
        if value == 0:
            pixmap = QPixmap("youtube_c/mute.png")
            self.video_browser.page().runJavaScript("document.getElementById('player').muted = true;")
        else:
            pixmap = QPixmap("youtube_c/volume.png")
            self.video_browser.page().runJavaScript("document.getElementById('player').muted = false;")
        self.volume_icon.setPixmap(pixmap)

    def pause_vid(self):
        self.video_browser.page().runJavaScript("pauseVideo();")

    def resume_vid(self):
        self.video_browser.page().runJavaScript("playVideo();")


    def send_to_home(self):
        manager.show_home()
        self.pause_vid()

    def send_to_upload(self):
        manager.show_upload()
        self.pause_vid()


    def update_title(self, new_title):
        self.title = new_title
        print(self.title + " watching")
# ========================================================================== class WatchWindow
# ========================================================================== handles the watch video screen
# ========================================================================== END



#========================================================================== class UploadWindow
#========================================================================== The screen that you upload videos through
#========================================================================== START
class UploadWindow(QtWidgets.QMainWindow):
    def __init__(self,key,sock):
        super().__init__()
        uic.loadUi("youtube_c/Upload.ui", self)
        self.key = key
        self.sock = sock
        self.home_button.clicked.connect(self.send_to_home)
        self.uploadButton.clicked.connect(self.try_upload)
        self.Logout_button.clicked.connect(self.log_out)
        self.settings_button.clicked.connect(self.send_to_settings)

        self.chooseFileButton.clicked.connect(self.open_file_dialog)
        self.change_thumbnail.clicked.connect(self.change_thumb)

        self.thumb = ""

        self.drop_label.hide()
        self.drag_label = DragDropLabel(self)
        self.drag_label.setGeometry(self.drop_label.geometry())
        self.drag_label.setStyleSheet(self.drop_label.styleSheet())

        global manager

    def log_out(self):
        msg = "EXIT"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.sock.close()
        exit()
    def send_to_settings(self):
        manager.show_settings()

    def show_error(self, message, duration=3000):
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: red; font: 20px;")
        QTimer.singleShot(duration, lambda: self.error_label.setText(""))

    def change_thumb(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".png":
                self.thumb = file_path
                print(ext)
                pixmap = QPixmap(file_path)
                self.thumb_label.setPixmap(pixmap)
            else:
                self.show_error("Thumbnail Must \nBe PNG File")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.drag_label.setText(f"Selected: {file_path.split('/')[-1]}")
            self.drag_label.file_path = file_path

    def upload_done(self):
        print("done")
        if self.thumb != "":
            title = self.title_text.text()
            msg = "THMB" + title
            msg = encrypt_message(self.key, msg)
            send_with_size(self.sock, msg)

            with open(self.thumb, "rb") as file:
                data = file.read()
                data = encrypt_message(self.key, data)
                send_with_size(self.sock, data)
        print(" Upload complete (including thumbnail)")

    def try_upload(self):
        path = self.drag_label.get_path()
        title = self.title_text.text()
        description = self.description_text.toPlainText()
        print(path)
        print(title)
        if path == "":
            self.show_error("Choose File")
            return
        if title == "":
            self.show_error("Enter Title")
            return
        valid_extensions = [".mp4", ".webm"]
        ext = os.path.splitext(path)[1].lower()

        if ext not in valid_extensions:
            self.show_error(f"Invalid file type.\n Please select a different file.")
            return

        size = os.path.getsize(path)
        chunk_size = 1048576
        chunk_count = math.ceil(size / chunk_size)

        msg = "UPLD" + str(chunk_count) + "~" + title + "~" + description + "~" + ext
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)



        self.uploadProgressBar.setValue(0)
        self.thread = UploadThread(path, self.sock, self.key)
        self.thread.progress.connect(self.uploadProgressBar.setValue)
        self.thread.finished.connect(self.upload_done)
        self.thread.error.connect(self.show_error)
        self.thread.start()



    def send_to_home(self):
        manager.show_home()
#========================================================================== class UploadWindow
#========================================================================== The screen that you upload videos through
#========================================================================== END


class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self,key,sock):
        super().__init__()
        uic.loadUi("youtube_c/settings.ui", self)
        self.key = key
        self.sock = sock
        self.home_button.clicked.connect(self.send_to_home)
        self.Logout_button.clicked.connect(self.log_out)
        self.upload_button.clicked.connect(self.send_to_upload)
        self.change_button.clicked.connect(self.update_data)


        global manager

    def send_to_upload(self):
        manager.show_upload()

    def update_data(self):
        name = self.username_edit.text()
        age = self.age_box.value()
        if self.male_radio.isChecked():
            gender = "Male"
        elif self.female_radio.isChecked():
            gender = "Female"
        else:
            self.error_label.setText("please check male or female")
            return

        msg = "UPDI" + name + "~" + str(age) + "~" + gender
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)


    def log_out(self):
        msg = "EXIT"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.sock.close()
        exit()

    def send_to_home(self):
        manager.show_home()

    def request_data(self):
        msg = "REQD"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)

        msg = recv_by_size(self.sock)
        data = decrypt_message(self.key, msg).decode()

        name, gender, age = data.split("~")

        self.username_edit.setText(name)
        self.age_box.setValue(int(age))
        if gender == "Male":
            self.male_radio.setChecked(True)
        elif gender == "Female":
            self.female_radio.setChecked(True)

        self.error_label.setText("")


#========================================================================== class HomeWindow
#========================================================================== The screen that you can see all videos through
#========================================================================== START
class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self,key,sock):

        super().__init__()
        uic.loadUi("youtube_c/home.ui", self)
        self.key = key
        self.sock = sock
        self.settings_button.clicked.connect(self.send_to_settings)

        self.upload_button.clicked.connect(self.send_to_upload)
        self.refresh_button.clicked.connect(self.load_videos_noserch)
        self.serch_button.clicked.connect(self.load_videos_serch)
        self.Logout_button.clicked.connect(self.log_out)
        self.gridLayout = self.scrollArea.widget().layout()

        self.upload_window = UploadWindow(self.key, self.sock)
        global manager

    def log_out(self):
        msg = "EXIT"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.sock.close()
        exit()

    def send_to_settings(self):
        manager.show_settings()


    def send_to_upload(self):
        manager.show_upload()

    def handle_card_click(self, t):
        manager.watch.update_title(t)
        manager.show_watch()

    def load_videos_serch(self):
        print("loading")
        to_serch = self.serch_bar.text()
        msg = "GETS" + to_serch
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.load_videos()

    def load_videos_noserch(self):
        print("loading")

        msg = "GETA"
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock, msg)
        self.load_videos()

    def load_videos(self):

        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        msg = recv_by_size(self.sock)
        msg = decrypt_message(self.key, msg).decode()
        count = int(msg)
        row, col = 0, 0

        for i in range(count):
            card = QWidget()
            loadUi("youtube_c/video.ui", card)
            card.setFixedSize(320, 250)

            msg = recv_by_size(self.sock)
            msg = decrypt_message(self.key, msg).decode()
            splitted = msg.split('~')

            title = splitted[0]
            creator = splitted[1]

            if splitted[2] == "T":

                pic = recv_by_size(self.sock)
                pic = decrypt_message(self.key, pic)

                byte_array = QByteArray(pic)
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.ReadOnly)
                image = QImage()
                image.loadFromData(buffer.data())
                pixmap = QPixmap.fromImage(image)
                thumbnail_label = title_label = card.findChild(QLabel, "thumbnail_label")
                thumbnail_label.setPixmap(pixmap)




            click_button = QPushButton(card)
            click_button.setGeometry(0, 0, card.width(), card.height())
            click_button.setStyleSheet("background-color: rgba(0, 0, 0, 0); border: none;")
            click_button.clicked.connect(lambda checked, t=title: self.handle_card_click(t))
            click_button.raise_()

            title_label = card.findChild(QLabel, "title")
            if title_label:
                title_label.setText(title)

            creator_label = card.findChild(QLabel, "creator")
            if creator_label:
                creator_label.setText(creator)

            self.gridLayout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

#========================================================================== class HomeWindow
#========================================================================== The screen that you can see all videos through
#========================================================================== END



#========================================================================== class LoginWindow
#========================================================================== The screen that you can log in through.    also handles connection and DP helman
#========================================================================== START
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self, ip):
        super().__init__()
        uic.loadUi("youtube_c/login.ui", self)
        self.connected = False
        self.ip = ip
        self.login_button.clicked.connect(self.try_login)
        self.sign_up_button.clicked.connect(self.call_signup)
        if not self.connected:
            self.try_connect()

        self.signup_window = signupWindow(self, self.key, self.sock)
        self.signup_window.show()
        self.signup_window.hide()

        self.home_window = HomeWindow(self.key, self.sock)


    #dp helman procedure
    def dp_helman(self):
        self.key = DH_client(self.sock)

    #tries to connect
    def try_connect(self):
        try:
            serv_ip = self.ip
            port = 8002
            self.sock = socket.socket()
            self.sock.connect((serv_ip, port))
            self.error_label.setText(f"connected")
            self.connected = True

        except Exception as e:
            self.error_label.setStyleSheet("color: red; font: 24px;")
            self.error_label.setText(f"Cant Connect Because Of Server \n Issues, Try Again Later ")
            return
        self.dp_helman()

    #tries to login. sends info to server
    #gets from server - LOGS: success - LOGF: fail
    def try_login(self):
        if not self.connected:
            self.try_connect()
        global manager
        # self.username_edit.setText("uriya2")
        # self.password_edit.setText("1234")

        name = self.username_edit.text()
        password = self.password_edit.text()

        username = hashlib.sha256(name.encode()).hexdigest()
        password = hashlib.sha256(password.encode()).hexdigest()

        msg = ("LOGI" + username +'~'+ password + '~' + name)
        msg = encrypt_message(self.key, msg)
        send_with_size(self.sock,msg )

        is_logged = recv_by_size(self.sock)
        is_logged = decrypt_message(self.key,is_logged)

        if is_logged == "LOGF":
            self.error_label.setStyleSheet("color: red; font: 24px;")
            self.error_label.setText(f"Username Or Password Is Incorrect ")
            return

        manager = AppManager(self.key, self.sock)
        manager.show_home()

        self.hide()

    # sends to the sign up screen
    def call_signup(self):
        if not self.connected:
            self.try_connect()
        self.signup_window.show()
        time.sleep(0.001)
        self.hide()
# ========================================================================== class LoginWindow
# ========================================================================== The screen that you can log in through
# ========================================================================== END







#========================================================================== class signupWindow
#========================================================================== The screen that you can use to sign up
#========================================================================== START
class signupWindow(QtWidgets.QMainWindow):
    def __init__(self,parent_window,key,sock):
        super().__init__()
        uic.loadUi("youtube_c/signup.ui", self)
        self.backtologin_button.clicked.connect(self.back_login)
        self.parent_window = parent_window
        self.sign_up_button.clicked.connect(self.try_signup)
        self.key = key
        self.sock = sock


    # sends back to the login screen
    def back_login(self):
        self.parent_window.show()
        self.hide()

    #tries to sign up. sends info for server
    # return - SGPS: success SGPF - fail

    def try_signup(self):
        name = self.username_edit.text()
        password = self.password_edit.text()
        age = self.age_box.value()
        if self.male_radio.isChecked():
            gender = "Male"
        elif self.female_radio.isChecked():
            gender = "Female"
        else:
            self.error_label.setText("please check male or female")
            return

        username = hashlib.sha256(name.encode()).hexdigest()
        password = hashlib.sha256(password.encode()).hexdigest()

        msg = "SGUP" + username+'~' + password+'~' + str(age)+'~' + gender + '~' + name
        msg = encrypt_message(self.key, msg)

        send_with_size(self.sock, msg)
        data = recv_by_size(self.sock)
        data = decrypt_message(self.key, data)


        if data[:4] == "LOGF":
            self.error_label.setStyleSheet("color: red; font: 24px;")
            self.error_label.setText(f"{data[4:]}")
        else:
            print(data)
#========================================================================== class signupWindow
#========================================================================== The screen that you can use to sign up
#========================================================================== END





def main():
     ip = "10.68.121.85"
     #ip = input("enter ip: ")
     app = QApplication(sys.argv)
     login_window = LoginWindow(ip)
     login_window.show()
     sys.exit(app.exec_())






if __name__ == "__main__":
    main()