import socket
import threading
import glob

HOST = '0.0.0.0'
PORT = 12345

EXPECTED_WORKERS = len(glob.glob('images_worker*'))
finished_workers = 0
finished_workers_lock = threading.Lock()

def recv_all(conn, length):
    data = b''
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_worker(conn, addr):
    global finished_workers
    print(f"[=] Воркер подключился: {addr}")
    try:
        while True:
            raw_len = recv_all(conn, 4)
            if not raw_len:
                break
            msg_len = int.from_bytes(raw_len, 'big')

            msg_bytes = recv_all(conn, msg_len)
            if not msg_bytes:
                break
            msg = msg_bytes.decode()

            if msg == "DONE":
                print(f"[=] Воркер {addr} закончил работу")
                break

            # Ожидаем дальше хэш (следующее сообщение)
            raw_hash_len = recv_all(conn, 4)
            if not raw_hash_len:
                break
            hash_len = int.from_bytes(raw_hash_len, 'big')

            hash_bytes = recv_all(conn, hash_len)
            if not hash_bytes:
                break
            filehash = hash_bytes.decode()

            print(f"[+] Получен результат: {msg} -> {filehash}")

    except Exception as e:
        print(f"[!] Ошибка с воркером {addr}: {e}")
    finally:
        conn.close()
        with finished_workers_lock:
            finished_workers += 1

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[+] Сервер запущен на порту {PORT}. Ожидание {EXPECTED_WORKERS} воркеров...")

        while True:
            if finished_workers >= EXPECTED_WORKERS:
                print("[*] Все воркеры отработали. Завершаем работу сервера.")
                break

            s.settimeout(1.0)  # таймаут для проверки условия выхода
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle_worker, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue

if __name__ == "__main__":
    main()
