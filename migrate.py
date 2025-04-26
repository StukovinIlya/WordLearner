from flask import Flask
from sqlalchemy.exc import IntegrityError

from migrations.word_group_migration import migrate_word_groups
from migrations.word_migration import migrate_words
from models import db
from migrations.user_migration import migrate_users

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wordlearner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            migrate_users()
        except IntegrityError:
            db.session.rollback()
        migrate_word_groups()
        migrate_words()

