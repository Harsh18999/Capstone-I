import psycopg2

conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
#$env:conn_str = cockroachdb://myproject20.com:<ZNfo9DxeFp-WoNzpTDJPmg>@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full
conn_str="postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full"
