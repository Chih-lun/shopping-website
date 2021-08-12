from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, email

class ContactForm(FlaskForm):
    name = StringField(label='Your name',validators=[DataRequired()])
    email = StringField(label='Email',validators=[DataRequired(),email()])
    phone = StringField(label='Phone',validators=[DataRequired()])
    message = TextAreaField(label='Message',validators=[DataRequired()])
    send = SubmitField(label='Send')

class SignupForm(FlaskForm):
    email = StringField(label='Email',validators=[DataRequired(),email()])
    password = PasswordField(label='Password',validators=[DataRequired()])
    name = StringField(label='Name',validators=[DataRequired()])
    submit = SubmitField(label='Submit')

class LoginForm(FlaskForm):
    email = StringField(label='Email',validators=[DataRequired(),email()])
    password = PasswordField(label='Password',validators=[DataRequired()])
    login = SubmitField(label='Login')