from telethon import TelegramClient
import asyncio
import csv
import os
import sys 

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

api_id = ""
api_hash = ""

session_name = "session_name"


client = TelegramClient(session_name, api_id, api_hash)


async def get_dialogs():

    dialogs = await client.get_dialogs(limit=50)
    channels = [dialog for dialog in dialogs if dialog.is_channel]

    print("\nСписок доступных каналов:")
    for idx, channel in enumerate(channels):
        print(f"{idx + 1}. {channel.name} ({channel.entity.username or 'без username'})")
    return channels


async def parse_channel(channel):

    print(f"\nВы выбрали канал: {channel.name}")
    print("Начинаем парсинг сообщений...\n")

    photos_dir = f"{channel.name}_photos"
    os.makedirs(photos_dir, exist_ok=True)

    csv_file = f"{channel.name}_content.csv"
    with open(csv_file, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Дата и время", "Фото", "Текст поста"])

        async for message in client.iter_messages(channel.entity, limit=100):
            date_time = message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "Не указано"
            text = message.text if message.text else "Нет текста"
            photo_path = ""

            if message.photo:
                photo_path = await client.download_media(message.photo, photos_dir)

            writer.writerow([date_time, photo_path, text])

    print(f"Парсинг завершен. Данные сохранены в файл {csv_file}")


async def post_from_csv(channel):

    csv_file = f"{channel.name}_content.csv"

    if not os.path.exists(csv_file):
        print(f"CSV файл {csv_file} не найден. Сначала выполните парсинг канала.")
        return

    print(f"Загружаем данные из {csv_file} для публикации...")

    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = row["Текст поста"]
            photo_path = row["Фото"]

            if photo_path and os.path.exists(photo_path):
                print(f"Отправляем пост с фото: {photo_path}")
                await client.send_file(channel.entity, photo_path, caption=text)
            else:
                print(f"Отправляем текстовый пост: {text}")
                await client.send_message(channel.entity, text)

    print("Публикация завершена!")


async def main():

    print("Добро пожаловать в Telegram парсер!")

    channels = await get_dialogs()

    choice = int(input("\nВведите номер канала, который хотите выбрать: ")) - 1

    if 0 <= choice < len(channels):
        channel = channels[choice]

        print("\nВыберите действие:")
        print("1. Парсинг канала")
        print("2. Публикация постов из CSV")
        action = input("Введите номер действия: ")

        if action == "1":
            await parse_channel(channel)
        elif action == "2":
            await post_from_csv(channel)
        else:
            print("Некорректное действие.")
    else:
        print("Некорректный выбор. Завершаем программу.")

with client:
    client.loop.run_until_complete(main())