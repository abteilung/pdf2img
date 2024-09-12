FROM python:3.9

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/usr/src/app
ENV PYTHONUNBUFFERED=1

# Make sure the entrypoint script has the correct permissions
RUN chmod +x entrypoint.sh

# Use ENTRYPOINT instead of CMD
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]