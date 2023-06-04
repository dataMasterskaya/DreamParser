FROM python:3.9

RUN apt-get update && \
    mkdir --parents /usr/local/share/ca-certificates/Yandex  && \
    wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" \
               --output-document /usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt && \
    chmod 655 /usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["upload_objects.py"]
