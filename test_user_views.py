"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from flask import session
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

from models import Follows, db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
bcrypt = Bcrypt()

def login(client, username, password):
        return client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    

def logout(client):
    return client.get('/logout', follow_redirects=True)


class UserViewsTestCase(TestCase):
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    

    def test_get_request_signup(self):
        """Does the signup page render?"""
        with self.client as c:
            resp = c.get('/signup')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.', resp.get_data(as_text=True))
    

    def test_post_request_signup(self):
        """Is a user able to sign up for an account?"""
        with self.client as c:
            resp = c.post('/signup', data={'username': 'joe', 'email': 'joe@joe.com', 'password': 'cookies'}, follow_redirects=True)
            joe = User.query.filter_by(username='joe').first()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(session[CURR_USER_KEY], joe.id)
            self.assertIn('Messages', resp.get_data(as_text=True))
    

    def test_get_request_user_following_logged_out(self):
        """Can a logged out user access the 'user_following' page?"""
        with self.client as c:
            resp = c.get('/users/5000/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("What's Happening?", resp.get_data(as_text=True))
    

    def test_get_request_user_followers_logged_out(self):
        """Can a logged out user access the 'user_followers' page?"""
        with self.client as c:
            resp = c.get('/users/300/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("What's Happening?", resp.get_data(as_text=True))
    

    def test_logged_in_create_message(self):
        """Can a logged in user create a new message?"""
        with self.client as c:
            login(self.client, self.testuser.username, 'testuser')
            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)

            resp = c.post('/messages/new', data={'text': 'my message', 'user_id': self.testuser.id}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Search Warbler', resp.get_data(as_text=True))
    

    def test_logged_in_delete_message(self):
        """Can a logged in user delete a message of their own?"""
        with self.client as c:
            message = Message(text='hi', user_id=self.testuser.id)
            db.session.add(message)
            db.session.commit()

            login(c, self.testuser.username, 'testuser')
            msg = Message.query.filter_by(text='hi').first()
            resp = c.post(f'messages/{msg.id}/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser', resp.get_data(as_text=True))
            all_msgs = Message.query.all()
            self.assertEqual(len(all_msgs), 0)


    def test_logged_out_create_message(self):
        """Is a user able to create a new message while logged out?"""
        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'new message'})
            all_msgs = Message.query.all()
            self.assertEqual(len(all_msgs), 0)
    
    def test_logged_out_delete_message(self):
        """Is a user able to delete a message while logged out?"""
        with self.client as c:
            message = Message(text='hi', user_id=self.testuser.id)
            db.session.add(message)
            db.session.commit()
            self.assertEqual(len(Message.query.all()), 1)

            msg = Message.query.filter_by(text='hi').first()
            resp = c.post(f'messages/{msg.id}/delete', follow_redirects=True)
            self.assertEqual(len(Message.query.all()), 1)
    

    def test_cant_delete_msg_as_other_user(self):
        """Does the app prevent you from deleting a message that is not yours, even if you are logged in?"""
        with self.client as c:
            login(c, self.testuser.username, 'testuser')
            user = User(username='jeff', email='jeff@gmail.com', password=bcrypt.generate_password_hash('heart').decode('utf-8'))
            db.session.add(user)
            user = User.query.filter_by(username='jeff').first()

            message = Message(text='hi', user_id=user.id)
            db.session.add(message)
            db.session.commit()
            self.assertEqual(len(Message.query.all()), 1)

            msg = Message.query.filter_by(text='hi').first()
            
            #logged in user with different id than msg.user_id should not be able to delete the message
            resp = c.post(f'messages/{msg.id}/delete', follow_redirects=True)
            self.assertEqual(len(Message.query.all()), 1)