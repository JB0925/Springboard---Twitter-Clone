"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
import bcrypt

from sqlalchemy.exc import IntegrityError
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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    

    def test_user_repr(self):
        """Does the repr method work correctly?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        self.assertEqual(repr(u), f'<User #{u.id}: testuser, test@test.com>')
    

    def test_user_is_following(self):
        """Does the follower/following relationship work correctly?"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        follow = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
        db.session.add(follow)
        db.session.commit()
        self.assertIn(u2, u1.following)
        self.assertTrue(u2.is_followed_by(u1))
    

    def test_user_not_following(self):
        """Does the follower / following relationship exclude non-followed users?"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertNotIn(u2, u1.following)
        self.assertFalse(u1.is_followed_by(u2))
    

    def test_user_signup_good_and_bad_credentials(self):
        """Does the db enforce the appropriate constraints when committing a user to the db?"""
        user = User.signup('joe', 'joe@gmail.com', 'cookie', 'https://wwww.myimage.com')
        self.assertIsNotNone(user)
        with self.assertRaises(Exception) as raises:
            User.signup('joe', 'j@gmail.com', 'banana', 'https://www.myimage.com')
            db.session.commit()
    
        self.assertEqual(IntegrityError, type(raises.exception))
    

    def test_authenticate_good_and_bad_credentials(self):
        """Does authentication appropriately for both valid and invalid credentials?"""
        u = User.signup('http', 'http@gmail.com', 'cookies', 'http://www.myimage.com')
        db.session.commit()
        user = User.query.all()[-1]
        auth = User.authenticate(user.username, 'cookies')
        self.assertTrue(auth)

        # invalid credentials test
        u = User.signup('https', 'https@gmail.com', 'cookies', 'http://www.myimage.com')
        db.session.commit()
        user = User.query.all()[-1]

        # invalid - bad password
        auth = User.authenticate(user.username, 'snake')
        self.assertFalse(auth)

        # invalid - bad username
        auth = User.authenticate('ralph', 'cookies')
        self.assertFalse(auth)

        