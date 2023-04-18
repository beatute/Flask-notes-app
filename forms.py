from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from flask_wtf.file import FileField,FileAllowed
from flask_login import current_user
import app

def notebook_query():
    return app.Notebook.query.filter_by(user_id=current_user.id).all()

def notes_query():
    return app.Notes.query

def get_pk(obj):
    return str(obj)


class RegistrationForm(FlaskForm):
    username = StringField('Username', [DataRequired()])
    email = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    checked_password = PasswordField("Repeat Password", [EqualTo('password', "The password should be the same.")])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = app.User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already used')

    def validate_email(self, email):
        user = app.User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already used')


class LoginForm(FlaskForm):
    email = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField('Login')
    
    
class NotebookForm(FlaskForm):
    title = StringField('Title', [DataRequired()])
    notes = QuerySelectMultipleField(query_factory=notes_query, allow_blank=True, get_label="title", get_pk=get_pk)
    submit = SubmitField('Add Notebook')
    

class NotesForm(FlaskForm):
    title = StringField('Title', [DataRequired()])
    description = StringField('Description', [DataRequired()])
    notebooks = QuerySelectMultipleField(query_factory=notebook_query, allow_blank=True, get_label="title", get_pk=get_pk)
    photo = FileField('Image', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add Note')
    
