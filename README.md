# Aeronexa Airways — Full-Stack Airline Reservation & Travel Platform

**Tagline**: *Connected Above the Clouds*

Aeronexa Airways is a complete, production-style, portfolio-ready full-stack airline reservation and travel web application developed with **Python Flask**, **SQLite**, **HTML5**, **Vanilla CSS3**, and **Vanilla JavaScript**. 

The system delivers a complete end-to-end passenger flight journey—from flight search, filtering, and dynamic fare selection to interactive seat mapping, baggage/meal customization, promotional code validation, sandbox dynamic QR payment simulation, unique PNR e-ticket generation, online check-in, printable digital boarding passes, loyalty reward tracking, and a server-protected administrator control panel.

---

## 🌟 Portfolio Description & Architecture

> **Aeronexa Airways — Full-Stack Airline Reservation & Travel Platform**
> 
> A full-stack airline reservation platform developed using Python Flask, SQLite, HTML5, CSS3, and Vanilla JavaScript. The system provides flight search and filtering, user authentication, passenger management, interactive seat selection, baggage and meal selection, promotional discounts, booking management, simulated QR payment, PNR generation, e-ticket generation, online check-in, boarding passes, flight status, AeroRewards, user dashboards, and an administrator panel.
>
> The application is designed as a responsive, deployment-ready portfolio project demonstrating frontend development, backend APIs, database management, authentication, transaction handling, REST-style communication, validation, security practices, and full-stack application architecture.

---

## 🛠️ Technology Stack

| Layer | Technology Used |
| :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Properties, CSS Grid, Flexbox), Vanilla JavaScript (ES Modules, Fetch API) |
| **Backend** | Python 3, Flask 3.0, Werkzeug 3.0 |
| **Database** | SQLite3 (Persistent relational database with foreign key enforcement and transactional safety) |
| **Security & Auth** | Werkzeug PBKDF2 Password Hashing, Flask Server Sessions, Transactional Rollbacks |
| **Design System** | Midnight Navy (`#071A33`), Deep Blue (`#0D2B4D`), Premium Gold (`#D4AF37`), White, Light Gray |

*No heavy frontend frameworks (React/Vue/Angular), styling frameworks (Bootstrap/Tailwind), or Node/npm dependencies are required.*

---

## ✈️ Core System Features

1. **Flight Search Engine**:
   - Round Trip, One Way, and Multi-City search modes.
   - Origin/Destination validation, passenger count counters, cabin class selectors.
   - Authoritative Flask backend route verification.

2. **Dynamic Flight Results & Filters**:
   - Real-time client-side filtering (Max price slider, stops, departure time slots, aircraft).
   - Dynamic sorting (Cheapest, Fastest, Earliest departure, Latest departure).
   - Fare comparison matrix (Economy Saver, Economy Flex, Business Premier).

3. **Multi-Step Booking Wizard**:
   - **Step 1: Fare Selection**: Dynamic price calculation per passenger.
   - **Step 2: Passenger Details**: Form validation for titles, DOB, gender, nationality, passport (for international routes), and phone formats (+91).
   - **Step 3: Interactive Seat Map**: Real-time cabin rendering (Available, Selected, Occupied, Premium, Exit Row). Prevents duplicate seat allocations via database constraints.
   - **Step 4: Baggage Selection**: Standard, +15kg, +20kg, +30kg.
   - **Step 5: Gourmet Meals**: Vegetarian, Non-Veg, Vegan, Jain, Gluten-Free options.
   - **Step 6: Travel Add-ons**: VIP Lounge Access, Priority Boarding, High-Speed Wi-Fi, Travel Insurance.
   - **Step 7: Promo Code Engine**: Backend validated coupons (`AERO10`, `WELCOME20`, `BUSINESS15`).

4. **Sandbox Payment Gateway & Dynamic QR**:
   - Real-time total breakdown (Base fare + Taxes + Extras - Discount).
   - Dynamic SVG QR code generator containing PNR, transaction ID, exact INR amount, and test mode string.
   - 5-minute countdown timer.
   - Server-side transaction verification transitioning booking status to `CONFIRMED`.

5. **E-Ticket & Boarding Pass**:
   - Unique 6-character PNR generation (e.g. `AX7K9P`).
   - Printable E-Ticket with route overview, traveler breakdown, and barcode visual.
   - Online Check-in lookup issuing digital boarding pass with Gate, Terminal, and Seat assignment.

6. **User Dashboard & AeroRewards**:
   - Profile overview, upcoming/past trips tabs, saved passengers.
   - Loyalty Tier progress (Blue, Silver, Gold, Platinum) with automatic points accrual.

7. **Protected Administrator Panel**:
   - Server-side role protection (`role == 'admin'`).
   - Analytical dashboard cards (Users, Bookings, Confirmed Trips, Demo Revenue).
   - Flight CRUD operations (Create new flight modal, edit status, delete).

8. **AI Destination Advisor**:
   - Rule-based recommendation engine recommending tailored destinations based on budget and travel style.

---

## 🗄️ Database Architecture (16 Tables)

```
aeronexa.db
├── users (id, name, email, password_hash, mobile, role, created_at)
├── airports (code, city, country, name, tagline, description, starting_fare, image)
├── aircraft (code, name, manufacturer, capacity, range_km, amenities, image)
├── flights (id, flight_number, origin, destination, departure_time, arrival_time, duration, stops, aircraft, prices, status, available)
├── seats (id, flight_id, seat_number, cabin_class, is_occupied, is_premium, is_exit_row, price_offset)
├── promo_codes (id, code, discount_percent, max_discount, min_spend, active)
├── bookings (id, pnr, user_id, flight_id, cabin_class, fare_type, booking_status, base_fare, taxes, extras, discount, total_amount, payment_status)
├── booking_passengers (id, booking_id, title, first_name, middle_name, last_name, dob, gender, nationality, passport_number, seat_number)
├── baggage (id, booking_id, passenger_id, weight_kg, price)
├── meals (id, booking_id, passenger_id, meal_code, meal_name, price)
├── booking_addons (id, booking_id, addon_type, description, price)
├── payments (id, booking_id, transaction_id, amount, currency, payment_method, payment_status, payment_mode)
├── checkins (id, booking_id, passenger_id, seat_number, boarding_pass_code, gate, terminal, checked_in_at)
├── aero_rewards (id, user_id, points_balance, tier, updated_at)
├── contact_messages (id, name, email, phone, subject, message, status, created_at)
└── newsletter_subscribers (id, email, subscribed_at)
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.9 or higher installed.

### 2. Installation & Database Seeding
```powershell
# Navigate to project directory
cd "d:\Aeronexa Airways"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize database schema & seed demo data
python database/seed_db.py
```

### 3. Run Application
```powershell
python app.py
```
Open your browser at: **`http://127.0.0.1:5000`**

---

## 🔑 Demo Accounts

| Account Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@aeronexa.com` | `Admin@123` | Full Admin Panel (`/admin`), Flight CRUD, Analytics |
| **Demo Traveler** | `demo@aeronexa.com` | `Demo@123` | User Dashboard (`/dashboard`), Pre-loaded Booking (`AX7K9P`), Gold Tier |

---

## 🧪 Automated Testing

Run the full unit test suite:
```powershell
python -m unittest discover -s tests
```

---

## ⚠️ Disclaimers

### Demo Payment Disclaimer
> **DEMO / SANDBOX PAYMENT**: All financial operations within this website are for demonstration and portfolio purposes only. No real money is charged, transferred, or requested. The QR code generator produces non-financial sandbox payloads.

### Fictional Airline Disclaimer
> **FICTIONAL AIRLINE**: Aeronexa Airways is a fictional airline created for educational and software engineering portfolio purposes. Flights, bookings, flight status, payment, check-in, and other airline services shown in this application use simulated/demo data and do not represent real airline services.

---

## 📄 License
MIT License. Created by Software Engineering Portfolio Demonstration.
