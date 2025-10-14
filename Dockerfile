# Use a base Python image
FROM python:3.12-slim-bookworm

# Set the working directory inside the container
WORKDIR /app/src

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the entry point for your application
CMD ["python", "main.py"]