# 1. Base Linux system with Python
FROM python:3.10-slim

# 2. Working directory inside the container
WORKDIR /app

# 3. Copy and install dependencies first (optimizes Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the application code
COPY . .

# 5. Command to keep the container running
CMD ["python", "-u", "app.py"]