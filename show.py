import threading
import base64
import io
from socket import *
from customtkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk, ImageEnhance
import random

# =======================
#   🩸  FNaF оформление
# =======================

FNAF_BG = "#080808"           # фон комнаты
FNAF_PANEL = "#111111"        # панель меню
FNAF_RED = "#ff2e2e"          # красный FNaF
FNAF_DARKRED = "#330000"
FNAF_BLACK = "#000000"

set_appearance_mode("dark")

# ===== ГОЛОВНЕ ВІКНО ЧАТУ =====
class MainWindow(CTk):
    def __init__(self, username, host, port, avatar_path=None):
        super().__init__()
        self.geometry("600x400")
        self.title("FNaF Chat Terminal")

        self.configure(fg_color=FNAF_BG)

        self.username = username or "одеяло"
        self.host = host
        self.port = port
        self.sock = None

        self.is_show_menu = False
        self.frame_width = 0
        self.menu_show_speed = 20

        self.avatar_path = avatar_path
        self.avatars: dict[str, bytes] = {}

        # --- Боковое меню ---
        self.menu_frame = CTkFrame(
            self, width=200, height=self.winfo_height(), fg_color=FNAF_PANEL
        )
        self.menu_frame.pack_propagate(False)
        self.menu_frame.configure(width=0)
        self.menu_frame.place(x=0, y=0)

        CTkLabel(
            self.menu_frame, text="Имя охранника", text_color=FNAF_RED, font=("Consolas", 14, "bold")
        ).pack(pady=10)

        self.name_entry = CTkEntry(
            self.menu_frame,
            fg_color="#1a1a1a",
            text_color=FNAF_RED,
            border_color=FNAF_RED
        )
        self.name_entry.insert(0, self.username)
        self.name_entry.pack()

        self.avatar_button = CTkButton(
            self.menu_frame,
            text="Выбрать аватар",
            fg_color=FNAF_DARKRED,
            hover_color="#550000",
            text_color=FNAF_RED,
            command=self.choose_avatar
        )
        self.avatar_button.pack(pady=10)

        self.theme_menu = CTkOptionMenu(
            self.menu_frame,
            values=["Темница FNaF", "Адская ночь"],
            fg_color=FNAF_DARKRED,
            button_color="#550000",
            text_color=FNAF_RED,
            command=self.change_theme
        )
        self.theme_menu.pack(side="bottom", pady=20)

        # Кнопка показа меню
        self.menu_btn = CTkButton(
            self,
            text="▶️",
            width=30,
            fg_color=FNAF_DARKRED,
            hover_color="#550000",
            text_color=FNAF_RED,
            command=self.toggle_menu
        )
        self.menu_btn.place(x=0, y=0)

        # --- Чат ---
        self.chat_field = CTkScrollableFrame(
            self, width=400, height=200, fg_color="#0b0b0b"
        )
        self.chat_field.place(x=0, y=30)

        # --- Нижняя панель ---
        self.message_entry = CTkEntry(
            self,
            placeholder_text="Введи сообщение...",
            height=40,
            fg_color="#1a1a1a",
            border_color=FNAF_RED,
            text_color=FNAF_RED
        )
        self.send_btn = CTkButton(
            self,
            text="SEND",
            width=70,
            height=40,
            fg_color=FNAF_DARKRED,
            hover_color="#660000",
            text_color=FNAF_RED,
            font=("Consolas", 13, "bold"),
            command=self.send_message
        )

        self.message_entry.place(x=0, y=self.winfo_height() - 40)
        self.send_btn.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)

        # адаптивність
        self.after(20, self.adaptive_ui)

        # эффект моргания камеры
        self.after(500, self.flicker_effect)

        # подключение
        self.connect_to_server()

    # ===== ЭФФЕКТ МОРГАНИЯ FNAF =====
    def flicker_effect(self):
        if random.randint(0, 12) == 1:
            self.configure(fg_color="#0f0f0f")
            self.after(60, lambda: self.configure(fg_color=FNAF_BG))
        self.after(500, self.flicker_effect)

    # ====== МЕРЕЖА ======
    def connect_to_server(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((self.host, self.port))

            self.sock.sendall(
                f"TEXT@SYSTEM@{self.username} вошёл в тёмную комнату\n".encode()
            )

            self.add_message(
                f"Подключение к серверу {self.host}:{self.port} установлено",
                system=True
            )

            if self.avatar_path:
                self.send_avatar()

            threading.Thread(target=self.recv_loop, daemon=True).start()

        except Exception as e:
            self.add_message(f"Ошибка подключения: {e}", system=True)

    def recv_loop(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(8192)
                if not chunk:
                    break
                buffer += chunk.decode(errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break

        try:
            self.sock.close()
        except:
            pass

        self.add_message("Связь потеряна...", system=True)

    def handle_line(self, line: str):
        if not line:
            return
        
        parts = line.split("@", 2)
        msg_type = parts[0]

        if msg_type == "TEXT" and len(parts) >= 3:
            author = parts[1]
            message = parts[2]

            if author == "SYSTEM":
                self.add_message(message, system=True)
            else:
                self.add_message(
                    message,
                    username=author,
                    self_message=(author == self.username)
                )

        elif msg_type == "AVATAR" and len(parts) >= 4:
            author = parts[1]
            filename = parts[2]
            encoded = parts[3]
            try:
                self.avatars[author] = base64.b64decode(encoded)
                self.add_message(f"{author} сменил аватар ({filename})", system=True)
            except:
                pass

        elif msg_type == "RENAME" and len(parts) >= 3:
            old = parts[1]
            new = parts[2]
            self.add_message(f"{old} → {new}", system=True)
            if old in self.avatars:
                self.avatars[new] = self.avatars.pop(old)
            if old == self.username:
                self.username = new
                self.name_entry.delete(0, "end")
                self.name_entry.insert(0, new)

        else:
            self.add_message(line, system=True)

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        
        self.username = self.name_entry.get().strip()
        data = f"TEXT@{self.username}@{text}\n"

        try:
            self.sock.sendall(data.encode())
        except:
            self.add_message("Ошибка отправки", system=True)

        self.add_message(text, username=self.username, self_message=True)
        self.message_entry.delete(0, "end")

    def choose_avatar(self):
        path = filedialog.askopenfilename(
            title="Выберите аватар",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if path:
            self.avatar_path = path
            self.send_avatar()

    def send_avatar(self):
        if not self.avatar_path:
            return
        try:
            with open(self.avatar_path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            filename = self.avatar_path.split("/")[-1]
            msg = f"AVATAR@{self.username}@{filename}@{encoded}\n"
            self.sock.sendall(msg.encode())
        except:
            self.add_message("Ошибка отправки аватара", system=True)

    def get_avatar_image(self, data: bytes, size=(30, 30)):
        try:
            img = Image.open(io.BytesIO(data)).resize(size, Image.Resampling.LANCZOS)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.7)
            return ImageTk.PhotoImage(img)
        except:
            return None

    # ====== UI ======
    def change_theme(self, value):
        pass  # FNaF стиль фиксированный

    def toggle_menu(self):
        self.is_show_menu = not self.is_show_menu
        if self.is_show_menu:
            self.show_menu()
        else:
            self.hide_menu()

    def show_menu(self):
        if self.frame_width <= 200:
            self.frame_width += self.menu_show_speed
            self.menu_frame.configure(width=self.frame_width, height=self.winfo_height())
            if self.frame_width >= 30:
                self.menu_btn.configure(width=self.frame_width, text="◀️")
        if self.is_show_menu:
            self.after(20, self.show_menu)

    def hide_menu(self):
        if self.frame_width >= 0:
            self.frame_width -= self.menu_show_speed
            self.menu_frame.configure(width=self.frame_width)
            if self.frame_width >= 30:
                self.menu_btn.configure(width=self.frame_width, text="▶️")
        if not self.is_show_menu:
            self.after(20, self.hide_menu)

    def adaptive_ui(self):
        menu_w = self.menu_frame.winfo_width()
        win_w = self.winfo_width()
        win_h = self.winfo_height()

        self.chat_field.configure(width=win_w - menu_w - 20, height=win_h - 40 - 50)
        self.chat_field.place(x=menu_w, y=30)

        self.message_entry.configure(width=win_w - menu_w - self.send_btn.winfo_width())
        self.message_entry.place(x=menu_w, y=win_h - 40)

        self.send_btn.place(
            x=win_w - self.send_btn.winfo_width(),
            y=win_h - self.send_btn.winfo_height()
        )

        self.after(20, self.adaptive_ui)

    def smooth_scroll_to_bottom(self, steps=10, delay=20):
        canvas = self.chat_field._parent_canvas
        start = canvas.yview()[0]
        end = 1.0
        diff = (end - start) / steps

        def step(i=0):
            if i < steps:
                canvas.yview_moveto(start + diff * (i + 1))
                self.after(delay, lambda: step(i + 1))
        step()

    def add_message(self, message, username=None, self_message=False, system=False):

        frame = CTkFrame(self.chat_field, fg_color="transparent")
        if system:
            frame.pack(anchor="center", pady=2, padx=5)
        elif self_message:
            frame.pack(anchor="e", pady=2, padx=5)
        else:
            frame.pack(anchor="w", pady=2, padx=5)

        # --- SYSTEM MESSAGE (RED WARNING)
        if system:
            CTkLabel(
                frame,
                text=message,
                text_color=FNAF_RED,
                font=("Consolas", 12, "bold")
            ).pack(anchor="center", padx=5, pady=2)
            self.smooth_scroll_to_bottom()
            return

        # --- Avatar
        if username and username in self.avatars:
            avatar_img = self.get_avatar_image(self.avatars[username])
            if avatar_img:
                lbl_img = CTkLabel(frame, image=avatar_img, text="")
                lbl_img.image = avatar_img
                lbl_img.pack(side="right" if self_message else "left", padx=5)

        # --- Message bubble ---
        bg_color = FNAF_DARKRED if self_message else "#111111"
        text_color = FNAF_RED if self_message else "#e5e5e5"

        bubble = CTkFrame(frame, fg_color=bg_color, corner_radius=10)
        bubble.pack(side="right" if self_message else "left", padx=5, pady=(0, 5))

        if username:
            CTkLabel(
                bubble,
                text=username,
                font=("Consolas", 10, "bold"),
                text_color=text_color
            ).pack(anchor="w", padx=5, pady=(3, 0))

        CTkLabel(
            bubble,
            text=message,
            wraplength=300,
            justify="left",
            anchor="w",
            text_color=text_color,
            font=("Consolas", 12)
        ).pack(anchor="w", padx=5, pady=(0, 5))

        self.smooth_scroll_to_bottom()


# ===== Вікно реєстрації =====
class RegistrationWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("350x300")
        self.title("FNaF Terminal — Login")
        self.configure(fg_color=FNAF_BG)

        self.username_var = StringVar(value="Охранник")
        self.host_var = StringVar(value="localhost")
        self.port_var = StringVar(value="8080")
        self.avatar_path = None

        CTkLabel(self, text="Имя", text_color=FNAF_RED).pack(pady=5)
        CTkEntry(self, textvariable=self.username_var, fg_color="#1a1a1a", text_color=FNAF_RED, border_color=FNAF_RED).pack(pady=5)

        CTkLabel(self, text="Сервер", text_color=FNAF_RED).pack(pady=5)
        CTkEntry(self, textvariable=self.host_var, fg_color="#1a1a1a", text_color=FNAF_RED, border_color=FNAF_RED).pack(pady=5)

        CTkLabel(self, text="Порт", text_color=FNAF_RED).pack(pady=5)
        CTkEntry(self, textvariable=self.port_var, fg_color="#1a1a1a", text_color=FNAF_RED, border_color=FNAF_RED).pack(pady=5)

        CTkButton(
            self,
            text="Войти",
            fg_color=FNAF_DARKRED,
            hover_color="#550000",
            text_color=FNAF_RED,
            command=self.start_client
        ).pack(pady=15)

    def start_client(self):
        username=self.username_var.get().strip() or "Охранник"
        host=self.host_var.get().strip() or "localhost"
        port=int(self.port_var.get().strip() or 8080)
        self.destroy()

        app = MainWindow(
            username=username,
            host=host,
            port=port,
            avatar_path=self.avatar_path,
        )
        app.mainloop()


if __name__ == "__main__":
    reg = RegistrationWindow()
    reg.mainloop()