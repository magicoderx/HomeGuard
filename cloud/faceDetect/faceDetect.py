import os
from flask import Flask, jsonify
from google.cloud import storage
import tempfile
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
err_str = "Specified environment variable is not set."

# Init generative model in Europe West3 region
vertexai.init(project=os.environ.get("GSTORAGE_ID", err_str), location="europe-west3")
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
        "Quanti volti vedi nell'immagine? Rispondimi con un numero intero e senza punteggiature",
    ]
    )
    try:
        # Send email only if there are 2 or more faces
        if int(ai.text)>=2:
            link='https://storage.cloud.google.com/'+os.environ.get("GSTORAGE_ID", err_str)+'/'+os.path.basename(file)+'.jpg'
            send_email(int(ai.text),link)
    except Exception as error:
        # handle the exception
        print("Error sending email:", error)

def upload_to_gcs(file_path):
    client = storage.Client()
    bucket = client.bucket(os.environ.get("GSTORAGE_ID", err_str))
    blob = bucket.blob(os.path.basename(file_path)+".jpg")
    blob.upload_from_filename(file_path)
    print(f'File {file_path} uploaded on Google Cloud Storage')

def send_email(faces,photourl):
    # SMTP variables
    smtp_user = os.environ.get("SMTP_LOGIN_USER", err_str)
    receiver_email = os.environ.get("SMTP_TO", err_str)
    password = os.environ.get("SMTP_LOGIN_PASS", err_str)

    # Compose message
    message = MIMEMultipart("alternative")
    message['Subject'] = "Anomalia in casa!"
    message['From'] = smtp_user
    message['To'] = receiver_email

    # HTML to send
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mail Content</title>
        <style>
            body{
                font-family: Arial, Helvetica, sans-serif;
            }
        </style>
    </head>
    <body>
        <p>Attenzione! Sono stati rilevati """
    # Append variables to html
    html=html+str(faces)
    html=html+" volti in casa! Guarda la foto: <a href="
    html=html+photourl
    html=html+">qui</a></p></body></html>"
    
    html_part = MIMEText(html, 'html')
    message.attach(html_part)
    
    # Send email
    smtp = smtplib.SMTP(os.environ.get("SMTP_SERVER", err_str), os.environ.get("SMTP_PORT", err_str))
    
    smtp.ehlo()
    smtp.starttls()
    smtp.login(smtp_user, password)
    smtp.sendmail(smtp_user, receiver_email, message.as_string())
    smtp.quit()

if __name__ == "__main__":
    app.run(debug=True)