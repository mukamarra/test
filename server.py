import socket
import threading

# --- Налаштування сервера ---
HOST = '0.0.0.0'  # адреса сервера (локальний комп'ютер)
PORT = 12345        # порт для з'єднання

# --- Глобальні структури ---
clients = []          # список усіх підключених клієнтів
usernames = {}        # словник: socket -> username (нік користувача)
avatars = {}          # словник: username -> (filename, base64) для збереження аватарів


# --- Відправка даних одному клієнту ---
def send_to_client(client_socket, data: str):
    try:
        client_socket.sendall(data.encode())  # відправляємо повідомлення у байтах
    except:
        pass  # якщо помилка — нічого не робимо


# --- Розсилка повідомлення усім клієнтам ---
def broadcast(data: str, exclude_socket=None):
    for client in clients:
        if client != exclude_socket:  # не відправляти назад відправнику
            send_to_client(client, data)


# --- Обробка клієнта в окремому потоці ---
def handle_client(client_socket):
    buffer = ""
    while True:
        try:
            # отримання даних від клієнта
            chunk = client_socket.recv(8192)
            if not chunk:
                break  # клієнт відключився
            buffer += chunk.decode(errors="ignore")

            # розділяємо повідомлення по символу "\n"
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                handle_line(client_socket, line.strip())  # обробляємо рядок
        except:
            break

    # якщо клієнт відключився
    if client_socket in clients:
        clients.remove(client_socket)
    if client_socket in usernames:
        left_user = usernames[client_socket]
        del usernames[client_socket]
        # повідомляємо іншим, що користувач вийшов
        broadcast(f"TEXT@SYSTEM@{left_user} вийшов з чату\n")
    client_socket.close()


# --- Обробка конкретного рядка повідомлення ---
def handle_line(client_socket, line: str):
    if not line:
        return

    parts = line.split("@", 3)  # розбиваємо рядок по символу "@"
    msg_type = parts[0]

    # --- Текстове повідомлення ---
    if msg_type == "TEXT" and len(parts) >= 3:
        author = parts[1]
        message = parts[2]
        usernames[client_socket] = author  # запам'ятовуємо нік користувача
        # розсилаємо іншим клієнтам
        broadcast(f"TEXT@{author}@{message}\n", exclude_socket=client_socket)

    # --- Аватар ---
    elif msg_type == "AVATAR" and len(parts) >= 4:
        author = parts[1]
        filename = parts[2]
        encoded = parts[3]
        usernames[client_socket] = author
        avatars[author] = (filename, encoded)  # зберігаємо аватар
        # повідомляємо інших
        broadcast(f"AVATAR@{author}@{filename}@{encoded}\n", exclude_socket=client_socket)

    # --- Зміна ніка ---
    elif msg_type == "RENAME" and len(parts) >= 3:
        old = parts[1]
        new = parts[2]
        usernames[client_socket] = new  # оновлюємо нік
        if old in avatars:
            avatars[new] = avatars.pop(old)  # переносимо аватар на новий нік
        # повідомляємо інших
        broadcast(f"RENAME@{old}@{new}\n", exclude_socket=client_socket)

    # --- Інші випадки ---
    else:
        broadcast(line + "\n", exclude_socket=client_socket)


# --- Відправлення новому клієнту вже існуючих аватарів ---
def send_existing_data(client_socket):
    for user, (filename, encoded) in avatars.items():
        send_to_client(client_socket, f"AVATAR@{user}@{filename}@{encoded}\n")


# --- Запуск сервера ---
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # створення сокета TCP
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # щоб порт не блокувався після перезапуску
    server_socket.bind((HOST, PORT))  # прив'язуємо сервер до адреси
    server_socket.listen(5)  # слухаємо підключення
    print(f"Сервер запущено на {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()  # приймаємо нове підключення
        print(f"Підключився клієнт: {addr}")
        clients.append(client_socket)

        # надсилаємо новому клієнту усі існуючі аватари
        send_existing_data(client_socket)

        # запускаємо новий потік для обробки клієнта
        t = threading.Thread(target=handle_client, args=(client_socket,))
        t.start()


if __name__ == "__main__":
    main()
