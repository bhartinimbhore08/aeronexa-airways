import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from database.init_db import init_db
from database.seed_db import seed_db

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(Config.BASE_DIR, 'instance', 'test_aeronexa.db')
        Config.DATABASE_PATH = self.test_db
        app.config['TESTING'] = True
        app.config['DATABASE_PATH'] = self.test_db
        seed_db(self.test_db)
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_login_success(self):
        res = self.client.post('/api/login', json={
            'email': 'demo@aeronexa.com',
            'password': 'Demo@123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'demo@aeronexa.com')

    def test_login_invalid_password(self):
        res = self.client.post('/api/login', json={
            'email': 'demo@aeronexa.com',
            'password': 'WrongPassword'
        })
        self.assertEqual(res.status_code, 401)

    def test_register_success(self):
        res = self.client.post('/api/register', json={
            'name': 'Test User',
            'email': 'newuser@aeronexa.com',
            'password': 'Password@123',
            'mobile': '+919999888877'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data['user']['email'], 'newuser@aeronexa.com')

if __name__ == '__main__':
    unittest.main()
