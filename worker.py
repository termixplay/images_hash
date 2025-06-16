import socket
import os
import hashlib
import time
import sys

HOST = '127.0.0.1'
PORT = 12345

def get_hash(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()

def send_message(conn, msg: str):
    data = msg.encode()
    conn.send(len(data).to_bytes(4, 'big'))
    conn.send(data)

def main():
    if len(sys.argv) < 2:
        print("Ошибка: не указана папка с изображениями.")
        return

    folder = sys.argv[1]  # папка задаётся при запуске

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                filehash = get_hash(file_path)
                send_message(s, filename)
                send_message(s, filehash)
                time.sleep(0.1)

        send_message(s, "DONE")

if __name__ == "__main__":
    main()
