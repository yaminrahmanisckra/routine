from .db import db

class AcademicYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(10), nullable=False)
    session = db.Column(db.String(20), nullable=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    callsign = db.Column(db.String(10), nullable=False, unique=True)
    courses = db.relationship('TeacherCourse', back_populates='teacher')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    type = db.Column(db.String(20), nullable=False)  # Theory/Sessional
    year = db.Column(db.String(10), nullable=False)
    term = db.Column(db.String(10), nullable=False, default='')
    credit = db.Column(db.Integer, nullable=False)
    class_count = db.Column(db.Integer, nullable=False, default=1)  # Number of classes per week
    shared_callsign = db.Column(db.String(20), nullable=True)  # For shared courses (e.g. PC/HM)
    teachers = db.relationship('TeacherCourse', back_populates='course')
    routine_slots = db.relationship('RoutineSlot', backref='course', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

class TeacherCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    part = db.Column(db.String(10), nullable=False, default='Full')  # 'Part A', 'Part B', 'Full'
    teacher = db.relationship('Teacher', back_populates='courses')
    course = db.relationship('Course', back_populates='teachers')

class RoutineSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)  # Sunday ... Thursday
    slot_index = db.Column(db.Integer, nullable=False)  # 0-based slot
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    # Optional: academic_year_id, etc.
