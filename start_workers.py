import os
import math
import shutil
import multiprocessing
import subprocess

SRC_FOLDER = r"C:\Users\termi\Desktop\project python\images"
DST_BASE_FOLDER = r"C:\Users\termi\Desktop\client"
FILES_PER_WORKER = 200

def prepare_folders_and_files():
    all_files = [f for f in os.listdir(SRC_FOLDER) if os.path.isfile(os.path.join(SRC_FOLDER, f))]
    total_files = len(all_files)
    num_workers = math.ceil(total_files / FILES_PER_WORKER)

    print(f"Всего файлов: {total_files}, требуется воркеров: {num_workers}")

    folders = []
    for i in range(num_workers):
        folder_name = os.path.join(DST_BASE_FOLDER, f"worker_{i+1}")
        os.makedirs(folder_name, exist_ok=True)
        folders.append(folder_name)

        start_idx = i * FILES_PER_WORKER
        end_idx = min(start_idx + FILES_PER_WORKER, total_files)
        files_chunk = all_files[start_idx:end_idx]

        # Копируем файлы
        for filename in files_chunk:
            src_path = os.path.join(SRC_FOLDER, filename)
            dst_path = os.path.join(folder_name, filename)
            shutil.copy2(src_path, dst_path)

    return folders

def run_worker(worker_num, folder):
    print(f"Запуск воркера {worker_num} для папки {folder}")
    subprocess.run(['python', 'worker.py', str(worker_num), folder])

if __name__ == '__main__':
    folders = prepare_folders_and_files()

    processes = []
    for i, folder in enumerate(folders, start=1):
        p = multiprocessing.Process(target=run_worker, args=(i, folder))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("Все воркеры завершили работу.")
