from fastapi import FastAPI

import psycopg2

from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(host='localhost', dbname='fastapi', user='postgres', password='1234',cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print('Connected to database')

except Exception as e:
    print(f'Error connecting to database: {e}')