from flask import jsonify
import os
from google.cloud import storage
from google.oauth2 import service_account
import datetime
from datetime import timedelta

# Initialize service account credentials
credentials = service_account.Credentials.from_service_account_file('./credentials.json')
err_str = "Specified environment variable is not set."
# Initialize google storage client
storage_client = storage.Client(credentials=credentials)

def get_images(request):
    # Get current timestamp and parse it in firestore format
    timestamp = request.args.get('timestamp')
    date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    date_str = date.strftime("%Y-%m-%d")

    # Get images from specified date
    images = get_images_by_date(os.environ.get("GSTORAGE_ID", err_str), date_str)
    if not images:
        return jsonify({'message': 'Nessuna immagine trovata per questa data.'}), 404
    
    # Get urls of images
    image_urls = [{'name': blob.name, 'url': generate_signed_url(blob)} for blob in images]
    
    return jsonify(image_urls)

def get_images_by_date(bucket_name, date):
    bucket = storage_client.bucket(bucket_name)
    # List all files in bucket
    blobs = bucket.list_blobs()
    images = []

    # Filter from date
    for blob in blobs:
        blob_date = blob.time_created.date()
        if (str(blob_date) == str(date)):
            images.append(blob)

    return images

def generate_signed_url(blob, expiration_minutes=5):
    # Generate signed url for images
    url = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
    return url