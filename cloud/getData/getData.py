from google.cloud import firestore
from flask import Flask, request

app = Flask(__name__)
db = firestore.Client()

@app.route("/", methods=["POST"])
def save_data(request):
    content = request.json
    temperature = content.get('temperature')
    consumption = content.get('consumption')
    
    doc_ref = db.collection('sensors').add({
        'temperature': temperature,
        'consumption': consumption,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    return "Data saved", 200

if __name__ == "__main__":
    app.run(debug=True)
