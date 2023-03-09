import os
import threading
import traceback
from pprint import pprint
from pyrogram import Client, filters, idle
from time import sleep
from datetime import datetime
from random import seed, shuffle, randint
from dotenv import load_dotenv
from pyrogram.types import Message

load_dotenv()

API_HASH = os.getenv("API_HASH")
API_ID = os.getenv("API_ID")

client = Client("8178841", api_id=API_ID, api_hash=API_HASH)
user_id = None
is_idle = True
width, height = 5, 10  # len(rows) == height, len(columns) == width


def generate_matrix(dt_posix=datetime.now().timestamp()):
    dt_posix = int(dt_posix // 60 // 10)
    # print("\n\nMATRIX DT:", dt_posix)
    alphabet = ["а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у",
                "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "0", "1", "2", "3", "4", "5", "6", "7", "8",
                "9", " ", ".", ","]
    seed(dt_posix - 1398)
    shuffle(alphabet)
    matrix = []
    for i in range(height):
        row = []
        for k in range(width):
            if len(alphabet) > 0:
                row.append(alphabet.pop())
            else:
                row.append("")
        matrix.append(row)
    return matrix


def generate_public_key():
    seed()
    start_row, start_col = randint(0x1F600, 0x1F6A9), randint(0x1F600, 0x1F6A9)
    key = {
        "rows": [chr(start_row + i) for i in range(height)],
        "columns": [chr(start_col + i) for i in range(width)]
    }
    shuffle(key["rows"])
    shuffle(key["columns"])
    return key


def show_all_keys(matrix, key):
    print('Ключ', key)
    print('Матриц', matrix)
    print('---')
    for row_index, row in enumerate(matrix):
        for col_index, col in enumerate(row):
            print(f" ({row_index}, {col_index}) '{col}' → "
                  f"'{key['rows'][row_index]}{key['columns'][col_index]}'", end=" |")
        print()


def encode_string(text, key):
    matrix = generate_matrix()
    # print('[ДАННЫЕ ДЛЯ ЗАШИФРОВКИ]')
    # show_all_keys(matrix, key)
    encoded_string = ""
    for char in text:
        for row_index, row in enumerate(matrix):
            for col_index, col in enumerate(row):
                if col == char:
                    encoded_string += key['rows'][row_index]
                    encoded_string += key['columns'][col_index]
    return encoded_string + "".join(key['rows']) + "".join(key['columns']), datetime.now().isoformat()


def decode_string(raw_string, dt_posix):
    matrix = generate_matrix(dt_posix)
    encoded_string = raw_string[:-width-height]
    public_key = {
        "rows": raw_string[-width-height:-width],
        "columns": raw_string[-width:],
    }
    # print('[ДАННЫЕ ДЛЯ РАСШИФРОВКИ]')
    # show_all_keys(matrix, public_key)
    decoded_string = ""
    for i in range(0, len(encoded_string) - 1, 2):
        row_symbol = encoded_string[i]
        col_symbol = encoded_string[i + 1]
        row_index = public_key["rows"].index(row_symbol)
        col_index = public_key["columns"].index(col_symbol)
        char = matrix[row_index][col_index]
        decoded_string += char
    return decoded_string


def background_sender():
    global is_idle
    while is_idle:
        raw_text = input("What to write? (or empty to go out) > ")
        if raw_text == "":
            is_idle = False
        else:
            raw_string, _ = encode_string(raw_text, generate_public_key())
            client.send_message(user_id, raw_string)
    print("Press CTRL+C if you sure to exit.")


@client.on_message(filters.private & filters.incoming)
def hello(client, message: Message):
    if message.from_user.id != int(user_id):
        return
    try:
        decoded_string = decode_string(str(message.text), message.date)
        decoded_string = f'[🔓✅ 21CRYPT] {decoded_string}'
    except Exception as e:
        print(e)
        traceback.print_exc()
        decoded_string = f'[🔓 ❌] {message.text}'
    print(f"\n{message.from_user.first_name} {message.from_user.last_name} wrote you: \"{decoded_string}\"\n> ", end="")


if __name__ == '__main__':
    # telegram auth
    client.start()
    # getting contacts
    contacts = client.get_contacts()
    # print(contacts)
    for i, contact in enumerate(contacts):
        print(f'{i + 1} id:{contact.id} - {contact.first_name}\n')
    # print(f"Hello, {client.get_me().first_name}! 🙌\n\nYour contact list:\n",
    #       *[f"{i + 1}) id: {contact['id']} - {contact['first_name']}" for i, contact in enumerate(contacts)], sep="\n")
    user_index = None
    try:
        user_order = int(input("\nChoose user by order (type 1, 2, 3 etc to process or empty to exit) > "))
        user_index = user_order - 1
        assert 0 <= user_index < len(contacts)
    except (ValueError, AssertionError):
        print(f"Error: invalid value: \"{user_index}\"")
        user_index = None
    # starting in background bot
    # user_index = 6
    print(f'Выбран {contacts[user_index].first_name}!')
    if user_index is not None:
        user_id = contacts[user_index].id
        sender = threading.Thread(target=background_sender)
        # starting sender in background (отправитель сообщений)
        sender.start()
        # starting telgram loop (приемник сообщений)
        idle()

    is_idle = False
    client.stop()
    print("Bot stopped, bye! 👋")