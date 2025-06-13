from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange

class AcademicYearForm(FlaskForm):
    year = StringField('Year', validators=[DataRequired()])
    session = StringField('Session', validators=[DataRequired()])
    submit = SubmitField('Save')

class TeacherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    callsign = StringField('Callsign', validators=[DataRequired()])
    submit = SubmitField('Save')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    code = StringField('Course Code', validators=[DataRequired()])
    type = SelectField('Type', choices=[('Theory', 'Theory'), ('Sessional', 'Sessional')], validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    term = IntegerField('Term', validators=[DataRequired(), NumberRange(min=1, max=2, message="Term must be 1 or 2")])
    credit = IntegerField('Credit', validators=[DataRequired()])
    submit = SubmitField('Save')

class RoomForm(FlaskForm):
    name = StringField('Room Name', validators=[DataRequired()])
    submit = SubmitField('Save')

class AssignCoursesForm(FlaskForm):
    teacher = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    courses = SelectField('Courses', coerce=int, validators=[DataRequired()])
    part = SelectField('Part', choices=[('Full', 'Full Course'), ('Part A', 'Part A'), ('Part B', 'Part B')], validators=[DataRequired()])
    submit = SubmitField('Assign')
