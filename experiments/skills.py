import config
from skills import Skills


def run():
    obj = Skills(config.skills)
    print(obj.run('Наутилус'))