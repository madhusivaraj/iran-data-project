FROM alpine:latest

# Extra APK's are for building numpy and pillow
RUN apk --no-cache update && \
    apk --no-cache add tor tesseract-ocr python3=3.6.4-r1 python3-dev=3.6.4-r1 musl-dev gcc zlib-dev jpeg-dev && \
    pip3 install --no-cache-dir --upgrade pip setuptools

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm -r /tmp/requirements.txt /root/.cache

COPY scraper /app/scraper
COPY scripts/main.py /app/
COPY scripts/start.sh /app/

VOLUME /logs
WORKDIR /app

ENTRYPOINT ["/bin/sh", "/app/start.sh"]
