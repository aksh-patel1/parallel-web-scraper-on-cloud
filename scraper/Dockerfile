# Use the official Python image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the Python scripts, the credentials file, and the requirements file
COPY scraper.py .
COPY iconic-range-412912-258f129777ff.json .
COPY requirements.txt .
COPY .env .
COPY scraper.log .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the scraper.py script
CMD ["python", "scraper.py"]
