#!/usr/bin/python3

import datetime
import unittest
from unittest.mock import Mock, patch

import eloader


class TestEloader(unittest.TestCase):
    @patch("eloader.goeapi.GoeAPI")
    def setUp(self, mock_goe):
        instance = mock_goe.return_value
        instance.phases = 1
        instance.ampere = 6
        self.el = eloader.EloaderController()
        self.el.smax = Mock(eloader.smaxsmt.SolarmaxSmt)
        self.el.log = Mock()
        self.el.now = Mock()
        # mock mid-day
        self.el.now.return_value = datetime.datetime(2022, 5, 14, 12, 0, 0)

    def test_eloader_will_pause_when_not_enough_power(self):
        # pretent we are at 1.4kw at the loader
        self.el.goe.power = 1.4
        self.el.goe.phases = 1
        self.el.goe.amere = 6
        # pretent 1kw from solar
        self.el.smax.current_power = 1.0
        self.assertEqual(self.el.tick(), 360)
        self.assertTrue(self.el.goe.force_pause)
        self.el.log.assert_called_with("not enough power, forcing pause")

    def test_eloader_manual_overriden(self):
        test_cases = [
            # paused or no car, divergence does not matter
            {"pau": True, "con": True, "cur_amp": 10, "goe_amp": 16, "exp": False},
            {"pau": False, "con": False, "cur_amp": 10, "goe_amp": 16, "exp": False},
            {"pau": True, "con": False, "cur_amp": 10, "goe_amp": 16, "exp": False},
            # manual overriden by user
            {"pau": False, "con": True, "cur_amp": 10, "goe_amp": 16, "exp": True},
        ]
        for t in test_cases:
            self.el.goe.force_pause = t["pau"]
            self.el.goe.car_connected = t["con"]
            self.el.current_ampere = t["cur_amp"]
            self.el.goe.ampere = t["goe_amp"]
            self.el.goe.phases = 1
            self.assertEqual(self.el.manual_overriden(), t["exp"], msg=t)

    def test_eloader_night_time(self):
        # midday
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 12, 0, 0)
        self.assertEqual(self.el.night_time(), False)
        # deep night
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 23, 0, 0)
        self.assertEqual(self.el.night_time(), True)
        # sunrise Berlin 2022-05-07 is 05:24, sunset 20:41
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 5, 20, 0)
        self.assertEqual(self.el.night_time(), True)
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 5, 30, 0)
        self.assertEqual(self.el.night_time(), False)
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 20, 40, 0)
        self.assertEqual(self.el.night_time(), False)
        self.el.now.return_value = datetime.datetime(2022, 5, 7, 20, 45, 0)
        self.assertEqual(self.el.night_time(), True)
