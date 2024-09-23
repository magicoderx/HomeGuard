from google.cloud import firestore
from flask import Flask

# Initialize flask app
app = Flask(__name__)
# Initialize firestore client
db = firestore.Client()

@app.route("/", methods=["POST"])
def save_data(request):
    # Get temperature and consumption values
    content = request.json
    temperature = content.get('temperature')
    consumption = content.get('consumption')
    
    # Add Values in firestore sensors collection
    db.collection('sensors').add({
        'temperature': temperature,
        'consumption': consumption,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    return "Data saved", 200

if __name__ == "__main__":
    app.run(debug=True)
