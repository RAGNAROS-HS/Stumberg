# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the project files to the container
COPY . /app

# Install system dependencies if needed (uncomment and customize if necessary)
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port if your app uses one (e.g., for Streamlit)
EXPOSE 8501

# Default command to run your app, customize if different entry point
CMD ["python", "main.py"]
