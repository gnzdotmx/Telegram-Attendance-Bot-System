import os
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from telegram import Update, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database configuration from environment variables.
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://user:password@postgres:5432/attendance_db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Attendance model
class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    masked_uid = Column(String, index=True)
    username = Column(String)
    check_in = Column(DateTime, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)

# Add retry decorator for database initialization
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

# Bot command handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to the Check-in Bot!\n"
        "Commands:\n"
        "/checkin - Check in\n"
        "/checkout - Check out\n"
        "/report - View your attendance records"
    )

def checkin(update: Update, context: CallbackContext):
    employee_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    # Generate a masked UID
    hash_object = hashlib.sha256(employee_id.encode())
    masked_uid = hash_object.hexdigest()[:8].upper()
    
    session = SessionLocal()
    try:
        # Prevent duplicate check-ins without checking out
        active = session.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.check_out == None
        ).first()
        if active:
            update.message.reply_text("❌ You already checked in and haven't checked out yet!")
            return

        # Record check-in
        current_time = datetime.utcnow()
        attendance = Attendance(
            employee_id=employee_id,
            masked_uid=masked_uid,
            username=username,
            check_in=current_time
        )
        session.add(attendance)
        session.commit()

        # Format check-in message
        day_of_week = current_time.strftime('%A')
        date_str = current_time.strftime('%B %d, %Y')
        time_str = current_time.strftime('%I:%M %p')
        
        message = (
            f"✅ *Check-in Successful!*\n\n"
            f"👤 *Employee*: {username}\n"
            f"📅 *Day*: {day_of_week}\n"
            f"📆 *Date*: {date_str}\n"
            f"⏰ *Time*: {time_str}\n\n"
            f"_Have a great day at work!_ 🌟"
        )
        
        update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error during checkin: {e}")
        session.rollback()
        update.message.reply_text("❌ An error occurred while checking in. Please try again.")
    finally:
        session.close()

def checkout(update: Update, context: CallbackContext):
    employee_id = str(update.effective_user.id)
    session = SessionLocal()
    try:
        # Find the open attendance record
        active = session.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.check_out == None
        ).first()
        if not active:
            update.message.reply_text("No active check-in found. Please check in first.")
            return

        # Record checkout
        active.check_out = datetime.utcnow()
        session.commit()
        update.message.reply_text(f"Checked out at {active.check_out.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"Error during checkout: {e}")
        session.rollback()
        update.message.reply_text("An error occurred while checking out.")
    finally:
        session.close()

def report(update: Update, context: CallbackContext):
    employee_id = str(update.effective_user.id)
    session = SessionLocal()
    try:
        records = session.query(Attendance).filter(
            Attendance.employee_id == employee_id
        ).all()
        if not records:
            update.message.reply_text("No attendance records found.")
            return

        lines = ["Your attendance records:"]
        for record in records:
            check_in_str = record.check_in.strftime('%Y-%m-%d %H:%M:%S')
            check_out_str = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else "Still Checked In"
            lines.append(f"Check-in: {check_in_str} | Check-out: {check_out_str}")
        update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        update.message.reply_text("An error occurred while generating your report.")
    finally:
        session.close()

def main():
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        return

    # Initialize database with retry
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database after retries: {e}")
        return

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("checkin", checkin))
    dp.add_handler(CommandHandler("checkout", checkout))
    dp.add_handler(CommandHandler("report", report))

    # Optional: set bot commands for Telegram clients
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("checkin", "Check in to work"),
        BotCommand("checkout", "Check out of work"),
        BotCommand("report", "Get your attendance report")
    ]
    updater.bot.set_my_commands(commands)

    updater.start_polling()
    logger.info("Bot started.")
    updater.idle()

if __name__ == '__main__':
    main()