from utils import setup_logging
from vseti import main as parse_vseti
from habr import main as parse_habr
import boto3
from botocore.exceptions import BotoCoreError
import os
from dotenv import load_dotenv
import logging
from sanic import Sanic
from sanic.response import text

app = Sanic(__name__)

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


@app.after_server_start
async def after_server_start(app, loop):
    _logger.info(f"App listening at port {os.environ['PORT']}")


@app.route("/upload")
async def upload(request):
    _logger.info("Upload to S3")
    #parse_vseti(days=10)
    #parse_habr()
    upload_s3()
    return text("Upload to S3")

@app.route("/parse")
async def parse(request):
    _logger.info("Run parse functions")
    parse_vseti(days=10)
    #parse_habr()
    #upload_s3()
    return text("Parse VSeti")

@app.route("/")
async def main(request):
    ip = request.headers["X-Forwarded-For"]
    _logger.info(f"Request from {ip}")
    #parse_vseti(days=10)
    #parse_habr()
    #upload_s3()
    return text("Main page")


if __name__ == "__main__":
    setup_logging(loglevel="DEBUG")
    _logger.info("Run parse process")
    app.run(host='0.0.0.0', port=int(os.environ['PORT']), motd=False, access_log=True)