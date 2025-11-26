import hashlib
import math
import pickle
import socket
import threading
import datetime
from Async_cln import username
from  tcp_by_size import send_with_size ,recv_by_size
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
import sys
from AES_e import encrypt_message, decrypt_message, get_aes_key
import sqlite3
import subprocess
import os
from DH import DH_server

#=====================================================
#=====================================================
#===================================================== IMPORTS END



sock_lock = threading.Lock()
accounts = {}
DB_NAME = "youtube/data.db"

with open("youtube/accounts_data.pkl", "rb") as file:
    accounts = pickle.load(file)
# print(accounts)
#=====================================================
#=====================================================
#===================================================== GLOBALS END


def convert_to_webm(input_path, output_path):
    try:
        ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
        command = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", "libvpx",
            "-b:v", "1M",
            "-c:a", "libvorbis",
            output_path
        ]
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print("webm convert error: '", e)
        return False

def datatype_fromDB(title, data_type):
    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()
    cursor.execute(f"""
            SELECT {data_type}
            FROM videos
            WHERE title = ?
        """, (title,))

    data = cursor.fetchone()
    conn.close()

    return data[0]

def update_video_stat(msg, column):
    title, delta = msg.split("~")

    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()

    cursor.execute(f"""
        UPDATE videos
        SET {column} = {column} + ?
        WHERE title = ?
    """, (delta, title))

    conn.commit()
    conn.close()

def send_permaters(sock, key, title):
    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()
    cursor.execute(f"""
                SELECT description, creator, upload_date, views, likes, dislikes
                FROM videos
                WHERE title = ?
            """, (title,))

    data = cursor.fetchone()
    conn.close()
    print(data[0])
    msg = data[1] + "~"+ data[2] + "~" + str(data[3]) + "~" + str(data[4]) + "~" + str(data[5]) + "~" + data[0]
    msg = encrypt_message(key, msg)
    send_with_size(sock, msg)

def add_video(title, description, creator, file_path, hash_val, file_ext):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
                INSERT INTO videos (
                    title, description, creator, upload_date,
                    file_path, hash, file_ext, views, likes, dislikes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            title, description, creator, datetime.datetime.now().isoformat(),
            file_path, hash_val, file_ext, 0, 0, 0
        ))
        conn.commit()

    except Exception as e:
        print("Insert failed:", e)

    conn.close()

def send_all_videos(sock,key, serch):
    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()

    if serch.strip() == "":
        cursor.execute("SELECT title, creator, file_path FROM videos")
    else:
        cursor.execute("SELECT title, creator, file_path FROM videos WHERE title LIKE ?", ('%' + serch + '%',))

    data = cursor.fetchall()
    conn.close()
    count = len(data)


    msg = str(count)
    msg = encrypt_message(key, msg)
    send_with_size(sock, msg)

    for video in data:
        has_thumb = "F"
        if video[2] != "":
            has_thumb = "T"



        msg = video[0] + "~" + video[1] + "~" + has_thumb
        msg = encrypt_message(key, msg)
        send_with_size(sock, msg)

        if has_thumb == "T":
            with open(video[2], "rb") as file:
                data = file.read()
                msg = data
                msg = encrypt_message(key, msg)
                send_with_size(sock, msg)

def dp_helman(sock):
    return DH_server(sock)

def check_login(msg,sock):
    splitted = msg.split('~')
    username = splitted[0]
    password = splitted[1]
    name = splitted[2]

    for v,t in accounts.items():
        if v == username and t[0] == password:
             return name, True
    return "", False

def sign_up(msg, sock):
    splitted = msg.split('~')

    username = splitted[0]
    password = splitted[1]
    age = splitted[2]
    gender = splitted[3]
    name = splitted[4]

    for v,t in accounts.items():
        if v == username:
            print(accounts)
            return "Username Already Taken"

    if int(age) < 18:
        return "You Need To Be At Least 18 /n To Sign Up"

    accounts[username] = [password, name, gender, int(age)]
    with open("youtube/accounts_data.pkl", "wb") as file:
        pickle.dump(accounts,file)

    print(f"{name} signed up")
    return "SGPS"

def send_data(sock, key, username):
    username = hashlib.sha256(username.encode()).hexdigest()
    data = accounts[username]
    msg = data[1] + "~" + data[2] + "~" +str(data[3])
    msg = encrypt_message(key, msg)
    send_with_size(sock, msg)

def recv_file(msg, sock, key, username):
    splitted = msg.split('~')

    count = int(splitted[0])
    title = splitted[1]
    description = splitted[2]
    f_type = splitted[3]
    author = username
    file_hash = ""
    mp4_path = f"youtube/{title}{f_type}"

    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE title = ?", (title,))
    exists = cursor.fetchone()[0]
    conn.close()

    if exists > 0:
        print(f"Duplicate title rejected: {title}")
        return "UPLF"


    try:
        with open(mp4_path, "wb") as file:
            for _ in range(count):
                data = recv_by_size(sock)
                data = decrypt_message(key, data)
                file.write(data)
        print("MP4 upload complete:", title)

        with open(mp4_path, "rb") as f:
            file_data = f.read()
            file_hash = hashlib.sha256(file_data).hexdigest()

        webm_path = f"youtube/{title}.webm"
        if not convert_to_webm(mp4_path, webm_path):
            return "UPLF"


        add_video(title, description, author, "", file_hash, ".webm")
        return "UPLS"

    except Exception as e:
        print("Upload failed:", e)
        return "UPLF"

def update_data(msg, username):
    username = hashlib.sha256(username.encode()).hexdigest()
    name, age, gender = msg.split("~")

    accounts[username][1] = name
    accounts[username][2] = gender
    accounts[username][3] = int(age)

    with open("youtube/accounts_data.pkl", "wb") as file:
        pickle.dump(accounts, file)

    print(f"Updated user {name}: age={age}, gender={gender}")
    return name

def add_thumb(msg, sock, key):

    title = msg
    file_name = f"youtube/{title}_thumb.png"
    with open(file_name, "wb") as file:
        data = recv_by_size(sock)
        data = decrypt_message(key, data)
        file.write(data)

    conn = sqlite3.connect("youtube/data.db")
    cursor = conn.cursor()

    cursor.execute("""
            UPDATE videos
            SET file_path = ?
            WHERE title = ?
        """, (file_name, title))
    conn.commit()
    conn.close()

def handle_request(msg,sock,key, name):
    code = msg[:4]
    print(f"client {name} made a request with code: {code}")
    username = name

    if code == "LOGI":
        name, is_ok = check_login(msg[4:], sock)
        if is_ok:
            msg = "LOGS"
            username = name

        else:
            msg = "LOGF"
        msg = encrypt_message(key,msg)
        send_with_size(sock,msg)
        return username , False


    if code == "SGUP":
        result = sign_up(msg[4:], sock)
        if result == "SGPS":
            msg = "SGPS"
        else:
            msg = "SGPF" + result
        msg = encrypt_message(key, msg)
        send_with_size(sock, msg)
        return username , False


    if code == "UPLD":
        result = recv_file(msg[4:], sock, key, username)
        msg = encrypt_message(key, result)
        send_with_size(sock, msg)

        return username , False

    if code == "THMB":
        add_thumb(msg[4:], sock, key)
        return username, False

    if code == "GETA":
        send_all_videos(sock,key, "")
        return username, False

    if code == "GETS":
        send_all_videos(sock,key,msg[4:])
        return username, False

    if code == "PERM":
        send_permaters(sock,key,msg[4:])
        return username, False

    if code == "UPDV":
        update_video_stat(msg[4:], "views")
        return username, False

    if code == "UPDL":
        update_video_stat(msg[4:], "likes")
        return username, False

    if code == "UPDD":
        update_video_stat(msg[4:], "dislikes")
        return username, False

    if code == "REQD":
        send_data(sock, key, username)
        return username, False

    if code == "UPDI":
        update_data(msg[4:], username)
        return username, False

    if code == "EXIT":
        return username, True


    else:
        print(f"cant find code for {name} request")
    return username, False

def handle_client(sock, addr):
    print("new clinet from addr: ", addr)
    key = dp_helman(sock)
    username = ""
    while True:
        try:
            msg = recv_by_size(sock)
            msg = decrypt_message(key,msg).decode()
            if msg == b'':
                print(f"client {addr} disconnected ")
                return
            username, done = handle_request(msg,sock,key, username)
            if done:
                sock.close()
                print(f"client {addr} disconnected ")
                return
        except Exception as e:
            print(f"client {addr} disconnected ")
            print(f"error was {e}")
            return



def main():

    srv_sock = socket.socket()
    srv_sock.bind(('0.0.0.0', 8002))
    srv_sock.listen(20)
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    while True:
        print('\nMain thread: before accepting ...')
        cli_sock, addr = srv_sock.accept()
        t = threading.Thread(target=handle_client, args=(cli_sock, addr))
        t.start()
    srv_sock.close()

if __name__ == "__main__":
    main()

