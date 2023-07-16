"""
Загрузка содержимого csv файлов в ClickHouse

Необходимые переменные окружения:
 - CH_CLUSTER_ID
 - CH_USERNAME
 - CH_PASSWORD
 - CH_DB
 - AWS_ACCESS_KEY_ID
 - AWS_DEFAULT_REGION
 - AWS_SECRET_ACCESS_KEY
"""
from clickhouse_driver import Client
import boto3
import os
from urllib.parse import urljoin
import logging

import argparse

S3_BUCKET="dreamparser"
TABLENAME = "raw"

_logger = logging.getLogger(__file__)


def creat_table(client: Client):
    s = f"""
            CREATE TABLE IF NOT EXISTS {TABLENAME} (
                title TEXT,
                company TEXT,
                country Nullable(TEXT),
                location Nullable(TEXT),
                salary Nullable(TEXT),
                source TEXT,
                link TEXT,
                date DATE,
                company_field Nullable(TEXT),
                description Nullable(TEXT),
                skills Nullable(TEXT),
                job_type Nullable(TEXT)
            ) ENGINE=ReplacingMergeTree(date)
            ORDER BY (title, company, source, link);
            """
    client.execute(s)


def setup_logging(logfile=None, loglevel="INFO"):
    """

    :param logfile:
    :param loglevel:
    :return:
    """

    loglevel = getattr(logging, loglevel)

    logger = logging.getLogger()
    logger.setLevel(loglevel)
    fmt = '%(asctime)s: %(levelname)s: %(filename)s: ' + \
          '%(funcName)s(): %(lineno)d: %(message)s'
    formatter = logging.Formatter(fmt)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(loglevel)
    logger.addHandler(ch)

    if logfile is not None:
        fh = logging.FileHandler(filename=logfile)
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def get_ch_client():
    """
    Initialize ClickHouse client
    :return:
    """
    return Client(
        host=os.environ["CH_CLUSTER_URL"],
        user=os.environ["CH_USERNAME"],
        password=os.environ["CH_PASSWORD"],
        database=os.environ["CH_DB"],
        secure=True)


def get_s3_objects():
    endpoint_url = 'https://storage.yandexcloud.net'
    session = boto3.session.Session()
    s3_client = session.client(service_name='s3', endpoint_url=endpoint_url)
    try:
        r = s3_client.list_objects(Bucket=S3_BUCKET)
    except Exception as err:
        _logger.error("Could not get list of objects")
        return []

    return ["/".join([endpoint_url, S3_BUCKET, el["Key"]])  for el in r["Contents"]]


def main(date):
    objects = get_s3_objects()
    ch_client=get_ch_client()

    #creat_table(ch_client)

    for file in objects:
        _logger.info("Upload S3 object %s", file)

        bucket_url = "/".join(["https://storage.yandexcloud.net", S3_BUCKET])
        file_url = urljoin(bucket_url, file)
        query = "INSERT INTO {:s} SELECT * FROM s3('{:s}', '{:s}', '{:s}')" \
                 .format(TABLENAME, file_url, os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
        _logger.debug(query)
        try:
            ch_client.execute(query)
        except Exception as err:
            _logger.error(repr(err))

    ch_client.execute(f"""OPTIMIZE TABLE {TABLENAME} FINAL DEDUPLICATE""")
    cnt = ch_client.execute(f"SELECT COUNT(*) FROM {TABLENAME}")[0][0]
    _logger.info("CLICKHOUSE WERE DEDUPLICATED")
    _logger.info("NOW COUNT: %d", cnt)


if __name__ == "__main__":
    setup_logging("upload_ch.log", "INFO")

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", type=str, default=None, help="")
    args = vars(parser.parse_args())

    main(args["date"])