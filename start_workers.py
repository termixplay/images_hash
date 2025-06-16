import multiprocessing
import subprocess
import time
import glob

def run_worker(worker_num, folder):
    print(f"Запуск воркера {worker_num} для папки {folder}")
    subprocess.run(['python', 'worker.py', folder])

if __name__ == '__main__':

    folders = sorted(glob.glob('images_worker*'))

    processes = []
    for i, folder in enumerate(folders, start=1):
        p = multiprocessing.Process(target=run_worker, args=(i, folder))
        p.start()
        processes.append(p)
        time.sleep(0.5)

    for p in processes:
        p.join()

    print("Все воркеры завершили работу.")
