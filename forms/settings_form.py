from wtforms import SubmitField, SelectField
from flask_wtf import FlaskForm


class SettingsForm(FlaskForm):
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark')])
    submit = SubmitField('Save Settings')
