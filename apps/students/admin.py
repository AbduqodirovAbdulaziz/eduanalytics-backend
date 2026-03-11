from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Score


class ScoreInline(admin.TabularInline):
    model               = Score
    extra               = 0
    fields              = ['attendance', 'homework', 'quiz', 'exam']
    verbose_name        = "Natija"
    verbose_name_plural = "Natijalar"


class PredictionInline(admin.StackedInline):
    from apps.predictions.models import Prediction
    model               = Prediction
    extra               = 0
    max_num             = 1
    can_delete          = False
    show_change_link    = True
    verbose_name        = "Prognoz va Tavsiya"
    verbose_name_plural = "Prognoz va Tavsiya"

    readonly_fields = [
        'level_badge', 'predicted_score_bar', 'risk_badge',
        'full_recommendation', 'predicted_at'
    ]
    fields = [
        'level_badge', 'predicted_score_bar', 'risk_badge',
        'full_recommendation', 'predicted_at'
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-predicted_at')

    @admin.display(description='Daraja')
    def level_badge(self, obj):
        colors = {
            'High Performance':   ('#d4edda', '#155724', '🟢'),
            'Medium Performance': ('#fff3cd', '#856404', '🟡'),
            'Low Performance':    ('#f8d7da', '#721c24', '🔴'),
        }
        labels = {
            'High Performance':   'Yuqori daraja',
            'Medium Performance': "O'rta daraja",
            'Low Performance':    'Past daraja',
        }
        bg, color, icon = colors.get(obj.level, ('#eee', '#333', '⚪'))
        label = labels.get(obj.level, obj.level)
        return format_html(
            '<span style="background:{};color:{};padding:4px 14px;'
            'border-radius:14px;font-weight:700;font-size:13px">'
            '{} {}</span>',
            bg, color, icon, label
        )

    @admin.display(description='Umumiy ball')
    def predicted_score_bar(self, obj):
        score     = obj.predicted_score
        color     = '#28a745' if score >= 70 else ('#ffc107' if score >= 40 else '#dc3545')
        width     = int(min(score, 100))
        # ✅ float ni oldindan str ga aylantiramiz
        score_str = f'{score:.1f}'
        return format_html(
            '<div style="min-width:160px">'
            '<div style="background:#e9ecef;border-radius:6px;height:10px;margin-bottom:4px">'
            '<div style="background:{};width:{}%;height:10px;border-radius:6px"></div>'
            '</div>'
            '<b style="color:{};font-size:14px">{} / 100</b>'
            '</div>',
            color, width, color, score_str
        )

    @admin.display(description='Xavf darajasi')
    def risk_badge(self, obj):
        risk      = obj.risk_percentage
        color     = '#dc3545' if risk >= 70 else ('#fd7e14' if risk >= 40 else '#28a745')
        label     = 'Yuqori xavf' if risk >= 70 else ("O'rta xavf" if risk >= 40 else 'Xavf past')
        # ✅ float ni oldindan str ga aylantiramiz
        risk_str  = f'{risk:.1f}'
        return format_html(
            '<span style="color:{};font-weight:700;font-size:13px">'
            '{}% — {}</span>',
            color, risk_str, label
        )

    @admin.display(description='💡 Tavsiya (Recommendation)')
    def full_recommendation(self, obj):
        if not obj.recommendation:
            return '—'
        lines  = obj.recommendation.strip().split('\n')
        parts  = []
        first  = True
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
                    f'<div style="background:#fff3cd;border-left:4px solid #ffc107;'
                    f'padding:5px 10px;margin:3px 0;border-radius:0 4px 4px 0;'
                    f'font-size:12px;color:#856404">{line}</div>'
                )
            elif line.startswith('📌'):
                parts.append(
                    f'<div style="background:#e8f4fd;border-left:4px solid #17a2b8;'
                    f'padding:5px 10px;margin:3px 0;border-radius:0 4px 4px 0;'
                    f'font-size:12px;color:#0c5460">{line}</div>'
                )
            else:
                parts.append(
                    f'<div style="padding:3px 4px;font-size:12px;color:#555">{line}</div>'
                )
        return format_html(
            '<div style="background:#f8f9fa;border:1px solid #dee2e6;'
            'border-radius:8px;padding:14px 18px;line-height:1.7">'
            '{}</div>',
            format_html(''.join(parts))
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'group_link', 'score_summary',
        'prediction_badge', 'enrolled_at'
    ]
    list_filter   = ['group__course']
    search_fields = ['name', 'email']
    inlines       = [ScoreInline, PredictionInline]
    list_per_page = 25

    fieldsets = (
        ("👤 O'quvchi ma'lumotlari", {
            'fields': ('name', 'email', 'phone', 'group')
        }),
        ('📅 Sana', {
            'fields': ('enrolled_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['enrolled_at']

    @admin.display(description='Guruh', ordering='group__name')
    def group_link(self, obj):
        return format_html(
            '<span style="font-size:12px;color:#555">{} › {}</span>',
            obj.group.course.name, obj.group.name
        )

    @admin.display(description='Natijalar')
    def score_summary(self, obj):
        try:
            s   = obj.score
            avg = round((s.attendance + s.homework + s.quiz + s.exam) / 4, 1)
            color = '#28a745' if avg >= 70 else ('#ffc107' if avg >= 40 else '#dc3545')
            # ✅ barcha float larni oldindan str ga aylantiramiz
            return format_html(
                '<span style="font-size:11px;color:#777">'
                'D:{} H:{} Q:{} I:{}</span><br>'
                '<b style="color:{}">&oslash; {}</b>',
                s.attendance, s.homework, s.quiz, s.exam,
                color, avg
            )
        except Exception:
            return format_html('<span style="color:#999">—</span>')

    @admin.display(description='Prognoz')
    def prediction_badge(self, obj):
        pred = obj.predictions.order_by('-predicted_at').first()
        if not pred:
            return format_html(
                '<span style="color:#999;font-size:11px">Hisob. yo\'q</span>'
            )
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
        bg, color, icon = colors.get(pred.level, ('#eee', '#333', '⚪'))
        label     = labels.get(pred.level, pred.level)
        # ✅ float ni oldindan str ga aylantiramiz
        score_str = f'{pred.predicted_score:.1f}'
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600">'
            '{} {}</span><br>'
            '<span style="font-size:11px;color:#777">{} ball</span>',
            bg, color, icon, label, score_str
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(group__course__teacher=request.user)
        return qs

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return ['group']
        return self.list_filter

    def has_add_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser and obj:
            return obj.group.course.teacher == request.user
        return request.user.is_superuser or request.user.is_staff
