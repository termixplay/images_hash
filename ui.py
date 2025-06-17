# Новый ui.py с двумя экранами: "История" и "Воркеры онлайн"
from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
import socket
import json

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


def fetch_data(msg_type):
    try:
        with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=2) as s:
            msg = msg_type.encode()
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
        print(f"[UI] Ошибка при получении {msg_type}: {e}")
        return []


class WorkerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        self.table = MDDataTable(
            background_color_cell=(1, 1, 1, 1),  # ← ДОБАВЛЕНО
            column_data=[
                ("Worker ID", dp(40)),
                ("Обработано файлов", dp(60)),
                ("Файл", dp(160)),
                ("Хэш", dp(280)),
                ("Завершён", dp(50)),
                ("Адрес", dp(100)),
            ],
            row_data=[],
            use_pagination=True,
            rows_num=10,
        )

        layout.add_widget(self.table)
        self.add_widget(layout)

        Clock.schedule_interval(self.update_status, 2)

    def update_status(self, dt):
        status = fetch_data("GET_STATUS")
        self.table.update_row_data(None, [
            (
                w.get("worker_id", ""),
                w.get("files_processed", 0),
                w.get("current_file", ""),
                w.get("current_hash", ""),
                "Да" if w.get("done") else "Нет",
                w.get("addr", "")
            ) for w in status
        ])


class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sort_column = "timestamp"
        self.sort_ascending = False

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

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

        Clock.schedule_interval(self.update_history, 2)
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
        history_list = fetch_data("GET_HISTORY")
        worker_status = fetch_data("GET_STATUS")
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

        if self.sort_column:
            history_list.sort(
                key=lambda x: x.get(self.sort_column, ""),
                reverse=not self.sort_ascending
            )
        history_list.sort(key=lambda x: 0 if x.get("status") == "В процессе" else 1)

        self.table.update_row_data(None, [
            (
                entry.get("filename", ""),
                entry.get("hash", ""),
                entry.get("status", ""),
                entry.get("timestamp", "").replace("T", " ").split(".")[0] if entry.get("timestamp") else ""
            ) for entry in history_list
        ])


class ScanHistoryApp(MDApp):
    def build(self):
        self.title = "Мониторинг системы"
        sm = MDScreenManager()
        self.history_screen = HistoryScreen(name="history")
        self.worker_screen = WorkerScreen(name="workers")
        sm.add_widget(self.history_screen)
        sm.add_widget(self.worker_screen)

        root = BoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(title="Сканер изображений", elevation=4)
        btn_hist = MDRaisedButton(text="История", on_release=lambda x: sm.switch_to(self.history_screen))
        btn_stat = MDRaisedButton(text="Воркеры", on_release=lambda x: sm.switch_to(self.worker_screen))
        toolbar.right_action_items = [["history", lambda x: sm.switch_to(self.history_screen)],
                                      ["server", lambda x: sm.switch_to(self.worker_screen)]]
        root.add_widget(toolbar)
        root.add_widget(sm)
        return root


if __name__ == '__main__':
    ScanHistoryApp().run()
