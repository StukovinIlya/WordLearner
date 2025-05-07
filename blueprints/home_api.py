from datetime import datetime

import flask
from flask import request
import pytz
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms import LoginForm, RegistrationForm, SettingsForm
from ip_files.get_client_ip import get_client_ip
from ip_files.set_offset import set_offset
from models import db, Word, WordGroup, User, UserStats

blueprint = flask.Blueprint(
    'home_api',
    __name__,
    template_folder='templates',
)


@blueprint.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('home')
    return redirect('/login', code=301)


@blueprint.route('/home')
@login_required
def home():
    return render_template('index.html')


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            user.set_ip_address()
            db.session.commit()
            login_user(user)
            user.offset = set_offset()
            db.session.commit()
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
        user.set_ip_address()
        user.offset = 0
        user.set_password(form.password.data)
        user.created_at = datetime.now()
        user.theme = 'light'
        db.session.add(user)
        db.session.commit()
        stats = UserStats()
        stats.user_id = user.id
        db.session.add(stats)
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
    ip_address = get_client_ip()
    user = User.query.get(current_user.id)
    if user:
        user.ip_address = ip_address
        db.session.commit()
    logout_user()
    return render_template('index.html')


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(current_user.id)
    stats = UserStats.query.filter_by(user_id=current_user.id).first()

    if stats and stats.last_activity:
        utc_time = stats.last_activity.replace(tzinfo=pytz.utc)

        user_offset = user.offset if user else 0

        try:
            tz_offset = f"Etc/GMT{-user_offset}" if user_offset >= 0 else f"Etc/GMT{+abs(user_offset)}"
            user_timezone = pytz.timezone(tz_offset)
        except pytz.exceptions.UnknownTimeZoneError:
            user_timezone = pytz.utc

        local_time = utc_time.astimezone(user_timezone)
        stats.last_activity = local_time

    word_count = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).count()
    group_count = WordGroup.query.filter_by(user_id=current_user.id).count()

    return render_template('profile.html',
                           stats=stats,
                           word_count=word_count,
                           group_count=group_count)
