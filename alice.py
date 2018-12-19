import logging
from sys import stdout
from argparse import ArgumentParser
from alice import WebApplication


def init_logger(file_path):
    if file_path is not None:
        handler = logging.FileHandler(file_path)
    else:
        handler = logging.StreamHandler(stdout)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger('alice')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


def main():
    parser = ArgumentParser()
    parser.add_argument("--socket")
    parser.add_argument("--log", default=None)
    args = parser.parse_args()
    init_logger(args.log)
    WebApplication().run(args.socket)


if __name__ == '__main__':
    main()
