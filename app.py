import random
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from models import db, User, Language
from flask_migrate import Migrate

from set_password import set_password

app = Flask(__name__)
app.config['SECRET_KEY'] = 'WordLearner-SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wordlearner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class WordForm(FlaskForm):
    original = StringField('Original Word', validators=[DataRequired()])
    translation = StringField('Translation', validators=[DataRequired()])
    group = SelectField('Group', coerce=int)
    submit = SubmitField('Add Word')


class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    language = SelectField('Language', coerce=int)
    parent_group = SelectField('Parent Group (optional)', coerce=int)
    submit = SubmitField('Create Group')


class SettingsForm(FlaskForm):
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark')])
    submit = SubmitField('Save Settings')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()
    if not Language.query.first():
        languages = [
            Language(name='English', code='en'),
            Language(name='Russian', code='ru'),
            Language(name='French', code='fr'),
            Language(name='German', code='de'),
            Language(name='Spanish', code='es')
        ]
        db.session.bulk_save_objects(languages)
        db.session.commit()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):  # Проверяем пароль
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.password_hash = set_password(form.password.data)  # Устанавливаем хэшированный пароль
        user.created_at = datetime.now()
        user.theme = 'light'
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
