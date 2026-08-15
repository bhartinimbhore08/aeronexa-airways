import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from database.seed_db import seed_db

class FlightsTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(Config.BASE_DIR, 'instance', 'test_flights.db')
        Config.DATABASE_PATH = self.test_db
        app.config['TESTING'] = True
        app.config['DATABASE_PATH'] = self.test_db
        seed_db(self.test_db)
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_search_flights_valid(self):
        res = self.client.post('/api/search-flights', json={
            'origin': 'BOM',
            'destination': 'LHR',
            'departure_date': '2026-09-12',
            'passengers': 1,
            'cabin': 'economy'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('flights', data)
        self.assertTrue(len(data['flights']) > 0)
        self.assertEqual(data['flights'][0]['origin'], 'BOM')
        self.assertEqual(data['flights'][0]['destination'], 'LHR')

    def test_search_same_origin_dest(self):
        res = self.client.post('/api/search-flights', json={
            'origin': 'BOM',
            'destination': 'BOM',
            'departure_date': '2026-09-12'
        })
        self.assertEqual(res.status_code, 400)

if __name__ == '__main__':
    unittest.main()
