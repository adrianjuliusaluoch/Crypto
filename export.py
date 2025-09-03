# Import Packages
import os
import sys
import json
import time

import pandas as pd
import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# Initialize BigQuery client
client = bigquery.Client(project='crypto-stocks-01')

# Define the scope for Google Sheets and BigQuery
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/cloud-platform'
]

# Load credentials from environment variable
credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)

# Initialize Google Sheets client
gc = gspread.authorize(creds)

# Open the Google Sheet by URL
spreadsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1gacmcpjcinT7Dtug--lQz5FGzK05gFJNOE2fklxMbqY')
worksheet = spreadsheet.sheet1  # Select the first sheet

# Get the total number of rows with data
all_records = worksheet.get_all_records()
num_rows = len(all_records)

# Check if there are more than 30 rows of data
if num_rows <= 31:
    print(f"Only {num_rows} rows found. Exiting without processing.")
    sys.exit()  # Exit the script if 30 or fewer rows are found

# Extract Data, Convert to DataFrame
df = pd.DataFrame(worksheet.get('A2:Z31'), columns=worksheet.row_values(1))

# Original Data
data = df.copy()

# Standardize Column Names
data.columns = data.columns.str.lower().str.replace(' ', '_').str.replace(r'[()]', '', regex=True)

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

# Delete Exported Rows
worksheet.delete_rows(2, 31)

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


















