from flask import Flask
from flask_login import LoginManager
from blueprints import home_api, learn_api, words_api
from models import db, User


app = Flask(__name__)
app.config['SECRET_KEY'] = 'WordLearner-SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wordlearner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(home_api.blueprint)
app.register_blueprint(learn_api.blueprint)
app.register_blueprint(words_api.blueprint)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app.run(debug=True)
