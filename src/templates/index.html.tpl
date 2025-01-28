{% args wclock, ldr, boardttemp %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WClock</title>
</head>
<body>

<h2>WiFi</h2>
<a href="/wifi/">Setup SSID...</a><br/>

<h2>Board</h2>
<table border="1">
    <tr>
        <td>RPi Pico temperature</td>
        <td>{{ boardttemp }}&deg;C</td>
    </tr>
</table>

<h2>WClock</h2>
<table border="1">
    <tr>
        <td>timezone offset</td>
        <td>{{ wclock.tz_offset }}h</td>
    </tr>
    <tr>
        <td>refresh period</td>
        <td>{{ wclock.refresh_period }}s</td>
    </tr>
    <tr>
        <td>FG brightness</td>
        <td>{{ wclock.brightness[0] }}</td>
    </tr>
    <tr>
        <td>BG brightness</td>
        <td>{{ wclock.brightness[1] }}</td>
    </tr>
</table>

<hr>

<form action="/charge2brightness" method="post">
    <table border="1">
        <tr>
            <th>Charge (&micro;s)</th>
            <th>FG/BG Brightness (<0-255>,<0-255>)</th>
        </tr>
        {% for key, values in sorted(wclock.charge2brightness.items()) %}
        <tr align="right">
            <td>-{{ key }}</td>
            <td><input type="text" id="{{ key }}" name="{{ key }}" value="{{ ','.join(map(str, values)) }}"></td>
        </tr>
        {% endfor %}
    </table>
    <input type="submit" value="Save">
</form>

<hr>

<form action="/time" method="post">
    <input type="submit" value="Refresh">
</form>

<h2>LDR</h2>

<table border="1">
    <tr>
        <td>charge</td>
        <td>{{ ldr.charge }}&micro;s</td>
    </tr>
</table>

</body>
</html>