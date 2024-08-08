# Use the official Python slim image
FROM python:3.12.4-slim
LABEL version="24.08.07.16.24"

# Set work directory
WORKDIR /app

# Install system dependencies including CMake and tree for debugging
RUN apt-get update && apt-get install -y \
    # file \
    bash \
    # gcc \
    # g++ \
    # cmake \
    # make \
    # tree \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/callbacks
RUN mkdir -p /app/data
RUN mkdir -p /app/cfg

# Copy requirements and setup files
COPY requirements.txt .

# Install requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory
COPY *.py /app
COPY callbacks/*.py /app/callbacks

# Debug: Print directory contents after copy
RUN echo "Contents of /app after COPY:" && ls -la /app

# Create a non-root user
RUN useradd -m appuser

# Make sure the application files are accessible to any user
RUN chmod -R 755 /app
RUN chown -R appuser:appuser /app/data

# Expose the port the app runs on
EXPOSE 8003

# Switch to non-root user
USER appuser

# Use JSON format for CMD
CMD ["sh", "-c", "python -u oodash.py"]