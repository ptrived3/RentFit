from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_admin import Admin
from models import DB_NAME, db, User, Follow, Post, Like, GameSession, Event, Category  # Import Event
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Add enumerate to Jinja globals
    app.jinja_env.globals.update(enumerate=enumerate)
    return app

app = create_app()
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from views import UserAdminView, PostAdminView, LikeAdminView, FollowAdminView, GameSessionView, SignoutView, CategoryView

admin = Admin(app, name='MySocial Admin', template_mode='bootstrap4')
admin.add_view(UserAdminView(User, db.session))
admin.add_view(PostAdminView(Post, db.session))
admin.add_view(LikeAdminView(Like, db.session))
admin.add_view(FollowAdminView(Follow, db.session))
admin.add_view(GameSessionView(GameSession, db.session))
admin.add_view(CategoryView(Category, db.session))
admin.add_view(SignoutView(name="Signout"))

# Optional: Add Event to Admin View
# from views import EventAdminView
# admin.add_view(EventAdminView(Event, db.session))

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
