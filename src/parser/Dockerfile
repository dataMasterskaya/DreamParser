FROM python:3.9

RUN apt-get update
RUN apt-get install -y xvfb xserver-xephyr
RUN apt-get install -y chromium

RUN pip install selenium requests pyvirtualdisplay lxml bs4

COPY . /app

WORKDIR /app

CMD ["python", "vseti.py"]