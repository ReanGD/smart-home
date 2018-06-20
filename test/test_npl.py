import unittest
from npl import Morphology
from etc import all_entitis


class TestNPL(unittest.TestCase):
    phrases = [
        ['Включи свет в коридоре',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'hall'}],
        ['Зажги лампочку на кухне',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'kitchen'}],
        ['Вруби люстру в зале',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'livingroom'}],
        ['Выключи освещение в туалете',
         {'room_device_action': 'turn_off', 'room_device': 'light', 'room': 'toilet'}],
        ['Выруби телевизор в спальне',
         {'room_device_action': 'turn_off', 'room_device': 'tv', 'room': 'livingroom'}],
        ['Включи пожалуйста колонку в детской',
         {'room_device_action': 'turn_on', 'room_device': 'music', 'room': 'playroom'}],
        ['Зажги свет в ванной',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'bathroom'}],
        ['Вруби лампочку в прихожей',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'hall'}],
        ['Телевизор выключи в игровой',
         {'room_device_action': 'turn_off', 'room_device': 'tv', 'room': 'playroom'}],
        ['Выруби музыку в большой комнате',
         {'room_device_action': 'turn_off', 'room_device': 'music', 'room': 'livingroom'}],
        ['Включи колонку в маленькой комнате',
         {'room_device_action': 'turn_on', 'room_device': 'music', 'room': 'playroom'}],
        ['Зажги везде лампочки',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'all'}],
        ['Вруби в доме музыку',
         {'room_device_action': 'turn_on', 'room_device': 'music', 'room': 'all'}],
        ['Выключи во всем доме освещение',
         {'room_device_action': 'turn_off', 'room_device': 'light', 'room': 'all'}],
        ['Выруби в квартире телевизор',
         {'room_device_action': 'turn_off', 'room_device': 'tv', 'room': 'all'}],
        ['Включи во всей квартире музыку',
         {'room_device_action': 'turn_on', 'room_device': 'music', 'room': 'all'}],
        ['Зажги тут свет',
         {'room_device_action': 'turn_on', 'room_device': 'light', 'room': 'here'}],
        ['Вруби здесь телевизор',
         {'room_device_action': 'turn_on', 'room_device': 'tv', 'room': 'here'}],
        ['Выключи во второй комнате освещение',
         {'room_device_action': 'turn_off', 'room_device': 'light', 'room': 'playroom'}],
    ]

    def setUp(self):
        self.morph = Morphology(all_entitis)

    def test_npl(self):
        for phrase, expect in TestNPL.phrases:
            result = self.morph.analyze(phrase)
            if 'unknown' in result:
                del result['unknown']

            self.assertEqual(result, expect)


if __name__ == '__main__':
    unittest.main()
