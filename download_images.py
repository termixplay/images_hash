import os
import requests
from PIL import Image
from io import BytesIO

# Настройки
API_KEY = "50892834-0d9273f841c1b13bbe865782b"  # ключ API
query = "nature"
save_folder = "images_worker1"
total_images = 100  # Сколько всего нужно скачать

# Создание папки, если её нет
os.makedirs(save_folder, exist_ok=True)

downloaded = 0
page = 1

while downloaded < total_images:
    url = f"https://pixabay.com/api/?key={API_KEY}&q={query}&image_type=photo&per_page=100&page={page}"
    print(f"[=] Запрос к {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print("[-] Ошибка при запросе: статус", response.status_code)
        break

    data = response.json()
    hits = data.get("hits", [])

    print(f"[=] Найдено изображений на странице: {len(hits)}")

    if not hits:
        print("[-] Больше изображений не найдено.")
        break

    for hit in hits:
        image_url = hit["largeImageURL"]
        try:
            image_response = requests.get(image_url)
            img = Image.open(BytesIO(image_response.content))
            filename = os.path.join(save_folder, f"img_{downloaded}.jpg")
            img.save(filename)
            downloaded += 1
            print(f"[+] Скачано: {filename}")
            if downloaded >= total_images:
                break
        except Exception as e:
            print(f"[-] Ошибка при загрузке {image_url}: {e}")
            continue
    page += 1

print(f"[✓] Всего скачано изображений: {downloaded}")
