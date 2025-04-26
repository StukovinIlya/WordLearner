import flask
from flask import redirect, request, flash, render_template, Response, url_for
from flask_login import login_required, current_user

from forms import WordForm, GroupForm
from models import WordGroup, db, Word

blueprint = flask.Blueprint(
    'words_api',
    __name__,
    template_folder='templates',
)


@blueprint.route('/words', methods=['GET'])
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


@blueprint.route('/word', methods=['POST'])
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


@blueprint.route('/word-delete', methods=['POST'])
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


@blueprint.route('/group', methods=['POST'])
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


@blueprint.route('/group-delete', methods=['POST'])
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
