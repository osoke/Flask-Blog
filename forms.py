from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email


##WTForm
class CreatePostForm(FlaskForm): # 新建post form
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField('Emaill', [Email()])
    password = PasswordField('Password', [DataRequired()])
    name = StringField('Name', [DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField('Emaill', [Email()])
    password = PasswordField('Password', [DataRequired()])
    submit = SubmitField("Sign In")

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()]) # 使用 CKEditor
    submit = SubmitField("Submit Comment")