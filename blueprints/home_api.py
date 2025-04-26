from datetime import datetime

import flask
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms import LoginForm, RegistrationForm, SettingsForm
from models import db, Word, WordGroup, User, UserStats

blueprint = flask.Blueprint(
    'home_api',
    __name__,
    template_folder='templates',
)


@blueprint.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('home')
    return redirect('/login', code=301)


@blueprint.route('/home')
@login_required
def index():
    return render_template('home.html')


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('home_api.home'))
        flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        user.created_at = datetime.now()
        user.theme = 'light'
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect('login')
    return render_template('register.html', form=form)


@blueprint.route('/privacy')
def privacy():
    return render_template('privacy.html')


@blueprint.route('/terms')
def terms():
    return render_template('terms.html')


@blueprint.route('/contact')
def contact():
    return render_template('contact.html')


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('home.html')


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    stats = UserStats.query.filter_by(user_id=current_user.id).first()
    word_count = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).count()
    group_count = WordGroup.query.filter_by(user_id=current_user.id).count()

    form = SettingsForm()
    if form.validate_on_submit():
        current_user.theme = form.theme.data
        db.session.commit()
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('home_api.profile'))

    form.theme.data = current_user.theme

    return render_template('profile.html',
                           stats=stats,
                           word_count=word_count,
                           group_count=group_count,
                           form=form)
