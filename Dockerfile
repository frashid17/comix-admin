# Use the official Python base image
FROM python:3.13

# Set the working directory inside the container
WORKDIR /app

# Install pipenv or just use pip directly (simple)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your app code into the container
COPY . .

# Expose port 8000 for Django
EXPOSE 8000

# Default command to run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
