FROM python:3.7

RUN mkdir -p /app

COPY setup.py /app/setup.py
COPY runserver.sh /app/runserver.sh
COPY webhook /app/webhook

ENTRYPOINT ["bash", "/app/runserver.sh"]