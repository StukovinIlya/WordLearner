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
        word_difficulties = session.get('word_difficulties', {})

        results = []
        for word_data in quiz_words:
            word = Word.query.get(word_data['id'])
            if not word:
                continue

            user_answer = user_answers.get(str(word.id), '').strip().lower()
            is_correct = user_answer == word.equivalent.lower()

            original_difficulty = word_difficulties.get(str(word.id), word.difficulty)
            if is_correct:
                word.difficulty = min(original_difficulty + 1, 100)
                score += 1
            else:
                decade = (100 - word.difficulty) // 10
                subtract_value = 2 ** min(decade, 3)
                word.difficulty = max(original_difficulty - subtract_value, 1)

            results.append({
                'word': word_data,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'new_difficulty': word.difficulty
            })

        db.session.commit()

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
        session['word_difficulties'] = {
            key[16:]: int(value) for key, value in request.form.items()
            if key.startswith('word_difficulty_')
        }
        return redirect(url_for('learn_api.timed_quiz', results=True, group_id=group_id))

    quiz_words = [{
        'id': word.id,
        'original': word.original,
        'equivalent': word.equivalent,
        'difficulty': word.difficulty
    } for word in random.sample(words, min(3, len(words)))]

    session['quiz_words'] = quiz_words
    session['user_answers'] = {}
    session['word_difficulties'] = {str(word['id']): word['difficulty'] for word in quiz_words}

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
            is_correct = (user_answer == word.equivalent)

            if is_correct:

                word.difficulty = min(word.difficulty + 1, 100)
                correct_count += 1
            else:
                decade = (100 - word.difficulty) // 10
                subtract_value = 2 ** min(decade, 3)
                word.difficulty = max(word.difficulty - subtract_value, 1)

            statistics = UserStats.query.filter_by(user_id=current_user.id).first()
            if statistics:
                if is_correct:
                    statistics.words_learned += 1
                statistics.last_activity = datetime.utcnow()

            quiz_words.append({
                'id': word.id,
                'original': word.original,
                'correct_answer': word.equivalent,
                'user_answer': user_answer,
                'answers': request.form.getlist(f'answers_{word.id}'),
                'difficulty': word.difficulty
            })

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
                'correct_answer': word.equivalent,
                'difficulty': word.difficulty
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
            is_correct = user_answer.lower() == word.equivalent.lower()

            if is_correct:
                word.difficulty = min(word.difficulty + 1, 100)
                correct_count += 1
            else:
                decade = (100 - word.difficulty) // 10
                subtract_value = 2 ** min(decade, 3)
                word.difficulty = max(word.difficulty - subtract_value, 1)

            statistics = UserStats.query.filter_by(user_id=current_user.id).first()
            if statistics and is_correct:
                statistics.words_learned += 1
                statistics.last_activity = datetime.utcnow()

        db.session.commit()

    return render_template('writing.html',
                           words=words,
                           current_group=current_group,
                           group_id=group_id,
                           show_results=show_results,
                           correct_count=correct_count,
                           total_words=total_words)


@blueprint.route('/check_answer', methods=['POST'])
def check_answer():
    word_id = request.form.get('word_id')
    user_answer = request.form.get(f'word_{word_id}')

    word = Word.query.get(word_id)

    if not word:
        return "Word not found", 404

    is_correct = (user_answer == word.translation)

    if is_correct:
        word.difficulty = min(word.difficulty + 1, 100)
    else:
        decade = (100 - word.difficulty) // 10
        subtract_value = 2 ** decade

        word.difficulty = max(word.difficulty - subtract_value, 1)

    db.session.commit()

    # Возвращаем результат
    return jsonify({
        'correct': is_correct,
        'correct_answer': word.translation,
        'new_difficulty': word.difficulty
    })
