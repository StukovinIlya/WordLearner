import random
from datetime import datetime

import flask
from flask import request, render_template, flash, redirect, url_for, session, jsonify
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
    current_group = WordGroup.query.get(group_id) if group_id else None
    show_results = request.args.get('results', False, type=bool)
    words = []
    if group_id and current_group:
        def get_all_words_in_group(group):
            words = group.words.copy()
            for child in group.child_groups:
                words.extend(get_all_words_in_group(child))
            return words

        words = get_all_words_in_group(current_group)
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()
    if not words:
        flash('No words found. Add words first.', 'warning')
        return redirect(url_for('words_api.get_words'))
    if show_results:
        score = 0
        quiz_words = session.get('quiz_words', [])
        user_answers = session.get('user_answers', {})

        results = []
        for word in quiz_words:
            user_answer = user_answers.get(str(word['id']), '').strip().lower()
            is_correct = user_answer == word['equivalent'].lower()
            if is_correct:
                score += 1
            results.append({
                'word': word,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if stats:
            stats.words_learned += score
            stats.last_activity = datetime.utcnow()
            db.session.commit()

        return render_template('timed_results.html',
                               score=score,
                               total=len(quiz_words),
                               results=results,
                               current_group=current_group)

    if request.method == 'POST':
        session['user_answers'] = {
            key[5:]: value for key, value in request.form.items()
            if key.startswith('word_')
        }
        return redirect(url_for('learn_api.timed_quiz', results=True, group_id=group_id))

    quiz_words = [{
        'id': word.id,
        'original': word.original,
        'equivalent': word.equivalent
    } for word in random.sample(words, min(15, len(words)))]

    session['quiz_words'] = quiz_words
    session['user_answers'] = {}
    return render_template('timed_quiz.html',
                           words=quiz_words,
                           current_group=current_group)


@blueprint.route('/flashcards')
@login_required
def flashcards():
    group_id = request.args.get('group_id', type=int)
    words = []
    current_group = WordGroup.query.get(group_id) if group_id else None
    if group_id:
        def get_all_words_in_group(group):
            words = group.words.copy()
            for child in group.child_groups:
                words.extend(get_all_words_in_group(child))
            return words

        if current_group:
            words = get_all_words_in_group(current_group)
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found in this group and its subgroups. Add some words first.', 'warning')
        return redirect(url_for('words_api.get_words'))

    random.shuffle(words)

    return render_template('flashcards.html',
                           words=words,
                           current_group=current_group)


@blueprint.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    group_id = request.args.get('group_id', type=int)
    words = []
    show_results = False

    current_group = WordGroup.query.get(group_id) if group_id else None

    if group_id:
        def get_all_words_in_group(group):
            words = group.words.copy()
            for child in group.child_groups:
                words.extend(get_all_words_in_group(child))
            return words

        if current_group:
            words = get_all_words_in_group(current_group)
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found in this group and its subgroups. Add some words first.', 'warning')
        return redirect(url_for('words_api.get_words'))

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
        all_user_words = Word.query.join(WordGroup).filter(
            WordGroup.user_id == current_user.id
        ).all()

        for word in words:
            wrong_answers = [w for w in all_user_words if w.id != word.id]
            wrong_answers = random.sample(wrong_answers, min(3, len(wrong_answers)))

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


@blueprint.route('/writing', methods=['GET', 'POST'])
@login_required
def writing_practice():
    group_id = request.args.get('group_id', type=int)
    if request.method == 'POST':
        group_id = request.form.get('group_id', type=int)
    words = []
    show_results = False
    correct_count = 0
    total_words = 0
    current_group = WordGroup.query.get(group_id) if group_id else None

    if group_id and current_group:
        def get_all_words_in_group(group):
            words = group.words.copy()
            for child in group.child_groups:
                words.extend(get_all_words_in_group(child))
            return words

        words = get_all_words_in_group(current_group)
    else:
        words = Word.query.join(WordGroup).filter(WordGroup.user_id == current_user.id).all()

    if not words:
        flash('No words found. Add some words first.', 'warning')
        return redirect(url_for('words_api.get_words'))

    total_words = len(words)

    if request.method == 'POST':
        show_results = True
        for word in words:
            user_answer = request.form.get(f'answer_{word.id}', '').strip()
            if user_answer.lower() == word.equivalent.lower():
                correct_count += 1
                # Обновляем статистику
                statistics = UserStats.query.filter_by(user_id=current_user.id).first()
                if statistics:
                    statistics.words_learned += 1
                    statistics.last_activity = datetime.utcnow()

        db.session.commit()

    return render_template('writing.html',
                           words=words,
                           current_group=current_group,
                           group_id=group_id,  # Важно передать для формы
                           show_results=show_results,
                           correct_count=correct_count,
                           total_words=total_words)


@blueprint.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    word_id = request.form.get('word_id')
    user_answer = request.form.get('answer', '').strip()

    word = Word.query.get_or_404(word_id)

    is_correct = user_answer.lower() == word.translation.lower()

    if is_correct:
        stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if stats:
            stats.words_learned += 1
            stats.last_activity = datetime.utcnow()
            db.session.commit()

    return jsonify({
        'correct': is_correct,
        'correct_answer': word.translation
    })
