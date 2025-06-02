FROM python:3.10

# Set environment variables
ENV APP_HOME /app
ENV PYTHONUNBUFFERED True
WORKDIR $APP_HOME

# Update and install system dependencies
RUN apt-get -y update && apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*  # Clean up

# Copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Set Xata API Key securely

# Copy the rest of the application code into the container
COPY . ./

# Set file permissions (optional)
RUN chmod 755 /app

# Run the web service on container startup
CMD exec gunicorn --bind :$PORT --log-level info --workers 1 --threads 8 --timeout 0 index:server
