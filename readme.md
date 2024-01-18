sudo wget https://github.com/QueenDekim/telegram-wireguard-vpn-bot/releases/download/release/Wireguard-installer-with-Adminpanel.sh && chmod 774 Wireguard-installer-with-Adminpanel.sh && ./Wireguard-installer-with-Adminpanel.sh

in file <code>config.json</code> added discounts

<code>
    "perc_1": 1,
    "perc_3": 3,
    "perc_6": 6,
</code>

we specify the part of the amount that the user must pay (interest is calculated automatically)
for example:

<code>config.json</code>
```
{
    "admin_tg_id": 123456,
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
in tg bot:
![example](https://github.com/QueenDekim/telegram-wireguard-vpn-bot/raw/main/example.png)