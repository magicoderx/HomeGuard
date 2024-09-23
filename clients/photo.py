import cv2
import time
import requests
from dotenv import load_dotenv
import os

def capture_photo():
    load_dotenv()
    # Open webcam
    capture = cv2.VideoCapture(0)
    
    if not capture.isOpened():
        print("Error opening webcam")
        return
    
    # Image capture
    isOk, img = capture.read()
    if isOk:
        # Save iamge
        filename = 'photo.jpg'
        cv2.imwrite(filename, img)
        
        # Close webcam
        capture.release()
        
        # Send photo to gcloud function
        with open(filename, 'rb') as f:
            response = requests.post('https://'+os.getenv("GFUNCTION_URL")+'.cloudfunctions.net/faceDetect', files={'file': f})
            print(response.text)
    else:
        print("Error capturing image")

def main():
    # Every minute generates data through the appropriate functions
    while True:
        capture_photo()
        time.sleep(60)

if __name__ == "__main__":
    main()
