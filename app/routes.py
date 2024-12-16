import base64

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, login_manager
from models import User, Follow, Post, Like, GameSession, Collection, Category, Item
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from models import Event

# Configure the upload folder for profile pictures
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        if current_user and current_user.is_authenticated:
            if current_user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch the user from the database
        user = User.query.filter_by(username=username).first()

        # Check if user exists and the password is correct
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
    elif request.method == 'GET':
        if current_user and current_user.is_authenticated:
            if current_user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # Flash a success message for user feedback
    flash('You have been logged out successfully.', 'success')
    # Redirect the user to the login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'User'

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Create a new user
        new_user = User(username=username, email=email, password=generate_password_hash(password),
                        role=role,active=True, profile_pic = 'images/default.png')

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

def get_feed_posts():
    followed_users = [follow.followed_id for follow in current_user.followed]
    posts = Post.query.filter(Post.user_id.in_(followed_users)).order_by(Post.timestamp.desc()).all()
    return posts

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'User':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    # Retrieve feed posts
    posts = get_feed_posts()

    # Retrieve the user's active games
    active_games = GameSession.query.filter(
        (GameSession.player1_id == current_user.id) |
        (GameSession.player2_id == current_user.id)
    ).all()

    return render_template('user_dashboard.html', posts=posts, active_games=active_games)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user information
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.bio = request.form['bio']

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename != '':
                filename = secure_filename(profile_pic.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(file_path)
                current_user.profile_pic = f'uploads/{filename}'

        # Save changes to the database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    # Load existing user data on GET
    return render_template('profile.html', user=current_user)

@app.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    # Query the user by ID
    user = User.query.get_or_404(user_id)
    is_following = current_user.is_following(user)  # Check if the current user is following this user
    # Render the profile page in view-only mode
    return render_template('view_profile.html', user=user, is_following=is_following)

# Route to create a new post
@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    text = request.form.get('text')
    image = request.files.get('image')

    # Handle image upload
    image_data = None
    if image:
        image_data = image.read()  # Store image as binary data
        image_mime_type = image.mimetype
    else:
        image_mime_type = None

    # Create new post
    post = Post(user_id=current_user.id, text=text, image_data=image_data, image_mime_type=image_mime_type)
    db.session.add(post)
    db.session.commit()

    flash('Your post has been created!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query')
    if query:
        search_results = User.query.filter(User.username.ilike(f'%{query}%')).filter(User.id != current_user.id).all()
        results = [{'id': user.id, 'username': user.username, 'is_following': current_user.is_following(user)} for user in search_results]
    else:
        results = []
    return jsonify(results)


@app.route('/search_game_users', methods=['GET'])
@login_required
def search_game_users():
    print("search_game_users called")
    query = request.args.get('query')
    game_id = request.args.get('game_id')  # Optional: for excluding already invited players
    excluded_user_ids = [current_user.id]

    if game_id:
        # Fetch the game and exclude invited players
        game = GameSession.query.get(int(game_id))
        if game and game.player2_id:
            excluded_user_ids.append(game.player2_id)

    if query:
        search_results = User.query.filter(
            User.username.ilike(f'%{query}%'),
            ~User.id.in_(excluded_user_ids)  # Exclude current user and already invited players
        ).all()

        results = [
            {'id': user.id, 'username': user.username, 'is_following': current_user.is_following(user)}
            for user in search_results
        ]
    else:
        results = []

    print(query, game_id)
    return jsonify(results)


# Route to follow a user
@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    current_user.follow(user_to_follow)
    db.session.commit()
    flash(f'You are now following {user_to_follow.username}!', 'success')
    return redirect(url_for('user_dashboard'))

# Route to unfollow a user
@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    user_to_unfollow = User.query.get_or_404(user_id)
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    flash(f'You have unfollowed {user_to_unfollow.username}.', 'info')
    return redirect(url_for('user_dashboard'))

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if not existing_like:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
    return jsonify({'success': True, 'liked': True, 'post_id': post_id})

@app.route('/unlike/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    return jsonify({'success': True, 'liked': False, 'post_id': post_id})

# Define a custom filter for Base64 encoding
@app.template_filter('b64encode')
def b64encode(value):
    """Base64 encode the given value."""
    if value:
        return base64.b64encode(value).decode('utf-8')
    return ''


@app.route('/create_game', methods=['POST'])
@login_required
def create_game():
    new_game = GameSession(player1_id=current_user.id, current_turn=current_user.id)
    db.session.add(new_game)
    db.session.commit()

    # Render the HTML for the game
    game_html = render_template('game.html', game=new_game)

    # Return both the rendered HTML and game_id as JSON
    return jsonify({'html': game_html, 'game_id': new_game.id})

@app.route('/invite/<int:user_id>/<int:game_id>', methods=['POST'])
@login_required
def invite_user(user_id, game_id):
    print(f"invite_user user_id: {user_id} game_id:{game_id}")
    game = GameSession.query.get_or_404(game_id)
    if game.player1_id != current_user.id or game.status != 'waiting':
        flash('Unauthorized action or game already started!', 'danger')
        return redirect(url_for('user_dashboard'))
    user = User.query.get_or_404(user_id)
    game.player2_id = user.id
    game.status = 'invited'
    db.session.commit()
    flash(f'You invited {user.username} to the game!', 'success')
    return jsonify({'success': True, 'message': f'You invited {user.username} to the game!'})

@app.route('/game/<int:game_id>', methods=['GET'])
@login_required
def view_game(game_id):
    game = GameSession.query.get_or_404(game_id)
    if current_user.id not in [game.player1_id, game.player2_id]:
        flash('Unauthorized access to this game.', 'danger')
        return redirect(url_for('user_dashboard'))

    if current_user.id == game.player1_id:
        game.player1_joined = True
    elif current_user.id == game.player2_id:
        game.player2_joined = True
    if game.player1_joined and game.player2_joined:
        game.status = 'ongoing'
    db.session.commit()
    return render_template('game.html', game=game)

@app.route('/games', methods=['GET'])
@login_required
def games():
    print("games() called!")
    active_games = GameSession.query.filter(
        (GameSession.player1_id == current_user.id) |
        (GameSession.player2_id == current_user.id)
    ).all()
    return render_template('games.html', active_games=active_games)


@app.route('/game/<int:game_id>/move', methods=['POST'])
@login_required
def make_move(game_id):
    if not request.is_json:  # Ensure the request is JSON
        return jsonify({'success': False, 'message': 'Request must be JSON!'}), 415

    data = request.get_json()  # Parse JSON payload
    position = data.get('position')
    print(position, type(position))
    if position is None or not (0 <= int(position) < 9):
        return jsonify({'success': False, 'message': f'Invalid position! position: {position}'}), 400

    position = int(position)
    game = GameSession.query.get_or_404(game_id)

    # Check if the game is ongoing
    if game.status != 'ongoing':
        return jsonify({'success': False, 'message': 'Game is not active!'})

    # Check if it is the current user's turn
    if current_user.id != game.current_turn:
        return jsonify({'success': False, 'message': 'It is not your turn!'})

    # Validate the position
    position = request.json.get('position')  # Position 0-8
    if position is None or not (0 <= position < 9):
        return jsonify({'success': False, 'message': f'Invalid position! position: {position}'})

    if game.board_state[position] != ' ':
        return jsonify({'success': False, 'message': 'Invalid move. Cell already taken!'})

    # Update the board
    marker = 'X' if current_user.id == game.player1_id else 'O'
    board_list = list(game.board_state)
    board_list[position] = marker
    game.board_state = ''.join(board_list)

    # Check for winner
    winner = check_winner(game.board_state)
    if winner:
        game.status = 'completed'
        game.winner_id = current_user.id
        db.session.commit()
        return jsonify({
            'success': True,
            'status': 'completed',
            'board_state': game.board_state,
            'winner': {'id': current_user.id, 'username': current_user.username},
        })

    # Check for draw
    if ' ' not in game.board_state:
        game.status = 'completed'
        db.session.commit()
        return jsonify({
            'success': True,
            'status': 'completed',
            'board_state': game.board_state,
            'winner': None,
        })

    # Switch turn
    game.current_turn = game.player2_id if current_user.id == game.player1_id else game.player1_id
    db.session.commit()

    return jsonify({
        'success': True,
        'status': 'ongoing',
        'board_state': game.board_state,
        'current_turn': game.current_turn,
    })


@app.route('/leaderboard', methods=['GET'])
@login_required
def leaderboard():
    winners = db.session.query(User.username, db.func.count(GameSession.winner_id).label('wins')) \
        .join(GameSession, User.id == GameSession.winner_id) \
        .group_by(User.id) \
        .order_by(db.desc('wins')) \
        .all()
    return render_template('leaderboard.html', winners=winners)

def check_winner(board):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6],             # Diagonals
    ]
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != ' ':
            return True
    return False

@app.route('/game/<int:game_id>/state', methods=['GET'])
@login_required
def get_game_state(game_id):
    game = GameSession.query.get_or_404(game_id)

    # Check if the user is a participant in the game
    if current_user.id not in [game.player1_id, game.player2_id]:
        return jsonify({'error': 'Unauthorized access'}), 403

    # Return the current game state
    response = {
        'game_id': game.id,
        'board_state': game.board_state,
        'status': game.status,
        #'current_turn': game.current_turn,
        'winner': {
            'id': game.winner_id,
            'username': game.winner.username
        } if game.winner else None
    }

    if game.status == 'ongoing':
        response['current_turn'] = game.current_turn
    return jsonify(response)


# Places
@app.route('/places')
def places():
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    print(google_maps_api_key)
    return render_template('places.html', api_key=google_maps_api_key)

# Fetch all events
@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        # Query all events using SQLAlchemy ORM
        events = Event.query.all()

        # Build the response list
        event_list = [
            {
                'id': event.id,
                'name': event.name or "No Name",
                'location': {
                    'lat': float(event.location_lat) if event.location_lat else 0.0,
                    'lng': float(event.location_lng) if event.location_lng else 0.0
                },
                'description': event.description or "No Description",
                'updated_at': event.updated_at.isoformat() if event.updated_at else None
            }
            for event in events
        ]

        return jsonify(event_list), 200

    except Exception as e:
        # Log the exception (optional, depending on your logging setup)
        print(f"Error fetching events: {e}")
        return jsonify({'error': 'Failed to fetch events. Please try again later.'}), 500


# Add a new event
@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.json

    # Validate input
    if not data or 'name' not in data or 'location' not in data or 'description' not in data:
        return jsonify({'error': 'Invalid input data'}), 400

    # Create new event
    new_event = Event(
        name=data['name'],
        location_lat=data['location']['lat'],
        location_lng=data['location']['lng'],
        description=data['description']
    )

    try:
        db.session.add(new_event)
        db.session.commit()
        return jsonify({
            'id': new_event.id,
            'name': new_event.name,
            'location': {
                'lat': new_event.location_lat,
                'lng': new_event.location_lng
            },
            'description': new_event.description
        }), 201  # 201 status for Created
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to save event'}), 500



# Update an existing event
@app.route('/api/events/<int:id>', methods=['PUT'])
def update_event(id):
    data = request.json

    # Validate incoming data
    if not data or 'name' not in data or 'location' not in data or 'description' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    if 'lat' not in data['location'] or 'lng' not in data['location']:
        return jsonify({'error': 'Invalid location data'}), 400

    # Find the event by ID
    event = Event.query.get(id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Update the event details
    event.name = data['name']
    event.location_lat = data['location']['lat']
    event.location_lng = data['location']['lng']
    event.description = data['description']
    event.updated_at = datetime.utcnow()

    # Commit changes to the database
    db.session.commit()

    return jsonify({
        'message': 'Event updated successfully!',
        'event': {
            'id': event.id,
            'name': event.name,
            'location': {
                'lat': event.location_lat,
                'lng': event.location_lng
            },
            'description': event.description,
            'updated_at': event.updated_at.isoformat()
        }
    }), 200

# Delete an event
@app.route('/api/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    try:
        # Find the event to delete
        event = db.session.query(Event).get(id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Delete the event
        db.session.delete(event)
        db.session.commit()

        return jsonify({'message': 'Event deleted successfully!'}), 200
    except Exception as e:
        print(f"Error deleting event: {e}")
        return jsonify({'error': 'Failed to delete the event. Please try again later.'}), 500
    

## Admin dashboard routes and methods
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))  # Redirect to login if not admin

    # Redirect to the /admin page directly
    return redirect(url_for('admin.index'))

@app.cli.command('set_default_pics')
def set_default_pics():
    users = User.query.filter((User.profile_pic == None) | (User.profile_pic == '')).all()
    for user in users:
        user.profile_pic = 'images/default.png'
    db.session.commit()
    print(f"Updated {len(users)} users with default profile pictures.")

@app.route('/collections', methods=['GET'])
@login_required
def collections():
    # Example: Fetch collections from the database for the current user
    user_collections = Collection.query.filter_by(user_id=current_user.id).all()
    return render_template('collections.html', collections=user_collections)

@app.route('/manage_collections', methods=['GET', 'POST'])
@login_required
def manage_collections():
    if request.method == 'POST':
        # Retrieve form data
        collection_name = request.form.get('collection_name')
        category_id = request.form.get('category_id')  # Selected category
        description = request.form.get('description')

        # Create a new collection
        new_collection = Collection(
            category_id=category_id,
            collection_name=collection_name,
            user_id=current_user.id,
            description=description
        )
        db.session.add(new_collection)
        db.session.commit()
        flash('Collection added successfully!', 'success')
        return redirect(url_for('manage_collections'))

    # Fetch user collections and categories for dropdown
    user_collections = Collection.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.all()
    return render_template(
        'manage_collections.html',
        collections=user_collections,
        categories=categories
    )


@app.route('/manage_items', methods=['GET', 'POST'])
@login_required
def manage_items():
    if request.method == 'POST':
        # Retrieve form data
        item_name = request.form.get('item_name')
        collection_id = request.form.get('collection_id')
        estimated_value = request.form.get('estimated_value')
        condition = request.form.get('condition')
        acquired_date = request.form.get('acquired_date')
        description = request.form.get('description')

        # Get the associated collection to determine the category
        collection = Collection.query.get(collection_id)
        if not collection or collection.user_id != current_user.id:
            flash('Invalid collection selected.', 'error')
            return redirect(url_for('manage_items'))

        # Create a new item
        new_item = Item(
            category_id=collection.category_id,  # Auto-populate category
            collection_id=collection_id,
            item_name=item_name,
            acquired_date=datetime.strptime(acquired_date, '%Y-%m-%d'),
            estimated_value=estimated_value,
            condition=condition,
            description=description
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('manage_items'))

    # Fetch collections and items for the current user
    user_collections = Collection.query.filter_by(user_id=current_user.id).all()
    items = Item.query.join(Collection).filter(Collection.user_id == current_user.id).all()
    return render_template(
        'manage_items.html',
        collections=user_collections,
        items=items
    )