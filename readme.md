![GitHub top language](https://img.shields.io/github/languages/top/QueenDekim/telegram-wireguard-vpn-bot)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/QueenDekim/telegram-wireguard-vpn-bot/total)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/QueenDekim/telegram-wireguard-vpn-bot?label=commits)
![GitHub Repo stars](https://img.shields.io/github/stars/QueenDekim/telegram-wireguard-vpn-bot)

---
<h1 align=center>This is fork of <a href="https://github.com/svishnevskii/telegram_wireguard">svishnevskii/telegram_wireguard</a> repositry</h1>

---
<h2>Quick installation:</h2>

```bash
sudo wget https://github.com/QueenDekim/telegram-wireguard-vpn-bot/releases/download/release/Wireguard-installer-with-Adminpanel.sh && chmod 774 Wireguard-installer-with-Adminpanel.sh && ./Wireguard-installer-with-Adminpanel.sh
```
- after configuring the wg, a choice will appear: `Hotite li ustanovit' srazu Telegram bota(1 - Da, 0 - Net):` We agree (press 1)
- Then we specify the `Telegram API` of the bot, which we received from **BotFather** when creating the bot, `YCassa API`, which we also received from **BotFather** when setting up the Payment of the bot and `Telegram-id Admin` - your telegram account ID

<h3>Сhecking the operation of the service</h3>

```bash
sudo systemctl status befutureAdmin
```

<h3>Start</h3>

```bash
sudo systemctl start befutureAdmin
```

<h3>Stop</h3>

```bash
sudo systemctl stop befutureAdmin
```

<h3>Restart</h3>

```bash
sudo systemctl restart befutureAdmin
```

---

<h2>In file <code>config.json</code> added discounts</h2>

```Json
{   
    ...
    "perc_1": 1,
    "perc_3": 3,
    "perc_6": 6,
    ...
}
```

We specify the number of months for which the user will actually pay (interest is calculated automatically)<br>
For example:
<code>config.json</code>

```Json
{
    "admin_tg_id": "",
    "one_month_cost": 500,
    "trial_period": 2,
    "perc_1": 1,
    "perc_3": 2.85,
    "perc_6": 5.4,
    "UTC_time": 3,
    "tg_token": "",
    "tg_shop_token": ""
}
```

That is, when paying for 3 months, the user will actually pay for 2.85 months (5% discount)<br>And when paying for 6 months, the user will pay for 5.4 months (10%)<br><br>
In telegram bot:<br>
![example](https://github.com/QueenDekim/telegram-wireguard-vpn-bot/raw/main/example.png)

---

<h2>Аn admin function has been added that sends an update notification to all users</h2>

in `main.py` file:

```python
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
        
    BotChecking.send_message(CONFIG['admin_tg_id'],
                                f"Сообщение отправлено {countSended} пользователям. {countBlocked} пользователей заблокировало бота", parse_mode="HTML")

```

in `buttons.py` file:

```python
Butt_admin.add(types.KeyboardButton(e.emojize(f"Уведомление об обновлении"))) 
```
in `texts.json` file:

```json
{
  "alert_to_update":"Выполнено обновление бота, проверьте, пожалуйста, функциональность бота.\nЕсли после этого сообщения у вас пропал таймер действия подписки, напишите /start\n\nО найденых ошибках просьба сообщить @admin",
}
```

<h2>The text of some messages is specified in <code>texts.json</code></h2>

```Json
{
  "hello_message": "<b>Почему стоит выбрать Your VPN?</b>\n\n1. Мы шифруем весь трафик клиентов \uD83D\uDD10\n2. Мы не сохраняем ваши конфиденциальные данные, в отличие от бесплатных VPN-сервисов \n3. Отличная скорость и нет ограничений по трафику \uD83C\uDFCE",
  "trial_message": "Чтобы вы смогли оценить наш VPN, даем вам бесплатный доступ на 1 день!\n\nКак пользоваться VPN и другие ответы, находятся в разделе \"Как подключить :gear:\"",
  "how_to_connect_info": "1. Скачайте файл настроек\n\n2. Установите VPN: <a href='https://apps.apple.com/us/app/wireguard/id1441195209'>iPhone</a>, <a href='https://play.google.com/store/apps/details?id=com.wireguard.android'>Android</a>, <a href='https://download.wireguard.com/windows-client/wireguard-installer.exe'>Windows</a> или <a href='https://itunes.apple.com/us/app/wireguard/id1451685025?ls=1&mt=12'>Mac</a> \n\n3. Откройте VPN и нажмите добавить туннель через файл настроек",
  "success_pay_message": "Оплата прошла успешно!\nПодписка продлена, спасибо что выбираете нас.",
  "ended_sub_message": "Ваша подписка закончилась!\n\nЕсли хотите продолжить пользоваться нашими услугами, пожалуйста продлите подписку.",
  "alert_to_renew_sub": "До конца действия подписки осталось меньше дня, пора продлить ее!",
  "alert_to_extend_sub": " \uD83C\uDF81 Your VPN снова предлагает тебе бесплатный тестовый период на 7 дней\n\n✅ Уверены ты оценишь наш VPN \n\nДанные для входа были обновлены, скачайте новый файл авторизации через раздел \"Как подключить :gear:\"",
  "alert_to_update":"Выполнено обновление бота, проверьте, пожалуйста, функциональность бота.\nЕсли после этого сообщения у вас пропал таймер действия подписки, напишите /start\n\nО найденых ошибках просьба сообщить @admin"
  "add_trial_days": 7
}
```
---

|                                                links                                                                         |                                 description                                         |
|:----------------------------------------------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|
|[![Discord](https://img.shields.io/discord/1003119748382466049?label=Ascento%20TEAM%20Discord)](https://discord.gg/HVZ5UfuZnq)|                              Our Discord server                                     |
|[![Static Badge](https://img.shields.io/badge/Discord-from__russia__with__love-purple)](https://about:blank)                  |                                My Discord tag                                       |
|[![Static Badge](https://img.shields.io/badge/Telegram-%40QueenDek1m-blue)](https://t.me/QueenDek1m)                          |                                  My telegram                                        |
|[![Static Badge](https://img.shields.io/badge/Telegram-%40Dekim__vpn__bot-blue)](https://t.me/Dekim_vpn_bot)                  |                     My telegram bot for example (fully operational)                 |
