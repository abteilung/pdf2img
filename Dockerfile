FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

ENV PYTHONPATH=/app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]