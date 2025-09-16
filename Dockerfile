FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' celery_user
USER celery_user

COPY . .
ENV PYTHONUNBUFFERED=1

# This CMD is for the web service. It's good practice to keep it generic.
CMD ["python", "run.py"]