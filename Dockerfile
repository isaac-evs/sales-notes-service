FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for PDF storage
RUN mkdir -p /tmp/sales_notes_pdfs && chmod 777 /tmp/sales_notes_pdfs

# Create a non-root user to run the app
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
