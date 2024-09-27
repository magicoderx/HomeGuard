from google.cloud import firestore

# Initialize firestore client
db = firestore.Client()

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
