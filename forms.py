from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateTimeField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from wtforms.widgets import DateTimeLocalInput

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    class_id = SelectField('Course', coerce=int, validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Create Class')

class AssignmentForm(FlaskForm):
    title = StringField('Assignment Title', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], widget=DateTimeLocalInput())
    max_score = IntegerField('Maximum Score', validators=[DataRequired(), NumberRange(min=1, max=100)], default=10)
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    attachment = FileField('Attachment', validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'], 'Invalid file type!')])
    submit = SubmitField('Create Assignment')

class SubmissionForm(FlaskForm):
    submission_text = TextAreaField('Submission Text')
    file = FileField('Upload File', validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'], 'Invalid file type!')])
    submit = SubmitField('Submit Assignment')

class GradeForm(FlaskForm):
    score = IntegerField('Score', validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField('Feedback')
    submit = SubmitField('Grade Submission')

class EnrollStudentForm(FlaskForm):
    student_email = StringField('Student Email', validators=[DataRequired(), Email()])
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Enroll Student')

class AdminClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    teacher_id = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')
