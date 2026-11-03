FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r requirements.txt

COPY frontend/app.py .
COPY frontend/templates ./templates

EXPOSE 3000

CMD ["python", "app.py"]