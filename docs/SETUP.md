# SMARTII Setup & Deployment Guide

## Quick Start (5 minutes)

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- Git

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/smartii.git
cd smartii
```

2. **Set up Python backend**:
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r ../requirements.txt
```

3. **Configure environment variables**:
```bash
# Create .env file in backend/
cp .env.example .env

# Edit .env with your API keys:
# GROQ_API_KEY=your_groq_key
# OPENAI_API_KEY=your_openai_key  # Optional fallback
# OPENWEATHER_API_KEY=your_weather_key
# G_NEWS_API_KEY=your_news_key
```

4. **Run the backend**:
```bash
python app.py
# Backend runs on http://localhost:8000
```

5. **In a new terminal, set up frontend** (optional):
```bash
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

6. **Test the system**:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Smartii!", "client_id": "test"}'
```

---

## Full Stack Setup (with all services)

### 1. Install Dependencies

**Windows**:
```powershell
# Install Python 3.9+
winget install Python.Python.3.9

# Install Node.js
winget install OpenJS.NodeJS

# Install Go (optional, for worker)
winget install GoLang.Go

# Install Docker Desktop (optional)
winget install Docker.DockerDesktop
```

**Linux (Ubuntu/Debian)**:
```bash
# Python
sudo apt update
sudo apt install python3.9 python3-pip python3-venv

# Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# Go (optional)
wget https://go.dev/dl/go1.20.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.20.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Database Setup (Optional for Full Features)

**Using Docker Compose**:
```bash
# Start all infrastructure services
docker-compose up -d

# Services started:
# - PostgreSQL (port 5432)
# - MongoDB (port 27017)
# - Redis (port 6379)
# - ChromaDB (port 8001)
# - Mosquitto MQTT (ports 1883, 9001)
```

**Manual Setup**:

**PostgreSQL**:
```bash
# Install
sudo apt install postgresql

# Create database
sudo -u postgres createdb smartii
sudo -u postgres psql -c "CREATE USER smartii_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smartii TO smartii_user;"
```

**Redis**:
```bash
# Install
sudo apt install redis-server

# Start
sudo systemctl start redis-server
```

**MongoDB**:
```bash
# Install
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start
sudo systemctl start mongod
```

### 3. Environment Configuration

Create `backend/.env`:
```env
# AI Providers (at least one required)
GROQ_API_KEY=gsk_your_groq_api_key
OPENAI_API_KEY=sk-your_openai_api_key

# External APIs
OPENWEATHER_API_KEY=your_weather_api_key
G_NEWS_API_KEY=your_gnews_api_key

# Databases (optional, uses fallbacks if not provided)
DATABASE_URL=postgresql://smartii_user:password@localhost:5432/smartii
MONGO_URL=mongodb://localhost:27017/smartii
REDIS_URL=redis://localhost:6379

# Home Automation (optional)
HA_BASE_URL=http://localhost:8123
HA_TOKEN=your_home_assistant_token
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=
MQTT_PASS=

# Security
SECRET_KEY=your_secret_key_here
```

### 4. Run Services

**Using PowerShell Script (Windows)**:
```powershell
# Simple startup
.\scripts\start_stack.ps1

# Skip dependency installation (faster restarts)
.\scripts\start_stack.ps1 -SkipInstall
```

**Manual Startup**:

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

**Terminal 2 - Node Realtime Gateway** (optional):
```bash
cd node-realtime
npm install
npm start
```

**Terminal 3 - Go Worker** (optional):
```bash
cd go-worker
go run main.go
```

**Terminal 4 - Frontend** (optional):
```bash
cd frontend
npm install
npm start
```

---

## API Keys Setup

### Required APIs

**Groq AI** (Recommended - Fast & Free Tier):
1. Visit https://console.groq.com/
2. Sign up for free account
3. Generate API key
4. Add to `.env`: `GROQ_API_KEY=gsk_...`

**OpenAI** (Optional Fallback):
1. Visit https://platform.openai.com/
2. Create account
3. Generate API key
4. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Optional APIs

**OpenWeatherMap** (Weather):
1. Visit https://openweathermap.org/api
2. Sign up for free tier
3. Get API key
4. Add to `.env`: `OPENWEATHER_API_KEY=...`

**GNews** (News):
1. Visit https://gnews.io/
2. Sign up for free tier
3. Get API key
4. Add to `.env`: `G_NEWS_API_KEY=...`

---

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Test
```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What's the weather in New York?",
    "client_id": "test_user"
  }'
```

### Action Execution Test
```bash
curl -X POST http://localhost:8000/v1/actions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "weather.get",
    "params": {"location": "London"}
  }'
```

### Memory Test
```bash
# Save memory
curl -X POST http://localhost:8000/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "action": "save",
    "item": {
      "kind": "preference",
      "user_id": "test_user",
      "content": "Likes coffee in the morning"
    }
  }'

# Query memory
curl -X POST http://localhost:8000/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query",
    "query": "coffee preferences",
    "user_id": "test_user"
  }'
```

---

## Deployment

### Production Deployment

**Docker**:
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale go-worker=3
```

**Kubernetes** (Coming Soon):
```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n smartii
```

### Cloud Platforms

**AWS**:
- Deploy backend on EC2 or ECS
- Use RDS for PostgreSQL
- Use ElastiCache for Redis
- Use DocumentDB for MongoDB

**Google Cloud**:
- Deploy on Cloud Run
- Use Cloud SQL
- Use Memorystore

**Azure**:
- Deploy on Azure Container Instances
- Use Azure Database for PostgreSQL
- Use Azure Cache for Redis

---

## Troubleshooting

### Backend Won't Start

**Issue**: Python dependencies not installed
```bash
cd backend
pip install -r ../requirements.txt
```

**Issue**: Port 8000 already in use
```bash
# Find process
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or change port in app.py
```

### Frontend Won't Start

**Issue**: Node modules not installed
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Port 3000 already in use
```bash
# Change port
PORT=3001 npm start  # Linux/Mac
set PORT=3001 && npm start  # Windows
```

### Database Connection Errors

**Issue**: PostgreSQL not running
```bash
sudo systemctl start postgresql
```

**Issue**: Connection refused
- Check DATABASE_URL in `.env`
- Verify PostgreSQL is listening: `sudo netstat -plnt | grep 5432`

### Audio Not Working

**Issue**: Microphone permission denied
- Grant microphone permission in browser
- Check system audio settings

**Issue**: Audio libraries missing
```bash
pip install pyaudio  # May need system dependencies
sudo apt install portaudio19-dev  # Linux
brew install portaudio  # Mac
```

---

## Development Tips

### Enable Developer Mode
```bash
curl -X POST http://localhost:8000/v1/mode \
  -H "Content-Type: application/json" \
  -d '{"developer": true}'
```

### View Logs
```bash
# Backend
cd backend
python app.py  # Logs to console

# Docker logs
docker-compose logs -f smartii-backend
```

### Hot Reload
Backend uses uvicorn with `reload=True` by default in development.

### Database Migrations
```bash
cd backend
python -c "from db.db import init_db; init_db()"
```

---

## Performance Optimization

### Backend
- Use Groq for fastest LLM responses
- Enable Redis caching
- Use vector database for memory queries
- Scale with multiple workers

### Frontend
- Enable production build: `npm run build`
- Use CDN for static assets
- Enable service workers for offline support

### Database
- Add indexes on frequently queried fields
- Regular vacuum/analyze for PostgreSQL
- Use connection pooling

---

## Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Enable HTTPS in production
- [ ] Set up firewall rules
- [ ] Implement rate limiting
- [ ] Enable JWT authentication
- [ ] Regular security updates
- [ ] Audit log monitoring
- [ ] Data encryption at rest

---

## Support & Resources

- **Documentation**: `/docs` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **API Reference**: `/docs/API.md`

---

*Happy building with SMARTII! 🚀*
