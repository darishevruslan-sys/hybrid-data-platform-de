FROM python:3.10-slim

# Устанавливаем системные зависимости для базы данных
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

# Ставим библиотеки напрямую
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    redis \
    psycopg2-binary \
    streamlit \
    email-validator \
    requests \
    pandas

# Копируем код приложений
COPY ./app ./app

# Открываем порты
EXPOSE 8000 8501
