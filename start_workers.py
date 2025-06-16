import multiprocessing
import subprocess
import time

def run_worker(worker_num, folder):
    print(f"Запуск воркера {worker_num} для папки {folder}")
    # Запускаем отдельный скрипт воркера через subprocess (предполагается, что он в файле worker.py)
    # Можно передавать имя папки через аргумент командной строки
    subprocess.run(['python', 'worker.py', folder])

if __name__ == '__main__':
    folders = ['images1', 'images2', 'images3', 'images4']  # Папки с изображениями для воркеров

    processes = []
    for i, folder in enumerate(folders, start=1):
        p = multiprocessing.Process(target=run_worker, args=(i, folder))
        p.start()
        processes.append(p)
        time.sleep(0.5)  # небольшой промежуток для старта

    # Ждём завершения всех воркеров
    for p in processes:
        p.join()

    print("Все воркеры завершили работу.")
