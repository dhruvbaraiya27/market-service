# Market Data Service

A production-ready microservice that fetches real-time market data, processes it through a streaming pipeline, and serves it via REST APIs. Built with FastAPI, Kafka, PostgreSQL, and Docker.

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI   │────▶│Market APIs │
│  (Browser)  │     │   Service   │     │(Alpha/Test)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ PostgreSQL  │
                    │  Database   │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Kafka    │
                    │Message Queue│
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Consumer   │
                    │(MA Calculator)│
                    └─────────────┘
```

## ✨ Features

- **Real-time Price Fetching**: Get latest stock prices from multiple providers
- **Background Polling**: Automatically fetch prices at configurable intervals
- **Streaming Pipeline**: Process price data through Kafka for scalability
- **Moving Averages**: Calculate 5-point moving averages in real-time
- **Multiple Providers**: Support for Alpha Vantage, YFinance, Finnhub, and Test provider
- **RESTful API**: Clean API design with automatic documentation
- **Containerized**: Fully Dockerized for easy deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd market-data-service
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements/base.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys (optional, test provider works without keys)
```

5. **Start Docker services**
```bash
docker-compose up -d
```

6. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

7. **Start the consumer (in a new terminal)**
```bash
python scripts/run_consumer.py
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Get Latest Price
```http
GET /api/v1/prices/latest?symbol={symbol}&provider={provider}
```

**Parameters:**
- `symbol` (required): Stock symbol (e.g., AAPL, MSFT)
- `provider` (optional): Market data provider (alpha_vantage, yfinance, finnhub, test)

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "timestamp": "2024-03-20T10:30:00Z",
  "provider": "test"
}
```

### Create Polling Job
```http
POST /api/v1/prices/poll
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT"],
  "interval": 60,
  "provider": "test"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "poll_123",
  "status": "accepted",
  "config": {
    "symbols": ["AAPL", "MSFT"],
    "interval": 60,
    "provider": "test"
  }
}
```

### Get Polling Job Status
```http
GET /api/v1/prices/poll/{job_id}
```

### Stop Polling Job
```http
DELETE /api/v1/prices/poll/{job_id}
```

## 🗄️ Database Schema

### Tables

1. **raw_market_data**: Stores raw API responses
2. **price_points**: Stores processed price data
3. **moving_averages**: Stores calculated moving averages
4. **polling_jobs**: Stores polling job configurations

## 🔧 Configuration

Configuration is managed through environment variables in `.env`:

```env
# API Configuration
APP_NAME="Market Data Service"
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/market_data

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PRICE_EVENTS=price-events

# Market Data Providers
ALPHA_VANTAGE_API_KEY=your_key_here  # Optional
FINNHUB_API_KEY=your_key_here        # Optional
DEFAULT_PROVIDER=test                 # Use 'test' for development
```

## 🧪 Testing

### Run all tests
```bash
# Test the complete flow
python scripts/test_kafka_flow.py

# Test polling functionality
python scripts/test_polling.py

# Test endpoints
python scripts/test_endpoints.py
```

### Manual testing with curl
```bash
# Get a price
curl "http://localhost:8000/api/v1/prices/latest?symbol=AAPL&provider=test"

# Create a polling job
curl -X POST "http://localhost:8000/api/v1/prices/poll" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"], "interval": 30, "provider": "test"}'
```

## 📊 Monitoring

### Kafka UI
Access Kafka UI at `http://localhost:8080` to monitor:
- Topics and messages
- Consumer groups
- Message flow

### Database Queries
```sql
-- Check recent prices
SELECT * FROM price_points ORDER BY created_at DESC LIMIT 10;

-- Check moving averages
SELECT * FROM moving_averages ORDER BY calculated_at DESC LIMIT 10;

-- Monitor polling jobs
SELECT * FROM polling_jobs WHERE status = 'running';
```

## 🐳 Docker Services

The `docker-compose.yml` includes:
- **PostgreSQL**: Primary database
- **Redis**: Cache layer (ready for implementation)
- **Kafka**: Message broker
- **Zookeeper**: Kafka coordinator
- **Kafka UI**: Visual monitoring interface

## 🏭 Production Deployment

### Using Docker

1. **Build the application image**
```bash
docker build -t market-data-service .
```

2. **Run with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
- Set `DEBUG=false`
- Use strong passwords for PostgreSQL
- Configure proper API keys
- Set up SSL/TLS for external endpoints

## 🔍 Troubleshooting

### Common Issues

1. **Kafka consumer not receiving messages**
   - Check if Kafka is running: `docker-compose ps`
   - Verify topic exists: Check Kafka UI
   - Check consumer logs for errors

2. **Price fetching fails**
   - Verify API keys in `.env`
   - Check provider status
   - Use 'test' provider for development

3. **Moving averages not calculated**
   - Ensure you have at least 5 prices for a symbol
   - Check consumer is running
   - Verify Kafka connectivity

## 🛠️ Development

### Project Structure
```
market-data-service/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core configuration
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic
├── scripts/              # Utility scripts
├── tests/                # Test files
├── docker-compose.yml    # Docker services
└── requirements/         # Python dependencies
```

### Adding a New Provider

1. Create provider class in `app/services/providers/`
2. Implement `MarketDataProvider` interface
3. Add to `MarketDataService` in `market_data_service.py`
4. Update schema enum in `schemas/market_data.py`

## 📈 Performance Considerations

- Kafka enables horizontal scaling of consumers
- PostgreSQL indexes on symbol and timestamp for fast queries
- Redis cache ready for implementation
- Configurable polling intervals to manage API rate limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Dhruv Baraiya

## 🙏 Acknowledgments

- Built for Blockhouse Capital Software Engineer Intern Assignment
- FastAPI for the excellent web framework
- Confluent for Kafka Python client
