import psycopg2
import os
conn = psycopg2.connect(os.environ["conn_str"])
conn_str=os.environ["conn_str"]
