import asyncio
import sys
import time

from machine import Pin


class LDR:
    def __init__(self, pin: int):
        self._value = 0
        self._value_lock = asyncio.Lock()

        self._pin = pin

    async def start(self, refresh_period: int):
        ldr = Pin(self._pin, Pin.IN)
        try:
            while True:
                try:
                    cycle_ts = time.ticks_us()

                    print("Drain capacitor...", end='')
                    # drain capacity
                    ldr.init(ldr.OUT)
                    ldr.low()
                    await asyncio.sleep(0.1)

                    print("OK\nCharge...", end='')
                    low_ts = time.ticks_us()
                    ldr.init(ldr.IN)
                    while ldr.value() == 0 and time.diff(time.ticks_us(), cycle_ts) < refresh_period * 1000000:
                        await asyncio.sleep_ms(10)
                    self.charge = time.ticks_diff(time.ticks_us(), low_ts)
                    print(f"OK ({self.charge}us)")

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    sys.print_exception(e)

                await asyncio.sleep(refresh_period)
        except asyncio.CancelledError:
            pass
        finally:
            ldr.init(ldr.IN)

    @property
    def charge(self) -> int | None:
        return self._value

    @charge.setter
    def charge(self, v: float):
        self._value = v
