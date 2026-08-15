import sqlite3
import os
import sys

# Add parent dir to path so config can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

def init_db(db_path=None):
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            mobile TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # 2. Airports / Destinations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS airports (
            code TEXT PRIMARY KEY,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            name TEXT NOT NULL,
            tagline TEXT,
            description TEXT,
            starting_fare REAL,
            image TEXT
        );
    ''')

    # 3. Aircraft
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aircraft (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            manufacturer TEXT,
            capacity INTEGER,
            range_km INTEGER,
            economy_seats INTEGER,
            premium_economy_seats INTEGER,
            business_seats INTEGER,
            first_seats INTEGER,
            amenities TEXT,
            image TEXT
        );
    ''')

    # 4. Flights
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            duration TEXT NOT NULL,
            stops INTEGER DEFAULT 0,
            aircraft TEXT NOT NULL,
            economy_price REAL NOT NULL,
            premium_economy_price REAL NOT NULL,
            business_price REAL NOT NULL,
            first_class_price REAL NOT NULL,
            status TEXT DEFAULT 'On Time',
            available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (origin) REFERENCES airports(code),
            FOREIGN KEY (destination) REFERENCES airports(code),
            FOREIGN KEY (aircraft) REFERENCES aircraft(code)
        );
    ''')

    # 5. Seats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            cabin_class TEXT NOT NULL,
            is_occupied INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0,
            is_exit_row INTEGER DEFAULT 0,
            price_offset REAL DEFAULT 0,
            FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
            UNIQUE(flight_id, seat_number)
        );
    ''')

    # 6. Promo Codes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percent REAL NOT NULL,
            max_discount REAL NOT NULL,
            min_spend REAL DEFAULT 0,
            description TEXT,
            active INTEGER DEFAULT 1
        );
    ''')

    # 7. Bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnr TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            flight_id INTEGER NOT NULL,
            cabin_class TEXT NOT NULL,
            fare_type TEXT NOT NULL,
            booking_status TEXT DEFAULT 'PENDING',
            base_fare REAL NOT NULL,
            taxes REAL NOT NULL,
            extras REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (flight_id) REFERENCES flights(id)
        );
    ''')

    # 8. Booking Passengers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            nationality TEXT NOT NULL,
            passport_number TEXT,
            seat_number TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );
    ''')

    # 9. Baggage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS baggage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            passenger_id INTEGER NOT NULL,
            weight_kg INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
            FOREIGN KEY (passenger_id) REFERENCES booking_passengers(id) ON DELETE CASCADE
        );
    ''')

    # 10. Meals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            passenger_id INTEGER NOT NULL,
            meal_code TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            price REAL DEFAULT 0,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
            FOREIGN KEY (passenger_id) REFERENCES booking_passengers(id) ON DELETE CASCADE
        );
    ''')

    # 11. Add-ons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_addons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            addon_type TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );
    ''')

    # 12. Payments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            transaction_id TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            payment_mode TEXT DEFAULT 'DEMO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );
    ''')

    # 13. Checkins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            passenger_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            boarding_pass_code TEXT UNIQUE NOT NULL,
            gate TEXT DEFAULT 'G12',
            terminal TEXT DEFAULT 'T2',
            checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
            FOREIGN KEY (passenger_id) REFERENCES booking_passengers(id) ON DELETE CASCADE
        );
    ''')

    # 14. AeroRewards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aero_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            points_balance INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'Blue',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

    # 15. Contact Messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Unread',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # 16. Newsletter Subscribers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    conn.commit()
    conn.close()
    print(f"[Aeronexa DB] Database successfully initialized at {db_path}")

if __name__ == '__main__':
    init_db()
