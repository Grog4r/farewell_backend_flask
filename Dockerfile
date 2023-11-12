# Use the official Python image as a base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the Flask app will run
EXPOSE 8000

# Set the entry point for the container
CMD ["gunicorn", "-t", "0", "-b" , "0.0.0.0:8000", "-R", "--log-level", "debug", "main_flask:app"]
