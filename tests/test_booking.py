import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from database.seed_db import seed_db

class BookingTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(Config.BASE_DIR, 'instance', 'test_booking.db')
        Config.DATABASE_PATH = self.test_db
        app.config['TESTING'] = True
        app.config['DATABASE_PATH'] = self.test_db
        seed_db(self.test_db)
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_create_booking(self):
        res = self.client.post('/api/bookings', json={
            'flight_id': 1,
            'cabin_class': 'economy',
            'fare_type': 'Saver',
            'passengers': [
                {
                    'title': 'Mr.',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'dob': '1990-01-01',
                    'gender': 'Male',
                    'nationality': 'Indian',
                    'passport_number': 'A1234567',
                    'seat_number': '12A'
                }
            ],
            'promo_code': 'AERO10'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('pnr', data)
        self.assertTrue(data['pnr'].startswith('AX'))

    def test_get_booking_by_pnr(self):
        res = self.client.get('/api/bookings/AX7K9P')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['booking']['pnr'], 'AX7K9P')

if __name__ == '__main__':
    unittest.main()
