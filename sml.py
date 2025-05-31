from typing import Callable, List, Optional

import datetime
from dataclasses import dataclass
import logging
import time

import serial

from smllib import SmlStreamReader, SmlFrame
from smllib.const import UNITS

# from smllib:const.py
_OBIS_POWER_CURRENT = "0100100700ff"
_OBIS_POWER_IN_TOTAL = "0100010800ff"
_OBIS_POWER_OUT_TOTAL = "0100020800ff"


@dataclass
class EnergyStats:
    current_power: int
    total_power_in: int
    total_power_out: int
    when: datetime.datetime

    def __init__(self, sml_frame: SmlFrame):
        obis_values = sml_frame.get_obis()
        for ov in obis_values:
            if ov.obis == _OBIS_POWER_CURRENT:
                self.current_power = ov.value
                assert UNITS[ov.unit] == "W"
            elif ov.obis == _OBIS_POWER_IN_TOTAL:
                self.total_power_in = ov.value
                assert UNITS[ov.unit] == "Wh"
            elif ov.obis == _OBIS_POWER_OUT_TOTAL:
                self.total_power_out = ov.value
                assert UNITS[ov.unit] == "Wh"
        self.when = datetime.datetime.now()


class EnergyMon:
    def __init__(self, serial_device: str = "/dev/ttyUSB0"):
        self._serial = serial.Serial(serial_device, 9600)
        self._current: Optional[EnergyStats] = None
        self._stream = SmlStreamReader()

    @property
    def current(self):
        return self._current

    def stop(self):
        self._serial.close()

    def read(self):
        while True:
            # we will always lack a little bit behind by just reading the first frame
            # but its just seconds so it should not matter
            data = self._serial.read(512)
            self._stream.add(data)
            sml_frame = self._stream.get_frame()
            if sml_frame is None:
                print("sml: no data")
                time.sleep(0.1)
                continue
            self._current = EnergyStats(sml_frame)
            print(f"got sml frame: {self._current}")
            return
