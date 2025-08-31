FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /data
COPY alembic/ /app/alembic/
COPY bot/ /app/bot/
COPY app/ /app/app/
COPY alembic.ini main.py /app/

CMD ["sh", "-c", "alembic upgrade head && python main.py"]