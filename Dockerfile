FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for vector database
RUN mkdir -p /app/vector_db

# Expose port for Streamlit
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py"]