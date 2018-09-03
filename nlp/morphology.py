import pymorphy2


class Morphology(object):
    def __init__(self, entitis):
        self._morph = pymorphy2.MorphAnalyzer()
        self._entitis = {key: Entity(self, entity) for key, entity in entitis.items()}

    @staticmethod
    def tokenize(text: str):
        return text.split(' ')

    def parse(self, text: str):
        for word in Morphology.tokenize(text):
            yield self._morph.parse(word)

    def analyze(self, text: str):
        nwords = [set(it.normal_form for it in self._morph.parse(word))
                  for word in Morphology.tokenize(text)]

        result = {}
        while len(nwords) != 0:
            max_num = 0
            max_name = None
            max_group = None
            for group, entity in self._entitis.items():
                name, num = entity.analyze(nwords)
                if num > max_num:
                    max_num = num
                    max_name = name
                    max_group = group

            if max_num == 0:
                if 'unknown' in result:
                    result['unknown'].append(nwords[0])
                else:
                    result['unknown'] = [nwords[0]]

                nwords = nwords[1:]
            else:
                nwords = nwords[max_num:]
                result[max_group] = max_name

        return result


class Expression(object):
    def __init__(self, morph: Morphology, text: str):
        self._nwords = [it[0].normal_form for it in morph.parse(text)]

    def analyze(self, nwords) -> int:
        if len(nwords) < len(self._nwords):
            return 0

        for ind, it in enumerate(self._nwords):
            if it not in nwords[ind]:
                return 0

        return len(self._nwords)


class Synonyms(object):
    def __init__(self, morph: Morphology, text_arr):
        self._expressions = [Expression(morph, text) for text in text_arr]

    def analyze(self, nwords) -> int:
        return max(expression.analyze(nwords) for expression in self._expressions)


class Entity(object):
    def __init__(self, morph: Morphology, raw_entities):
        self._synonyms = {key: Synonyms(morph, text_arr) for key, text_arr in raw_entities.items()}

    def analyze(self, nwords):
        max_name = None
        max_words_count = 0
        for name, synonyms in self._synonyms.items():
            words_count = synonyms.analyze(nwords)
            if words_count > max_words_count:
                max_name = name
                max_words_count = words_count

        return max_name, max_words_count
