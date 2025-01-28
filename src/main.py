import asyncio
import time

import machine
import network

from config import config_load
from ldr import LDR
from microdot import Microdot, Request
from microdot.utemplate import Template
from ntpsync import NTPSync
from wclock import WClock
from wifi import WIFI_CONFIG, wifiapp


def myprint(*values: object, sep: str | None = " ", end: str | None = "\n") -> None:
    print(*values, sep=sep, end=end)


btmp_adcpin = 4
btmp_sensor = machine.ADC(btmp_adcpin)


def boardttemp() -> float:
    adc_value = btmp_sensor.read_u16()
    volt = (3.3 / 65535) * adc_value
    temperature = 27 - (volt - 0.706) / 0.001721
    return round(temperature, 1)


myprint(f"Booting")

# 0. LED
led = machine.Pin("LED", machine.Pin.OUT)
led.on()

# start measuring light environment
ldr = LDR(15)
ldr_task = asyncio.create_task(ldr.start(3))

# wclock
wclock = WClock(22, ldr)
wclock_task = asyncio.create_task(wclock.start())

# 1. WLAN-Verbindung herstellen
ssid, password, country = config_load(WIFI_CONFIG, 'ssid', 'password', 'country')
network.country(country)

# Try connecting to the given SSID
wlan = network.WLAN(network.STA_IF)
if not wlan.isconnected():
    myprint(f"Connecting to {ssid}...", end='')
    wlan.active(True)
    try:
        wlan.connect(ssid, password)
        for i in range(20):
            if wlan.status() == 3:
                break
            led.toggle()
            time.sleep(0.5)
        if not wlan.isconnected():
            raise Exception("Failed to connect")

        myprint(f"OK")
    except Exception as e:
        myprint(f"{e}, switch to AP mode...", end='')
        wlan.active(False)
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid='wclock', security=0)
        wlan.active(True)
        myprint(f"OK")

        wifiapp.run(port=80, debug=True)
        machine.reset()

# from here on, we have Internet
myprint(f"IP: {wlan.ifconfig()[0]}")

# start syncing time
ntp = NTPSync()
ntp_task = asyncio.create_task(ntp.start_sync())

# web
app = Microdot()
app.mount(wifiapp, url_prefix='/wifi')


@app.get("/")
async def index(request: Request):
    return await Template('index.html.tpl').render_async(wclock, ldr, boardttemp()), {'Content-Type': 'text/html'}


@app.post("/charge2brightness")
async def charge2brightness(request: Request):
    wclock.charge2brightness = {int(key): tuple(map(int, values[0].split(','))) for key, values in request.form.items()}


@app.get("/checkmk")
async def checkmk(request: Request):
    return await Template('checkmk.txt.tpl').render_async(wclock, ldr, boardttemp()), {'Content-Type': 'text/ascii'}


async def main():
    server = asyncio.create_task(app.start_server(port=80, debug=True))
    await server

    wclock_task.cancel()
    ntp_task.cancel()
    ldr_task.cancel()
    await wclock_task
    await ntp_task
    await ldr_task


asyncio.run(main())
