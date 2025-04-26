import random
from datetime import datetime
from flask import Flask, render_template, redirect, flash, request, session, url_for, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, WordGroup, UserStats, Word
from forms import RegistrationForm, LoginForm, GroupForm, SettingsForm, WordForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'WordLearner-SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wordlearner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('home')
    return redirect(url_for('login', code=301))


@app.route('/home')
@login_required
def index():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.password_hash = user.set_password(form.password.data)
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


@app.route('/words', methods=['GET'])
def get_words() -> str:
    word_form = WordForm()
    group_form = GroupForm()

    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    word_form.group.choices = [(group.id, group.name) for group in groups]
    group_form.parent_group.choices = [(0, 'None')] + [(group.id, group.name) for group in groups]

    words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()
    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    return render_template('words.html',
                           word_form=word_form,
                           group_form=group_form,
                           words=words,
                           groups=groups)


@app.route('/word', methods=['POST'])
def create_word() -> Response:
    word_form = WordForm()
    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    word_form.group.choices = [(group.id, group.name) for group in groups]
    if not word_form.validate_on_submit() or 'original' not in request.form:
        flash('Adding error!', 'error')
        return redirect('/words')
    word = Word(
        original=word_form.original.data,
        equivalent=word_form.equivalent.data,
        group_id=word_form.group.data
    )
    db.session.add(word)
    db.session.commit()
    flash('The word was added successfully!', 'success')
    return redirect('/words')


@app.route('/word-delete', methods=['POST'])
def delete_word() -> Response:
    if 'delete_word' not in request.form:
        return redirect(url_for('words'))
    word_id = request.form['delete_word']
    word = Word.query.join(WordGroup).filter(
        Word.id == word_id,
        WordGroup.user_id == current_user.id
    ).first()

    if not word:
        flash('The word was not found or there are no rights to delete it.', 'error')
        return redirect(url_for('words'))
    db.session.delete(word)
    db.session.commit()
    flash('The word was deleted successfully!', 'success')
    return redirect(url_for('words'))


@app.route('/group', methods=['POST'])
def create_group() -> Response:
    group_form = GroupForm()

    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    group_form.parent_group.choices = [(0, 'None')] + [(group.id, group.name) for group in groups]
    if not group_form.validate_on_submit() or 'name' not in request.form:
        flash('Adding error!', 'error')
        return redirect(url_for('words'))
    parent_id = group_form.parent_group.data if group_form.parent_group.data != 0 else None
    group = WordGroup(
        name=group_form.name.data,
        user_id=current_user.id,
        parent_group_id=parent_id
    )
    db.session.add(group)
    db.session.commit()
    flash('The group was created successfully!', 'success')
    return redirect(url_for('words'))


@app.route('/group-delete', methods=['POST'])
def delete_group() -> Response:
    group_form = GroupForm()

    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    group_form.parent_group.choices = [(0, 'None')] + [(group.id, group.name) for group in groups]
    if 'delete_group' not in request.form:
        return redirect(url_for('words'))
    group_id = request.form['delete_group']
    group = WordGroup.query.filter_by(
        id=group_id,
        user_id=current_user.id
    ).first()

    if not group:
        flash('The group was not found or there are no rights to delete it.', 'error')
        return redirect(url_for('words'))
    Word.query.filter_by(group_id=group.id).delete()
    db.session.delete(group)
    db.session.commit()
    flash('The group and all its words have been deleted successfully!', 'success')
    return redirect(url_for('words'))


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
    stats = UserStats.query.filter_by(user_id=current_user.id).first()
    word_count = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).count()
    group_count = WordGroup.query.filter_by(user_id=current_user.id).count()

    form = SettingsForm()
    if form.validate_on_submit():
        current_user.theme = form.theme.data
        db.session.commit()
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('profile'))

    form.theme.data = current_user.theme

    return render_template('profile.html',
                           stats=stats,
                           word_count=word_count,
                           group_count=group_count,
                           form=form)


@app.route('/timed_quiz', methods=['GET', 'POST'])
@login_required
def timed_quiz():
    group_id = request.args.get('group_id', type=int)

    if group_id:
        words = Word.query.filter_by(group_id=group_id).all()
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found. Add words first.', 'warning')
        return redirect(url_for('words'))

    if request.method == 'POST':
        score = 0
        quiz_words = session.get('quiz_words', [])

        for word in quiz_words:
            user_answer = request.form.get(f'word_{word["id"]}', '').strip().lower()
            if user_answer == word['equivalent'].lower():
                score += 1

        stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if stats:
            stats.words_learned += score
            stats.last_activity = datetime.utcnow()
            db.session.commit()

        return render_template('timed_results.html',
                               score=score,
                               total=len(quiz_words),
                               group_id=group_id)

    quiz_words = []
    selected_words = random.sample(words, min(5, len(words)))

    for word in selected_words:
        quiz_words.append({
            'id': word.id,
            'original': word.original,
            'equivalent': word.equivalent
        })

    session['quiz_words'] = quiz_words
    session['quiz_start_time'] = datetime.utcnow().isoformat()

    return render_template('timed_quiz.html',
                           words=quiz_words,
                           group_id=group_id)


@app.route('/flashcards')
@login_required
def flashcards():
    group_id = request.args.get('group_id', type=int)
    words = []

    if group_id:
        words = Word.query.filter_by(group_id=group_id).all()
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found in this group. Add some words first.', 'warning')
        return redirect(url_for('words'))

    return render_template('flashcards.html', words=words)


@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    group_id = request.args.get('group_id', type=int)
    words = []
    show_results = False

    current_group = WordGroup.query.get(group_id) if group_id else None

    if group_id:
        words = Word.query.filter_by(group_id=group_id).all()
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found in this group. Add some words first.', 'warning')
        return redirect(url_for('words'))

    if request.method == 'POST':
        show_results = True
        correct_count = 0
        quiz_words = []

        for word in words:
            user_answer = request.form.get(f'word_{word.id}')
            quiz_words.append({
                'id': word.id,
                'original': word.original,
                'correct_answer': word.equivalent,
                'user_answer': user_answer
            })

            if user_answer == word.equivalent:
                correct_count += 1
                statistics = UserStats.query.filter_by(user_id=current_user.id).first()
                if statistics:
                    statistics.words_learned += 1
                    statistics.last_activity = datetime.utcnow()

        db.session.commit()
        flash(f'You got {correct_count} out of {len(words)} correct!', 'info')
    else:
        quiz_words = []
        for word in words:
            wrong_answers = Word.query.filter(
                Word.id != word.id,
                Word.group_id == word.group_id
            ).order_by(db.func.random()).limit(3).all()

            answers = [word.equivalent] + [w.equivalent for w in wrong_answers]
            random.shuffle(answers)

            quiz_words.append({
                'id': word.id,
                'original': word.original,
                'answers': answers,
                'correct_answer': word.equivalent
            })

    return render_template('quiz.html',
                           quiz_words=quiz_words,
                           show_results=show_results,
                           current_group=current_group)


@app.route('/writing', methods=['GET', 'POST'])
@login_required
def writing_practice():
    group_id = request.args.get('group_id', type=int)
    words = []
    show_results = False
    correct_count = 0
    total_words = 0

    if group_id:
        words = Word.query.filter_by(group_id=group_id).all()
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found in this group. Add some words first.', 'warning')
        return redirect(url_for('words'))

    total_words = len(words)

    if request.method == 'POST':
        show_results = True
        for word in words:
            user_answer = request.form.get(f'answer_{word.id}', '').strip()
            if user_answer.lower() == word.equivalent.lower():
                correct_count += 1
                statistics = UserStats.query.filter_by(user_id=current_user.id).first()
                if statistics:
                    statistics.words_learned += 1
                    statistics.last_activity = datetime.utcnow()

        db.session.commit()

    return render_template('writing.html',
                           words=words,
                           group_id=group_id,
                           show_results=show_results,
                           correct_count=correct_count,
                           total_words=total_words)


if __name__ == '__main__':
    app.run(debug=True)
