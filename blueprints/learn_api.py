import random
from datetime import datetime

import flask
from flask import request, render_template, flash, redirect, url_for, session
from flask_login import login_required, current_user

from models import WordGroup, Word, UserStats, db

blueprint = flask.Blueprint(
    'learn_api',
    __name__,
    template_folder='templates',
)


@blueprint.route('/learn')
@login_required
def learn():
    group_id = request.args.get('group_id', type=int)
    groups = WordGroup.query.filter_by(user_id=current_user.id).all()
    return render_template('learn.html', groups=groups, selected_group=group_id)


@blueprint.route('/timed_quiz', methods=['GET', 'POST'])
@login_required
def timed_quiz():
    group_id = request.args.get('group_id', type=int)

    # Получаем слова из выбранной группы
    if group_id:
        words = Word.query.filter_by(group_id=group_id).all()
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found. Add words first.', 'warning')
        return redirect(url_for('home_api.words'))

    # Обработка отправки формы
    if request.method == 'POST':
        score = 0
        quiz_words = session.get('quiz_words', [])

        for word in quiz_words:
            user_answer = request.form.get(f'word_{word["id"]}', '').strip().lower()
            if user_answer == word['translation'].lower():
                score += 1

        # Обновляем статистику
        stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if stats:
            stats.words_learned += score
            stats.last_activity = datetime.utcnow()
            db.session.commit()

        return render_template('timed_results.html',
                               score=score,
                               total=len(quiz_words),
                               group_id=group_id)

    # Подготовка 5 случайных слов (меньше для ручного ввода)
    quiz_words = []
    selected_words = random.sample(words, min(5, len(words)))

    for word in selected_words:
        quiz_words.append({
            'id': word.id,
            'original': word.original,
            'translation': word.translation
        })

    session['quiz_words'] = quiz_words
    session['quiz_start_time'] = datetime.utcnow().isoformat()

    return render_template('timed_quiz.html',
                           words=quiz_words,
                           group_id=group_id)


@blueprint.route('/flashcards')
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
        return redirect(url_for('home_api.words'))

    return render_template('flashcards.html', words=words)


@blueprint.route('/quiz', methods=['GET', 'POST'])
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
        return redirect(url_for('home_api.words'))

    if request.method == 'POST':
        show_results = True
        correct_count = 0
        quiz_words = []

        for word in words:
            user_answer = request.form.get(f'word_{word.id}')
            quiz_words.append({
                'id': word.id,
                'original': word.original,
                'correct_answer': word.translation,
                'user_answer': user_answer
            })

            if user_answer == word.translation:
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

            answers = [word.translation] + [w.translation for w in wrong_answers]
            random.shuffle(answers)

            quiz_words.append({
                'id': word.id,
                'original': word.original,
                'answers': answers,
                'correct_answer': word.translation
            })

    return render_template('quiz.html',
                           quiz_words=quiz_words,
                           show_results=show_results,
                           current_group=current_group)


@blueprint.route('/writing', methods=['GET', 'POST'])
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
        return redirect(url_for('home_api.words'))

    total_words = len(words)

    if request.method == 'POST':
        show_results = True
        for word in words:
            user_answer = request.form.get(f'answer_{word.id}', '').strip()
            if user_answer.lower() == word.translation.lower():
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