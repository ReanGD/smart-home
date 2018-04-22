class Skills(object):
    def __init__(self, configs):
        self._skills = {cfg.name(): cfg.create_skill() for cfg in configs}

    def run(self, text):
        for skill in self._skills.values():
            if skill.run(text):
                return True

        return False
