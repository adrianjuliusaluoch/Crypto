# Import Packages
import os
import sys
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# Initialize BigQuery client
client = bigquery.Client(project='crypto-stocks-01')

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "7d"
}

def fetch_crypto_data():
    response = requests.get(API_URL, params=PARAMS)
    data = response.json()
    df = pd.DataFrame(data)

    # Compute total volume (% of all 24h volumes)
    df["total_vol"] = (df["total_volume"] / df["total_volume"].sum()) * 100

    # Add timestamp in UTC+3 (Kenya time)
    local_time = datetime.now(timezone.utc) + timedelta(hours=3)
    df["timestamp"] = local_time.strftime("%Y-%m-%d %H:%M:%S")

    # Select and rename columns to your preferred structure
    df = df[[
        "timestamp",
        "name",
        "symbol",
        "current_price",
        "total_volume",
        "total_vol",
        "price_change_percentage_24h",
        "price_change_percentage_7d_in_currency",
        "market_cap"
    ]]

    df = df.rename(columns={
        "current_price": "price_usd",
        "total_volume": "vol_24h",
        "price_change_percentage_24h": "chg_24h",
        "price_change_percentage_7d_in_currency": "chg_7d",
        "market_cap": "market_cap"
    })

    # Format numeric fields for readability
    df["price_usd"] = df["price_usd"].map("${:,.2f}".format)
    df["market_cap"] = df["market_cap"].map("${:,.0f}".format)
    df["vol_24h"] = df["vol_24h"].map("${:,.2f}".format)
    df["chg_24h"] = df["chg_24h"].map("{:+.2f}%".format)
    df["chg_7d"] = df["chg_7d"].map("{:+.2f}%".format)
    df["total_vol"] = df["total_vol"].map("{:.2f}%".format)

    return df

# Example usage
if __name__ == "__main__":
    data = fetch_crypto_data()

# Standardize Data Types
data['price_usd'] = data['price_usd'].astype(str)

# Define Table ID
table_id = 'crypto-stocks-01.storage.top_cryptocurrency'

# Export Data to BigQuery
job = client.load_table_from_dataframe(data, table_id)
while job.state != 'DONE':
    time.sleep(2)
    job.reload()
    print(job.state)

# Define SQL Query to Retrieve Open Weather Data from Google Cloud BigQuery
sql = (
    'SELECT *'
    'FROM `crypto-stocks-01.storage.top_cryptocurrency`'
           )
    
# Run SQL Query
data = client.query(sql).to_dataframe()

# Check Shape of data from BigQuery
print(f"Shape of dataset from BigQuery : {data.shape}")

# Delete Original Table
client.delete_table(table_id)
print(f"Table deleted successfully.")

# Check Total Number of Duplicate Records
duplicated = data.duplicated(subset=[
    'timestamp', 
    'name', 
    'symbol', 
    'price_usd', 
    'vol_24h', 
    'total_vol', 
    'chg_24h', 
    'chg_7d', 
    'market_cap']).sum()
    
# Remove Duplicate Records
data.drop_duplicates(subset=[
    'timestamp', 
    'name', 
    'symbol', 
    'price_usd', 
    'vol_24h', 
    'total_vol', 
    'chg_24h', 
    'chg_7d', 
    'market_cap'], inplace=True)

# Define the dataset ID and table ID
dataset_id = 'storage'
table_id = 'top_cryptocurrency'
    
# Define the table schema for new table
schema = [
        bigquery.SchemaField("timestamp", "STRING"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("symbol", "STRING"),
        bigquery.SchemaField("price_usd", "STRING"),
        bigquery.SchemaField("vol_24h", "STRING"),
        bigquery.SchemaField("total_vol", "STRING"),
        bigquery.SchemaField("chg_24h", "STRING"),
        bigquery.SchemaField("chg_7d", "STRING"),
        bigquery.SchemaField("market_cap", "STRING"),
    ]
    
# Define the table reference
table_ref = client.dataset(dataset_id).table(table_id)
    
# Create the table object
table = bigquery.Table(table_ref, schema=schema)

try:
    # Create the table in BigQuery
    table = client.create_table(table)
    print(f"Table {table.table_id} created successfully.")
except Exception as e:
    print(f"Table {table.table_id} failed")

# Define the BigQuery table ID
table_id = 'crypto-stocks-01.storage.top_cryptocurrency'

# Load the data into the BigQuery table
job = client.load_table_from_dataframe(data, table_id)

# Wait for the job to complete
while job.state != 'DONE':
    time.sleep(2)
    job.reload()
    print(job.state)

# Return Data Info
print(f"Data {data.shape} has been successfully retrieved, saved, and appended to the BigQuery table.")

# Exit 
print(f'Cryptocurrency Data Export to Google BigQuery Successful')























