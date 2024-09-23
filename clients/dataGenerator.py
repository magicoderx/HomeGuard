import requests
import random
import time
from dotenv import load_dotenv
import os

# Function that sends data to speficied gfunction
def send_data(temperature, consumption):
    url = 'https://'+os.getenv("GFUNCTION_URL")+'.cloudfunctions.net/getData'
    data = {
        'temperature': temperature,
        'consumption': consumption
    }
    # Parse data into json and perform POST request
    response = requests.post(url, json=data)
    return response.status_code

# Temperature generator
def generate_data_temperature():
    # Temperatures should be a value between 19 and 32
    temperature = random.randrange(19,32)
    return temperature

# Consumption generator
def generate_data_consumption():
    # Generate random decimal
    decimal = random.random()
    # Generate random integer until kwh
    integer = random.randrange(0,3)
    consumption = integer+decimal
    # Limit consumption random number at 3.0
    if consumption > 3:
        consumption = 3.0
    return round(consumption,1)

def main():
    load_dotenv()
    # Every minute generates data through the appropriate functions
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
