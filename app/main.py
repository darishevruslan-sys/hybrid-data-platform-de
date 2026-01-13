from fastapi import FastAPI
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI(title="Data Platform API")

# Подключения
r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0)

def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database="ecom_db", user="user", password="password"
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/v1/revenue")
def get_revenue():
    # Забираем "горячую" метрику из Redis
    revenue = r.get("today_revenue")
    return {"total_revenue": float(revenue) if revenue else 0}

@app.get("/api/v1/user/{user_id}/history")
def get_user_history(user_id: int):
    # Достаем историю из Data Vault
    conn = get_pg_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT s.name, s.city, d.final_price, d.load_date
        FROM hub_users h
        JOIN sat_users s ON h.user_hash_key = s.user_hash_key
        JOIN link_orders l ON h.user_hash_key = l.user_hash_key
        JOIN sat_order_details d ON l.order_hash_key = d.order_hash_key
        WHERE h.user_id = %s
        ORDER BY d.load_date DESC
    """
    cur.execute(query, (user_id,))
    history = cur.fetchall()
    cur.close()
    conn.close()
    return {"user_id": user_id, "history": history}