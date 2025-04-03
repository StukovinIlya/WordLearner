from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Храним только хэш
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme = db.Column(db.String(10), default='light')
    stats = db.relationship('UserStats', backref='user', lazy=True)
    word_groups = db.relationship('WordGroup', backref='creator', lazy=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    words_learned = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime)


class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(5), nullable=False)

    groups = db.relationship('WordGroup', backref='language', lazy=True)


class WordGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_group_id = db.Column(db.Integer, db.ForeignKey('word_group.id'))

    parent = db.relationship('WordGroup', remote_side=[id], backref='subgroups')
    words = db.relationship('Word', backref='group', lazy=True)


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(100), nullable=False)
    translation = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('word_group.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime)
    difficulty = db.Column(db.Integer, default=1)
