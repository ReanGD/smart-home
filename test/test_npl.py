import unittest
from npl import Morphology
from etc import all_entitis


class TestNPL(unittest.TestCase):
    phrases = [
        ['Включи свет в коридоре',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'hall'}],
        ['Зажги лампочку на кухне',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'kitchen'}],
        ['Вруби люстру в зале',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'livingroom'}],
        ['Выключи освещение в туалете',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'restroom'}],
        ['Выруби телевизор в спальне',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'livingroom'}],
        ['Включи пожалуйста колонку в детской',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'playroom'}],
        ['Зажги свет в ванной',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'bathroom'}],
        ['Вруби лампочку в прихожей',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'hall'}],
        ['Телевизор выключи в игровой',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'playroom'}],
        ['Выруби музыку в большой комнате',
         {'device_action': 'turn_off', 'device': 'music', 'place': 'livingroom'}],
        ['Включи колонку в маленькой комнате',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'playroom'}],
        ['Зажги везде лампочки',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'all'}],
        ['Вруби в доме музыку',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'all'}],
        ['Выключи во всем доме освещение',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'all'}],
        ['Выруби в квартире телевизор',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'all'}],
        ['Включи во всей квартире музыку',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'all'}],
        ['Зажги тут свет',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'here'}],
        ['Вруби здесь телевизор',
         {'device_action': 'turn_on', 'device': 'tv', 'place': 'here'}],
        ['Выключи во второй комнате освещение',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'playroom'}],
    ]

    def setUp(self):
        self.morph = Morphology(all_entitis)

    def test_npl(self):
        for phrase, expect in TestNPL.phrases:
            result = self.morph.analyze(phrase)
            if 'unknown' in result:
                del result['unknown']

            self.assertEqual(result, expect)
