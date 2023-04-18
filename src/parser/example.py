from utils import setup_logging
import logging
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", default=8000, type=int, dest="first")
    parser.add_argument("--second", default="0.0.0.0", type=str, dest="second")
    return vars(parser.parse_args())


def main(args):
    print(args)
    logging.info("Run the script")
    # put you code here


if __name__ == "__main__":
    setup_logging("log.txt")
    args = parse_args()
    main(args)