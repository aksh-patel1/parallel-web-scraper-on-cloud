from dotenv import load_dotenv
import os
import requests
from concurrent.futures import ThreadPoolExecutor
import boto3
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, filename='scraper.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

logger.info(f'\n#### Initializing Scraping job at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ####')

# AWS
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")

# Define the function to scrape a single URL synchronously
def scrape_url(url, retries=4):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "connection": "keep-alive"
    }

    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=25)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            logger.info(f"Successfully scraped page: {url}")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping page: {url}, Error: {e}")
            
    return None

# Authenticate with Google Sheets API
def authenticate_google_sheets():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

# Read URLs from the Google Sheet
def read_urls_from_sheet(sheet_id, service):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range='Sheet1!B2:B').execute()
    values = result.get('values', [])
    urls = [url[0] for url in values]
    return urls

# Main function to scrape URLs and store HTML in S3
def main():
    # Authenticate with Google Sheets API
    service = authenticate_google_sheets()
    
    # Read URLs from the Google Sheet
    sheet_id = '1JinOtgZDuD8s8eM0QL72_7mPx3Jhkog59-nyqXLJdm4'
    urls = read_urls_from_sheet(sheet_id, service)

    # Scrape URLs using multithreading
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scrape_url, urls))

    # Store HTML content in S3
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    current_date = datetime.now().strftime('%Y-%m-%d')
    for idx, html_content in enumerate(results):
        if html_content:
            # Store HTML content in S3 bucket
            s3_key = f'{current_date}/page_{idx + 1}.html'
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=html_content.encode('utf-8'),
                ContentType='text/html'
            )

            logger.info(f'Stored page {idx + 1} HTML in S3')

    # Upload logs file to S3
    log_file_path = 'scraper.log'
    s3_key = 'scraper.log'

    with open(log_file_path, 'rb') as f:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=f,
            ContentType='text/plain'
        )

def trigger_processing_batch():

    client = boto3.client('events', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    response = client.put_events(
        Entries=[
            {
                'Source': "scraperapp.batch",
                'DetailType': "Batch Job State Change",
                'Detail': json.dumps({
                    "state": ["SUCCEEDED"]
                })
            },
        ],
    )

    return response


if __name__ == "__main__":
    try:
        main()

        response = trigger_processing_batch()
        logger.info(f'Response from EventBridge: {response}')

    except Exception as e:
        logger.error(f"Error: {e}")

