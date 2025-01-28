{% args ssid, password, country, path %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
</head>
<body>

<form action="{{ path }}" method="post">
  <label for="ssid">SSID:</label><br>
  <input type="text" id="ssid" name="ssid" value="{{ ssid }}"><br>
  <label for="password">Password:</label><br>
  <input type="password" id="password" name="password" value="{{ password }}"><br>
  <label for="country">Country:</label><br>
  <input type="text" id="country" name="country" value="{{ country }}"><br>
  <input type="submit" value="Save">
</form>

</body>
</html>