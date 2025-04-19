from wtforms import StringField, SubmitField, SelectField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired


class WordForm(FlaskForm):
    original = StringField('Original Word', validators=[DataRequired()])
    translation = StringField('Translation', validators=[DataRequired()])
    group = SelectField('Group', coerce=int)
    submit = SubmitField('Add Word')
