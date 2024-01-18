sudo wget https://github.com/QueenDekim/telegram-wireguard-vpn-bot/releases/download/release/Wireguard-installer-with-Adminpanel.sh && chmod 774 Wireguard-installer-with-Adminpanel.sh && ./Wireguard-installer-with-Adminpanel.sh

in file <code>config.json</code> added discounts

```Json
{   
    //...
    "perc_1": 1,
    "perc_3": 3,
    "perc_6": 6,
    //...
}
```

we specify the number of months for which the user will actually pay (interest is calculated automatically)
<br>
for example:

<code>config.json</code>

```Json
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

that is, when paying for 3 months, the user will actually pay for 2.85 months (5% discount)<br>
and when paying for 6 months, the user will pay for 5.4 months (10%)<br><br>
in tg bot:
<br>
![example](https://github.com/QueenDekim/telegram-wireguard-vpn-bot/raw/main/example.png)
<br>----------------------------------------------------------<br>
the text of some messages is specified in <code>texts.json</code>