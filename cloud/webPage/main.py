from flask import Flask, render_template_string, render_template
from google.cloud import firestore, storage
import datetime

# Initialize flask app
app = Flask(__name__)
# Initialize firestore client
db = firestore.Client()
# Initialize google storage client
storage_client = storage.Client()

@app.route("/", methods=["GET"])
def home(request):
    data_selected = request.args.get('data')
    
    # If a date is picked, retrieve data in that day
    if data_selected:
        start = datetime.datetime.strptime(data_selected, "%Y-%m-%d")
        end = start + datetime.timedelta(days=1)
        sensorDB = db.collection('sensori').where('timestamp', '>=', start).where('timestamp', '<', end).stream()
    # If there is no date selected print last 100 values
    else:
        sensorDB = db.collection('sensori').order_by('timestamp').limit(100).stream()
    
    data = [['Time', 'Temperature', 'Consumption']]
    # Save data in dictionary
    for doc in sensorDB:
        dati = doc.to_dict()
        data.append([dati['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), dati['temperature'], dati['consumption']])
    
    # Define HTML code
    html = "" # Paste here your HTML
    #return render_template_string(html, chart_data=data, data_selected=data_selected)
    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)