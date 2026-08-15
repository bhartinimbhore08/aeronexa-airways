import os
import sqlite3
import random
import string
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Database Connection Helper
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# PNR & Transaction ID Generators
def generate_pnr():
    chars = string.ascii_uppercase + string.digits
    while True:
        pnr = 'AX' + ''.join(random.choices(chars, k=5))
        db = get_db()
        cur = db.execute("SELECT id FROM bookings WHERE pnr = ?", (pnr,))
        if not cur.fetchone():
            return pnr

def generate_transaction_id():
    chars = string.ascii_uppercase + string.digits
    return 'AXPAY-' + ''.join(random.choices(chars, k=6))

def generate_boarding_pass_code():
    chars = string.ascii_uppercase + string.digits
    return 'BP-' + ''.join(random.choices(chars, k=8))

# Auth Helpers
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    db = get_db()
    cur = db.execute("SELECT id, name, email, mobile, role FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()

# Context Processor for HTML Templates
@app.context_processor
def inject_user():
    user = get_current_user()
    return dict(current_user=user)

# Custom Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/flights')
def flights_page():
    return render_template('flights.html')

@app.route('/booking')
def booking_page():
    return render_template('booking.html')

@app.route('/payment')
def payment_page():
    return render_template('payment.html')

@app.route('/confirmation')
def confirmation_page():
    return render_template('confirmation.html')

@app.route('/checkin')
def checkin_page():
    return render_template('checkin.html')

@app.route('/boarding-pass')
def boarding_pass_page():
    return render_template('boarding_pass.html')

@app.route('/manage-booking')
def manage_booking_page():
    return render_template('manage_booking.html')

@app.route('/destinations')
def destinations_page():
    return render_template('destinations.html')

@app.route('/flight-status')
def flight_status_page():
    return render_template('flight_status.html')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/fleet')
def fleet_page():
    return render_template('fleet.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/login')
def login_page():
    if session.get('user_id'):
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if session.get('user_id'):
        return redirect(url_for('dashboard_page'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard_page():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/aerorewards')
def aerorewards_page():
    return render_template('aerorewards.html')

@app.route('/admin')
def admin_page():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/robots.txt')
def robots_txt():
    return "User-agent: *\nDisallow: /admin\nDisallow: /api/\nSitemap: http://127.0.0.1:5000/sitemap.xml", 200, {'Content-Type': 'text/plain'}

@app.route('/sitemap.xml')
def sitemap_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemapforms.org/schemas/sitemap/0.9">
  <url><loc>http://127.0.0.1:5000/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
  <url><loc>http://127.0.0.1:5000/flights</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>http://127.0.0.1:5000/destinations</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>http://127.0.0.1:5000/manage-booking</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>http://127.0.0.1:5000/checkin</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>http://127.0.0.1:5000/aerorewards</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>http://127.0.0.1:5000/fleet</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
  <url><loc>http://127.0.0.1:5000/about</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>http://127.0.0.1:5000/contact</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>http://127.0.0.1:5000/help</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
</urlset>"""
    return xml, 200, {'Content-Type': 'application/xml'}


# ==================== REST API ENDPOINTS ====================

# AUTH APIs
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    mobile = data.get('mobile', '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    db = get_db()
    cur = db.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        return jsonify({'error': 'An account with this email already exists.'}), 409

    hashed = generate_password_hash(password)
    cur = db.execute(
        "INSERT INTO users (name, email, password_hash, mobile, role) VALUES (?, ?, ?, ?, 'user')",
        (name, email, hashed, mobile)
    )
    user_id = cur.lastrowid

    # Create initial AeroRewards account
    db.execute("INSERT INTO aero_rewards (user_id, points_balance, tier) VALUES (?, 500, 'Blue')", (user_id,))
    db.commit()

    session['user_id'] = user_id
    session['user_name'] = name
    session['user_role'] = 'user'

    return jsonify({
        'message': 'Registration successful! Welcome to Aeronexa Airways.',
        'user': {'id': user_id, 'name': name, 'email': email, 'mobile': mobile, 'role': 'user'}
    }), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    db = get_db()
    cur = db.execute("SELECT id, name, email, password_hash, mobile, role FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']

    return jsonify({
        'message': 'Login successful.',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'mobile': user['mobile'],
            'role': user['role']
        }
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'})

@app.route('/api/me', methods=['GET'])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'user': dict(user)
    })

# FLIGHT SEARCH & DATA APIs
@app.route('/api/search-flights', methods=['POST'])
def api_search_flights():
    data = request.get_json() or {}
    origin = data.get('origin', '').strip().upper()
    destination = data.get('destination', '').strip().upper()
    departure_date = data.get('departure_date', '').strip()
    return_date = data.get('return_date', '').strip()
    passengers = int(data.get('passengers', 1))
    cabin = data.get('cabin', 'economy').strip().lower()

    if not origin or not destination:
        return jsonify({'error': 'Origin and destination are required.'}), 400

    if origin == destination:
        return jsonify({'error': 'Origin and destination cannot be identical.'}), 400

    db = get_db()
    
    # Query matching flights
    query = """
        SELECT f.*, 
               o.city as origin_city, o.country as origin_country, o.name as origin_airport_name,
               d.city as dest_city, d.country as dest_country, d.name as dest_airport_name,
               a.name as aircraft_name
        FROM flights f
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        JOIN aircraft a ON f.aircraft = a.code
        WHERE f.origin = ? AND f.destination = ? AND f.available = 1
    """
    params = [origin, destination]
    cur = db.execute(query, params)
    rows = cur.fetchall()

    results = []
    for r in rows:
        fl = dict(r)
        # Select price based on cabin
        if cabin == 'economy':
            fl['price'] = fl['economy_price']
        elif cabin == 'premium_economy':
            fl['price'] = fl['premium_economy_price']
        elif cabin == 'business':
            fl['price'] = fl['business_price']
        elif cabin == 'first':
            fl['price'] = fl['first_class_price']
        else:
            fl['price'] = fl['economy_price']

        fl['departure_date'] = departure_date if departure_date else '2026-09-12'
        results.append(fl)

    # Also handle return flight search if round trip requested
    return_results = []
    if return_date and data.get('trip_type') == 'round_trip':
        ret_query = """
            SELECT f.*, 
                   o.city as origin_city, o.country as origin_country, o.name as origin_airport_name,
                   d.city as dest_city, d.country as dest_country, d.name as dest_airport_name,
                   a.name as aircraft_name
            FROM flights f
            JOIN airports o ON f.origin = o.code
            JOIN airports d ON f.destination = d.code
            JOIN aircraft a ON f.aircraft = a.code
            WHERE f.origin = ? AND f.destination = ? AND f.available = 1
        """
        cur_ret = db.execute(ret_query, [destination, origin])
        ret_rows = cur_ret.fetchall()
        for r in ret_rows:
            fl = dict(r)
            if cabin == 'economy':
                fl['price'] = fl['economy_price']
            elif cabin == 'premium_economy':
                fl['price'] = fl['premium_economy_price']
            elif cabin == 'business':
                fl['price'] = fl['business_price']
            elif cabin == 'first':
                fl['price'] = fl['first_class_price']
            else:
                fl['price'] = fl['economy_price']

            fl['departure_date'] = return_date
            return_results.append(fl)

    return jsonify({
        'flights': results,
        'return_flights': return_results,
        'query': {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'passengers': passengers,
            'cabin': cabin
        }
    })

@app.route('/api/flights', methods=['GET'])
def api_get_all_flights():
    db = get_db()
    cur = db.execute("""
        SELECT f.*, 
               o.city as origin_city, d.city as dest_city, a.name as aircraft_name
        FROM flights f
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        JOIN aircraft a ON f.aircraft = a.code
        ORDER BY f.id ASC
    """)
    flights = [dict(r) for r in cur.fetchall()]
    return jsonify({'flights': flights})

@app.route('/api/flights/<int:flight_id>', methods=['GET'])
def api_get_flight_by_id(flight_id):
    db = get_db()
    cur = db.execute("""
        SELECT f.*, 
               o.city as origin_city, o.country as origin_country, o.name as origin_airport,
               d.city as dest_city, d.country as dest_country, d.name as dest_airport,
               a.name as aircraft_name, a.amenities
        FROM flights f
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        JOIN aircraft a ON f.aircraft = a.code
        WHERE f.id = ?
    """, (flight_id,))
    flight = cur.fetchone()
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404
    fl_dict = dict(flight)
    fl_dict['amenities'] = json.loads(fl_dict['amenities']) if fl_dict['amenities'] else []
    return jsonify({'flight': fl_dict})

@app.route('/api/flights/<int:flight_id>/seats', methods=['GET'])
def api_get_flight_seats(flight_id):
    db = get_db()
    cur = db.execute("""
        SELECT seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset
        FROM seats
        WHERE flight_id = ?
        ORDER BY seat_number ASC
    """, (flight_id,))
    seats = [dict(r) for r in cur.fetchall()]
    return jsonify({'seats': seats})

@app.route('/api/flight-status', methods=['GET'])
def api_flight_status():
    query_str = request.args.get('q', '').strip().upper()
    db = get_db()
    if query_str:
        cur = db.execute("""
            SELECT f.*, 
                   o.city as origin_city, d.city as dest_city
            FROM flights f
            JOIN airports o ON f.origin = o.code
            JOIN airports d ON f.destination = d.code
            WHERE f.flight_number LIKE ? OR f.origin = ? OR f.destination = ? OR o.city LIKE ? OR d.city LIKE ?
        """, (f"%{query_str}%", query_str, query_str, f"%{query_str}%", f"%{query_str}%"))
    else:
        cur = db.execute("""
            SELECT f.*, 
                   o.city as origin_city, d.city as dest_city
            FROM flights f
            JOIN airports o ON f.origin = o.code
            JOIN airports d ON f.destination = d.code
        """)
    flights = [dict(r) for r in cur.fetchall()]
    return jsonify({'flights': flights})

# PROMO CODE VALIDATION
@app.route('/api/validate-promo', methods=['POST'])
def api_validate_promo():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    amount = float(data.get('amount', 0))

    if not code:
        return jsonify({'valid': False, 'error': 'Promo code is required.'}), 400

    db = get_db()
    cur = db.execute("SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code,))
    promo = cur.fetchone()

    if not promo:
        return jsonify({'valid': False, 'error': 'Invalid or expired promo code.'}), 400

    promo_dict = dict(promo)
    if amount < promo_dict['min_spend']:
        return jsonify({'valid': False, 'error': f"Minimum spend of ₹{promo_dict['min_spend']:,} required for code {code}."}), 400

    calc_discount = (amount * promo_dict['discount_percent']) / 100.0
    discount = min(calc_discount, promo_dict['max_discount'])

    return jsonify({
        'valid': True,
        'code': code,
        'discount': round(discount, 2),
        'description': promo_dict['description']
    })

# BOOKING SYSTEM & TRANSACTION SAFETY
@app.route('/api/bookings', methods=['POST'])
def api_create_booking():
    data = request.get_json() or {}
    flight_id = data.get('flight_id')
    cabin_class = data.get('cabin_class', 'economy').lower()
    fare_type = data.get('fare_type', 'Saver')
    passengers = data.get('passengers', [])
    promo_code = data.get('promo_code', '').upper()

    if not flight_id or not passengers:
        return jsonify({'error': 'Flight selection and passenger details are required.'}), 400

    db = get_db()
    try:
        # 1. Fetch flight & authoritative prices from DB
        cur = db.execute("SELECT * FROM flights WHERE id = ? AND available = 1", (flight_id,))
        flight = cur.fetchone()
        if not flight:
            return jsonify({'error': 'Flight unavailable or invalid.'}), 404

        flight_dict = dict(flight)
        if cabin_class == 'economy':
            base_unit_price = flight_dict['economy_price']
        elif cabin_class == 'premium_economy':
            base_unit_price = flight_dict['premium_economy_price']
        elif cabin_class == 'business':
            base_unit_price = flight_dict['business_price']
        elif cabin_class == 'first':
            base_unit_price = flight_dict['first_class_price']
        else:
            base_unit_price = flight_dict['economy_price']

        if fare_type == 'Flex':
            base_unit_price += 1500
        elif fare_type == 'SuperFlex':
            base_unit_price += 3500

        num_passengers = len(passengers)
        base_fare = base_unit_price * num_passengers
        taxes = round(base_fare * 0.12, 2)

        # 2. Check seat availability & calculate extra baggage/meal/addon prices
        extras = 0
        requested_seats = []

        for p in passengers:
            st = p.get('seat_number')
            if st:
                requested_seats.append(st)
                # Verify seat state in DB
                s_cur = db.execute("SELECT id, is_occupied, price_offset FROM seats WHERE flight_id = ? AND seat_number = ?", (flight_id, st))
                seat_row = s_cur.fetchone()
                if seat_row:
                    if seat_row['is_occupied'] == 1:
                        return jsonify({'error': f"Seat {st} was just booked by another traveler. Please select a different seat."}), 409
                    extras += seat_row['price_offset']

            # Baggage extras
            bag_weight = int(p.get('baggage_kg', 0))
            if bag_weight == 15:
                extras += 800
            elif bag_weight == 20:
                extras += 1400
            elif bag_weight == 30:
                extras += 2200

            # Meal extras
            meal_code = p.get('meal_code')
            if meal_code and meal_code != 'NONE':
                extras += 350

        # Add-ons
        addons_list = data.get('addons', [])
        for ad in addons_list:
            if ad == 'lounge':
                extras += 2500
            elif ad == 'priority':
                extras += 800
            elif ad == 'wifi':
                extras += 600
            elif ad == 'insurance':
                extras += 990

        # Calculate discount from promo code if valid
        discount = 0
        if promo_code:
            pr_cur = db.execute("SELECT * FROM promo_codes WHERE code = ? AND active = 1", (promo_code,))
            pr_row = pr_cur.fetchone()
            if pr_row:
                p_dict = dict(pr_row)
                if (base_fare + extras) >= p_dict['min_spend']:
                    calc_d = ((base_fare + extras) * p_dict['discount_percent']) / 100.0
                    discount = min(calc_d, p_dict['max_discount'])

        total_amount = max(0, (base_fare + taxes + extras) - discount)
        pnr = generate_pnr()
        user_id = session.get('user_id')

        # BEGIN DB TRANSACTION
        db.execute("BEGIN TRANSACTION;")

        # Insert Booking
        b_cur = db.execute("""
            INSERT INTO bookings (pnr, user_id, flight_id, cabin_class, fare_type, booking_status, base_fare, taxes, extras, discount, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, 'PENDING')
        """, (pnr, user_id, flight_id, cabin_class, fare_type, base_fare, taxes, extras, discount, total_amount))
        booking_id = b_cur.lastrowid

        # Insert Passengers & mark seats occupied
        for p in passengers:
            st = p.get('seat_number', '')
            p_cur = db.execute("""
                INSERT INTO booking_passengers (booking_id, title, first_name, middle_name, last_name, dob, gender, nationality, passport_number, seat_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id, p.get('title', 'Mr.'), p.get('first_name', ''), p.get('middle_name', ''),
                p.get('last_name', ''), p.get('dob', ''), p.get('gender', 'Other'),
                p.get('nationality', 'Indian'), p.get('passport_number', ''), st
            ))
            passenger_id = p_cur.lastrowid

            if st:
                db.execute("UPDATE seats SET is_occupied = 1 WHERE flight_id = ? AND seat_number = ?", (flight_id, st))

            # Baggage
            b_w = int(p.get('baggage_kg', 0))
            if b_w > 0:
                b_price = 800 if b_w == 15 else (1400 if b_w == 20 else 2200)
                db.execute("INSERT INTO baggage (booking_id, passenger_id, weight_kg, price) VALUES (?, ?, ?, ?)", (booking_id, passenger_id, b_w, b_price))

            # Meals
            m_code = p.get('meal_code')
            if m_code and m_code != 'NONE':
                m_name = p.get('meal_name', 'In-flight Gourmet Meal')
                db.execute("INSERT INTO meals (booking_id, passenger_id, meal_code, meal_name, price) VALUES (?, ?, ?, ?, 350)", (booking_id, passenger_id, m_code, m_name))

        # Add-ons
        for ad in addons_list:
            ad_price = 2500 if ad == 'lounge' else (800 if ad == 'priority' else (600 if ad == 'wifi' else 990))
            db.execute("INSERT INTO booking_addons (booking_id, addon_type, description, price) VALUES (?, ?, ?, ?)", (booking_id, ad, ad.title(), ad_price))

        db.commit()

        return jsonify({
            'message': 'Booking created successfully.',
            'pnr': pnr,
            'booking_id': booking_id,
            'summary': {
                'base_fare': base_fare,
                'taxes': taxes,
                'extras': extras,
                'discount': discount,
                'total_amount': total_amount,
                'currency': 'INR'
            }
        }), 201

    except Exception as e:
        db.execute("ROLLBACK;")
        return jsonify({'error': f"Booking failed: {str(e)}"}), 500

@app.route('/api/bookings/<pnr>', methods=['GET'])
def api_get_booking(pnr):
    pnr_clean = pnr.strip().upper()
    db = get_db()
    cur = db.execute("""
        SELECT b.*, 
               f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time, f.duration, f.aircraft, f.status as flight_status,
               o.city as origin_city, o.country as origin_country, o.name as origin_airport_name,
               d.city as dest_city, d.country as dest_country, d.name as dest_airport_name,
               a.name as aircraft_name
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        JOIN aircraft a ON f.aircraft = a.code
        WHERE b.pnr = ?
    """, (pnr_clean,))
    b_row = cur.fetchone()
    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    booking = dict(b_row)

    # Fetch Passengers
    p_cur = db.execute("SELECT * FROM booking_passengers WHERE booking_id = ?", (booking['id'],))
    passengers = [dict(p) for p in p_cur.fetchall()]

    # Fetch Baggage, Meals, Addons
    for p in passengers:
        bg_cur = db.execute("SELECT weight_kg, price FROM baggage WHERE booking_id = ? AND passenger_id = ?", (booking['id'], p['id']))
        p['baggage'] = [dict(bg) for bg in bg_cur.fetchall()]

        m_cur = db.execute("SELECT meal_code, meal_name, price FROM meals WHERE booking_id = ? AND passenger_id = ?", (booking['id'], p['id']))
        p['meals'] = [dict(m) for m in m_cur.fetchall()]

    # Fetch Payment
    pay_cur = db.execute("SELECT transaction_id, amount, payment_method, payment_status, created_at FROM payments WHERE booking_id = ? ORDER BY id DESC LIMIT 1", (booking['id'],))
    pay_row = pay_cur.fetchone()
    payment = dict(pay_row) if pay_row else None

    # Checkin Status
    chk_cur = db.execute("SELECT * FROM checkins WHERE booking_id = ?", (booking['id'],))
    checkins = [dict(ck) for ck in chk_cur.fetchall()]

    return jsonify({
        'booking': booking,
        'passengers': passengers,
        'payment': payment,
        'checkins': checkins
    })

# DEMO PAYMENT GATEWAY APIs
@app.route('/api/payment/create', methods=['POST'])
def api_payment_create():
    data = request.get_json() or {}
    pnr = data.get('pnr', '').strip().upper()
    payment_method = data.get('payment_method', 'UPI')

    if not pnr:
        return jsonify({'error': 'PNR is required.'}), 400

    db = get_db()
    cur = db.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    b_row = cur.fetchone()
    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    booking = dict(b_row)
    transaction_id = generate_transaction_id()
    amount = booking['total_amount']

    # Generate Official UPI Specification Deep Link Payload (Scannable by Google Pay, PhonePe, Paytm, BHIM)
    qr_payload = f"upi://pay?pa=aeronexa.demo@bank&pn=Aeronexa%20Airways%20Demo&tr={transaction_id}&tn=Flight%20Booking%20{pnr}%20DEMO&am={amount:.2f}&cu=INR"

    # Insert pending payment record
    db.execute("""
        INSERT INTO payments (booking_id, transaction_id, amount, currency, payment_method, payment_status, payment_mode)
        VALUES (?, ?, ?, 'INR', ?, 'PENDING', 'DEMO')
    """, (booking['id'], transaction_id, amount, payment_method))
    db.commit()

    return jsonify({
        'message': 'Payment transaction initialized.',
        'pnr': pnr,
        'transaction_id': transaction_id,
        'amount': amount,
        'currency': 'INR',
        'payment_method': payment_method,
        'qr_payload': qr_payload,
        'disclaimer': 'Demo Sandbox Payment — No real money will be charged.'
    }), 201

@app.route('/api/payment/verify', methods=['POST'])
def api_payment_verify():
    data = request.get_json() or {}
    transaction_id = data.get('transaction_id', '').strip()
    pnr = data.get('pnr', '').strip().upper()

    if not transaction_id or not pnr:
        return jsonify({'error': 'Transaction ID and PNR are required.'}), 400

    db = get_db()
    cur = db.execute("SELECT * FROM payments WHERE transaction_id = ?", (transaction_id,))
    pay_row = cur.fetchone()

    if not pay_row:
        return jsonify({'error': 'Transaction record not found.'}), 404

    b_cur = db.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    b_row = b_cur.fetchone()

    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    booking = dict(b_row)

    # BEGIN DB TRANSACTION FOR CONFIRMATION
    db.execute("BEGIN TRANSACTION;")
    db.execute("UPDATE payments SET payment_status = 'SUCCESS' WHERE transaction_id = ?", (transaction_id,))
    db.execute("UPDATE bookings SET payment_status = 'SUCCESS', booking_status = 'CONFIRMED' WHERE id = ?", (booking['id'],))

    # Award AeroRewards points to user if logged in (10 points per 100 INR spent)
    if booking['user_id']:
        earned_points = int(booking['total_amount'] / 10)
        db.execute("""
            INSERT INTO aero_rewards (user_id, points_balance, tier)
            VALUES (?, ?, 'Blue')
            ON CONFLICT(user_id) DO UPDATE SET
                points_balance = points_balance + excluded.points_balance,
                tier = CASE 
                    WHEN points_balance + excluded.points_balance >= 25000 THEN 'Platinum'
                    WHEN points_balance + excluded.points_balance >= 10000 THEN 'Gold'
                    WHEN points_balance + excluded.points_balance >= 3000 THEN 'Silver'
                    ELSE 'Blue'
                END,
                updated_at = CURRENT_TIMESTAMP
        """, (booking['user_id'], earned_points))

    db.commit()

    return jsonify({
        'message': 'Payment verified successfully! Booking confirmed.',
        'pnr': pnr,
        'transaction_id': transaction_id,
        'status': 'CONFIRMED',
        'disclaimer': 'Demo Sandbox Payment — Simulated successful transaction.'
    })

# CHECK-IN & BOARDING PASS APIs
@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.get_json() or {}
    pnr = data.get('pnr', '').strip().upper()
    last_name = data.get('last_name', '').strip().lower()

    if not pnr or not last_name:
        return jsonify({'error': 'PNR and passenger last name are required.'}), 400

    db = get_db()
    b_cur = db.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    b_row = b_cur.fetchone()

    if not b_row:
        return jsonify({'error': 'No booking found matching the provided PNR.'}), 404

    booking = dict(b_row)
    if booking['booking_status'] != 'CONFIRMED':
        return jsonify({'error': 'Check-in is only available for confirmed bookings. Please complete payment first.'}), 400

    # Verify last name
    p_cur = db.execute("SELECT * FROM booking_passengers WHERE booking_id = ? AND LOWER(last_name) = ?", (booking['id'], last_name))
    passengers = p_cur.fetchall()

    if not passengers:
        return jsonify({'error': 'Passenger last name does not match PNR records.'}), 404

    completed_checkins = []
    for p in passengers:
        p_dict = dict(p)
        # Check if already checked in
        ck_cur = db.execute("SELECT * FROM checkins WHERE booking_id = ? AND passenger_id = ?", (booking['id'], p_dict['id']))
        ck_existing = ck_cur.fetchone()

        if ck_existing:
            completed_checkins.append(dict(ck_existing))
        else:
            bp_code = generate_boarding_pass_code()
            seat_no = p_dict['seat_number'] if p_dict['seat_number'] else '14A'
            db.execute("""
                INSERT INTO checkins (booking_id, passenger_id, seat_number, boarding_pass_code, gate, terminal)
                VALUES (?, ?, ?, ?, 'G14', 'T2')
            """, (booking['id'], p_dict['id'], seat_no, bp_code))
            db.commit()

            c_new = db.execute("SELECT * FROM checkins WHERE boarding_pass_code = ?", (bp_code,)).fetchone()
            completed_checkins.append(dict(c_new))

    return jsonify({
        'message': 'Check-in complete! Boarding pass ready.',
        'pnr': pnr,
        'checkins': completed_checkins
    })

@app.route('/api/boarding-pass/<pnr>', methods=['GET'])
def api_get_boarding_pass(pnr):
    pnr_clean = pnr.strip().upper()
    db = get_db()
    b_cur = db.execute("""
        SELECT b.*, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time, f.aircraft,
               o.city as origin_city, d.city as dest_city
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        WHERE b.pnr = ?
    """, (pnr_clean,))
    b_row = b_cur.fetchone()

    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    booking = dict(b_row)
    ck_cur = db.execute("""
        SELECT c.*, p.title, p.first_name, p.middle_name, p.last_name
        FROM checkins c
        JOIN booking_passengers p ON c.passenger_id = p.id
        WHERE c.booking_id = ?
    """, (booking['id'],))

    passes = [dict(r) for r in ck_cur.fetchall()]

    if not passes:
        return jsonify({'error': 'No completed check-in found for this booking. Please check in first.'}), 404

    return jsonify({
        'booking': booking,
        'boarding_passes': passes
    })

# MANAGE BOOKING ACTIONS (Modify seat, add baggage/meal, cancel)
@app.route('/api/update-seat', methods=['POST'])
def api_update_seat():
    data = request.get_json() or {}
    pnr = data.get('pnr', '').strip().upper()
    passenger_id = data.get('passenger_id')
    new_seat = data.get('seat_number', '').strip().upper()

    if not pnr or not passenger_id or not new_seat:
        return jsonify({'error': 'PNR, passenger ID, and new seat number are required.'}), 400

    db = get_db()
    b_cur = db.execute("SELECT id, flight_id FROM bookings WHERE pnr = ?", (pnr,))
    b_row = b_cur.fetchone()
    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    flight_id = b_row['flight_id']
    booking_id = b_row['id']

    # Verify seat availability
    s_cur = db.execute("SELECT is_occupied FROM seats WHERE flight_id = ? AND seat_number = ?", (flight_id, new_seat))
    s_row = s_cur.fetchone()
    if not s_row:
        return jsonify({'error': 'Invalid seat number.'}), 400
    if s_row['is_occupied'] == 1:
        return jsonify({'error': 'Seat is already occupied.'}), 409

    # Fetch old seat
    p_cur = db.execute("SELECT seat_number FROM booking_passengers WHERE id = ? AND booking_id = ?", (passenger_id, booking_id))
    p_row = p_cur.fetchone()
    if p_row and p_row['seat_number']:
        db.execute("UPDATE seats SET is_occupied = 0 WHERE flight_id = ? AND seat_number = ?", (flight_id, p_row['seat_number']))

    db.execute("UPDATE seats SET is_occupied = 1 WHERE flight_id = ? AND seat_number = ?", (flight_id, new_seat))
    db.execute("UPDATE booking_passengers SET seat_number = ? WHERE id = ?", (new_seat, passenger_id))
    db.commit()

    return jsonify({'message': f"Seat updated to {new_seat} successfully."})

@app.route('/api/cancel-booking', methods=['POST'])
def api_cancel_booking():
    data = request.get_json() or {}
    pnr = data.get('pnr', '').strip().upper()
    reason = data.get('reason', 'User requested cancellation')

    if not pnr:
        return jsonify({'error': 'PNR is required.'}), 400

    db = get_db()
    b_cur = db.execute("SELECT id, flight_id, booking_status FROM bookings WHERE pnr = ?", (pnr,))
    b_row = b_cur.fetchone()

    if not b_row:
        return jsonify({'error': 'Booking not found.'}), 404

    if b_row['booking_status'] == 'CANCELLED':
        return jsonify({'error': 'Booking is already cancelled.'}), 400

    booking_id = b_row['id']
    flight_id = b_row['flight_id']

    db.execute("BEGIN TRANSACTION;")
    # Release seats
    p_cur = db.execute("SELECT seat_number FROM booking_passengers WHERE booking_id = ?", (booking_id,))
    for p in p_cur.fetchall():
        if p['seat_number']:
            db.execute("UPDATE seats SET is_occupied = 0 WHERE flight_id = ? AND seat_number = ?", (flight_id, p['seat_number']))

    db.execute("UPDATE bookings SET booking_status = 'CANCELLED' WHERE id = ?", (booking_id,))
    db.commit()

    return jsonify({'message': f"Booking {pnr} has been successfully cancelled."})

# USER DASHBOARD & AEROREWARDS APIs
@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    cur = db.execute("""
        SELECT b.*, f.flight_number, f.origin, f.destination, f.departure_time, f.arrival_time,
               o.city as origin_city, d.city as dest_city
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports o ON f.origin = o.code
        JOIN airports d ON f.destination = d.code
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (user['id'],))
    bookings = [dict(r) for r in cur.fetchall()]

    rw_cur = db.execute("SELECT points_balance, tier FROM aero_rewards WHERE user_id = ?", (user['id'],))
    rw_row = rw_cur.fetchone()
    rewards = dict(rw_row) if rw_row else {'points_balance': 0, 'tier': 'Blue'}

    return jsonify({
        'user': dict(user),
        'bookings': bookings,
        'rewards': rewards
    })

@app.route('/api/aerorewards', methods=['GET'])
def api_aerorewards():
    user = get_current_user()
    if not user:
        return jsonify({'points_balance': 12450, 'tier': 'Gold', 'authenticated': False})

    db = get_db()
    rw_cur = db.execute("SELECT points_balance, tier FROM aero_rewards WHERE user_id = ?", (user['id'],))
    rw_row = rw_cur.fetchone()
    rewards = dict(rw_row) if rw_row else {'points_balance': 500, 'tier': 'Blue'}
    rewards['authenticated'] = True
    return jsonify(rewards)

# CONTACT & NEWSLETTER APIs
@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not subject or not message:
        return jsonify({'error': 'Name, email, subject, and message are required.'}), 400

    db = get_db()
    db.execute("""
        INSERT INTO contact_messages (name, email, phone, subject, message)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, subject, message))
    db.commit()

    return jsonify({'message': 'Thank you! Your message has been received by Aeronexa Support.'}), 201

@app.route('/api/newsletter', methods=['POST'])
def api_newsletter():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'Valid email address is required.'}), 400

    db = get_db()
    try:
        db.execute("INSERT INTO newsletter_subscribers (email) VALUES (?)", (email,))
        db.commit()
        return jsonify({'message': 'Subscribed successfully to Aeronexa Airways updates!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'You are already subscribed to our newsletter.'}), 200

# RULE-BASED AI TRAVEL ASSISTANT
@app.route('/api/ai-assistant', methods=['POST'])
def api_ai_assistant():
    data = request.get_json() or {}
    budget = float(data.get('budget', 50000))
    travel_type = data.get('travel_type', 'leisure').lower()
    cabin = data.get('cabin', 'economy').lower()

    db = get_db()
    cur = db.execute("SELECT * FROM airports WHERE starting_fare <= ?", (budget,))
    airports = [dict(a) for a in cur.fetchall()]

    recommendations = []
    for a in airports:
        if travel_type == 'beach' and a['code'] in ['BKK', 'SYD', 'DXB', 'SIN']:
            recommendations.append(a)
        elif travel_type == 'culture' and a['code'] in ['DEL', 'LHR', 'CDG', 'HND', 'BOM']:
            recommendations.append(a)
        elif travel_type == 'luxury' and a['code'] in ['DXB', 'SIN', 'JFK', 'CDG']:
            recommendations.append(a)
        elif len(recommendations) < 3:
            recommendations.append(a)

    if not recommendations:
        cur_all = db.execute("SELECT * FROM airports ORDER BY starting_fare ASC LIMIT 3")
        recommendations = [dict(a) for a in cur_all.fetchall()]

    return jsonify({
        'mode': 'Rule-Based Demo AI Engine',
        'recommendations': recommendations[:3],
        'advice': f"Based on your budget of ₹{budget:,.0f} and preference for {travel_type} travel, we highly recommend these Aeronexa curated destinations."
    })

# PROTECTED ADMIN APIs
@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_bookings = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    confirmed_bookings = db.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'CONFIRMED'").fetchone()[0]
    todays_flights = db.execute("SELECT COUNT(*) FROM flights WHERE available = 1").fetchone()[0]
    demo_revenue = db.execute("SELECT COALESCE(SUM(total_amount), 0) FROM bookings WHERE payment_status = 'SUCCESS'").fetchone()[0]
    pending_checkins = db.execute("SELECT COUNT(*) FROM bookings WHERE booking_status = 'CONFIRMED' AND id NOT IN (SELECT booking_id FROM checkins)").fetchone()[0]

    return jsonify({
        'total_users': total_users,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'todays_flights': todays_flights,
        'demo_revenue': demo_revenue,
        'pending_checkins': pending_checkins
    })

@app.route('/api/admin/flights', methods=['GET', 'POST'])
def api_admin_flights():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    if request.method == 'GET':
        cur = db.execute("""
            SELECT f.*, o.city as origin_city, d.city as dest_city
            FROM flights f
            JOIN airports o ON f.origin = o.code
            JOIN airports d ON f.destination = d.code
            ORDER BY f.id DESC
        """)
        return jsonify({'flights': [dict(r) for r in cur.fetchall()]})

    elif request.method == 'POST':
        data = request.get_json() or {}
        db.execute("""
            INSERT INTO flights (flight_number, origin, destination, departure_time, arrival_time, duration, stops, aircraft, economy_price, premium_economy_price, business_price, first_class_price, status, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('flight_number'), data.get('origin'), data.get('destination'),
            data.get('departure_time'), data.get('arrival_time'), data.get('duration', '3h 00m'),
            data.get('stops', 0), data.get('aircraft', 'A320'), data.get('economy_price', 5000),
            data.get('premium_economy_price', 8000), data.get('business_price', 18000),
            data.get('first_class_price', 35000), data.get('status', 'On Time'), 1
        ))
        db.commit()
        return jsonify({'message': 'Flight created successfully'}), 201

@app.route('/api/admin/flights/<int:flight_id>', methods=['PUT', 'DELETE'])
def api_admin_flight_modify(flight_id):
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    if request.method == 'PUT':
        data = request.get_json() or {}
        db.execute("""
            UPDATE flights 
            SET status = ?, economy_price = ?, business_price = ?, available = ?
            WHERE id = ?
        """, (data.get('status', 'On Time'), data.get('economy_price'), data.get('business_price'), data.get('available', 1), flight_id))
        db.commit()
        return jsonify({'message': 'Flight updated successfully'})

    elif request.method == 'DELETE':
        db.execute("DELETE FROM flights WHERE id = ?", (flight_id,))
        db.commit()
        return jsonify({'message': 'Flight deleted successfully'})

@app.route('/api/admin/bookings', methods=['GET'])
def api_admin_bookings():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    cur = db.execute("""
        SELECT b.*, f.flight_number, f.origin, f.destination, u.name as user_name, u.email as user_email
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        LEFT JOIN users u ON b.user_id = u.id
        ORDER BY b.created_at DESC
    """)
    return jsonify({'bookings': [dict(r) for r in cur.fetchall()]})

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    cur = db.execute("SELECT id, name, email, mobile, role, created_at FROM users ORDER BY id DESC")
    return jsonify({'users': [dict(r) for r in cur.fetchall()]})

@app.route('/api/admin/contacts', methods=['GET'])
def api_admin_contacts():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized admin access'}), 403

    db = get_db()
    cur = db.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
    return jsonify({'messages': [dict(r) for r in cur.fetchall()]})

if __name__ == '__main__':
    # Initialize DB before running server
    with app.app_context():
        from database.init_db import init_db
        init_db()
    print("Aeronexa Airways server starting on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
