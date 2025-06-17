from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
import socket
import json


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


class HistoryScreen(MDScreen):

    def fetch_worker_status(self):
        try:
            with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=2) as s:
                msg = "GET_STATUS".encode()
                s.sendall(len(msg).to_bytes(4, 'big'))
                s.sendall(msg)

                raw_len = s.recv(4)
                if not raw_len:
                    return []
                resp_len = int.from_bytes(raw_len, 'big')
                data = b''
                while len(data) < resp_len:
                    packet = s.recv(resp_len - len(data))
                    if not packet:
                        return []
                    data += packet
                return json.loads(data.decode())
        except Exception as e:
            print(f"[UI] Ошибка при получении статуса воркеров: {e}")
            return []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sort_column = "timestamp"
        self.sort_ascending = False

        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)

        # Определяем колонки и заголовки
        self.columns = [
            ("filename", dp(160)),
            ("hash", dp(280)),
            ("status", dp(110)),
            ("timestamp", dp(180)),
        ]

        header_titles = {
            "filename": "Имя файла",
            "hash": "SHA-256 хэш",
            "status": "Статус",
            "timestamp": "Время сканирования",
        }

        # Создаем строку заголовков с кнопками сортировки
        header_layout = BoxLayout(size_hint_y=None, height=50, spacing=1)

        self.arrow_buttons = {}

        for col_key, col_width in self.columns:
            card = MDCard(
                orientation="horizontal",
                size_hint=(None, 1),
                width=col_width,
                padding=(1, 1),
                radius=[12]*4,
                elevation=2,
                style="filled",
                md_bg_color=(0.94, 0.94, 0.94, 1),
            )

            label = MDLabel(
                text=header_titles[col_key],
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(0, 0, 0, 1),
                halign="left",
                size_hint_x=0.8,
                padding=(6, 0),
            )

            btn = MDIconButton(
                icon="arrow-up-drop-circle-outline",
                theme_text_color="Custom",
                text_color=(0, 0, 0, 1),
                size_hint_x=0.2,
            )
            btn.bind(on_release=lambda inst, key=col_key: self.on_arrow_press(key))
            self.arrow_buttons[col_key] = btn

            card.add_widget(label)
            card.add_widget(btn)
            header_layout.add_widget(card)

        layout.add_widget(header_layout)

        # Создаем таблицу без встроенных заголовков
        self.table = MDDataTable(
            background_color_header=(0.88, 0.88, 0.88, 1),
            background_color_cell=(1, 1, 1, 1),
            background_color_selected_cell=(0.9, 0.95, 1, 1),
            size_hint=(0.98, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num=10,
            column_data=[("", col[1]) for col in self.columns],
            row_data=[],
        )

        layout.add_widget(self.table)

        self.add_widget(layout)

        # Запускаем обновление каждые 2 секунды
        Clock.schedule_interval(self.update_history, 2)

        # Начальная отрисовка стрелок
        self.update_arrows()

    def on_arrow_press(self, col_key):
        if self.sort_column == col_key:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = col_key
            self.sort_ascending = True

        self.update_arrows()
        self.update_history(0)

    def update_arrows(self):
        for key, btn in self.arrow_buttons.items():
            if key == self.sort_column:
                btn.icon = 'arrow-up-drop-circle' if self.sort_ascending else 'arrow-down-drop-circle'
                btn.text_color = (0.1, 0.5, 0.8, 1)
            else:
                btn.icon = 'arrow-up-drop-circle-outline'
                btn.text_color = (0.4, 0.4, 0.4, 1)

    def update_history(self, dt):
        try:
            with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=2) as s:
                msg = "GET_HISTORY".encode()
                s.sendall(len(msg).to_bytes(4, 'big'))
                s.sendall(msg)

                raw_len = s.recv(4)
                if not raw_len:
                    return
                resp_len = int.from_bytes(raw_len, 'big')
                data = b''
                while len(data) < resp_len:
                    packet = s.recv(resp_len - len(data))
                    if not packet:
                        return
                    data += packet
                history_list = json.loads(data.decode())

            worker_status = self.fetch_worker_status()

            current_filenames = {entry["filename"] for entry in history_list}
            for worker in worker_status:
                fname = worker.get("current_file", "")
                fhash = worker.get("current_hash", "")
                if fname and fname not in current_filenames:
                    history_list.append({
                        "filename": fname,
                        "hash": fhash,
                        "status": "В процессе",
                        "timestamp": "",
                    })

            # Сортируем по выбранной колонке
            if self.sort_column:
                history_list.sort(
                    key=lambda x: x.get(self.sort_column, ""),
                    reverse=not self.sort_ascending
                )

            # Приоритет "В процессе" — в начале списка
            history_list.sort(key=lambda x: 0 if x.get("status") == "В процессе" else 1)

            self.table.update_row_data(None, [
                (
                    entry.get("filename", ""),
                    entry.get("hash", ""),
                    entry.get("status", ""),
                    entry.get("timestamp", "").replace("T", " ").split(".")[0] if entry.get("timestamp") else ""
                )
                for entry in history_list
            ])

        except Exception as e:
            print(f"[UI] Ошибка при обновлении: {e}")


class ScanHistoryApp(MDApp):
    def build(self):
        self.title = "История сканирования изображений"
        return HistoryScreen()


if __name__ == '__main__':
    ScanHistoryApp().run()
