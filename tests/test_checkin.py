import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from database.seed_db import seed_db

class CheckinTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(Config.BASE_DIR, 'instance', 'test_checkin.db')
        Config.DATABASE_PATH = self.test_db
        app.config['TESTING'] = True
        app.config['DATABASE_PATH'] = self.test_db
        seed_db(self.test_db)
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_checkin_success(self):
        res = self.client.post('/api/checkin', json={
            'pnr': 'AX7K9P',
            'last_name': 'Nimbhore'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('checkins', data)
        self.assertTrue(len(data['checkins']) > 0)

    def test_checkin_invalid_pnr(self):
        res = self.client.post('/api/checkin', json={
            'pnr': 'INVALID',
            'last_name': 'Nimbhore'
        })
        self.assertEqual(res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
