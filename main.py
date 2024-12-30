import json
import string
import subprocess
from datetime import datetime
import sqlite3
import time

import aiosqlite

import buttons
import dbworker

from telebot import TeleBot
from pyqiwip2p import QiwiP2P
from pyqiwip2p import AioQiwiP2P
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
import emoji as e
import asyncio
import threading
from telebot import types
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

from buttons import main_buttons
from dbworker import User

with open("config.json", encoding="utf-8") as file_handler:
    CONFIG = json.load(file_handler)
    dbworker.CONFIG = CONFIG
    buttons.CONFIG = CONFIG
with open("texts.json", encoding="utf-8") as file_handler:
    text_mess = json.load(file_handler)
    texts_for_bot = text_mess

DBCONNECT = "data.sqlite"
BOTAPIKEY = CONFIG["tg_token"]

bot = AsyncTeleBot(CONFIG["tg_token"], state_storage=StateMemoryStorage())

class MyStates(StatesGroup):
    findUserViaId = State()
    editUser = State()
    editUserResetTime = State()

    UserAddTimeDays = State()
    UserAddTimeHours = State()
    UserAddTimeMinutes = State()
    UserAddTimeApprove = State()

    AdminNewUser = State()


@bot.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == "private":
        await bot.delete_state(message.from_user.id)
        user_dat = await User.GetInfo(message.chat.id)
        if user_dat.registered:
            await bot.send_message(message.chat.id, "Информация о подписке", parse_mode="HTML",
                                   reply_markup=await main_buttons(user_dat))
        else:
            try:
                username = "@" + str(message.from_user.username)
            except:

                username = str(message.from_user.id)

            await user_dat.Adduser(username, message.from_user.full_name)
            user_dat = await User.GetInfo(message.chat.id)
            await bot.send_message(message.chat.id, e.emojize(texts_for_bot["hello_message"]), parse_mode="HTML",
                                   reply_markup=await main_buttons(user_dat))
            await bot.send_message(message.chat.id, e.emojize(texts_for_bot["trial_message"]))


@bot.message_handler(state=MyStates.editUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']
    user_dat = await User.GetInfo(tgid)
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.reset_data(m.from_user.id)
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return
    if e.demojize(m.text) == "Добавить время":
        await bot.set_state(m.from_user.id, MyStates.UserAddTimeDays)
        Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
        await bot.send_message(m.from_user.id, "Введите сколько дней хотите добавить:", reply_markup=Butt_skip)
        return
    if e.demojize(m.text) == "Обнулить время":
        await bot.set_state(m.from_user.id, MyStates.editUserResetTime)
        Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Да")))
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Нет")))
        await bot.send_message(m.from_user.id, "Вы уверены что хотите сбросить время для этого пользователя ?",
                               reply_markup=Butt_skip)
        return


@bot.message_handler(state=MyStates.editUserResetTime, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']

    if e.demojize(m.text) == "Да":
        db = await aiosqlite.connect(DBCONNECT)
        db.row_factory = sqlite3.Row
        await db.execute(f"Update userss set subscription = ?, banned=false, notion_oneday=true where tgid=?",
                         (str(int(time.time())), tgid))
        await db.commit()
        await bot.send_message(m.from_user.id, "Время сброшено!")

    async with bot.retrieve_data(m.from_user.id) as data:
        usertgid = data['usertgid']
    user_dat = await User.GetInfo(usertgid)
    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)

    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")


@bot.message_handler(state=MyStates.UserAddTimeDays, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        days = 0
    else:
        try:
            days = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if days < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['days'] = days
    await bot.set_state(m.from_user.id, MyStates.UserAddTimeHours)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
    await bot.send_message(m.from_user.id, "Введите сколько часов хотите добавить:", reply_markup=Butt_skip)


@bot.message_handler(state=MyStates.UserAddTimeHours, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        hours = 0
    else:
        try:
            hours = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if hours < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['hours'] = hours
    await bot.set_state(m.from_user.id, MyStates.UserAddTimeMinutes)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
    await bot.send_message(m.from_user.id, "Введите сколько минут хотите добавить:", reply_markup=Butt_skip)


@bot.message_handler(state=MyStates.UserAddTimeMinutes, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        minutes = 0
    else:
        try:
            minutes = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if minutes < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['minutes'] = minutes
        hours = data['hours']
        days = data['days']
        tgid = data['usertgid']

    await bot.set_state(m.from_user.id, MyStates.UserAddTimeApprove)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Да")))
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Нет")))
    await bot.send_message(m.from_user.id,
                           f"Пользователю {str(tgid)} добавится:\n\nДни: {str(days)}\nЧасы: {str(hours)}\nМинуты: {str(minutes)}\n\nВсе верно ?",
                           reply_markup=Butt_skip)


@bot.message_handler(state=MyStates.UserAddTimeApprove, content_types=["text"])
async def Work_with_Message(m: types.Message):
    all_time = 0
    if e.demojize(m.text) == "Да":
        async with bot.retrieve_data(m.from_user.id) as data:
            minutes = data['minutes']
            hours = data['hours']
            days = data['days']
            tgid = data['usertgid']
        all_time += minutes * 60
        all_time += hours * 60 * 60
        all_time += days * 60 * 60 * 24
        await AddTimeToUser(tgid, all_time)
        await bot.send_message(m.from_user.id, e.emojize("Время добавлено пользователю!"), parse_mode="HTML")

    async with bot.retrieve_data(m.from_user.id) as data:
        usertgid = data['usertgid']
    user_dat = await User.GetInfo(usertgid)
    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)

    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")


@bot.message_handler(state=MyStates.findUserViaId, content_types=["text"])
async def Work_with_Message(m: types.Message):
    await bot.delete_state(m.from_user.id)
    try:
        user_id = int(m.text)
    except:
        await bot.send_message(m.from_user.id, "Неверный Id!", reply_markup=await buttons.admin_buttons())
        return
    user_dat = await User.GetInfo(user_id)
    if not user_dat.registered:
        await bot.send_message(m.from_user.id, "Такого пользователя не существует!",
                               reply_markup=await buttons.admin_buttons())
        return

    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)
    async with bot.retrieve_data(m.from_user.id) as data:
        data['usertgid'] = user_dat.tgid
    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")


@bot.message_handler(state=MyStates.AdminNewUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    if set(m.text) <= set(string.ascii_letters + string.digits):
        db = await aiosqlite.connect(DBCONNECT)
        await db.execute(f"INSERT INTO static_profiles (name) values (?)", (m.text,))
        await db.commit()
        check = subprocess.call(f'./addusertovpn.sh {str(m.text)}', shell=True)
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id,
                               "Пользователь добавлен!", reply_markup=await buttons.admin_buttons_static_users())
    else:
        await bot.send_message(m.from_user.id,
                               "Можно использовать только латинские символы и арабские цифры!\nПопробуйте заново.")
        return


@bot.message_handler(state="*", content_types=["text"])
async def Work_with_Message(m: types.Message):
    user_dat = await User.GetInfo(m.chat.id)

    if user_dat.registered == False:
        try:
            username = "@" + str(m.from_user.username)
        except:

            username = str(m.from_user.id)

        await user_dat.Adduser(username, m.from_user.full_name)
        await bot.send_message(m.chat.id,
                               texts_for_bot["hello_message"],
                               parse_mode="HTML", reply_markup=await main_buttons(user_dat))
        return
    await user_dat.CheckNewNickname(m)

    if m.from_user.id == CONFIG["admin_tg_id"]:
        if e.demojize(m.text) == "Админ-панель :smiling_face_with_sunglasses:":
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await buttons.admin_buttons())
            return
        if e.demojize(m.text) == "Главное меню :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, e.emojize("Админ-панель :smiling_face_with_sunglasses:"),
                                   reply_markup=await main_buttons(user_dat))
            return
        if e.demojize(m.text) == "Вывести пользователей :bust_in_silhouette:":
            await bot.send_message(m.from_user.id, e.emojize("Выберите каких пользователей хотите вывести."),
                                   reply_markup=await buttons.admin_buttons_output_users())
            return

        if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await buttons.admin_buttons())
            return

        if e.demojize(m.text) == "Всех пользователей":
            allusers = await user_dat.GetAllUsers()
            readymass = []
            readymes = ""
            for i in allusers:
                if int(i[2]) > int(time.time()):
                    if len(readymes) + len(f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>) :check_mark_button:\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>) :check_mark_button:\n"
                else:
                    if len(readymes) + len(f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>)\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>)\n"
            readymass.append(readymes)
            for i in readymass:
                await bot.send_message(m.from_user.id, e.emojize(i), reply_markup=await buttons.admin_buttons(),
                                       parse_mode="HTML")
            return

        if e.demojize(m.text) == "Продлить пробный период":
            db = sqlite3.connect(DBCONNECT)
            db.row_factory = sqlite3.Row
            c = db.execute(f"SELECT * FROM userss where banned=true and username <> '@None'")
            log = c.fetchall()
            c.close()
            db.close()
            BotChecking = TeleBot(BOTAPIKEY)
            timetoadd = 7 * 60 * 60 * 24
            countSended = 0
            db = sqlite3.connect(DBCONNECT)
            for i in log:
                try:
                    countSended += 1
                    db.execute(f"Update userss set subscription = ?, banned=false, notion_oneday=false where tgid=?",
                            (str(int(time.time()) + timetoadd), i["tgid"]))
                    db.commit()
                    db.close()
                    subprocess.call(f'./addusertovpn.sh {str(i["tgid"])}', shell=True)

                    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить :money_bag:")),
                                types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                    BotChecking.send_message(i['tgid'],
                                            texts_for_bot["alert_to_extend_sub"],
                                            reply_markup=Butt_main, parse_mode="HTML")
                except:
                    countSended -= 1
                    countBlocked += 1
                    pass
            BotChecking.send_message(CONFIG['admin_tg_id'],
                                        f"Добавлен пробный период {countSended} пользователям. {countBlocked} пользователей заблокировало бота", parse_mode="HTML")
        
        if e.demojize(m.text) == "Уведомление об обновлении":
            db = sqlite3.connect(DBCONNECT)
            db.row_factory = sqlite3.Row
            c = db.execute(f"SELECT * FROM userss where username <> '@None'")
            log = c.fetchall()
            c.close()
            db.close()
            BotChecking = TeleBot(BOTAPIKEY)
            countSended = 0
            countBlocked = 0
            for i in log:
                try: 
                    countSended += 1

                    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить :money_bag:")),
                                types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                    BotChecking.send_message(i['tgid'],
                                            texts_for_bot["alert_to_update"],
                                            reply_markup=Butt_main, parse_mode="HTML")
                except:
                    countSended -= 1
                    countBlocked += 1
                    pass

            BotChecking.send_message(CONFIG['admin_tg_id'],
                                        f"Сообщение отправлено {countSended} пользователям. {countBlocked} пользователей заблокировало бота", parse_mode="HTML")


        if e.demojize(m.text) == "Пользователей с подпиской":
            allusers = await user_dat.GetAllUsersWithSub()
            readymass = []
            readymes = ""
            if len(allusers) == 0:
                await bot.send_message(m.from_user.id, e.emojize("Нету пользователей с подпиской!"),
                                       reply_markup=await buttons.admin_buttons(), parse_mode="HTML")
                return
            for i in allusers:
                if int(i[2]) > int(time.time()):
                    if len(readymes) + len(
                            f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>) - {datetime.utcfromtimestamp(int(i[2]) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}\n\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i[6]} ({i[5]}|<code>{str(i[1])}</code>) - {datetime.utcfromtimestamp(int(i[2]) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}\n\n"
            readymass.append(readymes)
            for i in readymass:
                await bot.send_message(m.from_user.id, e.emojize(i), parse_mode="HTML")
        if e.demojize(m.text) == "Вывести статичных пользователей":
            db = await aiosqlite.connect(DBCONNECT)
            c = await db.execute(f"select * from static_profiles")
            all_staticusers = await c.fetchall()
            await c.close()
            await db.close()
            if len(all_staticusers) == 0:
                await bot.send_message(m.from_user.id, "Статичных пользователей нету!")
                return
            for i in all_staticusers:
                Butt_delete_account = types.InlineKeyboardMarkup()
                Butt_delete_account.add(types.InlineKeyboardButton(e.emojize("Удалить пользователя :cross_mark:"),
                                                                   callback_data=f'DELETE:{str(i[0])}'))

                config = open(f'/root/wg0-client-{str(str(i[1]))}.conf', 'rb')
                await bot.send_document(chat_id=m.chat.id, document=config,
                                        visible_file_name=f"{str(str(i[1]))}.conf",
                                        caption=f"Пользователь: <code>{str(i[1])}</code>", parse_mode="HTML",
                                        reply_markup=Butt_delete_account)

            return

        if e.demojize(m.text) == "Редактировать пользователя по id :pencil:":
            await bot.send_message(m.from_user.id, "Введите Telegram Id пользователя:",
                                   reply_markup=types.ReplyKeyboardRemove())
            await bot.set_state(m.from_user.id, MyStates.findUserViaId)
            return

        if e.demojize(m.text) == "Статичные пользователи":
            await bot.send_message(m.from_user.id, "Выберите пункт меню:",
                                   reply_markup=await buttons.admin_buttons_static_users())
            return

        if e.demojize(m.text) == "Добавить пользователя :plus:":
            await bot.send_message(m.from_user.id,
                                   "Введите имя для нового пользователя!\nМожно использовать только латинские символы и арабские цифры.",
                                   reply_markup=await buttons.admin_buttons_back())
            await bot.set_state(m.from_user.id, MyStates.AdminNewUser)
            return

    if e.demojize(m.text) == "Продлить :money_bag:":
        payment_info = await user_dat.PaymentInfo()
        if True:
            Butt_payment = types.InlineKeyboardMarkup()
            Butt_payment.add(
                types.InlineKeyboardButton(e.emojize(f"1 мес. 📅 - {str(round(CONFIG['perc_1'] * CONFIG['one_month_cost']))} руб. Выгода {round(((1 - CONFIG['perc_1']) / 1) * 100)}%"),
                                           callback_data="BuyMonth:1"))
            Butt_payment.add(
                types.InlineKeyboardButton(e.emojize(f"3 мес. 📅 - {str(round(CONFIG['perc_3'] * CONFIG['one_month_cost']))} руб. Выгода {round(((3 - CONFIG['perc_3']) / 3) * 100)}%"),
                                           callback_data="BuyMonth:3"))
            Butt_payment.add(
                types.InlineKeyboardButton(e.emojize(f"6 мес. 📅 - {str(round(CONFIG['perc_6'] * CONFIG['one_month_cost']))} руб. Выгода {round(((6 - CONFIG['perc_6']) / 6) * 100)}%"),
                                           callback_data="BuyMonth:6"))
            await bot.send_message(m.chat.id,
                                   "<b>Оплатить можно с помощью Банковской карты!</b>\n\nВыберите на сколько месяцев хотите приобрести подписку:",
                                   reply_markup=Butt_payment, parse_mode="HTML")

    if e.demojize(m.text) == "Как подключить :gear:":
        if user_dat.trial_subscription == False:
            Butt_how_to = types.InlineKeyboardMarkup()
            Butt_how_to.add(
                types.InlineKeyboardButton(e.emojize("Подробнее как подключить"),
                                           url="https://telegra.ph/Gajd-na-ustanovku-11-27"))
            Butt_how_to.add(
                types.InlineKeyboardButton(e.emojize("Проверить VPN"),
                                           url="https://2ip.ru/"))
            config = open(f'/root/wg0-client-{str(user_dat.tgid)}.conf', 'rb')
            await bot.send_document(chat_id=m.chat.id, document=config, visible_file_name=f"{str(user_dat.tgid)}.conf",
                                    caption=texts_for_bot["how_to_connect_info"], parse_mode="HTML",
                                    reply_markup=Butt_how_to)
        else:
            await bot.send_message(chat_id=m.chat.id, text="Сначала нужно купить подписку!")


@bot.callback_query_handler(func=lambda c: 'BuyMonth:' in c.data)
async def Buy_month(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    payment_info = await user_dat.PaymentInfo()
    if payment_info is None:
        Month_count = int(str(call.data).split(":")[1])
        await bot.delete_message(call.message.chat.id, call.message.id)
        if(Month_count == 1):
            count = CONFIG['perc_1']
        if(Month_count == 3):
            count = CONFIG['perc_3']
        if(Month_count == 6):
            count = CONFIG['perc_6']

        provider_data_wo_email = {
            "receipt": {
                "items": [{
                    "description": f"VPN на {str(Month_count)} мес.",
                    "quantity": f"1.00",
                    "amount": {
                        "value": f"{Month_count * CONFIG['one_month_cost']}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }]
            }
        }
        
        bill = await bot.send_invoice(
            call.message.chat.id,
            f"Оплата VPN",
            f"VPN на {str(Month_count)} мес. Выгода {round(((Month_count - count) / Month_count) * 100)}%",
            call.data,
            currency="RUB",
            prices=[
                types.LabeledPrice(f"VPN на {str(Month_count)} мес.  Выгода {round(((Month_count - count) / Month_count) * 100)}%", round(count * CONFIG['one_month_cost'] * 100))],
            provider_token=CONFIG["tg_shop_token"],
            provider_data=json.dumps(provider_data_wo_email)
    await bot.answer_callback_query(call.id)

async def AddTimeToUser(tgid, timetoadd):
    userdat = await User.GetInfo(tgid)
    db = await aiosqlite.connect(DBCONNECT)
    db.row_factory = sqlite3.Row
    if int(userdat.subscription) < int(time.time()):
        passdat = int(time.time()) + timetoadd
        await db.execute(f"Update userss set subscription = ?, banned=false, notion_oneday=false where tgid=?",
                         (str(int(time.time()) + timetoadd), userdat.tgid))
        check = subprocess.call(f'./addusertovpn.sh {str(userdat.tgid)}', shell=True)
        await bot.send_message(userdat.tgid, e.emojize(
            'Данные для входа были обновлены, скачайте новый файл авторизации через раздел "Как подключить :gear:"'))
    else:
        passdat = int(userdat.subscription) + timetoadd
        await db.execute(f"Update userss set subscription = ?, notion_oneday=false where tgid=?",
                         (str(int(userdat.subscription) + timetoadd), userdat.tgid))
    await db.commit()

    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
    dateto = datetime.utcfromtimestamp(int(passdat) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')
    timenow = int(time.time())
    if int(passdat) >= timenow:
        Butt_main.add(
            types.KeyboardButton(e.emojize(f":green_circle: До: {dateto} МСК:green_circle:")))

    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить :money_bag:")),
                  types.KeyboardButton(e.emojize(f"Как подключить :gear:")))


@bot.callback_query_handler(func=lambda c: 'DELETE:' in c.data or 'DELETYES:' in c.data or 'DELETNO:' in c.data)
async def DeleteUserYesOrNo(call: types.CallbackQuery):
    idstatic = str(call.data).split(":")[1]
    db = await aiosqlite.connect(DBCONNECT)
    c = await db.execute(f"select * from static_profiles where id=?", (int(idstatic),))
    staticuser = await c.fetchone()
    await c.close()
    await db.close()
    if staticuser[0] != int(idstatic):
        await bot.answer_callback_query(call.id, "Пользователь уже удален!")
        return

    if "DELETE:" in call.data:
        Butt_delete_account = types.InlineKeyboardMarkup()
        Butt_delete_account.add(
            types.InlineKeyboardButton(e.emojize("Удалить!"), callback_data=f'DELETYES:{str(staticuser[0])}'),
            types.InlineKeyboardButton(e.emojize("Нет"), callback_data=f'DELETNO:{str(staticuser[0])}'))
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=Butt_delete_account)
        await bot.answer_callback_query(call.id)
        return
    if "DELETYES:" in call.data:
        db = await aiosqlite.connect(DBCONNECT)
        await db.execute(f"delete from static_profiles where id=?", (int(idstatic),))
        await db.commit()
        await bot.delete_message(call.message.chat.id, call.message.id)
        check = subprocess.call(f'./deleteuserfromvpn.sh {str(staticuser[1])}', shell=True)
        await bot.answer_callback_query(call.id, "Пользователь удален!")
        return
    if "DELETNO:" in call.data:
        Butt_delete_account = types.InlineKeyboardMarkup()
        Butt_delete_account.add(types.InlineKeyboardButton(e.emojize("Удалить пользователя :cross_mark:"),
                                                           callback_data=f'DELETE:{str(idstatic)}'))
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=Butt_delete_account)
        await bot.answer_callback_query(call.id)
        return


@bot.pre_checkout_query_handler(func=lambda query: True)
async def checkout(pre_checkout_query):
    month = int(str(pre_checkout_query.invoice_payload).split(":")[1])
    if(month == 1):
            count = CONFIG['perc_1']
    if(month == 3):
            count = CONFIG['perc_3']
    if(month == 6):
            count = CONFIG['perc_6']
    if count * 100 * CONFIG['one_month_cost'] != pre_checkout_query.total_amount:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                            error_message="Нельзя купить по старой цене!")
        await bot.send_message(pre_checkout_query.from_user.id,
                               "<b>Цена изменилась! Нельзя приобрести по старой цене!</b>", parse_mode="HTML")
    else:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                            error_message="Оплата не прошла, попробуйте еще раз!")


@bot.message_handler(content_types=['successful_payment'])
async def got_payment(m):
    payment: types.SuccessfulPayment = m.successful_payment
    month = int(str(payment.invoice_payload).split(":")[1])

    user_dat = await User.GetInfo(m.from_user.id)
    await bot.send_message(m.from_user.id, texts_for_bot["success_pay_message"],
                           reply_markup=await buttons.main_buttons(user_dat), parse_mode="HTML")
    await AddTimeToUser(m.from_user.id, month * 30 * 24 * 60 * 60)
    if(month == 1):
        count = CONFIG['perc_1']
    if(month == 3):
        count = CONFIG['perc_3']
    if(month == 6):
        count = CONFIG['perc_6']
    await bot.send_message(CONFIG["admin_tg_id"], f"Новая оплата подписки на <b>{month}</b> мес. <b>{round(count * CONFIG['one_month_cost'])}</b> руб.", parse_mode="HTML")


bot.add_custom_filter(asyncio_filters.StateFilter(bot))

def checkTime():
    while True:
        try:
            time.sleep(15)
            db = sqlite3.connect(DBCONNECT)
            db.row_factory = sqlite3.Row
            c = db.execute(f"SELECT * FROM userss")
            log = c.fetchall()
            c.close()
            db.close()
            for i in log:
                time_now = int(time.time())
                remained_time = int(i[2]) - time_now
                if remained_time <= 0 and i[3] == False:
                    db = sqlite3.connect(DBCONNECT)
                    db.execute(f"UPDATE userss SET banned=true where tgid=?", (i[1],))
                    db.commit()
                    check = subprocess.call(f'./deleteuserfromvpn.sh {str(i[1])}', shell=True)

                    dateto = datetime.utcfromtimestamp(int(i[2]) + CONFIG['UTC_time'] * 3600).strftime(
                        '%d.%m.%Y %H:%M')
                    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    Butt_main.add(
                        types.KeyboardButton(e.emojize(f":red_circle: Закончилась: {dateto} МСК:red_circle:")))
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить :money_bag:")),
                                  types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                    BotChecking = TeleBot(BOTAPIKEY)
                    BotChecking.send_message(i['tgid'],
                                             texts_for_bot["ended_sub_message"],
                                             reply_markup=Butt_main, parse_mode="HTML")

                if remained_time <= 86400 and i[4] == False:
                    db = sqlite3.connect(DBCONNECT)
                    db.execute(f"UPDATE userss SET notion_oneday=true where tgid=?", (i[1],))
                    db.commit()
                    BotChecking = TeleBot(BOTAPIKEY)
                    BotChecking.send_message(i['tgid'], texts_for_bot["alert_to_renew_sub"], parse_mode="HTML")

                # Дарим бесплатную подписку на 7 дней если он висит 3 дня как неактивный и не ливнул
                # if remained_time <= 259200 and i['trial_continue'] == 0:
                #     BotChecking = TeleBot(BOTAPIKEY)
                #     timetoadd = 7 * 60 * 60 * 24
                #     db = sqlite3.connect(DBCONNECT)
                #     db.execute(f"UPDATE userss SET trial_continue=1 where tgid=?", (i[1],))
                #     db.execute(
                #         f"Update userss set subscription = ?, banned=false, notion_oneday=false where tgid=?",
                #         (str(int(time.time()) + timetoadd), i[1]))
                #     db.commit()
                #     db.close()
                #     subprocess.call(f'./addusertovpn.sh {str(i[1])}', shell=True)

                #     Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                #     Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить :money_bag:")),
                #                   types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                #     BotChecking.send_message(i['tgid'],
                #                              e.emojize(texts_for_bot["alert_to_extend_sub"]),
                #                              reply_markup=Butt_main, parse_mode="HTML")

        except Exception as err:
            print(err)
            pass


if __name__ == '__main__':

    threadcheckTime = threading.Thread(target=checkTime, name="checkTime1")
    threadcheckTime.start()

    asyncio.run(bot.polling(non_stop=True, interval=0, request_timeout=60, timeout=60))
