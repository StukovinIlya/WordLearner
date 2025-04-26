from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, SelectField
from wtforms.validators import DataRequired


class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    parent_group = SelectField('Parent Group (optional)', coerce=int)
    submit = SubmitField('Create Group')
