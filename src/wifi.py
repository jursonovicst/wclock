from config import config_load, config_save
from microdot import Microdot
from microdot.utemplate import Template

WIFI_CONFIG = "wifi.json"

wifiapp = Microdot()


@wifiapp.get("/")
async def wifi_get(request):
    return (await Template('wifi.html.tpl').render_async(*config_load(WIFI_CONFIG, 'ssid', 'password', 'country'),
                                                         request.path), {'Content-Type': 'text/html'})


@wifiapp.post('/')
async def wifi_set(request):
    assert 'ssid' in request.form and 'password' in request.form and 'country' in request.form, f"Invalid form data: {request.form}"
    config_save(WIFI_CONFIG, ssid=request.form['ssid'], password=request.form['password'],
                country=request.form['country'])
    request.app.shutdown()
    return 'The server is shutting down...'
