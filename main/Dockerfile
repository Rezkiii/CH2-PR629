# Use the official Python base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code to the container
COPY . .

# Expose the port on which the Flask app will run (default is 5000)
EXPOSE 8080

# Specify the command to run the Flask app
CMD ["python", "main.py"]