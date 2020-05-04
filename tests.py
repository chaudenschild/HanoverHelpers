import unittest

from app import app, db
from app.models import Recipient, Transaction, UserDirectory, Volunteer


class TransactionTest(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_volunteer(self):
        v = Volunteer(username='v1')
        db.session.add(v)
        db.session.commit()
        self.assertEqual(Volunteer.query.first(), v)
        self.assertEqual(UserDirectory.query.first().id, v.userdir_id)

    def test_register_recipient(self):
        r = Recipient(username='r1')
        db.session.add(r)
        db.session.commit()
        self.assertEqual(Recipient.query.first(), r)
        self.assertEqual(UserDirectory.query.first().id, r.userdir_id)

    def test_transaction_assign_recipient_volunteer(self):
        t = Transaction()
        r = Recipient(username='r1')
        v = Volunteer(username='v1')
        db.session.add_all([t, r, v])
        db.session.commit()
        t.assign_recipient(r)
        self.assertEqual(t.recipient, r)
        self.assertEqual(t.recipient_id, r.id)
        self.assertFalse(t.claimed)
        self.assertEqual(r.transactions[0], t)
        t.assign_volunteer(v)
        db.session.add(t)
        db.session.commit()
        self.assertEqual(t.volunteer, v)
        self.assertEqual(t.volunteer_id, v.id)
        self.assertTrue(t.claimed)
        self.assertEqual(v.transactions[0], t)

    def test_delete_user(self):
        v = Volunteer(username='v1')
        db.session.add(v)
        db.session.commit()
        self.assertIn(v, Volunteer.query.all())
        db.session.delete(v)
        db.session.commit()
        self.assertNotIn(v, Volunteer.query.all())
        all_userdir_ids = [u.id for u in UserDirectory.query.all()]
        self.assertNotIn(v.userdir_id, all_userdir_ids)


if __name__ == '__main__':
    unittest.main(verbosity=2)
