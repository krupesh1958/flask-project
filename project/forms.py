from dataclasses import field
from flask_wtf import *
from wtforms import *
from wtforms.validators import DataRequired, Email, EqualTo,Length
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import *


class LoginForm(FlaskForm):
    email = StringField("Email::",validators=[DataRequired()])
    password = PasswordField("Password::",validators=[DataRequired()])
    
class RegisterForm(FlaskForm):
    name = StringField("Name::",validators=[DataRequired()])
    email = StringField("Email::",validators=[DataRequired()])
    phone = TelField("Phone::",validators=[DataRequired(),Length(min=10, max=10)])
    password = PasswordField("Password::",validators=[DataRequired()])
    conf_password = PasswordField("Confirm_Password::",validators=[DataRequired()]) 
    otp = IntegerField("otp::",validators=[DataRequired()])
    comment = StringField("Comment::")    
    