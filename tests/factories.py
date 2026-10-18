"""Shared test fixtures.

``build_school`` creates a small, self-contained school (one admin, one
teacher, one class, one subject and a handful of students) so each test can
focus on the behaviour it is verifying rather than on setup.
"""
from decimal import Decimal
from types import SimpleNamespace

from apps.academics.models import (
    AcademicYear,
    AssessmentComponent,
    GradingBand,
    SchoolClass,
    SchoolSettings,
    Semester,
    Subject,
    TeachingAssignment,
)
from apps.accounts.models import User
from apps.results.forms import ensure_subject_marks
from apps.results.models import MarkEntry, ResultSheet, SubjectMark
from apps.students.models import Student
from apps.teachers.models import Teacher

# letter, min_score, point, remark
GRADING_SCALE = [
    ("A+", "90", "4.00", "Excellent"),
    ("A", "85", "4.00", "Very good"),
    ("B+", "80", "3.50", "Good"),
    ("B", "70", "3.00", "Satisfactory"),
    ("C+", "60", "2.50", "Fair"),
    ("C", "50", "2.00", "Pass"),
    ("D", "40", "1.00", "Weak"),
    ("F", "0", "0.00", "Fail"),
]

# key, label, max_score, weight_percent (weights total 100)
COMPONENTS = [
    ("assignment", "Assignment", "10", "10"),
    ("quiz", "Quiz", "10", "10"),
    ("midterm", "Midterm", "20", "20"),
    ("final", "Final exam", "60", "60"),
]


def make_user(username, password, **extra):
    extra.setdefault("role", User.Role.STUDENT)
    return User.objects.create_user(username, password, **extra)


def make_admin(username="admin", password="admin123", **extra):
    extra.setdefault("full_name", "Aman Registrar")
    extra.setdefault("role", User.Role.ADMIN)
    extra.setdefault("is_staff", True)
    extra.setdefault("is_superuser", True)
    return make_user(username, password, **extra)


def link_student_user(student, username="student", password="student123"):
    """Attach a login account to an existing student record."""
    user = make_user(
        username,
        password,
        role=User.Role.STUDENT,
        full_name=student.full_name,
    )
    student.user = user
    student.save(update_fields=["user"])
    return user


def build_school(student_count=3):
    """Create the baseline dataset used across the test-suite."""
    year = AcademicYear.objects.create(name="2025/26", is_current=True)
    semester = Semester.objects.create(
        academic_year=year, name="Semester I", order=1, is_current=True
    )

    for order, (letter, min_score, point, remark) in enumerate(GRADING_SCALE):
        GradingBand.objects.create(
            letter=letter,
            min_score=Decimal(min_score),
            point=Decimal(point),
            remark=remark,
            order=order,
        )

    components = [
        AssessmentComponent.objects.create(
            key=key,
            label=label,
            max_score=Decimal(max_score),
            weight_percent=Decimal(weight),
            order=index,
        )
        for index, (key, label, max_score, weight) in enumerate(COMPONENTS)
    ]

    conf = SchoolSettings.load()
    conf.current_academic_year = year
    conf.current_semester = semester
    conf.save()

    admin = make_admin()
    teacher_user = make_user(
        "teacher", "teacher123", role=User.Role.TEACHER, full_name="Tsehay Bekele"
    )
    teacher = Teacher.objects.create(
        teacher_id="TCH-01",
        name="Tsehay Bekele",
        gender="F",
        department="Mathematics",
        user=teacher_user,
    )

    klass = SchoolClass.objects.create(
        grade=9, section="A", room="R9A", academic_year=year, homeroom_teacher=teacher
    )
    subject = Subject.objects.create(
        code="MATH", name="Mathematics", grade=9, credit=4, department="Mathematics", teacher=teacher
    )
    TeachingAssignment.objects.create(
        teacher=teacher, subject=subject, school_class=klass, academic_year=year
    )

    students = [
        Student.objects.create(
            student_id=f"UNS-09A-{index:02d}",
            first_name=f"Student{index}",
            last_name="Test",
            gender="M" if index % 2 else "F",
            grade=9,
            section="A",
            school_class=klass,
            status="Active",
        )
        for index in range(1, student_count + 1)
    ]

    return SimpleNamespace(
        year=year,
        semester=semester,
        components=components,
        settings=conf,
        admin=admin,
        teacher=teacher,
        teacher_user=teacher_user,
        klass=klass,
        subject=subject,
        students=students,
    )


def make_sheet(fx, *, status=ResultSheet.Status.DRAFT, subject=None, teacher=None):
    """Create a result sheet with an empty SubjectMark row per active student."""
    sheet = ResultSheet.objects.create(
        academic_year=fx.year,
        semester=fx.semester,
        school_class=fx.klass,
        subject=subject or fx.subject,
        teacher=teacher or fx.teacher,
        exam_type="Final",
        status=status,
    )
    ensure_subject_marks(sheet)
    return sheet


def set_percentage(subject_mark, components, percentage):
    """Set every component so the subject mark totals ``percentage`` (0-100)."""
    for component in components:
        score = (Decimal(str(percentage)) * component.max_score / Decimal("100")).quantize(
            Decimal("0.01")
        )
        MarkEntry.objects.update_or_create(
            subject_mark=subject_mark, component=component, defaults={"score": score}
        )


def mark_sheet(sheet, fx, scores):
    """Apply ``{student: percentage}`` to a sheet's subject marks."""
    for student, percentage in scores.items():
        subject_mark = SubjectMark.objects.get(result_sheet=sheet, student=student)
        set_percentage(subject_mark, fx.components, percentage)
    return sheet
