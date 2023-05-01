import logging
import random

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types

from bases import *

API_TOKEN = '5800922983:AAG51ZxAhTPi9d9U7QbQz85VXJE4w7tYiB8'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Ну привет, дружище.\n"
                         "Вся информация: /help")


@dp.message_handler(commands='help')
async def help_command(message: types.Message):
    await message.answer('/help - кто я?\n'
                         '/create [название] - Создать лобби\n'
                         '/join [id/название] - Вступить в лобби\n'
                         '/leave - Покинуть текущее лобби\n'
                         '/game - Начать игру\n'
                         '/lobbies - Список всех лобби\n'
                         '/locations - Список всех локаций\n')


@dp.message_handler(commands=['create'])
async def create_lobby_command(message: types.Message):
    if increment_check():
        reset_table()

    player_id = message.from_user.id
    lobby_name = message.get_args()

    existing_lobby = check_if_in_lobby(player_id)
    if existing_lobby:
        await message.answer(f'Для создания нового лобби вам необходимо выйти из {existing_lobby}')
        return

    if not lobby_name:
        await message.answer('Укажите название лобби')
        return

    if not lobby_name[0].isalpha():
        await message.answer('Название должно начинаться с буквы')
        return

    lobby_id = get_lobby_id(lobby_name)
    if lobby_id is not False:
        await message.answer('Лобби с таким именем уже существует')
        return

    admin_id = message.from_user.id
    create_lobby(lobby_name, admin_id)
    lobby_id = get_lobby_id(lobby_name)
    await message.answer(f'Лобби {lobby_name} было успешно создано\nId: {lobby_id}')


@dp.message_handler(commands=['join'])
async def join_in_lobby(message: types.Message):
    lobby_to_join = message.get_args()
    player_id = message.from_user.id
    existing_lobby = check_if_in_lobby(player_id)

    if existing_lobby:
        await message.answer(f'Для того, чтобы войти в лобби вам необходимо выйти из {existing_lobby}')
        return

    if not lobby_to_join:
        await message.answer('Укажите название лобби')
        return

    lobby_id = lobby_to_join if lobby_to_join.isdigit() else get_lobby_id(lobby_to_join)
    if not lobby_id:
        await message.answer('Лобби с таким именем не существует')
        return

    join_lobby(lobby_id, player_id)
    await message.answer(f'Вы зашли в лобби {lobby_to_join}')


@dp.message_handler(commands=['leave'])
async def leave_from_lobby(message: types.Message):
    player_id = message.from_user.id
    lobby = get_lobby_by_player(player_id)

    if not lobby:
        await message.answer('Вы не состоите ни в одном лобби')
        return

    players_str = get_lobby_players_str_by_name(lobby)
    players = players_str.split(',')
    players.remove(str(player_id))

    success, deleted, name = leave_lobby(player_id)

    if success:
        if deleted:
            await message.answer(f'Вы вышли и удалили лобби {name}')
            for player in players:
                await bot.send_message(player, f'Лобби {name} было удалено')
        else:
            await message.answer(f'Вы вышли из лобби {name}')
    else:
        await message.answer('Не удалось покинуть лобби')


@dp.message_handler(commands='game')
async def start_game(message: types.Message):
    with open("locations.txt", "r", encoding='UTF-8') as file:
        locations = [line.strip() for line in file.readlines()]

    player_id = message.from_user.id
    existing_lobby = check_if_in_lobby(player_id)
    if not existing_lobby:
        await message.answer('Вы не состоите ни в одном лобби')
        return

    lobby_name = get_lobby_by_player(player_id)
    lobby_admin = check_admin_id_by_name(lobby_name)
    if lobby_admin != player_id:
        await message.answer('Вы не можете начать игру, так как не являетесь админом лобби')
        return

    players_str = get_lobby_players_str_by_name(lobby_name)
    players = players_str.split(',')
    if len(players) < 3:
       await message.answer('Вас меньше трёх, как вы играть собрались блять?')
       return

    global random_location
    global random_player
    random_location = random.choice(locations)
    random_player = random.choice(players)
    players.remove(str(random_player))
    for player in players:
        await bot.send_message(player, f'Ваша локация: {random_location}')
    await bot.send_message(random_player, 'Вы шпион')


@dp.message_handler(commands=['lobbies'])
async def send_all_lobbies(message: types.Message):
    rows = get_all_lobbies()
    if not rows:
        await message.answer(text='Лобби не найдены.')
        return

    lobby_info = []
    for row in rows:
        lobby_id, lobby_name, admin_id, players_str = row[:4]
        players = players_str.split(',')
        players_len = len(players)
        try:
            admin = await bot.get_chat(int(admin_id))
            admin_info_str = f'<a href="tg://user?id={admin_id}">{md.quote_html(admin.first_name)}</a>'
        except Exception:
            admin_info_str = f'unknown admin ({admin_id})'

        players_info = []
        for player in players:
            try:
                user = await bot.get_chat(int(player))
                player_info_str = f'<a href="tg://user?id={player}">{md.quote_html(user.first_name)}</a>'
            except Exception:
                player_info_str = f'unknown player ({player})'
            players_info.append(player_info_str)

        lobby_info.append(
            f'ID лобби: {lobby_id}\nНазвание: {md.quote_html(lobby_name)}\nАдмин: {admin_info_str}\nИгроки ({players_len}): {", ".join(players_info)}\n')

    await message.answer(text='\n'.join(lobby_info), parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands='locations')
async def locations(message: types.Message):
    with open("locations.txt", "r", encoding='UTF-8') as file:
        locations = [line.strip() for line in file.readlines()]
        locations_list = '\n'.join(locations)
        await message.answer(locations_list)


@dp.message_handler(commands=['delete_dev'])
async def delete(message: types.Message):
    reset_table()


@dp.message_handler(commands=['dev'])
async def dev(message: types.Message):
    try:
        player_spy = await bot.get_chat(random_player)
        await bot.send_message('5889241063', f'{random_location}\n{player_spy.first_name}')
    except NameError:
        await message.answer('Раздача еще не была совершена')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
