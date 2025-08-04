"""
Database connection module for Bentley Budget Bot
Handles MySQL database connections and queries
"""

import mysql.connector
import pandas as pd
import os
from typing import Optional, List, Dict, Any

class BentleyBudgetDB:
    """Database connection class for Bentley Budget application"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'mysql'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', 'rootpassword'),
                database=os.getenv('MYSQL_DATABASE', 'Bentley_Budget'),
                charset='utf8mb4',
                autocommit=True
            )
            print("Successfully connected to MySQL database")
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.connection = None
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        return self.connection is not None and self.connection.is_connected()
    
    def get_gdp_data(self, countries: Optional[List[str]] = None, 
                     start_year: int = 1960, end_year: int = 2022) -> pd.DataFrame:
        """
        Get GDP data from the normalized table
        
        Args:
            countries: List of country codes to filter by
            start_year: Start year for data range
            end_year: End year for data range
            
        Returns:
            DataFrame with GDP data
        """
        if not self.is_connected():
            self.connect()
            if not self.is_connected():
                return pd.DataFrame()
        
        try:
            query = """
            SELECT country_code, country_name, year, gdp_value
            FROM gdp_yearly_data
            WHERE year BETWEEN %s AND %s
            """
            params = [start_year, end_year]
            
            if countries:
                placeholders = ', '.join(['%s'] * len(countries))
                query += f" AND country_code IN ({placeholders})"
                params.extend(countries)
            
            query += " ORDER BY country_code, year"
            
            df = pd.read_sql(query, self.connection, params=params)
            return df
            
        except Exception as e:
            print(f"Error fetching GDP data: {e}")
            return pd.DataFrame()
    
    def get_countries(self) -> List[Dict[str, str]]:
        """Get list of all countries in the database"""
        if not self.is_connected():
            self.connect()
            if not self.is_connected():
                return []
        
        try:
            query = """
            SELECT DISTINCT country_code, country_name
            FROM gdp_yearly_data
            ORDER BY country_name
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            countries = cursor.fetchall()
            cursor.close()
            
            return countries
            
        except Exception as e:
            print(f"Error fetching countries: {e}")
            return []
    
    def get_gdp_summary(self, year: int = 2022) -> pd.DataFrame:
        """
        Get GDP summary for a specific year
        
        Args:
            year: Year to get summary for
            
        Returns:
            DataFrame with GDP summary
        """
        if not self.is_connected():
            self.connect()
            if not self.is_connected():
                return pd.DataFrame()
        
        try:
            query = """
            SELECT country_code, country_name, gdp_value
            FROM gdp_yearly_data
            WHERE year = %s AND gdp_value IS NOT NULL
            ORDER BY gdp_value DESC
            """
            
            df = pd.read_sql(query, self.connection, params=[year])
            return df
            
        except Exception as e:
            print(f"Error fetching GDP summary: {e}")
            return pd.DataFrame()
    
    def get_top_countries(self, year: int = 2022, limit: int = 10) -> pd.DataFrame:
        """
        Get top countries by GDP for a specific year
        
        Args:
            year: Year to get data for
            limit: Number of top countries to return
            
        Returns:
            DataFrame with top countries
        """
        if not self.is_connected():
            self.connect()
            if not self.is_connected():
                return pd.DataFrame()
        
        try:
            query = """
            SELECT country_code, country_name, gdp_value
            FROM gdp_yearly_data
            WHERE year = %s AND gdp_value IS NOT NULL
            ORDER BY gdp_value DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, self.connection, params=[year, limit])
            return df
            
        except Exception as e:
            print(f"Error fetching top countries: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

# Global database instance
db = BentleyBudgetDB() 