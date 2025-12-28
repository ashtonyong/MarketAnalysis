import pymysql
import os
from dotenv import load_dotenv

# Hardcode creds to be 100% sure we don't fail on path loading issues
host = 'cloudfinal-mysql-db.ce2nfvt6uyxm.us-east-1.rds.amazonaws.com'
user = 'admin'
password = 'YourStrongPassword123!'
dbname = 'cloud_db'

print(f"Connecting to {host} with user {user}...")

try:
    conn = pymysql.connect(host=host, user=user, password=password, database=dbname)
    print("Connected.")
    
    with conn.cursor() as cursor:
        # Check users table schema just in case
        cursor.execute("DESCRIBE users")
        print("Users table:", cursor.fetchall())

        print("Creating table 'files'...")
        sql = """
        CREATE TABLE IF NOT EXISTS files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            s3_key VARCHAR(255) NOT NULL,
            s3_bucket VARCHAR(255) NOT NULL,
            file_size INT,
            mime_type VARCHAR(100),
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted TINYINT(1) DEFAULT 0
            -- Removing explicit FK constraint to avoid potential engine mismatch issues during this critical fix
        )
        """
        cursor.execute(sql)
        print("Table 'files' created successfully.")
        
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
