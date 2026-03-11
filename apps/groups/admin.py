from django.contrib import admin
from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ['name', 'course', 'student_count', 'created_at']
    list_filter   = ['course']
    search_fields = ['name']

    def get_queryset(self, request):
        """O'qituvchilar faqat o'z kurslaridagi guruhlarni ko'rsin"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(course__teacher=request.user)
        return qs

    def has_add_permission(self, request):
        """Faqat o'qituvchilar guruh qo'sha olsin"""
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """O'qituvchilar faqat o'z kurslaridagi guruhlarni o'chira olsin"""
        if not request.user.is_superuser and obj:
            return obj.course.teacher == request.user
        return request.user.is_superuser
