FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN mkdir -p /app/data

ENV PYTHONPATH=/app/src
ENV DATABASE_PATH=/app/data/remediator.db

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "src"]
