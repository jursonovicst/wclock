{% args wclock, ldr, boardttemp %}<<<local>>>
P "board" temp={{ boardttemp }};40;57;; RPi Pico 2w board temperature
P "WClock" fg_b={{ wclock.brightness[0] }};;;0;255|bg_b={{ wclock.brightness[1] }};;;0;255 WClock properties
P "LRD" charging={{ ldr.charge }} LDR (us)