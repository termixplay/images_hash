import socket
import os
import hashlib
import time
import sys

HOST = '127.0.0.1'
PORT = 12345
MAX_RETRIES = 5
RETRY_DELAY = 2  # секунды

def get_hash(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()

def send_message(conn, msg: str):
    data = msg.encode()
    conn.send(len(data).to_bytes(4, 'big'))
    conn.send(data)

def connect_with_retries():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print(f"[+] Подключение к серверу установлено.")
            return s
        except Exception as e:
            print(f"[!] Не удалось подключиться к серверу (попытка {retries+1}/{MAX_RETRIES}): {e}")
            retries += 1
            time.sleep(RETRY_DELAY)
    return None

def main():
    if len(sys.argv) < 2:
        print("Ошибка: не указана папка с изображениями.")
        return

    folder = sys.argv[1]

    s = connect_with_retries()
    if not s:
        print("[!] Не удалось установить соединение с сервером. Завершаем работу воркера.")
        return

    with s:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                try:
                    filehash = get_hash(file_path)
                    send_message(s, filename)
                    send_message(s, filehash)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"[!] Ошибка при обработке файла {filename}: {e}")
        try:
            send_message(s, "DONE")
        except Exception as e:
            print(f"[!] Ошибка при отправке сообщения DONE: {e}")

if __name__ == "__main__":
    main()
