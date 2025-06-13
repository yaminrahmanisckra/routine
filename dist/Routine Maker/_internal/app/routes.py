from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from app import app, db
from app.forms import AcademicYearForm, TeacherForm, CourseForm, RoomForm, AssignCoursesForm
from app.models import AcademicYear, Teacher, Course, Room, TeacherCourse, RoutineSlot
from datetime import time
import json
import random
from io import BytesIO
from docx import Document
from docx.shared import Pt
import sys
from fpdf import FPDF
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
import os

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/academic_year', methods=['GET', 'POST'])
def academic_year():
    form = AcademicYearForm()
    if form.validate_on_submit():
        ay = AcademicYear(year=form.year.data, session=form.session.data)
        db.session.add(ay)
        db.session.commit()
        flash('Academic Year added!')
        return redirect(url_for('academic_year'))
    years = AcademicYear.query.all()
    return render_template('academic_year.html', form=form, years=years)

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    form = TeacherForm()
    if form.validate_on_submit():
        t = Teacher(name=form.name.data, callsign=form.callsign.data)
        db.session.add(t)
        db.session.commit()
        flash('Teacher added!')
        return redirect(url_for('teacher'))
    teachers = Teacher.query.all()
    return render_template('teacher.html', form=form, teachers=teachers)

@app.route('/teacher/edit/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    form = TeacherForm(obj=teacher)
    if form.validate_on_submit():
        teacher.name = form.name.data
        teacher.callsign = form.callsign.data
        db.session.commit()
        flash('Teacher updated!')
        return redirect(url_for('teacher'))
    teachers = Teacher.query.all()
    return render_template('teacher.html', form=form, teachers=teachers, edit_id=teacher_id)

@app.route('/teacher/delete/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted!')
    return redirect(url_for('teacher'))

@app.route('/course', methods=['GET', 'POST'])
def course():
    form = CourseForm()
    if form.validate_on_submit():
        c = Course(name=form.name.data, code=form.code.data, type=form.type.data, year=form.year.data, credit=form.credit.data)
        db.session.add(c)
        db.session.commit()
        flash('Course added!')
        return redirect(url_for('course'))
    courses = Course.query.all()
    return render_template('course.html', form=form, courses=courses)

@app.route('/course/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.name = form.name.data
        course.code = form.code.data
        course.type = form.type.data
        course.year = form.year.data
        course.term = form.term.data
        course.credit = form.credit.data
        db.session.commit()
        flash('Course updated!')
        return redirect(url_for('course'))
    courses = Course.query.all()
    return render_template('course.html', form=form, courses=courses, edit_id=course_id)

@app.route('/course/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted!')
    return redirect(url_for('course'))

@app.route('/room', methods=['GET', 'POST'])
def room():
    form = RoomForm()
    if form.validate_on_submit():
        r = Room(name=form.name.data)
        db.session.add(r)
        db.session.commit()
        flash('Room added!')
        return redirect(url_for('room'))
    rooms = Room.query.all()
    return render_template('room.html', form=form, rooms=rooms)

@app.route('/room/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    if form.validate_on_submit():
        room.name = form.name.data
        db.session.commit()
        flash('Room updated!')
        return redirect(url_for('room'))
    rooms = Room.query.all()
    return render_template('room.html', form=form, rooms=rooms, edit_id=room_id)

@app.route('/room/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted!')
    return redirect(url_for('room'))

@app.route('/assign_course', methods=['GET', 'POST'])
def assign_course():
    form = AssignCoursesForm()
    form.teacher.choices = [(t.id, f"{t.name} ({t.callsign})") for t in Teacher.query.all()]
    # Filter courses: exclude those with Full assigned, or both Part A and Part B assigned
    assigned_part_a = set(tc.course_id for tc in TeacherCourse.query.filter_by(part='Part A').all())
    assigned_part_b = set(tc.course_id for tc in TeacherCourse.query.filter_by(part='Part B').all())
    assigned_full = set(tc.course_id for tc in TeacherCourse.query.filter_by(part='Full').all())
    assigned_both_parts = assigned_part_a & assigned_part_b
    exclude_courses = assigned_full | assigned_both_parts
    form.courses.choices = [
        (c.id, f"{c.name} ({c.code})")
        for c in Course.query.all()
        if c.id not in exclude_courses
    ]
    if form.validate_on_submit():
        teacher_id = form.teacher.data
        course_id = form.courses.data
        part = form.part.data
        # Prevent duplicate Part A/B for the same course
        if part in ['Part A', 'Part B']:
            existing = TeacherCourse.query.filter_by(course_id=course_id, part=part).first()
            if existing:
                flash(f"{part} already assigned for this course!", "danger")
                return redirect(url_for('assign_course'))
        # Prevent same teacher getting same course+part multiple times
        TeacherCourse.query.filter_by(teacher_id=teacher_id, course_id=course_id, part=part).delete()
        tc = TeacherCourse(teacher_id=teacher_id, course_id=course_id, part=part)
        db.session.add(tc)
        db.session.commit()
        flash('Course assigned to teacher!')
        return redirect(url_for('assign_course') )
    assignments = []
    for t in Teacher.query.all():
        assigned = []
        for tc in t.courses:
            if tc.course is None:
                continue  # skip if course is missing
            # Calculate credit based on part
            if tc.part == 'Full':
                credit = tc.course.credit
            else:
                credit = tc.course.credit / 2
            assigned.append({'course': tc.course, 'part': tc.part, 'credit': credit, 'id': tc.id})
        assignments.append({'teacher': t, 'courses': assigned})
    years = AcademicYear.query.all()
    return render_template('assign_course.html', form=form, assignments=assignments, years=years)

@app.route('/generate_routine')
def generate_routine():
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    slots = [
        (time(9,10), time(10,0)),   # 0
        (time(10,10), time(11,0)),  # 1
        (time(11,10), time(12,0)),  # 2
        (time(12,10), time(13,0)),  # 3
        (time(13,0), time(13,50)),  # 4 (Lunch Break)
        (time(14,0), time(14,50)),  # 5
        (time(15,0), time(15,50)),  # 6
        (time(16,0), time(16,50)),  # 7
    ]
    rooms = Room.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()

    # Empty routine template
    routine = {day: [None for _ in range(len(slots))] for day in days}

    # Prepare data for frontend
    teacher_list = [{'id': t.id, 'name': t.name, 'callsign': t.callsign} for t in teachers]
    room_list = [{'id': r.id, 'name': r.name} for r in rooms]
    courses_by_id = {c.id: {'id': c.id, 'code': c.code, 'name': c.name} for c in courses}
    teachers_by_id = {t.id: {'id': t.id, 'callsign': t.callsign, 'name': t.name} for t in teachers}

    return render_template(
        'routine.html',
        routine=routine,
        slots=slots,
        days=days,
        teachers_json=teacher_list,
        rooms_json=room_list,
        rooms=rooms,
        courses_by_id=courses_by_id,
        teachers_by_id=teachers_by_id
    )

@app.route('/api/get_routine')
def api_get_routine():
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    slots = 8  # Including Lunch Break
    routine = {day: [None for _ in range(slots)] for day in days}
    return jsonify(routine)

@app.route('/api/update_slot', methods=['POST'])
def api_update_slot():
    data = request.get_json()
    day = data.get('day')
    slot = data.get('slot')
    room = data.get('room')
    course_id = data.get('courseId')
    teacher_id = data.get('teacherId')
    
    # Update or create routine slot
    slot = RoutineSlot.query.filter_by(
        day=day,
        slot_index=slot,
        room_id=room
    ).first()
    
    if not slot:
        slot = RoutineSlot(
            day=day,
            slot_index=slot,
            room_id=room
        )
        db.session.add(slot)
    
    slot.course_id = course_id
    slot.teacher_id = teacher_id
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/swap_slot', methods=['POST'])
def api_swap_slot():
    return jsonify({'success': True})

@app.route('/teacher_course/edit/<int:tc_id>', methods=['GET', 'POST'])
def edit_teacher_course(tc_id):
    tc = TeacherCourse.query.get_or_404(tc_id)
    form = AssignCoursesForm(obj=tc)
    # Set choices for all SelectFields to avoid WTForms error
    form.teacher.choices = [(t.id, f"{t.name} ({t.callsign})") for t in Teacher.query.all()]
    # Filter courses as in assign_course, but always include the current course
    assigned_full = set(tc2.course_id for tc2 in TeacherCourse.query.filter_by(part='Full').all() if tc2.id != tc.id)
    assigned_part_a = set(tc2.course_id for tc2 in TeacherCourse.query.filter_by(part='Part A').all() if tc2.id != tc.id)
    assigned_part_b = set(tc2.course_id for tc2 in TeacherCourse.query.filter_by(part='Part B').all() if tc2.id != tc.id)
    assigned_both_parts = assigned_part_a & assigned_part_b
    exclude_courses = assigned_full | assigned_both_parts
    form.courses.choices = [
        (c.id, f"{c.name} ({c.code})")
        for c in Course.query.all()
        if c.id not in exclude_courses or c.id == tc.course_id
    ]
    form.part.choices = [('Full', 'Full Course'), ('Part A', 'Part A'), ('Part B', 'Part B')]
    form.teacher.data = tc.teacher_id
    form.courses.data = tc.course_id
    form.part.data = tc.part
    if form.validate_on_submit():
        tc.teacher_id = form.teacher.data
        tc.course_id = form.courses.data
        tc.part = form.part.data
        db.session.commit()
        flash('Assignment updated!')
        return redirect(url_for('assign_course'))
    return render_template('edit_teacher_course.html', form=form, tc=tc)

@app.route('/teacher_course/delete/<int:tc_id>', methods=['POST'])
def delete_teacher_course(tc_id):
    tc = TeacherCourse.query.get_or_404(tc_id)
    db.session.delete(tc)
    db.session.commit()
    flash('Assignment deleted!')
    return redirect(url_for('assign_course'))

@app.route('/api/teacher_courses/<int:teacher_id>')
def api_teacher_courses(teacher_id):
    # Get all courses assigned to this teacher
    teacher_courses = TeacherCourse.query.filter_by(teacher_id=teacher_id).all()
    
    # Get course details and count how many times each course is used in routine
    courses = []
    for tc in teacher_courses:
        course = Course.query.get(tc.course_id)
        if course:
            # Count how many times this course is used in routine
            routine_count = RoutineSlot.query.filter_by(
                course_id=course.id,
                teacher_id=teacher_id
            ).count()
            # For 3-credit theory courses, only treat as shared if exactly two teachers and both FULL or PART A/B
            if course.credit == 3 and course.type.strip().lower() == 'theory':
                assigned_teachers = TeacherCourse.query.filter_by(course_id=course.id).all()
                if len(assigned_teachers) == 2:
                    parts = set(tc2.part.strip().lower() for tc2 in assigned_teachers)
                    if parts == {'part a', 'part b'}:
                        # Part A and Part B for the requested teacher only
                        for tc2 in assigned_teachers:
                            if tc2.part.strip().lower() == 'part a' and tc2.teacher_id == teacher_id:
                                courses.append({
                                    'id': course.id,
                                    'code': course.code,
                                    'name': course.name,
                                    'type': course.type,
                                    'class_count': 1,
                                    'shared_callsign': None,
                                    'part': 'Part A',
                                    'teacher_id': tc2.teacher_id
                                })
                            if tc2.part.strip().lower() == 'part b' and tc2.teacher_id == teacher_id:
                                courses.append({
                                    'id': course.id,
                                    'code': course.code,
                                    'name': course.name,
                                    'type': course.type,
                                    'class_count': 1,
                                    'shared_callsign': None,
                                    'part': 'Part B',
                                    'teacher_id': tc2.teacher_id
                                })
                        # Shared 1 class: only for the first assigned teacher
                        if assigned_teachers[0].teacher_id == teacher_id:
                            shared_callsign = '/'.join(sorted([t.teacher.callsign for t in assigned_teachers if t.teacher]))
                            courses.append({
                                'id': course.id,
                                'code': course.code,
                                'name': course.name,
                                'type': course.type,
                                'class_count': 1,
                                'shared_callsign': shared_callsign,
                                'part': 'Shared',
                                'teacher_id': assigned_teachers[0].teacher_id
                            })
                        continue
            # Sessional: if two teachers, split class count equally
            if course.type.strip().lower() == 'sessional':
                assigned_teachers = TeacherCourse.query.filter_by(course_id=course.id).all()
                if len(assigned_teachers) == 2:
                    class_count = int(round((float(course.credit) / 2) / 0.5))
                else:
                    class_count = int(round(float(course.credit) / 0.5))
            # Theory (non-shared): if two teachers, split class count equally
            elif course.type.strip().lower() == 'theory':
                assigned_teachers = TeacherCourse.query.filter_by(course_id=course.id).all()
                if len(assigned_teachers) == 2:
                    class_count = int(round(float(course.credit) / 2))
                else:
                    class_count = int(round(float(course.credit)))
            else:
                class_count = int(round(float(course.credit)))
            courses.append({
                'id': course.id,
                'code': course.code,
                'name': course.name,
                'type': course.type,
                'class_count': class_count,
                'shared_callsign': None,
                'part': tc.part
            })
    return jsonify(courses)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
    routine = data.get('routine', {})
    days = data.get('days', [])
    rooms = data.get('rooms', [])
    slots = data.get('slots', [])
    title = data.get('title', '')
    date = data.get('date', '')

    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    cell_style = ParagraphStyle(
        name='TableCell',
        fontSize=9,
        alignment=1,  # CENTER
        leading=10,
        wordWrap='CJK',
        spaceAfter=0,
        spaceBefore=0,
    )
    header_style = ParagraphStyle(
        name='HeaderCell',
        fontSize=10,
        alignment=1,  # CENTER
        leading=12,
        wordWrap='CJK',
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica-Bold',
    )

    def make_cell(val):
        return Paragraph(str(val) if val else '', cell_style)
    def make_header(val):
        return Paragraph(str(val) if val else '', header_style)

    table_data = [[make_header('Day'), make_header('Room')] + [make_header(s) for s in slots]]

    row_spans = []
    row_idx = 1
    for day in days:
        for r, room in enumerate(rooms):
            row = []
            if r == 0:
                row.append(make_cell(day))
            else:
                row.append(make_cell(''))
            room_name = room['name'] if isinstance(room, dict) and 'name' in room else str(room)
            room_id = str(room['id']) if isinstance(room, dict) and 'id' in room else str(room)
            row.append(make_cell(room_name))
            for s in range(len(slots)):
                if s == 4 and r == 0:
                    row.append(make_cell('Lunch\nBreak'))
                else:
                    val = routine.get(day, {}).get(room_id, ['']*len(slots))[s]
                    row.append(make_cell(val))
            table_data.append(row)
        row_spans.append(row_idx + len(rooms) - 1)
        row_idx += len(rooms)

    style = [
        ('LINEABOVE', (0,0), (-1,0), 3, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 3, colors.black),
        ('LINEBEFORE', (0,0), (0,-1), 3, colors.black),
        ('LINEAFTER', (-1,0), (-1,-1), 3, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.7, colors.black),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]

    for i, day in enumerate(days):
        start = 1 + i * len(rooms)
        end = start + len(rooms) - 1
        style.append(('SPAN', (0, start), (0, end)))
        style.append(('SPAN', (4+2, start), (4+2, end)))
        style.append(('ALIGN', (4+2, start), (4+2, end), 'CENTER'))
    for idx in row_spans:
        style.append(('LINEBELOW', (0, idx), (-1, idx), 3, colors.black))

    col_widths = [28*mm, 28*mm] + [18*mm]*8
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=8*mm, rightMargin=8*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubCenter', alignment=1, fontSize=12, spaceAfter=4))
    elements.append(Paragraph("Khulna University", styles['Center']))
    elements.append(Paragraph("Law Discipline", styles['Center']))
    elements.append(Paragraph(f"Class Routine of {title}", styles['SubCenter']))
    elements.append(Paragraph(f"Effective from {date}", styles['SubCenter']))
    elements.append(Spacer(1, 8))

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='routine.pdf', mimetype='application/pdf')

@app.route('/download_teacher_pdf/<int:teacher_id>')
def download_teacher_pdf(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    assignments = TeacherCourse.query.filter_by(teacher_id=teacher_id).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubHeader', alignment=0, fontSize=12, spaceAfter=4, fontName='Helvetica-Bold'))
    elements.append(Paragraph(f"Course Assignments for {teacher.name} ({teacher.callsign})", styles['Center']))
    elements.append(Spacer(1, 8))
    table_data = [["Course Name", "Code", "Part", "Credit"]]
    for tc in assignments:
        if not tc.course:
            continue
        table_data.append([
            tc.course.name,
            tc.course.code,
            tc.part,
            str(tc.course.credit)
        ])
    col_widths = [60*mm, 30*mm, 25*mm, 20*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'{teacher.callsign}_courses.pdf', mimetype='application/pdf')

@app.route('/download_all_teachers_pdf')
def download_all_teachers_pdf():
    teachers = Teacher.query.order_by(Teacher.name).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubHeader', alignment=0, fontSize=12, spaceAfter=4, fontName='Helvetica-Bold'))
    cell_style = ParagraphStyle('Cell', fontSize=9, alignment=TA_CENTER, leading=11, wordWrap='CJK')
    elements.append(Paragraph("All Teachers' Course Assignments", styles['Center']))
    elements.append(Spacer(1, 8))
    for teacher in teachers:
        assignments = TeacherCourse.query.filter_by(teacher_id=teacher.id).all()
        elements.append(Paragraph(f"{teacher.name} ({teacher.callsign})", styles['SubHeader']))
        table_data = [[Paragraph("Course Name", cell_style), Paragraph("Code", cell_style), Paragraph("Part", cell_style), Paragraph("Credit", cell_style)]]
        for tc in assignments:
            if not tc.course:
                continue
            table_data.append([
                Paragraph(tc.course.name, cell_style),
                Paragraph(tc.course.code, cell_style),
                Paragraph(tc.part, cell_style),
                Paragraph(str(tc.course.credit), cell_style)
            ])
        col_widths = [55*mm, 28*mm, 22*mm, 16*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='all_teachers_courses.pdf', mimetype='application/pdf')

@app.route('/download_year_term_pdf')
def download_year_term_pdf():
    year = request.args.get('year')
    term = request.args.get('term')
    teachers = Teacher.query.order_by(Teacher.name).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubHeader', alignment=0, fontSize=12, spaceAfter=4, fontName='Helvetica-Bold'))
    cell_style = ParagraphStyle('Cell', fontSize=9, alignment=TA_CENTER, leading=11, wordWrap='CJK')
    elements.append(Paragraph(f"Course Assignments for Year {year}, Term {term}", styles['Center']))
    elements.append(Spacer(1, 8))
    for teacher in teachers:
        assignments = [tc for tc in TeacherCourse.query.filter_by(teacher_id=teacher.id).all() if tc.course and str(tc.course.year) == str(year) and str(getattr(tc.course, 'term', '')) == str(term)]
        if not assignments:
            continue
        elements.append(Paragraph(f"{teacher.name} ({teacher.callsign})", styles['SubHeader']))
        table_data = [[Paragraph("Course Name", cell_style), Paragraph("Code", cell_style), Paragraph("Part", cell_style), Paragraph("Credit", cell_style)]]
        for tc in assignments:
            table_data.append([
                Paragraph(tc.course.name, cell_style),
                Paragraph(tc.course.code, cell_style),
                Paragraph(tc.part, cell_style),
                Paragraph(str(tc.course.credit), cell_style)
            ])
        col_widths = [55*mm, 28*mm, 22*mm, 16*mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'year_{year}_term_{term}_courses.pdf', mimetype='application/pdf')

@app.route('/download_all_courses_pdf')
def download_all_courses_pdf():
    courses = Course.query.order_by(Course.year, Course.term, Course.code).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    cell_style = ParagraphStyle('Cell', fontSize=9, alignment=TA_CENTER, leading=11, wordWrap='CJK')
    elements.append(Paragraph("All Courses (Year/Term-wise)", styles['Center']))
    elements.append(Spacer(1, 8))
    table_data = [[Paragraph("Year", cell_style), Paragraph("Term", cell_style), Paragraph("Course Code", cell_style), Paragraph("Course Name", cell_style), Paragraph("Credit", cell_style), Paragraph("Assigned Teacher(s)", cell_style)]]
    for c in courses:
        tcs = c.teachers
        callsigns = ', '.join(sorted(set(tc.teacher.callsign for tc in tcs if tc.teacher))) if tcs else '-'
        table_data.append([
            Paragraph(str(getattr(c, 'year', '')), cell_style),
            Paragraph(str(getattr(c, 'term', '')), cell_style),
            Paragraph(c.code, cell_style),
            Paragraph(c.name, cell_style),
            Paragraph(str(c.credit), cell_style),
            Paragraph(callsigns, cell_style)
        ])
    col_widths = [16*mm, 13*mm, 26*mm, 54*mm, 14*mm, 38*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='all_courses_year_term.pdf', mimetype='application/pdf')

ROUTINE_STATE_FILE = 'routine_state.json'

@app.route('/api/save_routine_state', methods=['POST'])
def api_save_routine_state():
    data = request.get_json()
    with open(ROUTINE_STATE_FILE, 'w', encoding='utf-8') as f:
        import json
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {'success': True}

@app.route('/api/load_routine_state', methods=['GET'])
def api_load_routine_state():
    import json
    if os.path.exists(ROUTINE_STATE_FILE):
        with open(ROUTINE_STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    else:
        return {}
