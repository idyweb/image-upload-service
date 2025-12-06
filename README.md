# Image Upload Service with Background Processing

A FastAPI service for uploading and processing images asynchronously. Upload images via API, process them in the background (resize, compress, create thumbnails), and retrieve results via status endpoints.

## Features

- Async Image Upload - Upload images via REST API with automatic processing

- Background Processing Image processing happens asynchronously using Celery workers

- Multiple Formats - Resize, compress, and generate thumbnails

- Status Tracking - Real-time status updates for each upload

- RESTful API - Clean API endpoints for upload, status, and results

## Prerequisites
- Python 3.11+

- PostgreSQL 15+

- Redis 7+

- Google Cloud Storage bucket (or use local storage for development)

## Installation & Setup

1. Clone the Repo

```bash
git clone https://github.com/idyweb/image-upload-service
cd upload-service
```

2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set Up Database

```bash
# Install PostgreSQL if not installed
# Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib
# Mac: brew install postgresql

# Create database
sudo -u postgres psql -c "CREATE DATABASE upload_service;"
sudo -u postgres psql -c "CREATE USER upload_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE upload_service TO upload_user;"

# Initialize database tables
python -c "from app.db.database import init_db; init_db()"
```

6. Install and Start Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Mac
brew install redis
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

7. Set Up Storage
For local development, create uploads directory:
```bash
mkdir -p uploads/originals uploads/thumbnails uploads/resized uploads/compressed
```

For Google Cloud Storage, download service account key:

```bash
# Create service-account.json with your GCP credentials
```

## Running the Application

### Start the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Celery Worker (in separate terminal)

```bash
celery -A api.v1.workers.celery_app worker --loglevel=info
```

## Access the Application
- API: http://localhost:8000

- API Documentation: http://localhost:8000/docs

- Redoc Documentation: http://localhost:8000/redoc


## Configuration (.env)

```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://upload_user:your_password@localhost:5432/upload_service

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
# For local development:
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./uploads

# For Google Cloud Storage:
# GOOGLE_STORAGE_BUCKET=your-bucket-name
# GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Image Processing
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp,image/gif
```

## API Endpoints

1. Upload Image

```bash
POST /api/v1/upload
Content-Type: multipart/form-data
```

Example using curl:

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"
  ```

  Response:

```json
{
  "status": "success",
  "message": "Image uploaded successfully. Processing started.",
  "data": {
    "upload_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_url": "/api/v1/upload/550e8400-e29b-41d4-a716-446655440000/status",
    "result_url": "/api/v1/upload/550e8400-e29b-41d4-a716-446655440000/result",
    "original_url": "/storage/originals/2023/12/06/550e8400/image.jpg",
    "created_at": "2023-12-06T10:30:00Z"
  }
}
```

2. Check Upload Status

```bash
GET /api/v1/upload/{upload_id}/status
```

Example:

```bash
curl "http://localhost:8000/api/v1/upload/550e8400-e29b-41d4-a716-446655440000/status"
```

