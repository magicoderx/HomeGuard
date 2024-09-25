from flask import Flask, request, render_template_string, render_template, jsonify
from google.cloud import firestore, storage
import datetime

# Initialize flask app
app = Flask(__name__)
# Initialize firestore client
db = firestore.Client()
# Initialize google storage client
storage_client = storage.Client()

@app.route("/", methods=["GET"])
def home():
    data_selected = request.args.get('data')
    
    # If a date is picked, retrieve data in that day
    if data_selected:
        start = datetime.datetime.strptime(data_selected, "%Y-%m-%d")
        end = start + datetime.timedelta(days=1)
        sensorDB = db.collection('sensors').where('timestamp', '>=', start).where('timestamp', '<', end).stream()
    # If there is no date selected print last 100 values
    else:
        sensorDB = db.collection('sensors').order_by('timestamp').limit(100).stream()
    
    data = [['Time', 'Temperature', 'Consumption']]
    # Save data in dictionary
    for doc in sensorDB:
        dati = doc.to_dict()
        data.append([dati['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), dati['temperature'], dati['consumption']])
    
    # Render the HTML page
    return render_template('dashboard.html', chart_data=data, data_selected=data_selected)

@app.route("/getImages", methods=["GET"])
def get_images():
    # Get current timestamp and parse it in firestore format
    timestamp = request.args.get('timestamp')
    date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    date_str = date.strftime("%Y-%m-%d")

    # Get images from specified date
    images = get_images_by_date('pcloud-pesole-2024',date_str)
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

# Run app on port 8080
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080,debug=True)