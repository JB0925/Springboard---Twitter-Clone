"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
import bcrypt

from sqlalchemy.exc import IntegrityError, InvalidRequestError
from flask_bcrypt import Bcrypt

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app
bcrypt = Bcrypt()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self) -> None:
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
    

    def tearDown(self) -> None:
        db.session.rollback()
    

    def create_user(self):
        user = User(
            email='test@test.com',
            username='joe',
            password=bcrypt.generate_password_hash('cookies').decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        return user
    

    def remove_from_db(self, item):
        db.session.delete(item)
        db.session.commit()
    

    def test_message_model(self):
        """Does the message model allow us to create a Message object to save to the db?"""
        user = self.create_user()
        message = Message(text='my message', user_id=user.id)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(len(Message.query.all()), 1)
        self.remove_from_db(message)
        self.remove_from_db(user)
    

    def test_message_no_text(self):
        """Does the database raise an error if no text is given?"""
        user = self.create_user()
        message = Message(user_id=user.id)
        db.session.add(message)
        
        with self.assertRaises(Exception) as raised:
            db.session.commit()
        
        self.assertEqual(IntegrityError, type(raised.exception))
    

    def test_message_no_user(self):
        """Does the database correctly reject a message with no text?"""
        db.session.rollback()
        user = User(
            email='ken@gmail.com',
            username='kenny5',
            password=bcrypt.generate_password_hash('cookies').decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()

        message = Message(text='my message')
        db.session.add(message)
        
        with self.assertRaises(Exception) as raised:
            db.session.commit()
        
        self.assertEqual(IntegrityError, type(raised.exception))
    

    def test_user_has_messages(self):
        """Do the messages get associated with the user as per the relationship defined in models?"""
        user = self.create_user()
        message = Message(text='my message', user_id=user.id)
        db.session.add(message)
        db.session.commit()
        self.assertIn(message, user.messages)