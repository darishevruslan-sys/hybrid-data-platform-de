from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from clickhouse_driver import Client

# 1. Инициализация Spark с драйверами S3
spark = SparkSession.builder \
    .appName("DataLakeCompaction") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("fs.s3a.endpoint", "http://minio-datalake:9000") \
    .config("fs.s3a.access.key", "admin") \
    .config("fs.s3a.secret.key", "password") \
    .config("fs.s3a.path.style.access", "true") \
    .config("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

try:
    # 2. Читаем все сырые JSON из архива
    print("Reading raw JSON files from Lake...")
    df = spark.read.json("s3a://orders-archive/archive/*.json")
    
    if df.count() > 0:
        # 3. Сохраняем в формате PARQUET (Золотой стандарт Big Data)
        # Папка 'gold_parquet' будет создана автоматически
        output_path = "s3a://orders-archive/gold_parquet/"
        print(f"Compressing {df.count()} rows into Parquet...")
        
        df.write.mode("overwrite").parquet(output_path)
        print(f"✅ Success! Optimized data saved to {output_path}")

        # 4. Считаем финальную статику для ClickHouse (теперь из Parquet!)
        pq_df = spark.read.parquet(output_path)
        city_stats = pq_df.groupBy("user_city").agg(F.avg("price").alias("average_check")).collect()

        if city_stats:
            ch_client = Client(host="clickhouse_target", user='admin', password='admin')
            data_to_insert = [(row['user_city'], float(row['average_check'])) for row in city_stats]
            ch_client.execute('TRUNCATE TABLE default.spark_city_stats')
            ch_client.execute('INSERT INTO default.spark_city_stats (user_city, average_check) VALUES', data_to_insert)
            print(f"📊 ClickHouse updated from Parquet source.")
    else:
        print("No data to process.")

except Exception as e:
    print(f"❌ Error: {e}")

spark.stop()