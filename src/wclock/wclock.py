import asyncio
import json
import math
import random
import sys

from machine import Timer

from ldr import LDR
from ntpsync import NTPSync
from .neopixel import Neopixel


class WClock:
    _WCLOCK_CONFIG = "wclock.json"

    @classmethod
    def xy2pos(cls, xy: tuple[int, int]) -> int:
        """
        Converts xy position to led position on strip.

        :param xy: tuple, upper left corner is (0,0), x is horizontal
        :return: led number on strip
        """

        assert len(xy) == 2, f"invalid xy tuple: {xy}"
        x = xy[0]
        y = xy[1]
        assert 0 <= x <= 10 and 0 <= y <= 10, f"invalid position: {x}, {y}"

        if y % 2 == 0:
            return (10 - y) * 11 + 10 - x
        else:
            return (10 - y) * 11 + x

    _red = (255, 0, 0)
    _orange = (255, 50, 0)
    _yellow = (255, 100, 0)
    _green = (0, 255, 0)
    _blue = (0, 0, 255)
    _indigo = (100, 0, 90)
    _violet = (200, 0, 100)

    _alphabet = {'A': (4, 3),
                 'Á': (1, 4),
                 'B': (0, 10),
                 'C': (7, 1),
                 'D': (10, 4),
                 'E': (7, 0),
                 'É': (2, 0),
                 'F': (9, 2),
                 'G': (8, 0),
                 'H': (6, 0),
                 'I': (4, 5),
                 'Í': (4, 0),
                 'J': (7, 3),
                 'K': (1, 0),
                 'L': (0, 1),
                 'M': (10, 0),
                 'N': (0, 2),
                 'O': (3, 4),
                 'Ó': (2, 2),
                 'Ö': (2, 2),
                 'Ő': (10, 8),
                 'P': (4, 2),
                 'Q': (10, 2),
                 'R': (0, 0),
                 'S': (2, 6),
                 'T': (2, 1),
                 'U': (0, 9),
                 'Ú': (1, 3),
                 'Ü': (3, 1),
                 'Ű': (8, 2),
                 'V': (3, 3),
                 'W': (1, 2),
                 'X': (0, 5),
                 'Y': (9, 0),
                 'Z': (5, 0)}

    _w_before = {'EGY': [(7, 0), (8, 0), (9, 0)],
                 'KÉT': [(1, 0), (2, 0), (3, 0)],
                 'ÖT': [(1, 1), (2, 1)],
                 'TÍZ': [(3, 0), (4, 0), (5, 0)]
                 }

    _w_unit = {'PERC MÚLVA': [(4, 1), (5, 1), (6, 1), (7, 1), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3)],
               'PERCCEL MÚLT': [(4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (3, 2), (4, 2), (5, 2),
                                (6, 2)]}

    _w_part = {'NEGYED': [(5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4)],
               'FÉL': [(8, 3), (9, 3), (10, 3)],
               'HÁROMNEGYED': [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4)]}

    _w_hour = {'ÉJFÉL': [(6, 3), (7, 3), (8, 3), (9, 3), (10, 3)],
               'EGY': [(8, 5), (9, 5), (10, 5)],
               'KETTŐ': [(6, 8), (7, 8), (8, 8), (9, 8), (10, 8)],
               'HÁROM': [(5, 6), (6, 6), (7, 6), (8, 6), (9, 6)],
               'NÉGY': [(1, 7), (2, 7), (3, 7), (4, 7)],
               'ÖT': [(0, 8), (1, 8)],
               'HAT': [(1, 5), (2, 5), (3, 5)],
               'HÉT': [(4, 10), (5, 10), (6, 10)],
               'NYOLC': [(6, 7), (7, 7), (8, 7), (9, 7), (10, 7)],
               'KILENC': [(5, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9)],
               'TÍZ': [(6, 10), (7, 10), (8, 10)],
               'TIZENEGY': [(3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5)],
               'TIZENKETTŐ': [(1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8)],
               'DÉL': [(2, 9), (3, 9), (4, 9)]}

    _hour2text = {0: "TIZENKETTŐ",
                  1: "EGY",
                  2: "KETTŐ",
                  3: "HÁROM",
                  4: "NÉGY",
                  5: "ÖT",
                  6: "HAT",
                  7: "HÉT",
                  8: "NYOLC",
                  9: "KILENC",
                  10: "TÍZ",
                  11: "TIZENEGY",
                  12: "TIZENKETTŐ",
                  13: "EGY",
                  14: "KETTŐ",
                  15: "HÁROM",
                  16: "NÉGY",
                  17: "ÖT",
                  18: "HAT",
                  19: "HÉT",
                  20: "NYOLC",
                  21: "KILENC",
                  22: "TÍZ",
                  23: "TIZENEGY"}

    def __init__(self, pin: int, ldr: LDR) -> None:
        self._strip = None
        self._pin = pin
        self._flag = asyncio.ThreadSafeFlag()
        self._ldr = ldr
        self._config = None
        self.load()

    def load(self):
        with open(self._WCLOCK_CONFIG) as f:
            config = json.load(f)
            self._config = {"tz_offset": int(config["tz_offset"]),
                            "refresh_period": int(config["refresh_period"]),
                            "charge2brightness": {int(key): [int(value[0]), int(value[1])] for key, value in
                                                  config["charge2brightness"].items()}
                            }

    def save(self):
        config = {"tz_offset": self.tz_offset,
                  "refresh_period": self.refresh_period,
                  "charge2brightness": {str(charge): [brightness[0], brightness[1]] for charge, brightness in
                                        self.charge2brightness.items()}
                  }
        with open(self._WCLOCK_CONFIG, "w") as f:
            json.dump(config, f)

    @property
    def tz_offset(self):
        return self._config['tz_offset']

    @property
    def refresh_period(self):
        return self._config['refresh_period']

    @property
    def charge2brightness(self) -> dict[int, tuple[int, int]]:
        return self._config['charge2brightness']

    @charge2brightness.setter
    def charge2brightness(self, ch2br: dict[int, tuple[int, int]]):
        assert True  # TODO: implement check
        self._config['charge2brightness'] = ch2br
        print(f"Update charge2brightness: {self._config['charge2brightness']}")
        self.save()

    # @property
    # def brightness(self) -> tuple[int, int]:
    #     charge_l = 0
    #     if self._ldr.charge is not None:
    #         for charge_h, brightness in sorted(self.charge2brightness.items()):
    #             if charge_l <= self._ldr.charge < charge_h:
    #                 return brightness
    #             charge_l = charge_h
    #     return 100, 2

    @staticmethod
    def _circle(charge: float, shape, charge_max: int, brightness_max: int) -> int:
        def base(x, r) -> float:
            def circle(x: float, r: float) -> float:
                assert r >= 1, f"Circle method assumes non smaller than 1 radius, got {r}"
                return -math.sqrt(r ** 2 - x ** 2)

            d = 0.5 + math.sqrt(r ** 2 - 0.5) / math.sqrt(2)
            return circle(x - d, r) + d

        return int(base(charge / charge_max, shape) * (brightness_max - 2) + 2)

    @staticmethod
    def _log(charge: float, charge_max: int, brightness_max: int) -> int:
        return brightness_max - int(math.log(charge, charge_max) * (brightness_max - 2))

    @staticmethod
    def _ch2br(charge: float) -> int:
        chargemax = 1000000
        brightnessmax = 255
        if charge is None or charge < 1:
            return 255
        elif charge > chargemax:
            return 2

        return WClock._circle(charge, 2, chargemax, brightnessmax)
        # return WClock._log(charge, chargemax, brightnessmax)

    @property
    def brightness(self) -> tuple[int, int]:

        charge = self._ldr.charge
        return self._ch2br(charge), int(self._ch2br(charge) * 0.10)

    async def start(self):
        self._strip = Neopixel(11 * 11, 1, self._pin, "GRB")
        await self.colorwave(1)
        try:
            timer = Timer(period=self.refresh_period * 1000, mode=Timer.PERIODIC, callback=self._tick)
            while True:
                try:
                    print("Display...", end='')
                    await self.timecolor()
                    print(f"OK {self.brightness}")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    sys.print_exception(e)

                await self._flag.wait()
        except asyncio.CancelledError:
            pass
        finally:
            timer.deinit()
            self._strip.clear()
            self._strip = None

    def _tick(self, t: Timer):
        self._flag.set()

    async def colorwave(self, n: int = 1) -> None:
        """
        Color wave animation
        :param n: number of waves
        """
        colors_rgb = [self._red, self._orange, self._yellow, self._green, self._blue, self._indigo, self._violet]

        colors = colors_rgb

        step = round(self._strip.num_leds / len(colors))
        current_pixel = 0
        self._strip.brightness(50)

        for color1, color2 in zip(colors, colors[1:]):
            self._strip.set_pixel_line_gradient(current_pixel, current_pixel + step, color1, color2)
            current_pixel += step

        self._strip.set_pixel_line_gradient(current_pixel, 11 * 11 - 1, self._violet, self._red)

        for i in range(n * self._strip.num_leds):
            self._strip.rotate_right(1)
            await asyncio.sleep(0.042)
            self._strip.show()

    def szia(self, names: list[str]) -> None:
        """
        Greetings
        :param names: list of names, from which one is chosen randomly
        :return:
        """
        self.print(f"Szia {names[random.randint(0, len(names) - 1)]}", (255, 255, 255))

    def set_pixel(self, xy: tuple[int, int], rgb_w: tuple[int, int, int], how_bright=None) -> None:
        """
        Set pixel fo xy coordinates.
        """
        self._strip.set_pixel(self.xy2pos(xy), rgb_w, how_bright)

    async def print(self, text: str, color: tuple[int, int, int] = (255, 255, 255), freq: float = 1) -> None:
        """
        Prints text by flashing its characters.
        :param text: text to print
        :param color: color
        :param freq: flashing frequency (Hz)
        :return:
        """
        for c in text.upper():
            self._strip.clear()
            if c == ' ':
                pass
            else:
                pos = self.xy2pos(self._alphabet[c])
                self._strip.set_pixel(pos, color)
            self._strip.show()
            await asyncio.sleep(1 / freq)

    async def timecolor(self) -> None:
        colors_rgb = [self._red, self._orange, self._yellow, self._green, self._blue, self._indigo, self._violet]

        colors = colors_rgb

        step = round(self._strip.num_leds / len(colors))
        current_pixel = 0

        for color1, color2 in zip(colors, colors[1:]):
            self._strip.set_pixel_line_gradient(current_pixel, current_pixel + step, color1, color2, self.brightness[1])
            current_pixel += step
        self._strip.set_pixel_line_gradient(current_pixel, 11 * 11 - 1, self._violet, self._red, self.brightness[1])

        await self.time()

    async def time(self) -> None:
        """
        Display current time.
        :return:
        """
        d, d, d, d, hour, minute, d, d = NTPSync.localTime(self.tz_offset)

        text = []

        if minute == 0:
            text = []
        elif minute == 1:
            text = [self._w_before['EGY'], self._w_unit['PERCCEL MÚLT']]
        elif minute == 2:
            text = [self._w_before['KÉT'], self._w_unit['PERCCEL MÚLT']]
        elif 3 <= minute <= 7:
            text = [self._w_before['ÖT'], self._w_unit['PERCCEL MÚLT']]
        elif 8 <= minute <= 12:
            text = [self._w_before['TÍZ'], self._w_unit['PERCCEL MÚLT']]
        elif minute == 13:
            text = [self._w_before['KÉT'], self._w_unit['PERC MÚLVA'], self._w_part['NEGYED']]
        elif minute == 14:
            text = [self._w_before['EGY'], self._w_unit['PERC MÚLVA'], self._w_part['NEGYED']]
        elif minute == 15:
            text = [self._w_part['NEGYED']]
        elif minute == 16:
            text = [self._w_before['EGY'], self._w_unit['PERCCEL MÚLT'], self._w_part['NEGYED']]
        elif minute == 17:
            text = [self._w_before['KÉT'], self._w_unit['PERCCEL MÚLT'], self._w_part['NEGYED']]
        elif 18 <= minute <= 15 + 7:
            text = [self._w_before['ÖT'], self._w_unit['PERCCEL MÚLT'], self._w_part['NEGYED']]
        elif 15 + 8 <= minute <= 27:
            text = [self._w_before['ÖT'], self._w_unit['PERC MÚLVA'], self._w_part['FÉL']]
        elif minute == 28:
            text = [self._w_before['KÉT'], self._w_unit['PERC MÚLVA'], self._w_part['FÉL']]
        elif minute == 29:
            text = [self._w_before['EGY'], self._w_unit['PERC MÚLVA'], self._w_part['FÉL']]
        elif minute == 30:
            text = [self._w_part['FÉL']]
        elif minute == 31:
            text = [self._w_before['EGY'], self._w_unit['PERCCEL MÚLT'], self._w_part['FÉL']]
        elif minute == 32:
            text = [self._w_before['KÉT'], self._w_unit['PERCCEL MÚLT'], self._w_part['FÉL']]
        elif 33 <= minute <= 30 + 7:
            text = [self._w_before['ÖT'], self._w_unit['PERCCEL MÚLT'], self._w_part['FÉL']]
        elif 30 + 8 <= minute <= 42:
            text = [self._w_before['ÖT'], self._w_unit['PERC MÚLVA'], self._w_part['HÁROMNEGYED']]
        elif minute == 43:
            text = [self._w_before['KÉT'], self._w_unit['PERC MÚLVA'], self._w_part['HÁROMNEGYED']]
        elif minute == 44:
            text = [self._w_before['EGY'], self._w_unit['PERC MÚLVA'], self._w_part['HÁROMNEGYED']]
        elif minute == 45:
            text = [self._w_part['HÁROMNEGYED']]
        elif minute == 46:
            text = [self._w_before['EGY'], self._w_unit['PERCCEL MÚLT'], self._w_part['HÁROMNEGYED']]
        elif minute == 47:
            text = [self._w_before['KÉT'], self._w_unit['PERCCEL MÚLT'], self._w_part['HÁROMNEGYED']]
        elif 48 <= minute <= 45 + 7:
            text = [self._w_before['TÍZ'], self._w_unit['PERC MÚLVA']]
        elif 45 + 8 <= minute <= 57:
            text = [self._w_before['ÖT'], self._w_unit['PERC MÚLVA']]
        elif minute == 58:
            text = [self._w_before['KÉT'], self._w_unit['PERC MÚLVA']]
        elif minute == 59:
            text = [self._w_before['EGY'], self._w_unit['PERC MÚLVA']]

        if hour == 0 and minute <= 12 or hour == 23 and minute >= 48:
            text.append(self._w_hour["ÉJFÉL"])
        elif hour == 12 and minute <= 12 or hour == 11 and minute >= 48:
            text.append(self._w_hour["DÉL"])
        else:
            if minute <= 12:
                text.append(self._w_hour[self._hour2text[hour]])
            elif minute >= 13:
                text.append(self._w_hour[self._hour2text[(hour + 1) % 24]])

        for xys in text:
            for xy in xys:
                self.set_pixel(xy, (100, 100, 100), self.brightness[0])
        self._strip.show()
