FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgles2 libegl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000
EXPOSE 10000

# 1 worker + beberapa thread supaya hemat RAM (model & MediaPipe dimuat sekali)
CMD gunicorn -b 0.0.0.0:${PORT} -w 1 --threads 4 --timeout 120 app:app
