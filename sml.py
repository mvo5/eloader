from typing import Callable, List, Optional

import datetime
from dataclasses import dataclass
import logging
import time

import serial

import smllib.errors
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
        self._serial_device = serial_device
        self._current: Optional[EnergyStats] = None
        self._stream = SmlStreamReader()

    @property
    def current(self):
        return self._current

    def stop(self):
        # nothing
        pass

    def read(self):
        """
        Read will open the device and read a single sml frame,
        its not meant to use frequently.
        """
        with serial.Serial(self._serial_device, 9600) as ser:
            data = ser.read(512)
            self._stream.add(data)
            while True:
                try:
                    sml_frame = self._stream.get_frame()
                except smllib.errors.CrcError as e:
                    print(f"{type(e)}, keep reading")
                    sml_frame = None
                if sml_frame is None:
                    print("no sml_frame, keep reading")
                    data = ser.read(512)
                    self._stream.add(data)
                    continue
                self._current = EnergyStats(sml_frame)
                print(f"got sml frame: {self._current}")
                return
