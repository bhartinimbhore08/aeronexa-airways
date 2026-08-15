import sqlite3
import json
import os
import sys
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from database.init_db import init_db

def seed_db(db_path=None):
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data')

    # Seed Admin and Demo User
    admin_pw = generate_password_hash('Admin@123')
    user_pw = generate_password_hash('Demo@123')

    cursor.execute("INSERT OR IGNORE INTO users (id, name, email, password_hash, mobile, role) VALUES (1, 'Aeronexa Admin', 'admin@aeronexa.com', ?, '+919876543210', 'admin')", (admin_pw,))
    cursor.execute("INSERT OR IGNORE INTO users (id, name, email, password_hash, mobile, role) VALUES (2, 'Bharti Nimbhore', 'demo@aeronexa.com', ?, '+919876543211', 'user')", (user_pw,))
    cursor.execute("INSERT OR IGNORE INTO aero_rewards (user_id, points_balance, tier) VALUES (2, 12450, 'Gold')")

    # Seed Airports / Destinations
    dest_file = os.path.join(data_dir, 'destinations.json')
    if os.path.exists(dest_file):
        with open(dest_file, 'r', encoding='utf-8') as f:
            destinations = json.load(f)
            for d in destinations:
                cursor.execute('''
                    INSERT OR REPLACE INTO airports (code, city, country, name, tagline, description, starting_fare, image)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (d['code'], d['city'], d['country'], d['airport'], d['tagline'], d['description'], d['starting_fare'], d['image']))

    # Seed Aircraft
    aircraft_file = os.path.join(data_dir, 'aircraft.json')
    if os.path.exists(aircraft_file):
        with open(aircraft_file, 'r', encoding='utf-8') as f:
            aircrafts = json.load(f)
            for a in aircrafts:
                cursor.execute('''
                    INSERT OR REPLACE INTO aircraft (code, name, manufacturer, capacity, range_km, economy_seats, premium_economy_seats, business_seats, first_seats, amenities, image)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (a['code'], a['name'], a['manufacturer'], a['capacity'], a['range_km'], a['economy_seats'], a['premium_economy_seats'], a['business_seats'], a['first_seats'], json.dumps(a['amenities']), a['image']))

    # Seed Promo Codes
    promo_file = os.path.join(data_dir, 'promotions.json')
    if os.path.exists(promo_file):
        with open(promo_file, 'r', encoding='utf-8') as f:
            promos = json.load(f)
            for p in promos:
                cursor.execute('''
                    INSERT OR REPLACE INTO promo_codes (code, discount_percent, max_discount, min_spend, description, active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (p['code'], p['discount_percent'], p['max_discount'], p['min_spend'], p['description']))

    # Seed Flights
    flights_file = os.path.join(data_dir, 'flights.json')
    flight_ids = []
    if os.path.exists(flights_file):
        with open(flights_file, 'r', encoding='utf-8') as f:
            flights = json.load(f)
            for fl in flights:
                cursor.execute('''
                    INSERT OR REPLACE INTO flights (flight_number, origin, destination, departure_time, arrival_time, duration, stops, aircraft, economy_price, premium_economy_price, business_price, first_class_price, status, available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fl['flight_number'], fl['origin'], fl['destination'], fl['departure_time'], fl['arrival_time'],
                    fl['duration'], fl['stops'], fl['aircraft'], fl['economy_price'], fl['premium_economy_price'],
                    fl['business_price'], fl['first_class_price'], fl['status'], fl['available']
                ))
                flight_ids.append(cursor.lastrowid)

    # Seed Seats for each flight
    # Seat map generator:
    # First Class: Rows 01-02 (A, B, E, F)
    # Business Class: Rows 03-05 (A, B, D, E, F)
    # Premium Economy: Rows 06-08 (A, B, C, D, E, F) - Exit Row 06
    # Economy: Rows 10-25 (A, B, C, D, E, F) - Exit Row 10
    cursor.execute("SELECT id FROM flights")
    all_flights = [row[0] for row in cursor.fetchall()]

    for fid in all_flights:
        # First Class (Rows 01 to 02)
        for r in range(1, 3):
            row_str = f"{r:02d}"
            for col in ['A', 'B', 'E', 'F']:
                seat_no = f"{row_str}{col}"
                cursor.execute('''
                    INSERT OR IGNORE INTO seats (flight_id, seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset)
                    VALUES (?, ?, 'first', 0, 1, 0, 1500)
                ''', (fid, seat_no))

        # Business Class (Rows 03 to 05)
        for r in range(3, 6):
            row_str = f"{r:02d}"
            for col in ['A', 'B', 'D', 'E', 'F']:
                seat_no = f"{row_str}{col}"
                cursor.execute('''
                    INSERT OR IGNORE INTO seats (flight_id, seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset)
                    VALUES (?, ?, 'business', 0, 1, 0, 1000)
                ''', (fid, seat_no))

        # Premium Economy (Rows 06 to 08)
        for r in range(6, 9):
            row_str = f"{r:02d}"
            is_exit = 1 if r == 6 else 0
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                seat_no = f"{row_str}{col}"
                cursor.execute('''
                    INSERT OR IGNORE INTO seats (flight_id, seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset)
                    VALUES (?, ?, 'premium_economy', 0, 0, ?, ?)
                ''', (fid, seat_no, is_exit, 500 if is_exit else 300))

        # Economy (Rows 10 to 22)
        for r in range(10, 23):
            row_str = f"{r:02d}"
            is_exit = 1 if r == 10 else 0
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                seat_no = f"{row_str}{col}"
                # Randomly occupy a few seats to make UI look realistic
                is_occ = 1 if (r in [11, 14] and col in ['B', 'E']) else 0
                cursor.execute('''
                    INSERT OR IGNORE INTO seats (flight_id, seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset)
                    VALUES (?, ?, 'economy', ?, 0, ?, ?)
                ''', (fid, seat_no, is_occ, is_exit, 400 if is_exit else 0))

    # Seed one sample confirmed booking for demo user
    sample_pnr = "AX7K9P"
    cursor.execute('''
        INSERT OR IGNORE INTO bookings (pnr, user_id, flight_id, cabin_class, fare_type, booking_status, base_fare, taxes, extras, discount, total_amount, payment_status)
        VALUES (?, 2, 1, 'economy', 'Flex', 'CONFIRMED', 58500, 6300, 1300, 2000, 64100, 'SUCCESS')
    ''', (sample_pnr,))

    cursor.execute("SELECT id FROM bookings WHERE pnr = ?", (sample_pnr,))
    b_row = cursor.fetchone()
    if b_row:
        b_id = b_row[0]
        cursor.execute('''
            INSERT OR IGNORE INTO booking_passengers (booking_id, title, first_name, middle_name, last_name, dob, gender, nationality, passport_number, seat_number)
            VALUES (?, 'Ms.', 'Bharti', '', 'Nimbhore', '1995-06-15', 'Female', 'Indian', 'Z9876543', '14A')
        ''', (b_id,))

        cursor.execute("SELECT id FROM booking_passengers WHERE booking_id = ?", (b_id,))
        p_row = cursor.fetchone()
        if p_row:
            p_id = p_row[0]
            cursor.execute("INSERT OR IGNORE INTO baggage (booking_id, passenger_id, weight_kg, price) VALUES (?, ?, 15, 800)", (b_id, p_id))
            cursor.execute("INSERT OR IGNORE INTO meals (booking_id, passenger_id, meal_code, meal_name, price) VALUES (?, ?, 'VEG', 'Vegetarian Gourmet Meal', 500)", (b_id, p_id))

        cursor.execute('''
            INSERT OR IGNORE INTO payments (booking_id, transaction_id, amount, currency, payment_method, payment_status, payment_mode)
            VALUES (?, 'AXPAY-8F29K1', 64100, 'INR', 'UPI', 'SUCCESS', 'DEMO')
        ''', (b_id,))

    conn.commit()
    conn.close()
    print(f"[Aeronexa DB] Database successfully seeded at {db_path}")

if __name__ == '__main__':
    seed_db()
