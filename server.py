import socket
import threading
import uuid

HOST = '0.0.0.0'
PORT = 12345

active_workers = {}
active_workers_lock = threading.Lock()

server_running = True

def recv_all(conn, length):
    data = b''
    while len(data) < length:
        try:
            packet = conn.recv(length - len(data))
        except ConnectionResetError:
            print("[!] Соединение сброшено клиентом")
            return None
        except Exception as e:
            print(f"[!] Ошибка при получении данных: {e}")
            return None
        if not packet:
            return None
        data += packet
    return data

def handle_worker(conn, addr):
    worker_id = str(uuid.uuid4())
    print(f"[=] Воркер {worker_id} подключился: {addr}")

    with active_workers_lock:
        active_workers[worker_id] = {'addr': addr, 'files_processed': 0, 'done': False}

    try:
        while True:
            raw_len = recv_all(conn, 4)
            if not raw_len:
                print(f"[!] Воркер {worker_id} отключился внезапно")
                break
            msg_len = int.from_bytes(raw_len, 'big')

            msg_bytes = recv_all(conn, msg_len)
            if not msg_bytes:
                print(f"[!] Воркер {worker_id} отключился во время чтения сообщения")
                break
            msg = msg_bytes.decode()

            if msg == "DONE":
                print(f"[=] Воркер {worker_id} закончил работу")
                with active_workers_lock:
                    active_workers[worker_id]['done'] = True
                break

            raw_hash_len = recv_all(conn, 4)
            if not raw_hash_len:
                print(f"[!] Воркер {worker_id} отключился во время чтения хэша")
                break
            hash_len = int.from_bytes(raw_hash_len, 'big')

            hash_bytes = recv_all(conn, hash_len)
            if not hash_bytes:
                print(f"[!] Воркер {worker_id} отключился во время чтения хэша")
                break
            filehash = hash_bytes.decode()

            with active_workers_lock:
                active_workers[worker_id]['files_processed'] += 1

            print(f"[+] Воркер {worker_id}: {msg} -> {filehash}")

    except Exception as e:
        print(f"[!] Ошибка с воркером {worker_id}: {e}")
    finally:
        conn.close()
        with active_workers_lock:
            if worker_id in active_workers:
                active_workers[worker_id]['done'] = True
        print(f"[=] Воркер {worker_id} отключился")

def main():
    global server_running

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
        print(f"[+] Сервер запущен на порту {PORT}. Ожидание воркеров...")

        try:
            while server_running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=handle_worker, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    pass

                # Проверяем, все ли воркеры завершились
                with active_workers_lock:
                    if active_workers and all(w['done'] for w in active_workers.values()):
                        print("[*] Все воркеры завершили работу. Завершаем сервер.")
                        break

        except KeyboardInterrupt:
            print("\n[!] Получен сигнал прерывания. Завершаем работу сервера...")

        finally:
            server_running = False

if __name__ == "__main__":
    main()
