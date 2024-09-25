# Use minimal image of python
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all in working directory
COPY . /app

# Install requirements
RUN pip install -r requirements.txt

# Execute flask app
CMD ["python", "main.py"]
