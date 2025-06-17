from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivy.uix.boxlayout import BoxLayout
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

        layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        # Заголовки + стрелки
        self.columns = [
            ("filename", dp(130)),
            ("hash", dp(230)),
            ("status", dp(90)),
            ("timestamp", dp(180)),  # Новый столбец времени
        ]

        header_titles = {
            "filename": "Имя файла",
            "hash": "SHA-256 хэш",
            "status": "Статус",
            "timestamp": "Время сканирования",
        }

        header_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
        self.arrow_buttons = {}

        for col_key, col_width in self.columns:
            col_box = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=col_width, spacing=5)

            label = MDRaisedButton(
                text=header_titles[col_key],
                md_bg_color=(0.93, 0.93, 0.93, 1),
                text_color=(0, 0, 0, 1),
                elevation=0,
                size_hint=(None, None),
                height=32,
                width=col_width - 35,
                disabled=True
            )

            btn = MDIconButton(
                icon='arrow-up-drop-circle-outline',
                font_size='18sp',
                size_hint=(None, None),
                size=(32, 32),
            )
            btn.bind(on_release=lambda inst, key=col_key: self.on_arrow_press(key))
            self.arrow_buttons[col_key] = btn

            col_box.add_widget(label)
            col_box.add_widget(btn)
            header_layout.add_widget(col_box)

        layout.add_widget(header_layout)

        # Таблица без встроенных заголовков
        self.table = MDDataTable(
            size_hint=(0.95, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num=10,
            column_data=[
                ("", dp(130)),
                ("", dp(230)),
                ("", dp(90)),
                ("", dp(180)),
            ],
            row_data=[],
        )
        layout.add_widget(self.table)

        self.add_widget(layout)

        Clock.schedule_interval(self.update_history, 2)

    def on_arrow_press(self, col_key):
        if self.sort_column == col_key:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = col_key
            self.sort_ascending = True

        for key, btn in self.arrow_buttons.items():
            if key == self.sort_column:
                btn.icon = 'arrow-up-drop-circle' if self.sort_ascending else 'arrow-down-drop-circle'
            else:
                btn.icon = 'arrow-up-drop-circle-outline'

        self.update_history(0)

    def update_history(self, dt):
        try:
            # Получаем историю
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

            # Получаем список активных воркеров
            worker_status = self.fetch_worker_status()

            # Добавим записи "в процессе", если их ещё нет в истории
            current_filenames = {entry["filename"] for entry in history_list}
            for worker in worker_status:
                fname = worker.get("current_file", "")
                fhash = worker.get("current_hash", "")
                if fname and fname not in current_filenames:
                    history_list.append({
                        "filename": fname,
                        "hash": fhash,
                        "status": "В процессе",
                        "timestamp": "",  # Можно не указывать
                    })

            # Сортировка, если включена
            if self.sort_column:
                history_list.sort(
                    key=lambda x: x.get(self.sort_column, ""),
                    reverse=not self.sort_ascending
                )

            # Всегда показывать "В процессе" вверху независимо от сортировки
            history_list.sort(key=lambda x: 0 if x.get("status") == "В процессе" else 1)

            # Обновим таблицу
            self.table.update_row_data(None, [
                (
                    file.get("filename", ""),
                    file.get("hash", ""),
                    file.get("status", ""),
                    file.get("timestamp", "").replace("T", " ").split(".")[0] if file.get("timestamp") else ""
                )
                for file in history_list
            ])

        except Exception as e:
            print(f"[UI] Ошибка при обновлении: {e}")


class ScanHistoryApp(MDApp):
    def build(self):
        self.title = "История сканирования изображений"
        return HistoryScreen()


if __name__ == '__main__':
    ScanHistoryApp().run()
