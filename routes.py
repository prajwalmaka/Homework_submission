import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_, func
from functools import wraps

from app import db
from models import User, Class, Assignment, Submission, Enrollment
from forms import LoginForm, RegisterForm, ClassForm, AssignmentForm, SubmissionForm, GradeForm, EnrollStudentForm, AdminClassForm
from utils import allowed_file, save_uploaded_file

# Create blueprints
auth_bp = Blueprint('auth', __name__)
teacher_bp = Blueprint('teacher', __name__)
student_bp = Blueprint('student', __name__)
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)

# Main routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.is_teacher():
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@main_bp.route('/api/calendar-events')
@login_required
def calendar_events():
    if current_user.is_teacher():
        # Teachers see all assignments they created
        assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
    else:
        # Students see assignments from their enrolled classes
        enrolled_classes = [e.class_id for e in current_user.enrollments]
        assignments = Assignment.query.filter(Assignment.class_id.in_(enrolled_classes)).all()
    
    events = []
    for assignment in assignments:
        events.append({
            'id': assignment.id,
            'title': assignment.title,
            'start': assignment.due_date.isoformat(),
            'description': assignment.description or '',
            'className': 'assignment-event'
        })
    
    return jsonify(events)

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = request.args.get('role', 'student')
    if role not in ['teacher', 'student']:
        role = 'student'
    form = RegisterForm()
    # For students, populate course choices
    if role == 'student':
        courses = Class.query.all()
        form.class_id.choices = [(c.id, c.name) for c in courses]
    else:
        form.class_id.choices = []
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', form=form, role=role)
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=role,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        # If student, enroll in selected course
        if role == 'student' and form.class_id.data:
            enrollment = Enrollment(student_id=user.id, class_id=form.class_id.data)
            db.session.add(enrollment)
            db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, role=role)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register/choice')
def register_choice():
    return render_template('auth/register_choice.html')

# Teacher routes
@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get teacher's classes and assignments
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    recent_assignments = Assignment.query.filter_by(teacher_id=current_user.id).order_by(Assignment.created_at.desc()).limit(5).all()
    
    # Get pending submissions
    pending_submissions = db.session.query(Submission).join(Assignment).filter(
        Assignment.teacher_id == current_user.id,
        Submission.score.is_(None)
    ).count()
    
    return render_template('teacher/dashboard.html', 
                         classes=classes, 
                         recent_assignments=recent_assignments,
                         pending_submissions=pending_submissions)

@teacher_bp.route('/students')
@login_required
def students():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all students enrolled in teacher's classes
    teacher_classes = Class.query.filter_by(teacher_id=current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    enrollments = Enrollment.query.filter(Enrollment.class_id.in_(class_ids)).all()
    students = [e.student for e in enrollments]
    
    # Remove duplicates
    unique_students = list({s.id: s for s in students}.values())
    
    form = EnrollStudentForm()
    form.class_id.choices = [(c.id, c.name) for c in teacher_classes]
    
    return render_template('teacher/students.html', students=unique_students, form=form, classes=teacher_classes)

@teacher_bp.route('/enroll-student', methods=['POST'])
@login_required
def enroll_student():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    form = EnrollStudentForm()
    teacher_classes = Class.query.filter_by(teacher_id=current_user.id).all()
    form.class_id.choices = [(c.id, c.name) for c in teacher_classes]
    
    if form.validate_on_submit():
        student = User.query.filter_by(email=form.student_email.data, role='student').first()
        if not student:
            flash('Student not found with that email.', 'danger')
            return redirect(url_for('teacher.students'))
        
        # Check if already enrolled
        existing = Enrollment.query.filter_by(student_id=student.id, class_id=form.class_id.data).first()
        if existing:
            flash('Student is already enrolled in this class.', 'warning')
            return redirect(url_for('teacher.students'))
        
        enrollment = Enrollment(student_id=student.id, class_id=form.class_id.data)
        db.session.add(enrollment)
        db.session.commit()
        
        flash(f'Student {student.name} enrolled successfully!', 'success')
    
    return redirect(url_for('teacher.students'))

@teacher_bp.route('/create-class', methods=['GET', 'POST'])
@login_required
def create_class():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    form = ClassForm()
    if form.validate_on_submit():
        class_obj = Class(
            name=form.name.data,
            description=form.description.data,
            teacher_id=current_user.id
        )
        db.session.add(class_obj)
        db.session.commit()
        
        flash('Class created successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('teacher/create_class.html', form=form)

@teacher_bp.route('/assignments')
@login_required
def assignments():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).order_by(Assignment.due_date.desc()).all()
    return render_template('teacher/assignments.html', assignments=assignments)

@teacher_bp.route('/create-assignment', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    form = AssignmentForm()
    teacher_classes = Class.query.filter_by(teacher_id=current_user.id).all()
    form.class_id.choices = [(c.id, c.name) for c in teacher_classes]
    
    if not teacher_classes:
        flash('You need to create a class first before creating assignments.', 'warning')
        return redirect(url_for('teacher.create_class'))
    
    if form.validate_on_submit():
        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            max_score=form.max_score.data,
            teacher_id=current_user.id,
            class_id=form.class_id.data
        )
        
        # Handle file upload
        if form.attachment.data:
            file_path = save_uploaded_file(form.attachment.data)
            if file_path:
                assignment.attachment_path = file_path
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('teacher.assignments'))
    
    return render_template('teacher/create_assignment.html', form=form)

@teacher_bp.route('/assignment/<int:assignment_id>/submissions')
@login_required
def view_submissions(assignment_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.assignments'))
    
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    return render_template('teacher/view_submissions.html', assignment=assignment, submissions=submissions)

@teacher_bp.route('/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
def grade_submission(submission_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    submission = Submission.query.get_or_404(submission_id)
    if submission.assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.assignments'))
    
    form = GradeForm()
    if form.validate_on_submit():
        submission.score = form.score.data
        submission.feedback = form.feedback.data
        submission.graded_at = datetime.utcnow()
        submission.graded_by = current_user.id
        
        db.session.commit()
        flash('Submission graded successfully!', 'success')
        return redirect(url_for('teacher.view_submissions', assignment_id=submission.assignment_id))
    
    # Pre-populate form if already graded
    if submission.is_graded():
        form.score.data = submission.score
        form.feedback.data = submission.feedback
    
    return render_template('teacher/grade_submission.html', submission=submission, form=form)

# Student routes
@student_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get student's enrolled classes
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    classes = [e.class_obj for e in enrollments]
    
    # Get upcoming assignments
    class_ids = [c.id for c in classes]
    upcoming_assignments = Assignment.query.filter(
        Assignment.class_id.in_(class_ids),
        Assignment.due_date > datetime.utcnow()
    ).order_by(Assignment.due_date.asc()).limit(5).all()
    
    # Get recent submissions
    recent_submissions = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html', 
                         classes=classes, 
                         upcoming_assignments=upcoming_assignments,
                         recent_submissions=recent_submissions)

@student_bp.route('/assignments')
@login_required
def assignments():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get assignments from enrolled classes
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    class_ids = [e.class_id for e in enrollments]
    
    assignments = Assignment.query.filter(Assignment.class_id.in_(class_ids)).order_by(Assignment.due_date.desc()).all()
    
    # Get submission status for each assignment
    submissions = {s.assignment_id: s for s in Submission.query.filter_by(student_id=current_user.id).all()}
    
    return render_template('student/assignments.html', assignments=assignments, submissions=submissions)

@student_bp.route('/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is enrolled in the class
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, class_id=assignment.class_id).first()
    if not enrollment:
        flash('You are not enrolled in this class.', 'danger')
        return redirect(url_for('student.assignments'))
    
    # Check if already submitted
    existing_submission = Submission.query.filter_by(assignment_id=assignment_id, student_id=current_user.id).first()
    
    form = SubmissionForm()
    if form.validate_on_submit():
        if existing_submission:
            # Update existing submission
            submission = existing_submission
            submission.submission_text = form.submission_text.data
            submission.submitted_at = datetime.utcnow()
            # Reset grading if resubmitted
            submission.score = None
            submission.feedback = None
            submission.graded_at = None
            submission.graded_by = None
        else:
            # Create new submission
            submission = Submission(
                assignment_id=assignment_id,
                student_id=current_user.id,
                submission_text=form.submission_text.data
            )
            db.session.add(submission)
        
        # Handle file upload
        if form.file.data:
            file_path = save_uploaded_file(form.file.data)
            if file_path:
                submission.file_path = file_path
        
        db.session.commit()
        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('student.assignments'))
    
    # Pre-populate form if already submitted
    if existing_submission:
        form.submission_text.data = existing_submission.submission_text
    
    return render_template('student/submit_assignment.html', assignment=assignment, form=form, submission=existing_submission)

@student_bp.route('/performance')
@login_required
def performance():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all graded submissions
    graded_submissions = Submission.query.filter(
        Submission.student_id == current_user.id,
        Submission.score.isnot(None)
    ).order_by(Submission.graded_at.desc()).all()
    
    return render_template('student/performance.html', submissions=graded_submissions)

# File download route
@main_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.', 'danger')
        return redirect(url_for('main.index'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    from sqlalchemy import func
    # Stat cards
    total_users = User.query.count()
    total_courses = Class.query.count()
    total_assignments = Assignment.query.count()
    # User role distribution
    role_counts = dict(db.session.query(User.role, func.count()).group_by(User.role).all())
    # Recent registrations (last 6 months)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    months = []
    registrations = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=now.day-1)).replace(month=(now.month-i-1)%12+1, year=now.year-((now.month-i-1)//12))
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        count = User.query.filter(User.created_at >= month_start, User.created_at < month_end).count()
        months.append(month_start.strftime('%b %Y'))
        registrations.append(count)
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_courses=total_courses,
        total_assignments=total_assignments,
        role_counts=role_counts,
        months=months,
        registrations=registrations
    )

@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    # Placeholder: will use a form in the template
    return render_template('admin/add_user.html')

@admin_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    # Placeholder: will use a form in the template
    return render_template('admin/edit_user.html', user_id=user_id)

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete another admin.', 'danger')
        return redirect(url_for('admin.admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/courses')
@admin_required
def admin_courses():
    courses = Class.query.all()
    teachers = {u.id: u for u in User.query.filter_by(role='teacher').all()}
    return render_template('admin/courses.html', courses=courses, teachers=teachers)

@admin_bp.route('/admin/courses/add', methods=['GET', 'POST'])
@admin_required
def admin_add_course():
    form = AdminClassForm()
    teachers = User.query.filter_by(role='teacher').all()
    form.teacher_id.choices = [(t.id, t.name) for t in teachers]
    if form.validate_on_submit():
        new_class = Class(
            name=form.name.data,
            description=form.description.data,
            teacher_id=form.teacher_id.data
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin.admin_courses'))
    return render_template('admin/add_course.html', form=form)

@admin_bp.route('/admin/courses/<int:class_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_course(class_id):
    class_obj = Class.query.get_or_404(class_id)
    form = AdminClassForm(obj=class_obj)
    teachers = User.query.filter_by(role='teacher').all()
    form.teacher_id.choices = [(t.id, t.name) for t in teachers]
    if request.method == 'GET':
        form.teacher_id.data = class_obj.teacher_id
    if form.validate_on_submit():
        class_obj.name = form.name.data
        class_obj.description = form.description.data
        class_obj.teacher_id = form.teacher_id.data
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.admin_courses'))
    return render_template('admin/edit_course.html', form=form, class_obj=class_obj)

@admin_bp.route('/admin/courses/<int:class_id>/delete', methods=['POST'])
@admin_required
def admin_delete_course(class_id):
    class_obj = Class.query.get_or_404(class_id)
    db.session.delete(class_obj)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin.admin_courses'))
