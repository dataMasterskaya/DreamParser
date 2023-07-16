from utils import setup_logging
from vseti import main as parse_vseti
from habr import main as parse_habr
from hh import main as parse_hh
import boto3
from botocore.exceptions import BotoCoreError
import os
import logging

_logger = logging.getLogger(__name__)


def upload_s3():
    """
    Upload data to S3 bucket
    :return:
    """
    _logger.info("Upload data to S3")
    session = boto3.session.Session()
    s3 = session.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net')
    bucket_name = "dreamparser"
    for el in os.scandir(os.path.join(os.path.dirname(__file__), "data")):
        if not el.name.endswith(".csv"):
            continue
        try:
            s3.upload_file(el.path, bucket_name, el.name)
        except BotoCoreError as err:
            _logger.error(err)


def main():
    _logger.info("Run parse process")
    parse_vseti(days=2)
    parse_habr()
    parse_hh()
    upload_s3()


if __name__ == "__main__":
    setup_logging(loglevel="INFO")
    main()
