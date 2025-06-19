from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'student', 'teacher', 'admin'
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    taught_classes = db.relationship('Class', backref='teacher', lazy=True, foreign_keys='Class.teacher_id')
    assignments_created = db.relationship('Assignment', backref='creator', lazy=True, foreign_keys='Assignment.teacher_id')
    submissions = db.relationship('Submission', backref='student', lazy=True, foreign_keys='Submission.student_id')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, foreign_keys='Enrollment.student_id')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'

    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # No description
    classes = db.relationship('Class', backref='course', lazy=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='class_obj', lazy=True)
    enrollments = db.relationship('Enrollment', backref='class_obj', lazy=True)
    
    def __repr__(self):
        return f'<Class {self.name}>'

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (db.UniqueConstraint('student_id', 'class_id', name='unique_enrollment'),)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    max_score = db.Column(db.Integer, default=10)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    attachment_path = db.Column(db.String(255))  # Path to uploaded assignment file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='assignment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'
    
    def is_overdue(self):
        return datetime.utcnow() > self.due_date
    
    def get_submission_by_student(self, student_id):
        return Submission.query.filter_by(assignment_id=self.id, student_id=student_id).first()

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_text = db.Column(db.Text)
    file_path = db.Column(db.String(255))  # Path to uploaded submission file
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Grading fields
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime)
    graded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Unique constraint to prevent multiple submissions
    __table_args__ = (db.UniqueConstraint('assignment_id', 'student_id', name='unique_submission'),)
    
    def __repr__(self):
        return f'<Submission {self.id}>'
    
    def is_graded(self):
        return self.score is not None
    
    def is_late(self):
        return self.submitted_at > self.assignment.due_date if self.assignment else False

# Utility to create the default admin user
def create_default_admin():
    with current_app.app_context():
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@gmail.com',
                role='admin'
            )
            admin.set_password('admin@123')
            db.session.add(admin)
            db.session.commit()
