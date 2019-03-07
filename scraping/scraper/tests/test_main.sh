#!/bin/sh
export $(cat scraper_secrets.env | xargs)
python3 scripts/main.py "$@"
