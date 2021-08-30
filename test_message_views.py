"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from flask import session

from models import db, connect_db, Message, User

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


def login(client, username, password):
        return client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    

def logout(client):
    return client.get('/logout', follow_redirects=True)


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

    def test_add_message(self):
        """Can users add a message?"""

        with self.client as c:
            login(c, self.testuser.username, 'testuser')
            self.assertEqual(session[CURR_USER_KEY], self.testuser.id)
            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.all()
            self.assertEqual(len(msg), 1)
            msg = Message.query.one()
            self.assertEqual(msg.text, 'Hello')
    

    def test_delete_message(self):
        """Can users delete a message?"""

        with self.client as c:
            login(c, self.testuser.username, 'testuser')
            c.post('/messages/new', data={'text': 'Hi'})
            msg = Message.query.filter_by(text='Hi').first()
            resp = c.post(f'/messages/{msg.id}/delete')
            message_count = len(Message.query.all())
            self.assertEqual(message_count, 0)
    

    def test_show_messages(self):
        """Can logged in users see a particular message?"""
        with self.client as c:
            login(c, self.testuser.username, 'testuser')
            c.post('/messages/new', data={'text': 'Hi'})
            msg = Message.query.filter_by(text='Hi').first()

            resp = c.get(f'/messages/{msg.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hi', resp.get_data(as_text=True))

            
