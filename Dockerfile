# Dockerfile

# Use an official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for pyodbc
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    apt-transport-https\
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    apt-utils \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update
RUN env ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app code
COPY ./app /app

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]