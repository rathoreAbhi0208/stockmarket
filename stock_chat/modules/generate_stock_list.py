# scripts/generate_stock_list.py

import pandas as pd
import requests
import os
import io
import json

# URL for the CSV file of all securities available for trading on NSE
NSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

# The path to save the generated JSON file
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'data_sources', 'nse_stocks.json')

def fetch_and_save_nse_stocks():
    """
    Fetches the list of all equity stocks from the NSE website,
    formats it, and saves it as a JSON file.
    """
    print(f"Fetching stock list from NSE: {NSE_URL}")
    
    try:
        # NSE website often blocks simple requests, so we use headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(NSE_URL, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Read the CSV content into a pandas DataFrame
        csv_data = io.StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Create a dictionary of Symbol -> Name of the Company
        # We strip whitespace from column names as they can sometimes have it
        stock_dict = pd.Series(df['NAME OF COMPANY'].values, index=df['SYMBOL']).to_dict()
        
        # Save the dictionary to a JSON file
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(stock_dict, f, indent=4)
            
        print(f"✅ Successfully saved {len(stock_dict)} stocks to {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Failed to fetch or process NSE stock list: {e}")

if __name__ == "__main__":
    # Ensure the target directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    fetch_and_save_nse_stocks()