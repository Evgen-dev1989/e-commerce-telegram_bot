# 🤖 E-Commerce Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![aiogram](https://img.shields.io/badge/aiogram-3.21.0-green.svg)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-336791.svg)](https://www.postgresql.org/)

A comprehensive Telegram bot for tracking luxury watch prices from premium brands including **Omega**, **Rolex**, and **Jaeger-LeCoultre**. The bot provides real-time price monitoring, multilingual support, and personalized watch lists with automated notifications.

## 🌟 Features

### Core Functionality
- 🔍 **Real-time Price Tracking** - Monitor prices across multiple luxury watch brands
- 🌐 **Multilingual Support** - Available in English, Russian, Ukrainian, and Polish
- 📱 **Interactive Interface** - Intuitive inline keyboards and user-friendly navigation
- 💾 **Personal Watch Lists** - Save favorite watches and track their price changes
- 🔔 **Automated Notifications** - Get notified when prices change or new models are available
- 🎯 **Advanced Filtering** - Filter watches by price range, brand, and availability

### Supported Brands
- **Omega** - Complete collection with real-time pricing
- **Rolex** - Premium watches with availability tracking
- **Jaeger-LeCoultre** - Luxury timepieces with detailed specifications

## 🛠 Technology Stack

### Backend
- **Python 3.12** - Core programming language
- **aiogram 3.21.0** - Modern Telegram Bot API framework
- **asyncio** - Asynchronous programming for high performance
- **asyncpg 0.30.0** - PostgreSQL async driver

### Web Scraping
- **Selenium WebDriver 4.15.0** - Browser automation
- **undetected-chromedriver 3.5.0** - Anti-detection Chrome driver
- **lxml 5.3.0** - XML/HTML processing
- **requests 2.32.0** - HTTP library for API calls

### Database
- **PostgreSQL 13** - Primary database
- **asyncpg** - Async PostgreSQL adapter
- **psycopg2 2.9.9** - PostgreSQL adapter

### DevOps & Deployment
- **Docker** - Containerization
- **docker-compose** - Multi-container orchestration
- **Chrome Headless** - Browser automation in containers

### Additional Libraries
- **python-dotenv 1.0.0** - Environment variable management

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- PostgreSQL (or use Docker Compose)

### 1. Clone Repository
```bash
git clone https://github.com/Evgen-dev1989/e-commerce-telegram_bot.git
cd e-commerce-telegram_bot
```

### 2. Environment Setup
Create a `.env` file in the project root:
```env
# Telegram Bot Configuration
token=YOUR_TELEGRAM_BOT_TOKEN

# Database Configuration
user=postgres
password=your_secure_password
database=telegram_bot
host=localhost
port=5432
```

### 3. Docker Deployment (Recommended)
```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

### 4. Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations (ensure PostgreSQL is running)
python main.py
```

## 📋 Installation Details

### System Requirements
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 1GB free space
- **Network**: Stable internet connection for web scraping

### Docker Configuration
The application uses a multi-stage Docker setup:
- **Base Image**: `python:3.12-slim`
- **Chrome Installation**: Google Chrome Stable + ChromeDriver
- **Security**: Non-root user execution
- **Health Checks**: PostgreSQL connection validation

### Database Schema
```sql
-- Users table
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watches table
CREATE TABLE watches (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    url TEXT,
    user_id BIGINT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎮 Bot Commands

### Basic Commands
- `/start` - Initialize bot and select language
- `/help` - Show available commands and features
- `/language` - Change interface language

### Watch Management
- **Browse Watches** - View available watches by brand
- **Add to Favorites** - Save watches to personal list
- **Price Alerts** - Set up price change notifications
- **Search Filters** - Filter by price range and availability

## 🌐 Multilingual Support

The bot supports 4 languages with complete localization:

| Language | Code | Coverage |
|----------|------|----------|
| English | `en` | 100% |
| Russian | `ru` | 100% |
| Ukrainian | `uk` | 100% |
| Polish | `pl` | 100% |

### Language Features
- **Dynamic Switching** - Change language anytime
- **Persistent Settings** - Language preference saved per user
- **Complete Localization** - All messages, buttons, and notifications
- **Cultural Adaptation** - Currency and date formats

## 🔧 Configuration

### Environment Variables
```env
# Required
token=your_telegram_bot_token
user=database_username
password=database_password
database=database_name
host=database_host
port=database_port

# Optional
DEBUG=true
LOG_LEVEL=INFO
SCRAPING_INTERVAL=3600  # seconds
```

### Scraping Configuration
- **Request Delay**: 2-5 seconds between requests
- **Anti-Detection**: Randomized user agents and headers
- **Error Handling**: Automatic retry with exponential backoff
- **Rate Limiting**: Respectful scraping practices

## 📊 Architecture

### Application Structure
```
├── main.py              # Core bot application
├── words.py             # Multilingual support
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Multi-service setup
└── .env               # Environment variables
```

### Design Patterns
- **FSM (Finite State Machine)** - User interaction flow
- **MVC Pattern** - Separation of concerns
- **Async/Await** - Non-blocking operations
- **Factory Pattern** - Dynamic scraper selection

### Performance Features
- **Connection Pooling** - Database connection optimization
- **Async Operations** - Concurrent request handling
- **Caching** - In-memory price data caching
- **Background Tasks** - Scheduled price monitoring

## 🛡 Security Features

### Data Protection
- **Environment Variables** - Sensitive data protection
- **SQL Injection Prevention** - Parameterized queries
- **Input Validation** - User input sanitization
- **Secure Headers** - HTTP security headers

### Operational Security
- **Non-root Containers** - Docker security best practices
- **Network Isolation** - Container networking
- **Log Sanitization** - No sensitive data in logs
- **Regular Updates** - Dependency security updates

## 📈 Monitoring & Logging

### Logging Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks
- **Database Connectivity** - PostgreSQL health monitoring
- **Bot Status** - Telegram API connection status
- **Scraping Health** - Website availability checks
- **Container Health** - Docker health checks

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `pytest tests/`
5. Submit a pull request

### Code Standards
- **PEP 8** - Python style guide compliance
- **Type Hints** - Full type annotation
- **Docstrings** - Comprehensive documentation
- **Testing** - Unit and integration tests

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **aiogram community** - Excellent Telegram Bot framework
- **Selenium maintainers** - Reliable web automation
- **PostgreSQL team** - Robust database system
- **Docker community** - Containerization platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Evgen-dev1989/e-commerce-telegram_bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Evgen-dev1989/e-commerce-telegram_bot/discussions)
- **Email**: [your-email@example.com]

## 🔄 Changelog

### Version 1.0.0 (Current)
- ✅ Initial release with full functionality
- ✅ Multi-brand watch tracking
- ✅ Multilingual support (4 languages)
- ✅ Docker containerization
- ✅ PostgreSQL integration
- ✅ Automated price monitoring

---

**Made with ❤️ by [Evgen-dev1989](https://github.com/Evgen-dev1989)**
