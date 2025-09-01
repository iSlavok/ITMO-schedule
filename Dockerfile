FROM python:3.13-slim

WORKDIR /src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY bot/ ./bot/
COPY alembic/ ./alembic/

COPY alembic.ini .
COPY main.py .

CMD ["sh", "-c", "alembic upgrade head && python -m main"]