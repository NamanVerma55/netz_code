import psycopg2
# Update DB_CONFIG to use the new database

DB_CONFIG = {
    "host": "localhost",
    "dbname": "demo", #"dbname": "postgres"
    "user": "postgres",
    "password": "",
    "port": "5432"
}

def create_table(command):
    try:
        # Connect to the new database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create a table
        cursor.execute(command)
        conn.commit()
        print("Table created successfully.")

    except Exception as e:
        print(f"Error creating table: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()

def insert_user(username, password):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Insert a new user
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s);",
            (username, password)
        )
        conn.commit()
        print(f"User '{username}' inserted successfully.")

    except Exception as e:
        print(f"Error inserting user: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()


def create_database(db_name):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # Enable auto-commit to execute DDL commands
        cursor = conn.cursor()

        # Create the database
        cursor.execute(f"CREATE DATABASE {db_name};")
        print(f"Database '{db_name}' created successfully.")

    except Exception as e:
        print(f"Error creating database: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()



table1="""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
        """
table2="""CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    user_msg TEXT NOT NULL,
    ai_msg TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
"""


# Create 'demo' database
# create_database("demo")

# create_table(table1)
# create_table(table2)

# insert_user("user1", "password1")
# insert_user("user2", "password2")

