#!/bin/sh
docker run --name scraper-$(date +%s) -it -v container-logs:/logs:rw --env-file scraper_secrets.env scraper "$@"
