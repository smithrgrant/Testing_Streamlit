import requests
import pandas as pd
from urllib.parse import quote
from pathlib import Path

# Airtable credentials and table info
AIRTABLE_TOKEN = 'pat6MRHBPUXfjG1dg.096c6d98af12fae41a3e5736b2ea8946d69b0bfdd53b430e2e2aff9f6145f162'
BASE_ID = 'app6DojqHx8o9ULRx'
TABLE_NAME = 'Menu Items'  # Must be URL-safe (e.g., no spaces or encode with %20)

# URL-encode table name (handles spaces and special characters)
TABLE_NAME_ENCODED = quote(TABLE_NAME)

# Construct the API endpoint URL
url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME_ENCODED}'

# Set the authorization header using personal access token
headers = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}'
}

def fetch_airtable_view():
    records = []
    offset = None

    while True:
        # Include the view name in the query parameters
        params = {
            # 'view': VIEW_NAME,
            'pageSize': 100

        }
        if offset:
            params['offset'] = offset

        # Send the request
        response = requests.get(url, headers=headers, params=params)
        # print('REPONSE:')
        # print(response.status_code, response.text)
        response.raise_for_status()

        data = response.json()
        records.extend(data['records'])

        
        # Pagination handling
        offset = data.get('offset')
        if not offset:
            break

    # Convert the result to a pandas DataFrame
    df = pd.json_normalize([r['fields'] for r in records])
    return df

# Run the script
if __name__ == '__main__':
    df = fetch_airtable_view()
    print(df.head())

    
    # Build a CSV path next to your script (e.g. script.py → script.csv)
    out_path = Path(__file__).with_suffix('.csv')
    # Or explicitly:
    # out_path = Path(__file__).parent / 'menu_items.csv'

    # Export to CSV (no index column)
    df.to_csv(out_path, index=False)
    print(f"Exported to {out_path.resolve()}")