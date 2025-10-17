# Newsletter Application Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd ailert
uv pip install -r requirements.txt
```

### 2. Configure Environment
Create your configuration files:

**Option A: Use sample files (for testing)**
```bash
# Copy sample configuration
copy db_handler\sample_vault\secrets.ini db_handler\vault\secrets.ini
copy db_handler\sample_vault\recipients.csv db_handler\vault\recipients.csv
```

**Option B: Set environment variables (recommended)**
```bash
set SENDGRID_API_KEY=your_sendgrid_api_key
set AWS_REGION=us-east-1
set JWT_SECRET=your_jwt_secret
set MAX_EMAIL_CONCURRENT=10
set LOG_LEVEL=INFO
```

### 3. Run the Application
```bash
# Using uv
uv run python run.py

# Or directly
python run.py
```

## 📋 Configuration Files

### Required Files:
- `db_handler/vault/secrets.ini` - API keys and secrets
- `db_handler/vault/recipients.csv` - Subscriber email list

### Sample secrets.ini:
```ini
[Dynamo]
region = us-east-1

[Sendgrid]
api_key = your_sendgrid_api_key_here

[JWT]
user_id = admin
secret = your_jwt_secret_here

[GitHub]
client_id = your_github_app_id
pem_path = path/to/github/private/key.pem
```

### Sample recipients.csv:
```csv
email,subscribed_at
user1@example.com,2024-01-01
user2@example.com,2024-01-02
```

## 🌐 Web Interface

Once running, access the web interface at:
- **Main App**: http://localhost:5001
- **Health Check**: http://localhost:5001/internal/v1/health
- **Metrics**: Included in health check response

## 📊 API Endpoints

### Authentication
```bash
# Get JWT token
curl -X POST http://localhost:5001/internal/v1/login
```

### Newsletter Operations
```bash
# Generate newsletter
curl -X POST http://localhost:5001/internal/v1/generate-newsletter \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sections": ["news"], "task_type": "daily"}'

# Start scheduler
curl -X POST http://localhost:5001/internal/v1/start-scheduler/daily \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check scheduler status
curl -X GET http://localhost:5001/internal/v1/scheduler-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Subscriber Management
```bash
# Subscribe email
curl -X POST http://localhost:5001/internal/v1/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com"}'

# Unsubscribe email
curl -X POST http://localhost:5001/internal/v1/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## 🔧 Troubleshooting

### Common Issues:

1. **Import Errors**
   ```bash
   # Make sure you're in the ailert directory
   cd ailert
   # Install missing packages
   uv pip install schedule boto3 sendgrid pandas beautifulsoup4
   ```

2. **Configuration Errors**
   ```bash
   # Check if config files exist
   dir db_handler\vault\
   # Create missing directories
   mkdir db_handler\vault
   ```

3. **Permission Errors**
   ```bash
   # Run with proper permissions
   # Make sure AWS credentials are configured
   aws configure
   ```

4. **Port Already in Use**
   ```bash
   # Change port in launch.py or kill existing process
   netstat -ano | findstr :5001
   taskkill /PID <PID> /F
   ```

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:5001/internal/v1/health
```

### Logs
- Application logs: `newsletter.log`
- Console output shows real-time status

### Metrics
The application tracks:
- Newsletter generation time
- Email sending success/failure rates
- Subscriber count
- System health status

## 🔒 Security Notes

1. **Never commit secrets** to version control
2. **Use environment variables** in production
3. **Rotate API keys** regularly
4. **Enable HTTPS** in production
5. **Use AWS Secrets Manager** for production secrets

## 🚀 Production Deployment

For production deployment:

1. **Use Docker**:
   ```bash
   docker build -t newsletter-app .
   docker run -p 5001:5001 newsletter-app
   ```

2. **Set environment variables**:
   ```bash
   export SENDGRID_API_KEY=your_key
   export AWS_REGION=us-east-1
   export LOG_LEVEL=WARNING
   ```

3. **Use a process manager**:
   ```bash
   # Install PM2 or similar
   pm2 start run.py --name newsletter-app
   ```

## 📞 Support

If you encounter issues:
1. Check the logs in `newsletter.log`
2. Verify configuration files exist and are valid
3. Test API endpoints with curl
4. Check system health endpoint