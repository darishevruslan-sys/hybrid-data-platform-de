import hashlib, json, io, psycopg2, redis, requests, os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from clickhouse_driver import Client
from minio import Minio

# --- ТВОИ НАСТРОЙКИ ТЕЛЕГРАМА ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_TOKEN = "8228197910:AAFHWEu6qKYpJwvdDxzP1RU9IlStuWEMUvc"
TELEGRAM_CHAT_ID = "817435154"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send telegram: {e}")

# --- ОСТАЛЬНЫЕ НАСТРОЙКИ ---
PG_CONN = "host=postgres_source dbname=ecom_db user=user password=password"
CH_HOST = "clickhouse_target"
MINIO_HOST = "minio-datalake:9000"

def get_hash(text):
    return hashlib.md5(str(text).encode()).hexdigest()

def load_to_vault():
    pg_conn = psycopg2.connect(PG_CONN)
    cur = pg_conn.cursor()
    cur.execute("SELECT * FROM staging_orders")
    rows = cur.fetchall()
    if not rows: return
    for r in rows:
        u_hkey = get_hash(r[1]); p_hkey = get_hash(r[4]); o_hkey = get_hash(r[0])
        now = datetime.now()
        cur.execute("INSERT INTO hub_users VALUES (%s, %s, %s, 'WEB') ON CONFLICT DO NOTHING", (u_hkey, r[1], now))
        cur.execute("INSERT INTO hub_products VALUES (%s, %s, %s, 'WEB') ON CONFLICT DO NOTHING", (p_hkey, r[4], now))
        cur.execute("INSERT INTO link_orders VALUES (%s, %s, %s, %s, 'WEB') ON CONFLICT DO NOTHING", (o_hkey, u_hkey, p_hkey, now))
        cur.execute("INSERT INTO sat_users VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (u_hkey, r[2], r[3], now))
        cur.execute("INSERT INTO sat_order_details VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (o_hkey, 1, r[7], r[8], now))
    cur.execute("TRUNCATE staging_orders")
    pg_conn.commit()
    cur.close(); pg_conn.close()

def load_to_mart():
    ch_client = Client(host=CH_HOST, user='admin', password='admin')
    result = ch_client.execute('SELECT MAX(created_at) FROM default.orders')
    max_dt = result[0][0] or datetime(1970, 1, 1)
    
    pg_conn = psycopg2.connect(PG_CONN)
    cur = pg_conn.cursor()
    query = """
        WITH latest_users AS (SELECT DISTINCT ON (user_hash_key) * FROM sat_users ORDER BY user_hash_key, load_date DESC)
        SELECT substring(l.order_hash_key::text, 1, 8), h_u.user_id, lu.name, lu.city, h_p.product_id,
               'Product_' || CAST(h_p.product_id AS TEXT), f.final_price, f.load_date
        FROM link_orders l
        JOIN hub_users h_u ON l.user_hash_key = h_u.user_hash_key
        JOIN latest_users lu ON h_u.user_hash_key = lu.user_hash_key
        JOIN hub_products h_p ON l.product_hash_key = h_p.product_hash_key
        JOIN sat_order_details f ON l.order_hash_key = f.order_hash_key
        WHERE f.load_date > %s
    """
    cur.execute(query, (max_dt,))
    data = cur.fetchall()
    
    if data:
        ch_client.execute('INSERT INTO default.orders VALUES', data)
        # Обновляем Redis
        r_client = redis.Redis(host="redis_hot_data", port=6379, db=0)
        batch_rev = sum(float(row[6]) for row in data)
        r_client.incrbyfloat("today_revenue", batch_rev)
        
        # ОТПРАВЛЯЕМ ТЕЛЕГРАМ!
        send_telegram_msg(f"✅ *ETL Success!*\nЗагружено строк: `{len(data)}` \nВыручка в пачке: `${batch_rev:,.2f}`")
    
    cur.close(); pg_conn.close()

def backup_to_minio():
    # ... (код бэкапа без изменений) ...
    pg_conn = psycopg2.connect(PG_CONN)
    cur = pg_conn.cursor()
    query = "SELECT h_u.user_id, lu.name, lu.city, f.final_price, 'Product_' || h_p.product_id FROM link_orders l JOIN hub_users h_u ON l.user_hash_key = h_u.user_hash_key JOIN sat_users lu ON h_u.user_hash_key = lu.user_hash_key JOIN hub_products h_p ON l.product_hash_key = h_p.product_hash_key JOIN sat_order_details f ON l.order_hash_key = f.order_hash_key WHERE f.load_date > now() - interval '5 minutes'"
    cur.execute(query)
    rows = cur.fetchall()
    if not rows: return
    m_client = Minio(MINIO_HOST, access_key="admin", secret_key="password", secure=False)
    keys = ['user_id', 'user_name', 'user_city', 'price', 'product_name']
    jsonl = ""
    for r in rows: jsonl += json.dumps(dict(zip(keys, r)), default=str) + "\n"
    filename = f"archive/backup_{datetime.now().strftime('%H%M%S')}.json"
    m_client.put_object("orders-archive", filename, io.BytesIO(jsonl.encode()), len(jsonl))
    cur.close(); pg_conn.close()

with DAG('1_core_data_vault_ingestion', start_date=datetime(2023, 1, 1), schedule_interval=timedelta(minutes=2), catchup=False) as dag:
    t1 = PythonOperator(task_id='load_to_vault', python_callable=load_to_vault)
    t2 = PythonOperator(task_id='update_clickhouse_mart', python_callable=load_to_mart)
    t3 = PythonOperator(task_id='backup_to_s3_lake', python_callable=backup_to_minio)
    t1 >> t2 >> t3