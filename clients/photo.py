import cv2
import time
import requests
from dotenv import load_dotenv
import os

def capture_photo():
    load_dotenv()
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error opening webcam")
        return
    
    # Image capture
    isOk, img = cap.read()
    if isOk:
        # Save iamge
        filename = 'photo.jpg'
        cv2.imwrite(filename, img)
        
        # Close webcam
        cap.release()
        
        # Send photo to gcloud function
        with open(filename, 'rb') as f:
            response = requests.post('https://'+os.getenv("GFUNCTION_URL")+'.cloudfunctions.net/faceDetect', files={'file': f})
            print(response.text)
    else:
        print("Error capturing image")

def main():
    while True:
        capture_photo()
        # Wait 1 minute
        time.sleep(60)

if __name__ == "__main__":
    main()
