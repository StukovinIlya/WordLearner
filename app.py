import random
from datetime import datetime
from flask import Flask, render_template, redirect, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from models import db, User, Language, WordGroup, UserStats, Word
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
        return redirect('index')
    return render_template('login.html')


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
            return redirect(next_page) if next_page else redirect('index')
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
        return redirect('login')
    return render_template('register.html', form=form)


@app.route('/learn')
@login_required
def learn():
    group_id = request.args.get('group_id', type=int)
    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    return render_template('learn.html', groups=groups, selected_group=group_id)


@app.route('/words', methods=['GET', 'POST'])
@login_required
def words():
    word_form = WordForm()
    group_form = GroupForm()

    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    word_form.group.choices = [(group.id, group.name) for group in groups]
    group_form.language.choices = [(language.id, language.name) for language in Language.query.all()]
    group_form.parent_group.choices = [(0, 'None')] + [(group.id, group.name) for group in groups]

    if word_form.validate_on_submit():
        word = Word(
            original=word_form.original.data,
            translation=word_form.translation.data,
            group_id=word_form.group.data
        )
        db.session.add(word)
        db.session.commit()
        flash('Word added successfully!', 'success')
        return redirect('words', code=301)

    if group_form.validate_on_submit():
        parent_id = group_form.parent_group.data if group_form.parent_group.data != 0 else None
        group = WordGroup(
            name=group_form.name.data,
            language_id=group_form.language.data,
            user_id=current_user.id,
            parent_group_id=parent_id
        )
        db.session.add(group)
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect('words', code=301)

    if request.method == 'POST' and 'delete_word' in request.form:
        word_id = request.form['delete_word']
        word = Word.query.join(WordGroup).filter(
            Word.id == word_id,
            WordGroup.user_id == current_user.id
        ).first()

        if word:
            db.session.delete(word)
            db.session.commit()
            flash('Word deleted successfully!', 'success')
        else:
            flash('Word not found or you don\'t have permission to delete it', 'error')
        return redirect('words', code=301)

    if request.method == 'POST' and 'delete_group' in request.form:
        group_id = request.form['delete_group']
        group = WordGroup.query.filter_by(
            id=group_id,
            user_id=current_user.id
        ).first()

        if group:
            Word.query.filter_by(group_id=group.id).delete()
            db.session.delete(group)
            db.session.commit()
            flash('Group and all its words deleted successfully!', 'success')
        else:
            flash('Group not found or you don\'t have permission to delete it', 'error')
        return redirect('words', code=301)

    words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()
    groups = WordGroup.query.filter_by(user_id=current_user.id).all()

    return render_template('words.html',
                           word_form=word_form,
                           group_form=group_form,
                           words=words,
                           groups=groups)


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('home.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')


@app.route('/timed_quiz', methods=['GET', 'POST'])
@login_required
def timed_quiz():
    return render_template('timed_quiz.html')


@app.route('/learn/flashcards')
@login_required
def flashcards():
    return render_template('flashcards.html')


@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    return render_template('quiz.html')


@app.route('/writing', methods=['GET', 'POST'])
@login_required
def writing_practice():
    return render_template('writing.html')


if __name__ == '__main__':
    app.run(debug=True)
