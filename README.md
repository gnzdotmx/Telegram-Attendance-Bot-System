# 🤖 Attendance Bot System

A Telegram bot system for tracking employee attendance with a web monitoring interface.

## 📋 Features

- ✅ Check-in via Telegram command
- 🚪 Check-out tracking
- 📊 Web monitoring interface
- 📈 Daily, weekly, and monthly reports
- ⏰ Working hours tracking
- 🚨 Overtime alerts (>9 hours/week)
- 🔒 Privacy-focused with masked user IDs

![demo](src/demo.gif)

## 🛠️ Prerequisites

- Docker and Docker Compose
- Telegram account
- Git (for cloning the repository)

## 🔧 Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to:
   - Set a name for your bot
   - Choose a username (must end in 'bot')
4. Save the API token provided by BotFather

### 2. Configure Environment

1. Clone this repository:
```bash
git clone https://github.com/gnzdotmx/Telegram-Attendance-Bot-System.git
cd Telegram-Attendance-Bot-System
```

2. Update `docker-compose.yml` with your credentials:
```yaml
environment:
  - TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. 🚀 Launch the System

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## 💻 Usage

### Telegram Commands

- `/start` - Initialize the bot and see available commands
- `/checkin` - Record attendance check-in
- `/checkout` - Record attendance check-out
- `/report` - View personal attendance history

### 🌐 Web Monitor

Access the monitoring dashboard at:
```
http://localhost:3366
```

Features:
- View all attendance records
- Track daily, weekly, and monthly hours
- Red highlighting for weeks exceeding 9 hours
- Privacy-focused display (no employee IDs shown)
- Real-time updates of check-in/check-out records

## 🗃️ Database Management

### View Records
```bash
# Connect to database
docker compose exec postgres psql -U postgres -d attendance_db

# Common queries
-- View all records
SELECT * FROM attendance;

-- View today's attendance
SELECT * FROM attendance 
WHERE DATE(check_in) = CURRENT_DATE;

-- View active check-ins
SELECT * FROM attendance 
WHERE check_out IS NULL;

-- View weekly totals
SELECT 
    username,
    DATE_TRUNC('week', check_in) as week,
    SUM(EXTRACT(EPOCH FROM (check_out - check_in))/3600) as total_hours
FROM attendance 
WHERE check_out IS NOT NULL
GROUP BY username, DATE_TRUNC('week', check_in)
ORDER BY week DESC;
```

### Reset Database
```bash
# Complete reset (removes all data)
docker compose down -v
docker compose up --build -d

# Or using SQL (keeps container running)
docker compose exec postgres psql -U postgres -d attendance_db -c "TRUNCATE TABLE attendance RESTART IDENTITY;"
```

### Test Data
```sql
-- Insert test check-in/out records
INSERT INTO attendance (employee_id, masked_uid, username, check_in, check_out) 
VALUES 
('12345', 'A1B2C3D4', 'testuser', '2025-02-24 09:00:00', '2025-02-24 19:00:00'),
('12345', 'A1B2C3D4', 'testuser', '2025-02-25 08:00:00', '2025-02-25 18:00:00'),
('12345', 'A1B2C3D4', 'testuser', '2025-02-26 09:00:00', '2025-02-26 19:00:00');
```

## 📁 Project Structure

```
attendance-bot/
├── app.py                  # Main bot application
├── monitor/               # Web monitoring interface
│   ├── app.py            # Monitor application
│   └── templates/        # HTML templates
│       └── index.html    # Dashboard template
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Service orchestration
└── requirements.txt      # Python dependencies
```

## 🔒 Security Features

- Employee IDs are masked in the database and interface
- Database credentials managed via environment variables
- Containerized services for isolation
- Health checks for database connection
- Automatic service recovery
- No sensitive data exposed in web interface

## ⚠️ Important Notes

- All times are stored in UTC
- Week is defined as Monday-Friday
- Overtime alert threshold is 9 hours/week
- Masked UIDs are generated using SHA-256 hashing
- Database persists data using Docker volumes
- Web interface refreshes on page load

## 🐛 Troubleshooting

1. Bot not responding:
```bash
# Check bot logs
docker compose logs bot
# Verify bot token in docker-compose.yml
# Ensure bot is running
docker compose ps
```

2. Monitor issues:
```bash
# Check monitor logs
docker compose logs monitor
# Verify port 3366 is available
# Access http://localhost:3366
```

3. Database problems:
```bash
# Check database logs
docker compose logs postgres
# Reset database if needed
docker compose down -v
docker compose up --build -d
```

## 🔄 Updates and Maintenance

1. Pull latest changes:
```bash
git pull origin main
```

2. Rebuild services:
```bash
docker compose down
docker compose up --build -d
```

3. Backup database:
```bash
docker compose exec postgres pg_dump -U postgres attendance_db > backup.sql
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
