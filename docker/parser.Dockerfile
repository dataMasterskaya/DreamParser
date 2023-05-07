FROM python:3.9

RUN apt-get update && \
    apt-get install -y xvfb xserver-xephyr chromium

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt && \
    mv ./driver/chromedriver112 ./driver/chromedriver

CMD ["python", "app.py"]