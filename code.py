import time
import json
import wifi
from adafruit_magtag.magtag import MagTag
from adafruit_display_shapes.rect import Rect
from secrets import secrets
from adafruit_datetime import datetime, date
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests

lightOn = False

magtag = MagTag()

TRASH = "Müllabfuhr"
WIFI = "WLAN"
LIGHT = "Licht"

TRASH_INITIAL_Y = 45
TRASH_AMOUNT = 4
TRASH_STEPSIZE = 15


# Get time
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]
location = secrets.get("timezone", None)
TIME_URL = "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s&tz=%s" % (aio_username, aio_key, location)
TIME_URL += "&fmt=%25Y-%25m-%25d+%25H%3A%25M%3A%25S.%25L+%25j+%25u+%25z+%25Z"

wifi.radio.connect(secrets["ssid"], secrets["password"])
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
response = requests.get(TIME_URL)
currentTime = response.text[0:16]
battery = str(magtag.peripherals.battery)[0:3] + "V"
buttons = magtag.peripherals.buttons

def showNextTrashDates(lines):
    y = TRASH_INITIAL_Y
    for line in lines:
        trashType = line[0]
        trashDate = line[1][0:10]
        magtag.add_text(text_position=(10, y), text_color=0x000000, text_scale=1, text=trashType)
        magtag.add_text(text_position=(140, y), text_color=0x000000, text_scale=1, text=trashDate)
        y += TRASH_STEPSIZE

def showWifiPage():
    magtag.set_text(WIFI, headerTextBox)
    wifiqrdata = b"WIFI:T:WPA;S:"+secrets['ssid']+";P:"+secrets['password']+";;"
    magtag.graphics.qrcode(wifiqrdata, qr_size=2, x=100, y=30)

def clearContent():
    magtag.graphics.splash.append(Rect(0, 21, magtag.graphics.display.width, magtag.graphics.display.height - 36, fill=0xFFFFFF))

def readTrashCsv():
    with open("abfuhrkalender_2023.csv", "r", encoding="utf-8") as file:
        lines = file.readlines()[1:]
        transformed = [line.split(";")[0:2] for index, line in enumerate(lines)]
        return transformed

def timestampToDateStr(timestamp):
    datetimeObject = datetime.fromtimestamp(timestamp)
    day = ("0" + str(datetimeObject.day))[-2:]
    month = ("0" + str(datetimeObject.month))[-2:]
    return day + "." + month + "." + str(datetimeObject.year)

# order: Y for year, M for month, D for day
# Example dateStr = "2022-01-25"; delimeter = "-"; ["Y","M","D"]
def dateStringToTimestamp(dateStr, delimeter, order):
    try:
        dateArray = dateStr.split(delimeter)
        dayString = dateArray[order.index("D")]
        monthString = dateArray[order.index("M")]
        yearString = dateArray[order.index("Y")]
        dateObject = datetime.fromisoformat(yearString + "-" + monthString + "-" + dayString)
        return dateObject.timestamp()
    except:
        return 0

def dateFromLine(line):
    dateString = line[1][0:10]
    return dateStringToTimestamp(dateString, ".",["D","M","Y"])   

def getNextTrashDates(allEntries, now, maxAmount):
    index_pos_list = [ i for i in range(len(allEntries)) if dateFromLine(allEntries[i]) > now ]
    nextEntries = [allEntries[i] for i in index_pos_list]
    amountOfEntries = min(maxAmount, len(nextEntries))
    return nextEntries[0:amountOfEntries]

def showTrashPage():
    magtag.set_text(TRASH, headerTextBox)
    lines = readTrashCsv()
    now = dateStringToTimestamp(currentTime[0:10], "-",["Y","M","D"])
    nextEntries = getNextTrashDates(lines, now, TRASH_AMOUNT)
    showNextTrashDates(nextEntries)

currentTimestamp = dateStringToTimestamp(currentTime[0:10], "-",["Y","M","D"])
magtag.graphics.splash.append(Rect(0, magtag.graphics.display.height - 14, magtag.graphics.display.width, magtag.graphics.display.height, fill=0x0))
magtag.add_text(text= timestampToDateStr(currentTimestamp) + " " + currentTime[11:16], text_position=(197, 5), text_color=0x000000)
magtag.add_text(text=WIFI, text_position=(18, 120), text_color=0xFFFFFF)
magtag.add_text(text=TRASH, text_position=(75, 120), text_color=0xFFFFFF)
magtag.add_text(text=LIGHT, text_position=(233, 120), text_color=0xFFFFFF)
batteryBox = magtag.add_text(text= battery, text_position=(268, 16), text_color=0x000000)
headerTextBox = magtag.add_text(text_position=(10, 10), text_color=0x000000,text_scale=2)

showTrashPage()
while True:
    newBattery = str(magtag.peripherals.battery)[0:3] + "V"
    if battery != newBattery:
        battery = newBattery
        magtag.set_text(TRASH, batteryBox)

    if (magtag.peripherals.button_a_pressed):
        clearContent()
        showWifiPage()
        
    if (magtag.peripherals.button_b_pressed):
        clearContent()
        showTrashPage()

    if (magtag.peripherals.button_d_pressed):
        lightOn = not lightOn
        if (lightOn):
            magtag.peripherals.neopixels.fill((255, 255, 255))
        else:
            magtag.peripherals.neopixels.fill((0, 0, 0))
    magtag.refresh()
    time.sleep(1)