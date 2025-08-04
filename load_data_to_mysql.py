#!/usr/bin/env python3
"""
Script to load GDP data from CSV into MySQL database
This script can be run manually to populate the database
"""

import pandas as pd
import mysql.connector
import os
from pathlib import Path
import time

def load_gdp_data():
    """Load GDP data from CSV into MySQL database"""
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'mysql'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'rootpassword'),
        'database': os.getenv('MYSQL_DATABASE', 'Bentley_Budget'),
        'charset': 'utf8mb4'
    }
    
    # Wait for database to be ready
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = mysql.connector.connect(**db_config)
            print("Successfully connected to MySQL database")
            break
        except mysql.connector.Error as err:
            print(f"Attempt {retry_count + 1}: Waiting for MySQL to be ready... ({err})")
            retry_count += 1
            time.sleep(2)
    
    if retry_count >= max_retries:
        print("Failed to connect to MySQL after maximum retries")
        return
    
    try:
        cursor = conn.cursor()
        
        # Read the CSV file
        csv_path = Path('data/gdp_data.csv')
        if not csv_path.exists():
            print(f"CSV file not found at {csv_path}")
            return
            
        print(f"Reading GDP data from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from CSV")
        
        # Load data into the normalized gdp_yearly_data table
        print("Loading data into gdp_yearly_data table...")
        yearly_count = 0
        
        for index, row in df.iterrows():
            try:
                country_name = row['Country Name']
                country_code = row['Country Code']
                
                for year in range(1960, 2023):
                    year_col = str(year)
                    if year_col in row and pd.notna(row[year_col]):
                        gdp_value = float(row[year_col])
                        
                        query = """
                        INSERT INTO gdp_yearly_data (country_code, country_name, year, gdp_value)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE gdp_value = VALUES(gdp_value)
                        """
                        cursor.execute(query, (country_code, country_name, year, gdp_value))
                        yearly_count += 1
                        
            except Exception as e:
                print(f"Error processing yearly data for row {index}: {e}")
                continue
        
        # Commit the changes
        conn.commit()
        print("GDP data loaded successfully!")
        print(f"Total yearly records in gdp_yearly_data: {yearly_count}")
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    load_gdp_data() 