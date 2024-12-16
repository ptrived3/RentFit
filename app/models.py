from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import base64

db = SQLAlchemy()
DB_NAME = "social.sqlite"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Admin")
    active = db.Column(db.Boolean, default=True)
    bio = db.Column(db.String(200),  nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True)

    # Relationship for followers and followed
    followed = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower_user',
                               lazy='dynamic', cascade="all, delete-orphan")
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', backref='followed_user',
                                lazy='dynamic', cascade="all, delete-orphan")
    # Backref to access posts from a user easily
    posts = db.relationship('Post', backref=db.backref('user', lazy=True), lazy=True, cascade="all, delete-orphan")

    @property
    def is_user_active(self):
        return self.active

    @property
    def profile_picture(self):
        # Returns default.png if profile_pic is None or empty
        return self.profile_pic or 'images/default.png'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def follow(self, user):
        """Follow another user."""
        if not self.is_following(user):
            follow_entry = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow_entry)

    def unfollow(self, user):
        """Unfollow a user."""
        follow_entry = self.followed.filter_by(followed_id=user.id).first()
        if follow_entry:
            db.session.delete(follow_entry)

    def is_following(self, user):
        """Check if the user is following another user."""
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        """Check if the user is followed by another user."""
        return self.followers.filter_by(follower_id=user.id).first() is not None

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # When the follow occurred

    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=True)  # For text content
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store image binary data
    image_mime_type = db.Column(db.String(50), nullable=True)  # To track the MIME type (e.g., "image/png")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of the post

    def is_liked_by(self, user):
        """Check if the post is liked by a specific user."""
        return any(like.user_id == user.id for like in self.likes)

    def to_dict(self):
        """Convert the post to a dictionary for JSON response."""
        post_data = {
            'id': self.id,
            'user_id': self.user_id,
            'text': self.text,
            'timestamp': self.timestamp,
        }
        if self.image_data:
            post_data['image'] = f"data:{self.image_mime_type};base64,{base64.b64encode(self.image_data).decode('utf-8')}"
        return post_data

    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)

    # Backref to access likes for a user
    user = db.relationship('User', backref=db.backref('likes', lazy=True))

    # Backref to access likes for a post
    post = db.relationship('Post', backref=db.backref('likes', lazy=True))

    def __repr__(self):
        return f'<Like User {self.user_id} on Post {self.post_id}>'

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    board_state = db.Column(db.String(9), default=' ' * 9)  # 3x3 grid as a string
    current_turn = db.Column(db.Integer, nullable=False)  # Player1 starts
    status = db.Column(db.String(20), default='waiting')  # 'waiting', 'invited', 'ongoing', 'completed'
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # ID of the winner
    player1_joined = db.Column(db.Boolean, default=False)
    player2_joined = db.Column(db.Boolean, default=False)

    player1 = db.relationship('User', foreign_keys=[player1_id], backref='games_as_player1')
    player2 = db.relationship('User', foreign_keys=[player2_id], backref='games_as_player2')
    winner = db.relationship('User', foreign_keys=[winner_id], backref='games_won')

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_lat = db.Column(db.Float, nullable=False)
    location_lng = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default="No description provided.")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates('location_lat')
    def validate_latitude(self, key, value):
        """Ensure latitude is in the range -90 to 90."""
        if not (-90 <= value <= 90):
            raise ValueError("Latitude must be between -90 and 90.")
        return value

    @validates('location_lng')
    def validate_longitude(self, key, value):
        """Ensure longitude is in the range -180 to 180."""
        if not (-180 <= value <= 180):
            raise ValueError("Longitude must be between -180 and 180.")
        return value

    def to_dict(self):
        """Convert an Event instance to a dictionary for JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'location': {
                'lat': self.location_lat,
                'lng': self.location_lng
            },
            'description': self.description or "No description provided.",
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        """Provide a string representation of the Event instance."""
        return (
            f"<Event id={self.id}, name='{self.name}', "
            f"location=({self.location_lat}, {self.location_lng}), "
            f"description='{self.description[:20] if self.description else 'None'}'>"
        )