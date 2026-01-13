FROM apache/airflow:2.7.1-python3.10

USER root

# 1. Системные зависимости и Docker CLI
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg lsb-release libpq-dev gcc && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Установка библиотек СИСТЕМНО (для всех пользователей)
# Мы выключаем режим пользователя, чтобы пакеты попали в /usr/local
RUN PIP_USER=false python3 -m pip install --no-cache-dir --upgrade pip && \
    PIP_USER=false python3 -m pip install --no-cache-dir \
    clickhouse-driver \
    psycopg2-binary \
    minio \
    redis \
    fastapi \
    uvicorn \
    streamlit \
    email-validator>=2.0.0 \
    requests \
    pandas \
    pyspark