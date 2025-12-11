import psycopg2
from datetime import datetime, timedelta

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="lms",
    user="postgres",
    password="1111"
)

cur = conn.cursor()

# Check current state of effective_from and effective_until
print("Checking class_schedules dates...")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(effective_from) as with_from,
        COUNT(effective_until) as with_until
    FROM class_schedules
""")
result = cur.fetchone()
print(f"Total schedules: {result[0]}")
print(f"With effective_from: {result[1]}")
print(f"With effective_until: {result[2]}")

# Check a few sample records
print("\nSample records:")
cur.execute("""
    SELECT id, day_of_week, start_time, end_time, effective_from, effective_until
    FROM class_schedules 
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Day: {row[1]}, Time: {row[2]}-{row[3]}, From: {row[4]}, Until: {row[5]}")

# Update schedules that don't have dates
# Academic year: September 15, 2024 to June 14, 2025 (current academic year)
academic_start = datetime(2024, 9, 15).date()
academic_end = datetime(2025, 6, 14).date()

print(f"\nUpdating schedules without dates to: {academic_start} - {academic_end}")

cur.execute("""
    UPDATE class_schedules
    SET 
        effective_from = %s,
        effective_until = %s,
        is_recurring = true
    WHERE effective_from IS NULL OR effective_until IS NULL
""", (academic_start, academic_end))

affected = cur.rowcount
print(f"Updated {affected} records")

conn.commit()

# Verify update
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(effective_from) as with_from,
        COUNT(effective_until) as with_until
    FROM class_schedules
""")
result = cur.fetchone()
print(f"\nAfter update:")
print(f"Total schedules: {result[0]}")
print(f"With effective_from: {result[1]}")
print(f"With effective_until: {result[2]}")

cur.close()
conn.close()

print("\nDone!")
