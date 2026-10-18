"""School structure: academic years, classes, subjects, grading and settings."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

DEPARTMENTS = [
    "Mathematics",
    "Languages",
    "Natural Science",
    "Social Science",
    "ICT",
    "Physical Education",
]

GRADE_CHOICES = [(g, f"Grade {g}") for g in range(7, 13)]
SECTION_CHOICES = [("A", "Section A"), ("B", "Section B")]


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2025/26")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)


class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
    name = models.CharField(max_length=60, help_text="e.g. Semester I")
    order = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-academic_year__name", "order"]
        unique_together = [("academic_year", "name")]

    def __str__(self):
        return f"{self.academic_year.name} · {self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            Semester.objects.exclude(pk=self.pk).update(is_current=False)


class GradingBand(models.Model):
    """One row of the configurable grading scale (A+ … F)."""

    letter = models.CharField(max_length=4)
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    point = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0"))
    remark = models.CharField(max_length=120, blank=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Highest band first.")

    class Meta:
        ordering = ["-min_score"]
        unique_together = [("letter", "min_score")]

    def __str__(self):
        return f"{self.letter} (≥ {self.min_score})"


class AssessmentComponent(models.Model):
    """Configurable assessment weighting, e.g. assignment / quiz / midterm / final."""

    key = models.SlugField(max_length=32, unique=True)
    label = models.CharField(max_length=60)
    max_score = models.DecimalField(max_digits=6, decimal_places=2)
    weight_percent = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Share of the final grade, all weights should total 100."
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.label} (/{self.max_score})"

    @classmethod
    def total_max_score(cls):
        return cls.objects.aggregate(models.Sum("max_score"))["max_score__sum"] or Decimal("0")

    @classmethod
    def weights_total(cls):
        return cls.objects.aggregate(models.Sum("weight_percent"))["weight_percent__sum"] or Decimal("0")


class SchoolSettings(models.Model):
    """Singleton row holding school-wide configuration."""

    school_name = models.CharField(max_length=150, default="Bariso Dukale Secondary School")
    motto = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    website = models.CharField(max_length=120, blank=True)
    pass_mark = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("50"))
    compact_tables = models.BooleanField(default=False)
    show_school_rank = models.BooleanField(default=True, help_text="Allow students to see school-wide rank.")
    rank_tie_policy = models.CharField(
        max_length=16,
        choices=[("dense", "Dense (1,2,2,3)"), ("competition", "Competition (1,2,2,4)")],
        default="dense",
    )
    current_academic_year = models.ForeignKey(
        AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    current_semester = models.ForeignKey(
        Semester, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "School settings"
        verbose_name_plural = "School settings"

    def __str__(self):
        return self.school_name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class SchoolClass(models.Model):
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    section = models.CharField(max_length=4, choices=SECTION_CHOICES)
    room = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveSmallIntegerField(default=45)
    academic_year = models.ForeignKey(
        AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="classes"
    )
    homeroom_teacher = models.ForeignKey(
        "teachers.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="homeroom_classes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["grade", "section"]
        unique_together = [("grade", "section", "academic_year")]

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"Grade {self.grade} — {self.section}"

    @property
    def student_count(self):
        return self.students.filter(status="Active").count()


class Subject(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=80)
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    credit = models.PositiveSmallIntegerField(default=3)
    department = models.CharField(max_length=60, choices=[(d, d) for d in DEPARTMENTS])
    teacher = models.ForeignKey(
        "teachers.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="subjects"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["grade", "name"]
        unique_together = [("code", "grade")]

    def __str__(self):
        return f"{self.name} · Grade {self.grade}"

    @property
    def full_code(self):
        return f"{self.code}-{self.grade}"


class TeachingAssignment(models.Model):
    """Explicit teacher ↔ subject ↔ class ↔ year assignment."""

    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="teaching_assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="teaching_assignments")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="teaching_assignments")
    academic_year = models.ForeignKey(
        AcademicYear, null=True, blank=True, on_delete=models.SET_NULL, related_name="assignments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["school_class__grade", "subject__name"]
        unique_together = [("teacher", "subject", "school_class", "academic_year")]

    def __str__(self):
        return f"{self.teacher.name} → {self.subject.name} ({self.school_class.name})"

    def clean(self):
        if self.subject and self.school_class and self.subject.grade != self.school_class.grade:
            raise ValidationError("A subject can only be assigned to a class of the same grade.")


# ---------------------------------------------------------------------------
# Grading helpers (configurable scale, never hardcoded)
# ---------------------------------------------------------------------------
def grade_band_for(total):
    """Return the grading band matching a total score."""
    total = Decimal(str(total or 0))
    return GradingBand.objects.filter(min_score__lte=total).order_by("-min_score").first()


def grade_letter(total):
    band = grade_band_for(total)
    return band.letter if band else "—"


def grade_point(total):
    band = grade_band_for(total)
    return band.point if band else Decimal("0")


def grade_remark(total):
    band = grade_band_for(total)
    return band.remark if band else ""


def weights_are_consistent():
    """Assessment weights must total 100 before final grades are trusted."""
    total = AssessmentComponent.weights_total()
    return total == Decimal("100")
