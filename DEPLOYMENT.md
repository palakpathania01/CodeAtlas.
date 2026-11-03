# CodeAtlas Deployment Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for GitHub repository analysis, optional for ZIP uploads)

## Local Development Deployment

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables (Optional)

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 3: Run the Server

```bash
uvicorn app:app --reload
```

The application will be available at: `http://127.0.0.1:8000`

## Production Deployment

### Option 1: Using Gunicorn (Linux/Mac)

```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 2: Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t codeatlas .
docker run -p 8000:8000 codeatlas
```

### Option 3: Using Railway

1. Push your code to GitHub
2. Connect your repository to Railway
3. Railway will automatically detect it's a Python project
4. Set environment variables in Railway dashboard
5. Deploy

### Option 4: Using Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. Deploy

## Environment Variables

- `SECRET_KEY`: JWT secret key (minimum 32 characters)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes (default: 30)

## Database

The application uses SQLite by default (`codeatlas.db`). For production, consider:

- PostgreSQL (recommended for production)
- MySQL

To use PostgreSQL, modify `backend/database.py`:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/codeatlas")
engine = create_engine(DATABASE_URL)
```

## Security Considerations

1. Change the default `SECRET_KEY` in production
2. Use HTTPS in production
3. Set up proper CORS if needed
4. Use a production-grade database
5. Implement rate limiting
6. Set up monitoring and logging

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Kill the process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # Linux/Mac
```

### Database Issues

Delete `codeatlas.db` and restart the server to recreate the database.

### Git Not Found

Install Git for Windows from: https://git-scm.com/download/win

Or use ZIP upload instead of GitHub URL.

## Performance Optimization

1. Use a production ASGI server (Gunicorn + Uvicorn)
2. Enable database connection pooling
3. Use Redis for caching (optional)
4. Implement CDN for static files
5. Use a reverse proxy (Nginx)

## Monitoring

Consider adding:
- Sentry for error tracking
- Prometheus for metrics
- Log aggregation (ELK stack)
