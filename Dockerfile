FROM python:3.10-alpine
ENV PYTHONUNBUFFERED 1
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .