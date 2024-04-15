# Web Scraping and Processing Architecture with AWS

This project demonstrates an event-driven architecture for web scraping and processing tasks using AWS services. The architecture includes a scraper job running on AWS Batch, which collects data from web pages and stores it in AWS S3. The processing job, triggered by AWS EventBridge, processes the scraped data and updates a Google Sheet with a updated price of a particular product.

## Features

*   **Scalable**: The architecture can scale to handle large volumes of web scraping and processing tasks.
*   **Automated**: The processing job is triggered automatically after the scraping job completes, reducing manual intervention.
*   **Parallel Scraping**: The scraper job can scrape multiple web pages simultaneously, improving efficiency.
*   **Flexible**: The architecture can be adapted to different scraping and processing requirements.

## Technologies Used

*   AWS Batch: For running the scraper job at scale.
*   AWS EventBridge: For triggering the processing job after the scraping job completes.
*   AWS S3: For storing scraped data and logs.
*   AWS ECS: For running Docker containers.
*   AWS ECR: For storing Docker images.
*   Google Sheets API: For updating a Google Sheet with processed data.

## Usage

1.  **Configure Google Sheets API**:
    *   Enable the Google Sheets API in the Google Cloud Console.
    *   Create credentials (OAuth 2.0 client ID) for your project.
    *   Download the credentials JSON file and save it as `credentials.json` in the project directory.
    *   Share the Google Sheet with the email address specified in the credentials JSON file.
2.  **Set Up AWS Services**: Set up AWS Batch, AWS EventBridge, AWS S3 and AWS ECR.
3.  **Deploy Docker Images**: Deploy the Docker images for the scraper job and processing job to AWS ECR.
4.  **Configure EventBridge**: Set up an EventBridge rule to trigger the processing job after the scraping job completes.
5.  **Run the Scraping Job**: Run the scraper job on AWS Batch to start scraping web pages.
6.  **Monitor and Troubleshoot**: Monitor the progress of the scraping and processing jobs and troubleshoot any issues.

### Scraping Task Google-sheet:
[Scraping Task Sheet](https://docs.google.com/spreadsheets/d/1uz4fp17ZDldDJWwfbTyUOCXHNs3GUveK181kQHI5L0w/edit?usp=sharing)

## Getting Started

1.  Clone the repository:
    
    `git clone https://github.com/aj225patel/parallel-web-scraper-on-cloud.git` 
2.  Set up AWS services following the instructions in the `README.md` file.
3.  Configure the Google Sheets API following the instructions in the `README.md` file.
4.  Deploy the Docker images for the scraper job and processing job to AWS ECR. 
5.  Set up an EventBridge rule to trigger the processing job after the scraping job completes.
6.  Run the scraping job on AWS Batch.
7.  Monitor the progress of the scraping and processing jobs and troubleshoot any issues.

## Acknowledgements

*   This project was inspired by the need for a scalable and automated web scraping solution.
*   Special thanks to the AWS documentation and community for valuable insights and resources.
