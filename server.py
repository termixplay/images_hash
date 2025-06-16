import socket
import threading
import json
from datetime import datetime

HOST = '0.0.0.0'
PORT = 12345

server_running = True

active_workers = {}
active_workers_lock = threading.Lock()

scan_history = []
scan_history_lock = threading.Lock()

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_ui_connection(conn, addr):
    try:
        with active_workers_lock:
            status_list = []
            for wid, data in active_workers.items():
                status_list.append({
                    "worker_id": wid,
                    "files_processed": data.get('files_processed', 0),
                    "done": data.get('done', False),
                    "current_file": data.get('current_file', ''),
                    "current_hash": data.get('current_hash', ''),
                    "addr": f"{data['addr'][0]}:{data['addr'][1]}"
                })
        response = json.dumps(status_list).encode()

        conn.sendall(len(response).to_bytes(4, 'big'))
        conn.sendall(response)
    except Exception as e:
        print(f"[!] Ошибка при обработке UI: {e}")
    finally:
        conn.close()

def handle_ui_history_request(conn):
    try:
        with scan_history_lock:
            history_copy = list(scan_history)
        response = json.dumps(history_copy).encode()

        conn.sendall(len(response).to_bytes(4, 'big'))
        conn.sendall(response)
    except Exception as e:
        print(f"[!] Ошибка при отправке истории: {e}")
    finally:
        conn.close()

def handle_worker(conn, addr, worker_id):
    print(f"[+] Подключился воркер {worker_id} с {addr}")
    with active_workers_lock:
        active_workers[worker_id] = {
            'files_processed': 0,
            'done': False,
            'current_file': '',
            'current_hash': '',
            'addr': addr
        }

    try:
        while True:
            raw_len = recv_all(conn, 4)
            if not raw_len:
                break
            msg_len = int.from_bytes(raw_len, 'big')
            msg_bytes = recv_all(conn, msg_len)
            if not msg_bytes:
                break
            filename = msg_bytes.decode()

            if filename == "DONE":
                with active_workers_lock:
                    active_workers[worker_id]['done'] = True
                print(f"[+] Воркер {worker_id} завершил работу")
                break

            raw_len = recv_all(conn, 4)
            if not raw_len:
                break
            hash_len = int.from_bytes(raw_len, 'big')
            hash_bytes = recv_all(conn, hash_len)
            if not hash_bytes:
                break
            filehash = hash_bytes.decode()

            with active_workers_lock:
                active_workers[worker_id]['current_file'] = filename
                active_workers[worker_id]['current_hash'] = filehash
                active_workers[worker_id]['files_processed'] += 1

            with scan_history_lock:
                scan_history.append({
                    "filename": filename,
                    "hash": filehash,
                    "status": "Выполнено",
                    "worker_id": worker_id,
                    "timestamp": datetime.now().isoformat()  # добавим время
                })

            print(f"[Worker {worker_id}] Обработан файл {filename} с хэшем {filehash}")

    except Exception as e:
        print(f"[!] Ошибка с воркером {worker_id}: {e}")
    finally:
        with active_workers_lock:
            if worker_id in active_workers:
                del active_workers[worker_id]
        print(f"[-] Воркер {worker_id} отключился")
        conn.close()

def handle_connection(conn, addr):
    try:
        raw_len = recv_all(conn, 4)
        if not raw_len:
            conn.close()
            return
        msg_len = int.from_bytes(raw_len, 'big')
        msg_bytes = recv_all(conn, msg_len)
        if not msg_bytes:
            conn.close()
            return
        msg = msg_bytes.decode()

        if msg == "GET_STATUS":
            handle_ui_connection(conn, addr)
        elif msg == "GET_HISTORY":
            handle_ui_history_request(conn)
        else:
            handle_worker(conn, addr, msg)
    except Exception as e:
        print(f"[!] Ошибка в handle_connection: {e}")
        conn.close()

def main():
    global server_running
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
        print(f"[+] Сервер запущен на {HOST}:{PORT}")

        try:
            while server_running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print("\n[!] Завершение работы сервера...")
        finally:
            server_running = False

if __name__ == "__main__":
    main()
