#!/bin/bash
exec gunicorn --bind 0.0.0.0:5000 --workers $SV_WORKERS app:app