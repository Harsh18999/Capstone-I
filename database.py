import psycopg2

conn = psycopg2.connect(
    dbname="project",
    user="MYPROJECT20.COM",
    password="ZNfo9DxeFp-WoNzpTDJPmg",
    host="almond-heron-1166.j77.cockroachlabs.cloud",
    port="26257",
    sslmode="verify-full",
    sslrootcert="/root.crt"
)
#$env:DATABASE_URL = "cockroachdb://myproject20.com:<ZNfo9DxeFp-WoNzpTDJPmg>@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full"
conn_str="postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=require&sslrootcert=root.crt"
