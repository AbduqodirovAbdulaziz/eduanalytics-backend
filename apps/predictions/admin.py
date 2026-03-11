from django.contrib import admin
from django.utils.html import format_html
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display    = [
        'student_name', 'level_badge', 'predicted_score_bar',
        'risk_badge', 'short_recommendation', 'predicted_at'
    ]
    list_filter     = ['level']
    search_fields   = ['student__name']
    readonly_fields = [
        'student', 'attendance', 'homework', 'quiz', 'exam',
        'predicted_score', 'level', 'risk_percentage',
        'full_recommendation', 'predicted_at'
    ]
    list_per_page   = 20

    fieldsets = (
        ("👤 O'quvchi", {
            'fields': ('student',)
        }),
        ('📥 Kirish ko\'rsatkichlari', {
            'fields': (('attendance', 'homework'), ('quiz', 'exam')),
        }),
        ('📤 Prognoz natijasi', {
            'fields': ('predicted_score', 'level', 'risk_percentage'),
        }),
        ('💡 Tavsiya (Recommendation)', {
            'fields': ('full_recommendation',),
            'classes': ('wide',),
        }),
        ('📅 Sana', {
            'fields': ('predicted_at',),
        }),
    )

    @admin.display(description="O'quvchi", ordering='student__name')
    def student_name(self, obj):
        return format_html(
            '<b style="font-size:13px">{}</b><br>'
            '<small style="color:#888">{}</small>',
            obj.student.name,
            obj.student.group.name,
        )

    @admin.display(description='Daraja', ordering='level')
    def level_badge(self, obj):
        colors = {
            'High Performance':   ('#d4edda', '#155724', '🟢'),
            'Medium Performance': ('#fff3cd', '#856404', '🟡'),
            'Low Performance':    ('#f8d7da', '#721c24', '🔴'),
        }
        labels = {
            'High Performance':   'Yuqori',
            'Medium Performance': "O'rta",
            'Low Performance':    'Past',
        }
        bg, color, icon = colors.get(obj.level, ('#eee', '#333', '⚪'))
        label = labels.get(obj.level, obj.level)
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;'
            'border-radius:12px;font-weight:600;font-size:12px">'
            '{} {}</span>',
            bg, color, icon, label
        )

    @admin.display(description='Ball', ordering='predicted_score')
    def predicted_score_bar(self, obj):
        score = obj.predicted_score
        bar_color = '#28a745' if score >= 70 else ('#ffc107' if score >= 40 else '#dc3545')
        width     = int(min(score, 100))
        # ✅ float ni oldindan str ga aylantiramiz
        score_str = f'{score:.1f}'
        return format_html(
            '<div style="min-width:120px">'
            '<div style="background:#e9ecef;border-radius:4px;height:8px;margin-bottom:3px">'
            '<div style="background:{};width:{}%;height:8px;border-radius:4px"></div>'
            '</div>'
            '<span style="font-weight:700;color:{}">{}/100</span>'
            '</div>',
            bar_color, width, bar_color, score_str
        )

    @admin.display(description='Xavf %', ordering='risk_percentage')
    def risk_badge(self, obj):
        risk = obj.risk_percentage
        color = '#dc3545' if risk >= 70 else ('#fd7e14' if risk >= 40 else '#28a745')
        # ✅ float ni oldindan str ga aylantiramiz
        risk_str = f'{risk:.1f}'
        return format_html(
            '<span style="color:{};font-weight:700">{}%</span>',
            color, risk_str
        )

    @admin.display(description='Tavsiya (qisqa)')
    def short_recommendation(self, obj):
        if not obj.recommendation:
            return '—'
        first_line = obj.recommendation.strip().split('\n')[0]
        if len(first_line) > 80:
            first_line = first_line[:77] + '...'
        return format_html(
            '<span style="font-size:12px;color:#555">{}</span>',
            first_line
        )

    @admin.display(description="💡 To'liq Tavsiya (Recommendation)")
    def full_recommendation(self, obj):
        if not obj.recommendation:
            return '—'
        lines = obj.recommendation.strip().split('\n')
        parts = []
        first = True
        for line in lines:
            line = line.strip()
            if not line:
                parts.append('<br>')
                continue
            if first:
                parts.append(
                    f'<div style="font-size:15px;font-weight:700;'
                    f'margin-bottom:8px;color:#333">{line}</div>'
                )
                first = False
            elif line.startswith(('🔴', '🟡', '🎯', '⚡', '🔍', '📋', '📊', '🏆', '🏅', '✅', '🚨')):
                parts.append(
                    f'<div style="font-size:13px;font-weight:600;'
                    f'margin-top:10px;margin-bottom:4px;color:#444">{line}</div>'
                )
            elif line.startswith('⚠️'):
                parts.append(
                    f'<div style="background:#fff3cd;border-left:3px solid #ffc107;'
                    f'padding:4px 8px;margin:2px 0;border-radius:0 4px 4px 0;'
                    f'font-size:12px;color:#856404">{line}</div>'
                )
            elif line.startswith('📌'):
                parts.append(
                    f'<div style="background:#e8f4fd;border-left:3px solid #17a2b8;'
                    f'padding:4px 8px;margin:2px 0;border-radius:0 4px 4px 0;'
                    f'font-size:12px;color:#0c5460">{line}</div>'
                )
            else:
                parts.append(
                    f'<div style="padding:2px 0;font-size:12px;color:#666">{line}</div>'
                )

        inner_html = ''.join(parts)
        # ✅ mark_safe ishlatmaymiz — format_html ichida xom HTML safe qilinadi
        return format_html(
            '<div style="background:#f8f9fa;border:1px solid #dee2e6;'
            'border-radius:6px;padding:12px 16px;max-width:700px;line-height:1.6">'
            '{}</div>',
            format_html(inner_html)   # inner_html ni safe qilish
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(student__group__course__teacher=request.user)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser and obj:
            return obj.student.group.course.teacher == request.user
        return request.user.is_superuser
