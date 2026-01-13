import psycopg2
import time
import random
from faker import Faker

conn_params = {"host": "localhost", "database": "ecom_db", "user": "user", "password": "password", "port": "5432"}
fake = Faker()

def generate_staging_data():
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            while True:  # ЦИКЛ НАЧИНАЕТСЯ ТУТ
                # 1. Генерируем город
                city = fake.city()
                
                # 2. Логика цен: богатые и бедные города
                if city[0] in 'ABCDEFGH':
                    price = round(random.uniform(500, 2000), 2)
                else:
                    price = round(random.uniform(10, 300), 2)
                
                # 3. Вставляем данные, используя наши переменные (city и price)
                cur.execute("""
                    INSERT INTO staging_orders 
                    (order_id, user_id, user_name, user_city, product_id, product_name, product_category, price, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    random.randint(1000, 999999), 
                    random.randint(1, 50), 
                    fake.name(), 
                    city,  # Используем переменную!
                    random.randint(1, 10), 
                    f"Prod_{random.randint(1, 10)}", 
                    "Electronics",
                    price, # Используем переменную!
                    "completed"
                ))
                conn.commit()
                print(f"Raw order in staging: {city} - ${price}")
                time.sleep(1) # Ускорим до 1 сек для наглядности

if __name__ == "__main__":
    generate_staging_data()