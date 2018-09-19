import pytest
from nlp import Morphology
from etc import all_entitis


class TestNLP:
    def setup(self):
        self.morph = Morphology(all_entitis)

    @pytest.mark.parametrize("phrase,expect", [
        pytest.param('Включи свет в коридоре',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'hall'},
         id='turn_on light hall'),
        pytest.param('Зажги лампочку на кухне',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'kitchen'},
         id='turn_on light kitchen'),
        pytest.param('Вруби люстру в зале',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'livingroom'},
         id='turn_on light livingroom'),
        pytest.param('Выключи освещение в туалете',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'restroom'},
         id='turn_off light restroom'),
        pytest.param('Выруби телевизор в спальне',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'livingroom'},
         id='turn_off tv livingroom'),
        pytest.param('Включи пожалуйста колонку в детской',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'playroom'},
         id='turn_on music playroom'),
        pytest.param('Зажги свет в ванной',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'bathroom'},
         id='turn_on light bathroom'),
        pytest.param('Вруби лампочку в прихожей',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'hall'},
         id='turn_on light hall'),
        pytest.param('Телевизор выключи в игровой',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'playroom'},
         id='turn_off tv playroom'),
        pytest.param('Выруби музыку в большой комнате',
         {'device_action': 'turn_off', 'device': 'music', 'place': 'livingroom'},
         id='turn_off music livingroom'),
        pytest.param('Включи колонку в маленькой комнате',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'playroom'},
         id='turn_on music playroom'),
        pytest.param('Зажги везде лампочки',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'all'},
         id='turn_on light all'),
        pytest.param('Вруби в доме музыку',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'all'},
         id='turn_on music all'),
        pytest.param('Выключи во всем доме освещение',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'all'},
         id='turn_off light all'),
        pytest.param('Выруби в квартире телевизор',
         {'device_action': 'turn_off', 'device': 'tv', 'place': 'all'},
         id='turn_off tv all'),
        pytest.param('Включи во всей квартире музыку',
         {'device_action': 'turn_on', 'device': 'music', 'place': 'all'},
         id='turn_on music all'),
        pytest.param('Зажги тут свет',
         {'device_action': 'turn_on', 'device': 'light', 'place': 'here'},
         id='turn_on light here'),
        pytest.param('Вруби здесь телевизор',
         {'device_action': 'turn_on', 'device': 'tv', 'place': 'here'},
         id='turn_on tv here'),
        pytest.param('Выключи во второй комнате освещение',
         {'device_action': 'turn_off', 'device': 'light', 'place': 'playroom'},
         id='turn_off light playroom'),
    ])
    def test_nlp(self, phrase, expect):
        result = self.morph.analyze(phrase)
        if 'unknown' in result:
            del result['unknown']

        assert result == expect
