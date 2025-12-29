import os
import mysql.connector
from urllib.parse import urlparse

def get_railway_connection():
    """Production-ready Railway MySQL connection"""
    
    # Railway provides DATABASE_URL
    db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL')
    
    if db_url:
        # Parse Railway URL: mysql://user:pass@host:port/db
        parsed = urlparse(db_url)
        config = {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:],  # Remove leading /
            'autocommit': True,
            'ssl_disabled': False
        }
    else:
        # Fallback to individual env vars
        config = {
            'host': os.getenv('MYSQL_HOST'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'), 
            'database': os.getenv('MYSQL_DATABASE'),
            'autocommit': True
        }
    
    return mysql.connector.connect(**config)