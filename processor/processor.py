import os
from dotenv import load_dotenv
import json
from datetime import datetime
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
import time
import logging
from logging.handlers import RotatingFileHandler


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, filename='processor.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

logger.info(f'\n#### Initializing Processing job at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ####')

# Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')  # Path to your credentials JSON file

# AWS S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET")

# Authenticate with Google Sheets API
def authenticate_google_sheets():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

SHEET = authenticate_google_sheets().spreadsheets()

def update_price(sheet_id, range_name, row_index, price):
    value_input_option = 'RAW'

    # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_time = datetime.now().strftime("%Y-%m-%d")

    value_range_body = {
        "values": [
            [price, current_time]
        ]
    }

    try:
        SHEET.values().update(
            spreadsheetId=sheet_id,
            range=f'{range_name}!C{row_index+1}:D{row_index}',
            valueInputOption=value_input_option,
            body=value_range_body
        ).execute()

        logger.info(f'For row-{row_index}, Updated price: {row_index}, PriceUpdatedAt: {current_time}\n')
    except Exception as e:
        logger.error(f"Error updating price for row {row_index}: {e}")

def extract_price(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    if script_tag:
        script_content = script_tag.string
        json_data = json.loads(script_content)

        product_key = 'product:{\"productId\":\"%s\"}' % json_data['props']['pageProps']['id']

        if 'props' in json_data and 'pageProps' in json_data['props'] \
        and 'apolloState' in json_data['props']['pageProps'] \
        and 'ROOT_QUERY' in json_data['props']['pageProps']['apolloState'] \
        and product_key in json_data['props']['pageProps']['apolloState']['ROOT_QUERY'] \
        and 'productBasicData' in json_data['props']['pageProps']['apolloState']['ROOT_QUERY'][product_key]:
            product_data = json_data['props']['pageProps']['apolloState']['ROOT_QUERY'][product_key]['productBasicData']
            if 'price' in product_data:
                logger.info(f"extracted_price: {product_data['price'].get('value')}")
                return product_data['price'].get('value')
    return None

def process_page(bucket_name, page_key, sheet_id, range_name, row_index, s3):
    logger.info(f'Processing started for row index: {row_index}')
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=page_key)
        html_content = response['Body'].read().decode('utf-8')

        price = extract_price(html_content)

        if price:
            update_price(sheet_id, range_name, row_index, price)
        else:
            logger.warning(f"We are unable to find price for page_{row_index-1}")
    except Exception as e:
        logger.error(f"Error processing page_{row_index-1}: {e}")


def main():
    sheet_id = '1JinOtgZDuD8s8eM0QL72_7mPx3Jhkog59-nyqXLJdm4'
    range_name = 'Sheet1'

    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Delimiter='/')

    # Get the prefixes (folder names)
    folders = response.get('CommonPrefixes', [])

    # Sort the folders by name and pick the latest one
    latest_updated_at = sorted(folders, key=lambda x: x['Prefix'], reverse=True)[0]['Prefix']

    values = SHEET.values().get(spreadsheetId=sheet_id, range=range_name).execute().get('values', [])

    for row_index, _ in enumerate(values[1:], start=2):  # Skip the header row
        page_key = f'{latest_updated_at}page_{row_index - 1}.html'
        process_page(BUCKET_NAME, page_key, sheet_id, range_name, row_index, s3_client)
        time.sleep(0.6)

    # Upload logs file to S3
    log_file_path = 'processor.log'
    s3_key = f'processor.log'

    with open(log_file_path, 'rb') as f:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=f,
            ContentType='text/plain'
        )

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}")
