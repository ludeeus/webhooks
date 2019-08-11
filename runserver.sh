#!/usr/bin bash
cd /app
python3 setup.py install
python3 -u webhooks/server.py