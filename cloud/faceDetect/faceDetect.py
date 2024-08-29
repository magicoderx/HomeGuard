import os
from flask import Flask, request, jsonify
from google.cloud import storage
import tempfile
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Load key for Service Account
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './credentials.json'

# Init generative model in Europe West3 region
vertexai.init(project=os.getenv("GSTORAGE_ID"), location="europe-west3")
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

@app.route('/', methods=['POST'])
def analyze_and_upload(request):
    # Get file received
    file = request.files['file']
    
    # Save temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file.save(temp_file.name)
    
    # Check how many faces there are in the photo
    result = analyze_photo(temp_file.name)
    
    # Upload image on GCS
    upload_to_gcs(temp_file.name)

    return jsonify({'result': result})

def analyze_photo(file):
    # Generate question from image
    ai = model.generate_content(
    [
        Part.from_image(Image.load_from_file(file)),
        "Quanti volti vedi nell'immagine? Rispondimi con un numero intero",
    ]
    )
    try:
        # Send email only if there are 2 or more faces
        if int(ai.text)>=2:
            send_email(int(ai.text))
    except:
        print("Error sending email")

def upload_to_gcs(file_path):
    client = storage.Client()
    bucket = client.bucket(os.getenv("GSTORAGE_ID"))
    blob = bucket.blob(os.path.basename(file_path))
    blob.upload_from_filename(file_path)
    print(f'File {file_path} loaded on Google Cloud Storage')

def send_email(faces):
    # Set Up the SMTP Server
    smtp_server = os.getenv("SMTP_SERVER")
    port = os.getenv("SMTP_PORT")
    server = smtplib.SMTP(smtp_server,port)

    # Create SMTP Session
    server.starttls()

    # Login to the Server
    server.login(os.getenv("SMTP_LOGIN_USER"), os.getenv("SMTP_LOGIN_PASS"))

    # Compose the Email
    from_address = os.getenv("SMTP_FROM")
    to_address = os.getenv("SMTP_TO")
    subject = "Videosorveglianza: ATTENZIONE"
    body = "Attenzione! Sono stati rilevati ",faces," volti in casa!"
    email = f"Subject: {subject}\n\n{body}"
    try:
        # Send the Email
        server.sendmail(from_address, to_address, email)
        print("Email sent")
    except:
        print("Error: email was not sent")

    # Close the SMTP Session
    server.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)