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

# Check if there are more than 20 rows of data
if num_rows <= 160:
    print(f"Only {num_rows} rows found. Exiting without processing.")
    sys.exit()  # Exit the script if 20 or fewer rows are found

# Extract Data, Convert to DataFrame
df = pd.DataFrame(worksheet.get('A2:Z160'), columns=worksheet.row_values(1))

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
    time.sleep(4)
    job.reload()
    print(job.state)

# Delete Exported Rows
worksheet.delete_rows(2, 160)

# Exit 
print(f'Cryptocurrency Data Export to Google BigQuery Successful')











