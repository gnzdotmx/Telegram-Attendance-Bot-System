from flask import Flask, render_template
from sqlalchemy import create_engine, func, text
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Use the same database configuration as the bot
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@postgres:5432/attendance_db')
engine = create_engine(DATABASE_URL)

def calculate_duration(check_in, check_out):
    if not check_out:
        return 0
    duration = check_out - check_in
    return duration.total_seconds() / 3600  # Convert to hours

@app.route('/')
def index():
    with engine.connect() as conn:
        # Get all records with calculated durations
        query = text("""
            SELECT 
                masked_uid,
                username,
                DATE(check_in) as date,
                check_in,
                check_out,
                EXTRACT(EPOCH FROM (check_out - check_in))/3600 as duration,
                DATE_TRUNC('week', check_in) as week_start,
                DATE_TRUNC('month', check_in) as month_start
            FROM attendance
            WHERE check_out IS NOT NULL
            ORDER BY check_in DESC
        """)
        
        records = conn.execute(query).fetchall()
        
        # Process records to calculate totals
        daily_totals = {}
        weekly_totals = {}
        monthly_totals = {}
        
        for record in records:
            # Daily totals
            date_key = record.date
            if date_key not in daily_totals:
                daily_totals[date_key] = 0
            daily_totals[date_key] += record.duration
            
            # Weekly totals
            week_key = record.week_start
            if week_key not in weekly_totals:
                weekly_totals[week_key] = 0
            weekly_totals[week_key] += record.duration
            
            # Monthly totals
            month_key = record.month_start
            if month_key not in monthly_totals:
                monthly_totals[month_key] = 0
            monthly_totals[month_key] += record.duration

    return render_template('index.html',
                         records=records,
                         daily_totals=daily_totals,
                         weekly_totals=weekly_totals,
                         monthly_totals=monthly_totals,
                         datetime=datetime,
                         WEEKLY_HOUR_LIMIT=9)  # Add the 9-hour limit as a constant

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3366) 