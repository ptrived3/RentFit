from app import app, db  # Ensure you import app and db from your Flask app
from models import Category, Collection, Event, Follow, GameSession, Item, Like, Post, User
from datetime import datetime

def import_sample_data():
    # Make sure you're inside the application context
    with app.app_context():
        # Drop all tables (be careful with this as it deletes all data)
        db.drop_all()
        db.create_all()

        # Add sample categories
        categories = [
            Category(category_name="Sports", description="Items related to sports"),
            Category(category_name="Music", description="Music related items"),
            Category(category_name="Art", description="Art related items")
        ]
        db.session.add_all(categories)
        db.session.commit()

        # Add sample collections
        collections = [
            Collection(category_id=1, collection_name="Football Collection", user_id=1, description="A collection of football memorabilia"),
            Collection(category_id=2, collection_name="Guitar Collection", user_id=2, description="A collection of guitars"),
            Collection(category_id=3, collection_name="Painting Collection", user_id=3, description="A collection of paintings")
        ]
        db.session.add_all(collections)
        db.session.commit()

        # Add sample users
        users = [
            User(username="john_doe", email="john@example.com", password="password", role="admin", active=True, bio="A football enthusiast", profile_pic="profile1.jpg"),
            User(username="jane_doe", email="jane@example.com", password="password", role="user", active=True, bio="A music lover", profile_pic="profile2.jpg"),
            User(username="bob_smith", email="bob@example.com", password="password", role="user", active=True, bio="A fan of art", profile_pic="profile3.jpg")
        ]
        db.session.add_all(users)
        db.session.commit()

        # Add sample posts
        posts = [
            Post(user_id=1, text="Football is my favorite sport!", timestamp=datetime.now()),
            Post(user_id=2, text="I love playing the guitar!", timestamp=datetime.now()),
            Post(user_id=3, text="Art is a way to express yourself.", timestamp=datetime.now())
        ]
        db.session.add_all(posts)
        db.session.commit()

        # Add sample events
        events = [
            Event(name="Football Tournament", location_lat=34.0522, location_lng=-118.2437, description="A thrilling football tournament!", created_at=datetime.now(), updated_at=datetime.now()),
            Event(name="Guitar Concert", location_lat=40.7128, location_lng=-74.0060, description="A live concert featuring talented guitarists!", created_at=datetime.now(), updated_at=datetime.now())
        ]
        db.session.add_all(events)
        db.session.commit()

        # Add sample game sessions
        game_sessions = [
            GameSession(player1_id=1, player2_id=2, board_state="XOXOXOXOX", current_turn=1, status="ongoing", winner_id=None, player1_joined=True, player2_joined=True),
            GameSession(player1_id=2, player2_id=3, board_state="OXOXOXOXO", current_turn=2, status="ongoing", winner_id=None, player1_joined=True, player2_joined=True)
        ]
        db.session.add_all(game_sessions)
        db.session.commit()

        # Add sample items (ensure that acquired_date is a datetime object)
        items = [
            Item(category_id=1, collection_id=1, item_name="Football", acquired_date=datetime.strptime("2023-01-01", "%Y-%m-%d"), estimated_value=50.00, condition="New", description="A signed football"),
            Item(category_id=2, collection_id=2, item_name="Guitar", acquired_date=datetime.strptime("2022-05-15", "%Y-%m-%d"), estimated_value=200.00, condition="Used", description="An electric guitar"),
            Item(category_id=3, collection_id=3, item_name="Painting", acquired_date=datetime.strptime("2021-11-23", "%Y-%m-%d"), estimated_value=150.00, condition="Good", description="A beautiful abstract painting")
        ]
        db.session.add_all(items)
        db.session.commit()

        # Add sample follows
        follows = [
            Follow(follower_id=1, followed_id=2, timestamp=datetime.now()),
            Follow(follower_id=2, followed_id=3, timestamp=datetime.now())
        ]
        db.session.add_all(follows)
        db.session.commit()

        print("Sample data imported successfully!")

if __name__ == "__main__":
    import_sample_data()
