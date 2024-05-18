Raspberry Pi Pico Wでインターホンと宅配ボックスの通知をします

１．配線
GP14-GND ブザー
GP15-GND インターフォンのA接点 
GP13-GND 宅配ボックスのマグネットスイッチ
GP12-GND LED(オンボードのLEDと同時に光る)
※使いたいところだけ配線すれば動きます。

２．settings.txtで設定
WIFI_SSID = your_ssid
WIFI_PASSWORD = your_password
LINE_TOKEN = your_token
MES1 = インターフォン
MES2 = 宅配BOX

自己責任でお使いください。
