import requests
import random
import time
from dotenv import load_dotenv
import os

def send_data(temperature, consumption):
    url = 'https://'+os.getenv("GFUNCTION_URL")+'.cloudfunctions.net/getData'
    data = {
        'temperature': temperature,
        'consumption': consumption
    }
    response = requests.post(url, json=data)
    return response.status_code

def generate_data_temperature():
    temperature = random.randrange(19,32)
    return temperature

def generate_data_consumption():
    decimal = random.random()
    integer = random.randrange(0,3)
    consumption = integer+decimal
    return round(consumption,1)

def main():
    load_dotenv()
    while True:
        temperature = generate_data_temperature()
        consumption = generate_data_consumption()
        status_code = send_data(temperature, consumption)
        if status_code == 200:
            print("Data sent successful")
        else:
            print("Error sending data: Code ",status_code)
        time.sleep(60)

if __name__ == "__main__":
    main()
