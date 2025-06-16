import socket
import threading
import os
import pickle

HOST = '0.0.0.0'
PORT = 12345

# Пути к папкам с изображениями для каждого воркера
worker_folders = [
    "images_worker1",
    "images_worker2",
    "images_worker3",
    "images_worker4"
]

clients = []
results = []
lock = threading.Lock()
connected_workers = 0

def send_task(conn, folder):
    """Отправляем воркеру все изображения из папки."""
    files = os.listdir(folder)
    tasks = []
    for fname in files:
        path = os.path.join(folder, fname)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                data = f.read()
            tasks.append({"name": fname, "data": data})

    # Отправим количество задач
    conn.sendall(len(tasks).to_bytes(4, 'big'))

    # Отправляем по одной задаче (пиклированный объект с длиной)
    for task in tasks:
        data_bytes = pickle.dumps(task)
        conn.sendall(len(data_bytes).to_bytes(4, 'big'))
        conn.sendall(data_bytes)

def receive_results(conn):
    """Получаем от воркера результаты (хэши) и сохраняем их."""
    global results
    while True:
        # Ждём длину результата (4 байта)
        length_bytes = conn.recv(4)
        if not length_bytes:
            break
        length = int.from_bytes(length_bytes, 'big')

        data = b''
        while len(data) < length:
            more = conn.recv(length - len(data))
            if not more:
                break
            data += more
        if not data:
            break

        result = pickle.loads(data)
        with lock:
            results.append(result)
        print(f"[+] Получен результат: {result['name']} -> {result['hash']}")

def handle_worker(conn, addr, folder):
    print(f"[=] Воркер подключился: {addr}, папка: {folder}")
    try:
        send_task(conn, folder)
        receive_results(conn)
    except Exception as e:
        print(f"[!] Ошибка с воркером {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Воркер {addr} отключился")

def main():
    global connected_workers

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[+] Сервер запущен на порту {PORT}. Ожидание 4 воркеров...")

        threads = []

        while connected_workers < 4:
            conn, addr = s.accept()
            folder = worker_folders[connected_workers]
            connected_workers += 1

            t = threading.Thread(target=handle_worker, args=(conn, addr, folder), daemon=True)
            threads.append(t)
            t.start()

        print("[*] Все воркеры подключились. Ждём завершения работы...")

        # Ждём, пока все потоки не закончат работу
        for t in threads:
            t.join()

        print("\n=== Итоговые результаты ===")
        with lock:
            for r in results:
                print(f"{r['name']} -> {r['hash']}")

if __name__ == "__main__":
    main()
