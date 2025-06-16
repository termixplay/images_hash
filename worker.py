import socket
import pickle
import hashlib

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

def compute_hash(data):
    return hashlib.sha256(data).hexdigest()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER_HOST, SERVER_PORT))
        print("[*] Подключено к серверу")

        # Получаем количество задач (4 байта)
        length_bytes = sock.recv(4)
        if not length_bytes:
            print("[!] Нет задач")
            return
        task_count = int.from_bytes(length_bytes, 'big')
        print(f"[*] Получено {task_count} задач")

        for _ in range(task_count):
            # Получаем длину задачи (4 байта)
            length_bytes = sock.recv(4)
            if not length_bytes:
                print("[!] Преждевременное завершение")
                return
            task_len = int.from_bytes(length_bytes, 'big')

            # Получаем задачу
            data = b''
            while len(data) < task_len:
                part = sock.recv(task_len - len(data))
                if not part:
                    print("[!] Потеря данных")
                    return
                data += part

            task = pickle.loads(data)
            fname = task["name"]
            fdata = task["data"]

            print(f"[*] Обрабатываю {fname}")

            h = compute_hash(fdata)
            result = pickle.dumps({"name": fname, "hash": h})

            # Отправляем длину результата + данные
            sock.sendall(len(result).to_bytes(4, 'big'))
            sock.sendall(result)

            print(f"[✓] Отправлен хэш: {h}")

        print("[*] Все задачи выполнены, воркер завершает работу")

if __name__ == "__main__":
    main()
