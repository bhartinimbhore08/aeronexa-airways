import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from database.seed_db import seed_db

class PaymentTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(Config.BASE_DIR, 'instance', 'test_payment.db')
        Config.DATABASE_PATH = self.test_db
        app.config['TESTING'] = True
        app.config['DATABASE_PATH'] = self.test_db
        seed_db(self.test_db)
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_payment_creation_and_verification(self):
        # 1. Create Payment
        res = self.client.post('/api/payment/create', json={
            'pnr': 'AX7K9P',
            'payment_method': 'UPI'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('transaction_id', data)
        self.assertIn('qr_payload', data)
        txn_id = data['transaction_id']

        # 2. Verify Payment
        v_res = self.client.post('/api/payment/verify', json={
            'pnr': 'AX7K9P',
            'transaction_id': txn_id
        })
        self.assertEqual(v_res.status_code, 200)
        v_data = v_res.get_json()
        self.assertEqual(v_data['status'], 'CONFIRMED')

if __name__ == '__main__':
    unittest.main()
