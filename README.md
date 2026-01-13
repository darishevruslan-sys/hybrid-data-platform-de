# End-to-End Hybrid Data Platform (Lambda Architecture)

Спроектированная и реализованная с нуля платформа сбора, хранения и анализа данных об интернет-заказах. Проект демонстрирует принципы работы современных Data Lake и DWH решений.

## 🏗 Архитектура
Проект построен на принципах **Lambda Architecture**:
- **Batch Layer (Spark):** Тяжелая обработка исторических данных в формате Parquet.
- **Speed Layer (Airflow + Redis):** Оперативный расчет метрик (Revenue) "на лету".
- **Serving Layer (FastAPI):** Единая точка доступа к данным для фронтенда.


### Архитектура проекта

```mermaid
graph TD
    subgraph "External Sources"
        Gen[Python Generator] -->|Insert| PG_SRC[(Postgres Source)]
    end

    subgraph "Data Lake & Processing"
        PG_SRC -->|Python ETL| Lake[(MinIO S3 Lake)]
        Lake -->|PySpark| Spark[Apache Spark]
        Spark -->|Aggregates| CH[(ClickHouse OLAP)]
    end

    subgraph "DWH (Data Vault 2.0)"
        PG_SRC -->|Airflow DAG| DV[(Postgres DWH)]
    end

    subgraph "Serving Layer"
        DV -->|History| API[FastAPI]
        CH -->|Metrics| API
        API -->|JSON| UI[Streamlit / Grafana]
    end
```

### Технологический стек:
- **Оркестрация:** Apache Airflow
- **Обработка данных:** Apache Spark (PySpark)
- **Хранилище (DWH):** PostgreSQL (Data Vault 2.0 methodology)
- **OLAP:** ClickHouse
- **Data Lake:** MinIO (S3 compatible)
- **Кэш:** Redis
- **Визуализация:** Grafana, Streamlit
- **Инфраструктура:** Docker, Docker Compose

## 📊 Визуализация данных (Grafana)
На дашборде отображаются результаты работы Spark-аналитики: средний чек в зависимости от города проживания пользователя.

![Grafana Dashboard](./images/grafana_dashboard.png)

## 🚀 Как запустить
1. Клонируйте репозиторий.
2. Создайте файл `.env` и добавьте туда `TELEGRAM_TOKEN`.
3. Запустите платформу:
   ```bash
   docker-compose up -d --build
4. Запустите генератор данных:
    python generator.py


### 📊 Ключевые фичи
    Data Vault 2.0: Гибкая модель данных с Hubs, Links и Satellites.
    Compaction: Оптимизация хранения путем конвертации сырых JSON в сжатый Parquet через Spark.
    Monitoring: Уведомления о статусе ETL-процессов в Telegram.
    Real-time API: FastAPI эндпоинты для получения горячих данных из Redis.
    text

### Модель данных (Data Vault 2.0)

```mermaid
erDiagram
    HUB_USERS ||--o{ LINK_ORDERS : "user_hash_key"
    HUB_PRODUCTS ||--o{ LINK_ORDERS : "product_hash_key"
    HUB_USERS ||--|| SAT_USERS : "attributes"
    LINK_ORDERS ||--|| SAT_ORDER_DETAILS : "metrics"
```