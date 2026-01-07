# Use official Python base image
FROM python:3.11-slim
# Set working directory
WORKDIR /app
# Copy the project files to the container
COPY . /app
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (for Streamlit)
EXPOSE 8501
CMD ["python", "main.py"]
