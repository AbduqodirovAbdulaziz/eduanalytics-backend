from django.db import models
from apps.courses.models import Course


class Group(models.Model):
    """Guruh modeli"""
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    name       = models.CharField(max_length=100, verbose_name="Guruh nomi")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'groups'
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        ordering = ['name']
        indexes = [
            models.Index(fields=['course', 'name']),
        ]

    def __str__(self):
        return f"{self.name} — {self.course.name}"

    @property
    def student_count(self):
        return self.students.count()
