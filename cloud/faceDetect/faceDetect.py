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
            link='https://storage.cloud.google.com/'+os.getenv("GSTORAGE_ID")+'/'+file
            send_email(int(ai.text),link)
    except:
        print("Error sending email")

def upload_to_gcs(file_path):
    client = storage.Client()
    bucket = client.bucket(os.getenv("GSTORAGE_ID"))
    blob = bucket.blob(os.path.basename(file_path))
    blob.upload_from_filename(file_path)
    print(f'File {file_path} uploaded on Google Cloud Storage')

def send_email(faces,photourl):
    # SMTP variables
    smtp_user = os.getenv("SMTP_LOGIN_USER")
    receiver_email = os.getenv("SMTP_TO")
    password = os.getenv("SMTP_LOGIN_PASS")

    # Generate headers
    msg = MIMEText(f"Attenzione! Sono stati rilevati ",faces," volti in casa! Guarda la foto: {photourl}")
    msg["Subject"] = "Videosorveglianza: ATTENZIONE"
    msg["From"] = os.getenv("SMTP_FROM")
    msg["To"] = receiver_email

    server = smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT"))
    server.login(smtp_user, password)
    try:
        # Send the Email
        server.sendmail(smtp_user, receiver_email, msg.as_string())
        server.quit()
        print("Email sent")
    except:
        server.quit()
        print("Error: email was not sent")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)