from utils import setup_logging
from vseti import main as parse_vseti


def main():
    setup_logging()
    parse_vseti()


if __name__ == "__main__":
    main()