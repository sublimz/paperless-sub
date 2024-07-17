#!/bin/sh
cd /opt/paperless-dev2/src
../venv/bin/python3 ./manage.py runserver & \
../venv/bin/python3 ./manage.py document_consumer  & \
../venv/bin/celery --app paperless worker
