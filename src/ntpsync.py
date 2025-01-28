import asyncio
import json
import struct
import sys
import time

import usocket as socket
from machine import RTC


class NTPSync:
    _NTP_CONFIG = "ntp.json"
    # Sommerzeiten: 2021 bis 2037
    _dst_ranges = [(1616893200, 1635645600), (1648342800, 1667095200), (1679792400, 1698544800),
                   (1711846800, 1729994400), (1743296400, 1761444000), (1774746000, 1792893600),
                   (1806195600, 1824948000), (1837645200, 1856397600), (1869094800, 1887847200),
                   (1901149200, 1919296800), (1932598800, 1950746400), (1964048400, 1982800800),
                   (1995498000, 2014250400), (2026947600, 2045700000), (2058397200, 2077149600),
                   (2090451600, 2108599200), (2121901200, 2140048800)]

    @staticmethod
    # Funktion: Lokale Zeit mit Zeitumstellung ausgeben
    def localTime(tz_offset):
        dst_adjust = 0
        utc = time.time()
        # Prüfen ob Sommerzeit ist
        if any(lwr <= utc < upr for (lwr, upr) in NTPSync._dst_ranges): dst_adjust = 3600
        # Lokale Zeit ermitteln
        lt = time.gmtime(utc + (tz_offset * 3600) + dst_adjust)
        return (lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], 0)

    @staticmethod
    def getntptime(ntp_host: str) -> tuple[int, int, int, int, int, int, int, int]:
        EPOCH_YEAR = time.gmtime(0)[0]
        if EPOCH_YEAR == 2000:
            NTP_DELTA = 3155673600  # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        elif EPOCH_YEAR == 1970:
            NTP_DELTA = 2208988800  # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        else:
            raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

        ntp_query = bytearray(48)
        ntp_query[0] = 0x1B
        addr = socket.getaddrinfo(ntp_host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(ntp_query, addr)
            msg = s.recv(48)
            rt = time.gmtime(struct.unpack("!I", msg[40:44])[0] - NTP_DELTA)
        except:
            rt = (0, 0, 0, 0, 0, 0, 0)
        finally:
            s.close()
        return (rt[0], rt[1], rt[2], rt[6], rt[3], rt[4], rt[5], 0)

    def __init__(self):
        self._config = None
        self.load()

    def load(self):
        with open(self._NTP_CONFIG) as f:
            config = json.load(f)
            self._config = {"sync_period": int(config["sync_period"]),
                            "host": str(config["host"])}

    def save(self):
        config = {"sync_period": self._config["sync_period"],
                  "host": self._config["host"]}
        with open(self._NTP_CONFIG, "w") as f:
            json.dump(config)

    @property
    def sync_period(self):
        return self._config['sync_period']

    @property
    def host(self):
        return self._config['host']

    async def start_sync(self):
        try:
            while True:
                try:
                    print("NTP sync...", end='')
                    tm = self.getntptime(self.host)
                    RTC().datetime((tm[0], tm[1], tm[2], tm[3], tm[4], tm[5], tm[7], 0))
                    print(f"OK {tm}")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    sys.print_exception(e)

                await asyncio.sleep(self.sync_period)
        except asyncio.CancelledError:
            pass
