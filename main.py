from machine import Pin, I2C
from utime import sleep, time, mktime, localtime
import framebuf, sys
import ntptime
import network
import urequests

# ファイルから設定を読み込む
def read_settings():
    WIFI_SSID = None
    WIFI_PASSWORD = None
    LINE_TOKEN = None
    MES1 = ""
    MES2 = ""
    try:
        with open("settings.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("WIFI_SSID"):
                    WIFI_SSID = line.split("=")[1].strip()
                elif line.startswith("WIFI_PASSWORD"):
                    WIFI_PASSWORD = line.split("=")[1].strip()
                elif line.startswith("LINE_TOKEN"):
                    LINE_TOKEN = line.split("=")[1].strip()
                elif line.startswith("MES1"):
                    MES1 = line.split("=")[1].strip()
                elif line.startswith("MES2"):
                    MES2 = line.split("=")[1].strip()
            return WIFI_SSID, WIFI_PASSWORD, LINE_TOKEN, MES1, MES2
    except Exception as e:
        print("Error reading settings file:", e)
        return None, None, None, None, None

def send_LineNotufy(line_message):
    buzzer_beep(1)  # 送信開始ブザー
    # Wi-Fi接続
    wlan = network.WLAN(network.STA_IF)  # ステーションモード（クライアント）でWi-Fiインターフェースを作成
    wlan.active(True)  # Wi-Fiを有効にする
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)  # Wi-Fiに接続する
        while not wlan.isconnected():
            pass
        print('connected to Wi-Fi')
    req = urequests.post('https://notify-api.line.me/api/notify', headers=line_header, data=line_message)
    req.close()
    # NTPサーバーから時刻を取得して同期
    sync_time()
    buzzer_beep(3)  # 送信完了ブザー
    led_warning(10)  # 送信完了LED

## NTPサーバーから時刻を取得
def sync_time():
    try:
        # NTPサーバーから時刻を取得
        ntptime.host = NTP_SERVER
        ntptime.settime()
        # 取得した時刻をUTCからJST（日本標準時）に変換
        utc_time = localtime()
        jst_time = mktime(utc_time) + 9 * 3600  # 9時間（JSTとUTCの時差）を加算
        local_time = localtime(jst_time)
        print("Synced time:", local_time)
        return local_time
    except Exception as e:
        print("sync_time error:", str(e))
        led_warning(5)
        buzzer_beep(5)
        sys.exit()

# ブザーを鳴らす
def buzzer_beep(qty):
    for i in range(qty):
        if i > 0:
            sleep(0.05)
        buzzer_pin.on()
        sleep(0.1)
        buzzer_pin.off()

# オンボードLEDを点滅させる
def led_warning(qty):
    for i in range(qty):
        if i > 0:
            sleep(0.1)
        onboard_led.on()
        led.on()
        sleep(0.1)
        onboard_led.off()
        led.off()

# NTPサーバー
NTP_SERVER = "ntp.nict.jp"

# ブートセルボタン
bootsel_sw = rp2.bootsel_button

# センサー
pin1 = Pin(15, Pin.IN, Pin.PULL_UP)
pin2 = Pin(13, Pin.IN, Pin.PULL_UP)

# ONの状態はどっち？
PIN1_ON = 0
PIN2_ON = 1

# PINの状態 OFF->ONの時だけ動くようにする(ONのままだと動作しないこと)
PIN1_STATUS = PIN1_ON
PIN2_STATUS = PIN2_ON

# ブザー
buzzer_pin = Pin(14, Pin.OUT)

# LED
onboard_led = Pin("LED", Pin.OUT)
led = Pin(12, Pin.OUT)

# 設定をファイルから読み込む
WIFI_SSID, WIFI_PASSWORD, LINE_TOKEN, MES1, MES2 = read_settings()

# LAN接続
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
line_header = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer ' + LINE_TOKEN
}

# NTPサーバーから時刻を取得して同期
sync_time()

while True:
    # オンボードLEDを点灯
    led_warning(1)

    if not wlan.isconnected():
        while not wlan.isconnected():
            print('connecting...')
            led_warning(5)
            sleep(1)
        print('Wi-Fi connected.')
        sleep(1)

    now_date = ""
    now_time = ""
    retry_limit = 3
    retry_count = 0

    while retry_count < retry_limit:
        try:
            time_now = time()  # 現在時刻を取得
            jst_time_now = time_now + 9 * 3600  # JSTに変換
            year, month, day, hour, minute, second, *_ = localtime(jst_time_now)
            now_date = "{:02d}/{:02d}/{:02d}".format(year, month, day)
            now_time = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
        except Exception as e:
            print("get_time error:", str(e))
            retry_count += 1
            if retry_count < retry_limit:
                print("Retrying... (Retry count: {})".format(retry_count))
                led_warning(5)
            else:
                print("Retry limit exceeded. Exiting.")
                led_warning(10)
                break  # ループを抜ける
        else:
            break  # 成功したらループを抜ける

    # 次回のLINE通知の許可時間（この時間までは送信しない）
    if 'nextLineTime1' not in globals():
        nextLineTime1 = time_now
    if 'nextLineTime2' not in globals():
        nextLineTime2 = time_now

    # この時点のピンの状態で動作させる
    PIN1_NOW = pin1()
    PIN2_NOW = pin2()

    # ブートセルボタンが押された
    if bootsel_sw() == 1:
        send_LineNotufy("message=" + "test")
        while bootsel_sw() == 1:
            led_warning(3)
            buzzer_beep(1)
            sleep(5)

    # PIN1動作
    if PIN1_STATUS != PIN1_ON and PIN1_NOW == PIN1_ON:
        if time_now > nextLineTime1:
            send_LineNotufy("message=" + MES1)
        else:
            year, month, day, hour, minute, second, *_ = localtime(nextLineTime1 + 9 * 3600)
            next_time = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
            print("Not yet time for next notify. After:", next_time)

    # PIN2動作
    if PIN2_STATUS != PIN2_ON and PIN2_NOW == PIN2_ON:
        if time_now > nextLineTime2:
            send_LineNotufy("message=" + MES2)
        else:
            year, month, day, hour, minute, second, *_ = localtime(nextLineTime2 + 9 * 3600)
            next_time = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
            print("Not yet time for next notify. After:", next_time)

    # 今回動作のピンの状態をキープ
    PIN1_STATUS = PIN1_NOW
    PIN2_STATUS = PIN2_NOW

    # 時計表示
    print_str = now_date + " " + now_time
    print(print_str)
    sleep(1.0)  # ここが長いとブートセルボタンチョン押しが検知できない
