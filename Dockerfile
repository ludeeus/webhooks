FROM python:3.7

RUN mkdir -p /app

COPY setup.py /app/setup.py
COPY runserver.sh /app/runserver.sh
COPY webhooks /app/webhooks

ENTRYPOINT ["bash", "/app/runserver.sh"]