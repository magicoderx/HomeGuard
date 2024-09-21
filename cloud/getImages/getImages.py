from flask import Flask, request, jsonify
from google.cloud import storage
import datetime

app = Flask(__name__)
storage_client = storage.Client()

@app.route("/", methods=["GET"])
def get_images(request):
    timestamp = request.args.get('timestamp')
    date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    date_str = date.strftime("%Y-%m-%d")

    # Get images from specified date
    images = get_images_by_date("pcloud-pesole-2024", date_str)
    if not images:
        return jsonify({'message': 'Nessuna immagine trovata per questa data.'}), 404
    
    # Get urls of images
    image_urls = [{'name': blob.name, 'url': blob.public_url} for blob in images]
    
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

if __name__ == "__main__":
    app.run(debug=True)