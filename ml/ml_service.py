"""
EduAnalytics ML Service — v2.0
O'quvchining o'zlashtirish darajasini AQLLI tahlil qilish va prognozlash.

Yangiliklar (v2.0):
    - get_prediction_with_trends() — kunlik ma'lumotlar asosida kengaytirilgan prognoz
    - Trend feature'lar: attendance_trend, consecutive_absent, hw_streak, quiz_improvement
    - Risk_percentage formulasi to'g'irlandi (past ball = yuqori xavf)
    - ML model trend feature'larni ham qabul qiladi (agar model yangilangan bo'lsa)
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  RISK PERCENTAGE — To'g'irlangan formula
# ═══════════════════════════════════════════════════════════════

def _calculate_risk(predicted_score: float, level: str,
                    consecutive_absent: int = 0,
                    attendance_trend: float = 0.0) -> float:
    """
    Xavf foizini hisoblash. Qoida: past ball = yuqori xavf.

    Asosiy formula:
        High:   risk = 100 - predicted_score        (kam xavf)
        Medium: risk = 70 - predicted_score × 0.5   (o'rta xavf) — to'g'irlandi
        Low:    risk = min(100, 100 - score × 0.3)  (yuqori xavf)

    Trend korreksiyasi:
        + 3 kun ketma-ket kelmagan → risk +10
        + attendance pasaymoqda    → risk +5
    """
    if level == 'High Performance':
        risk = round(100 - predicted_score, 1)
    elif level == 'Medium Performance':
        # To'g'irlangan: score=40 → risk=60, score=69 → risk=31
        risk = round(max(0.0, 100 - predicted_score), 1)
        risk = round(risk * 0.7, 1)   # Medium uchun ozroq kamaytirish
    else:
        # Low Performance
        risk = round(min(100.0, 110 - predicted_score), 1)

    # Trend korreksiyalari
    if consecutive_absent >= 3:
        risk = min(100.0, risk + 10.0)
    if attendance_trend < -10:
        risk = min(100.0, risk + 5.0)
    elif attendance_trend > 10:
        risk = max(0.0, risk - 3.0)

    return round(risk, 1)


# ═══════════════════════════════════════════════════════════════
#  AQLLI RECOMMENDATION TIZIMI
# ═══════════════════════════════════════════════════════════════

def _analyze_weak_points(attendance, homework, quiz, exam) -> list:
    problems = []

    if attendance < 40:
        problems.append(f"⚠️ Davomat juda past ({attendance:.0f}%) — darslarning yarmidan ko'pi o'tkazib yuborilgan")
    elif attendance < 70:
        problems.append(f"📌 Davomat o'rtacha ({attendance:.0f}%) — muntazamlik oshirilishi kerak")

    if homework < 40:
        problems.append(f"⚠️ Uy vazifalari juda kam bajarilgan ({homework:.0f}%) — mustaqil ishga e'tibor zarur")
    elif homework < 70:
        problems.append(f"📌 Uy vazifasi o'rtacha ({homework:.0f}%) — uyda ko'proq takrorlash tavsiya etiladi")

    if quiz < 40:
        problems.append(f"⚠️ Quiz natijalari juda past ({quiz:.0f}%) — mavzularni tushunishda jiddiy muammolar bor")
    elif quiz < 70:
        problems.append(f"📌 Quiz natijalari o'rtacha ({quiz:.0f}%) — nazariy bilimlarni mustahkamlash kerak")

    if exam < 40:
        problems.append(f"⚠️ Imtihon natijasi juda past ({exam:.0f}%) — bilim darajasi past, tezkor yordam kerak")
    elif exam < 70:
        problems.append(f"📌 Imtihon natijasi o'rtacha ({exam:.0f}%) — imtihonga tayyorgarlikni kuchaytirish kerak")

    return problems


def _find_strongest_point(attendance, homework, quiz, exam) -> str:
    scores = {'Davomat': attendance, 'Uy vazifasi': homework, 'Quiz': quiz, 'Imtihon': exam}
    best   = max(scores, key=scores.get)
    return f"{best} ({scores[best]:.0f}%)"


def _trend_comment(attendance_trend, consecutive_absent, hw_streak, quiz_improvement) -> list:
    """Trend asosida qo'shimcha izohlar"""
    comments = []

    if consecutive_absent >= 5:
        comments.append(f"🚨 Ketma-ket {consecutive_absent} kun kelmagan — ZUDLIK BILAN murojaat qiling!")
    elif consecutive_absent >= 3:
        comments.append(f"⚠️ So'nggi {consecutive_absent} kun ketma-ket kelmagan — e'tibor bering")

    if attendance_trend >= 10:
        comments.append(f"📈 Davomat oxirgi haftada {attendance_trend:+.0f}% — zo'r tendensiya!")
    elif attendance_trend <= -10:
        comments.append(f"📉 Davomat oxirgi haftada {attendance_trend:+.0f}% — pasaymoqda, sababini aniqlang")

    if hw_streak >= 5:
        comments.append(f"🔥 {hw_streak} ta uy vazifani ketma-ket topshirdi — ajoyib!")

    if quiz_improvement >= 10:
        comments.append(f"📊 Quiz natijalar +{quiz_improvement:.0f}% yaxshilandi — progress bor!")
    elif quiz_improvement <= -10:
        comments.append(f"📉 Quiz natijalar {quiz_improvement:.0f}% pasaydi — sababini toping")

    return comments


def _get_action_items(attendance, homework, quiz, exam) -> list:
    actions = []
    if attendance < 70:
        missed = round((100 - attendance) / 100 * 20)
        actions.append(f"📅 Oyiga taxminan {missed} darsni qayta ko'rib chiqing")
    if homework < 70:
        actions.append("📝 Har kuni 30-45 daqiqa uy vazifasiga vaqt ajrating")
    if quiz < 70:
        actions.append("📖 Har mavzu oxirida o'z-o'zini tekshirish testlarini yechib ko'ring")
    if exam < 70:
        actions.append("✏️ O'tgan imtihon savollarini takrorlang, sinov imtihonlar yozing")
    return actions[:3]


def _get_urgent_actions(attendance, homework, quiz, exam) -> list:
    actions = []
    if attendance < 40:
        actions.append("👨‍🏫 O'qituvchi bilan individual uchrashuv rejalashtiring")
        actions.append("📱 Ota-onani dars qatnashishi haqida xabardor qiling")
    if homework < 40:
        actions.append("📚 Qo'shimcha o'quv materiallari (video darslar, kitoblar) toping")
    if quiz < 40:
        actions.append("🔁 Oxirgi 3 oy davomida o'tilgan mavzularni qaytadan o'rganing")
    if exam < 40:
        actions.append("👥 Guruhda birgalikda tayyorgarlik mashg'ulotlari o'tkazing")
    if not actions:
        actions.append("💬 O'qituvchi bilan qo'shimcha mashg'ulotlar jadvalini tuzing")
    return actions[:4]


def _calculate_needed_improvement(attendance, homework, quiz, exam) -> str:
    current = attendance * 0.20 + homework * 0.20 + quiz * 0.30 + exam * 0.30
    needed  = 70 - current
    if needed <= 5:
        return "kichik qo'shimcha sa'y-harakat yetarli"
    elif needed <= 15:
        return f"~{needed:.0f} ball yaxshilanish kerak (5-6 hafta intensiv ish)"
    else:
        return f"~{needed:.0f} ball yaxshilanish kerak (jiddiy rejali ish talab etiladi)"


def generate_smart_recommendation(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
    level: str,
    predicted_score: float,
    attendance_trend: float = 0.0,
    consecutive_absent: int = 0,
    hw_streak: int = 0,
    quiz_improvement: float = 0.0,
) -> str:
    """
    O'quvchining barcha ko'rsatkichlari va trend ma'lumotlari asosida
    SHAXSIY va ANIQ tavsiya generatsiya qiladi.
    """
    problems    = _analyze_weak_points(attendance, homework, quiz, exam)
    best_point  = _find_strongest_point(attendance, homework, quiz, exam)
    trend_notes = _trend_comment(attendance_trend, consecutive_absent, hw_streak, quiz_improvement)
    lines       = []

    # ── HIGH PERFORMANCE ──────────────────────────────────────────
    if level == 'High Performance':
        lines.append(f"✅ Ajoyib natija! Umumiy ball: {predicted_score:.1f}/100")
        lines.append(f"🏆 Eng kuchli ko'rsatkich: {best_point}")

        if trend_notes:
            lines.append("\n📈 Trend:")
            lines.extend(f"   {t}" for t in trend_notes)

        if not problems:
            lines.append("\n📊 Barcha ko'rsatkichlar yaxshi darajada. Joriy sur'atni saqlang!")
        else:
            lines.append("\n📊 Kichik takomillashtirish imkoniyatlari:")
            lines.extend(f"   {p}" for p in problems)

        if abs(exam - quiz) > 25:
            if exam > quiz:
                lines.append(f"\n💡 Imtihon ({exam:.0f}%) va quiz ({quiz:.0f}%) orasida katta farq bor")
            else:
                lines.append(f"\n💡 Quiz ({quiz:.0f}%) yaxshi, lekin imtihon ({exam:.0f}%) pastroq")

    # ── MEDIUM PERFORMANCE ────────────────────────────────────────
    elif level == 'Medium Performance':
        lines.append(f"📊 O'rta daraja. Umumiy ball: {predicted_score:.1f}/100")
        lines.append(f"🏅 Kuchli tomoni: {best_point}")

        if trend_notes:
            lines.append("\n📈 Trend:")
            lines.extend(f"   {t}" for t in trend_notes)

        if problems:
            lines.append("\n🔍 Yaxshilash kerak bo'lgan sohalar:")
            lines.extend(f"   {p}" for p in problems)

        action_items = _get_action_items(attendance, homework, quiz, exam)
        if action_items:
            lines.append("\n📋 Tavsiya etilgan harakatlar:")
            lines.extend(f"   {a}" for a in action_items)

        lines.append(
            f"\n🎯 Maqsad: Umumiy ballni {predicted_score:.0f}→70 ga yetkazish uchun "
            f"haftalik {_calculate_needed_improvement(attendance, homework, quiz, exam)}"
        )

    # ── LOW PERFORMANCE ───────────────────────────────────────────
    else:
        lines.append(f"🚨 Darhol e'tibor talab etiladi! Ball: {predicted_score:.1f}/100")

        if trend_notes:
            lines.append("\n⚡ Joriy holat:")
            lines.extend(f"   {t}" for t in trend_notes)

        critical = [p for p in problems if p.startswith("⚠️")]
        moderate = [p for p in problems if p.startswith("📌")]

        if critical:
            lines.append(f"\n🔴 Jiddiy muammolar ({len(critical)} ta):")
            lines.extend(f"   {p}" for p in critical)

        if moderate:
            lines.append(f"\n🟡 O'rtacha muammolar ({len(moderate)} ta):")
            lines.extend(f"   {p}" for p in moderate)

        worst_metric = min(
            [('Davomat', attendance), ('Uy vazifasi', homework),
             ('Quiz', quiz), ('Imtihon', exam)],
            key=lambda x: x[1]
        )
        lines.append(
            f"\n🎯 BIRINCHI NAVBATDA: {worst_metric[0]} ({worst_metric[1]:.0f}%) — "
            f"shu ko'rsatkichni yaxshilash eng katta ta'sir beradi"
        )

        lines.append("\n⚡ Zudlik bilan kerak bo'lgan yordam:")
        lines.extend(f"   {a}" for a in _get_urgent_actions(attendance, homework, quiz, exam))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  ASOSIY PROGNOZ FUNKSIYALARI
# ═══════════════════════════════════════════════════════════════

def calculate_prediction(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
    attendance_trend: float = 0.0,
    consecutive_absent: int = 0,
    hw_streak: int = 0,
    quiz_improvement: float = 0.0,
) -> dict:
    """
    Weighted formula asosida prognoz hisoblash.

    Formula:
        predicted_score = attendance×0.20 + homework×0.20 + quiz×0.30 + exam×0.30

    Trend korreksiyasi (kichik):
        attendance_trend yoki quiz_improvement yaxshi bo'lsa → +2 ball
        consecutive_absent >= 3 → -3 ball
    """
    base_score = (
        attendance * 0.20 +
        homework   * 0.20 +
        quiz       * 0.30 +
        exam       * 0.30
    )

    # Trend korreksiyasi — kichik bonus/malus
    correction = 0.0
    if attendance_trend > 10:
        correction += 1.5
    elif attendance_trend < -10:
        correction -= 1.5

    if quiz_improvement > 10:
        correction += 1.5
    elif quiz_improvement < -10:
        correction -= 1.0

    if consecutive_absent >= 5:
        correction -= 3.0
    elif consecutive_absent >= 3:
        correction -= 1.5

    if hw_streak >= 7:
        correction += 1.0

    predicted_score = round(max(0.0, min(100.0, base_score + correction)), 1)

    # Daraja
    if predicted_score >= 70:
        level = 'High Performance'
    elif predicted_score >= 40:
        level = 'Medium Performance'
    else:
        level = 'Low Performance'

    risk_percentage = _calculate_risk(
        predicted_score, level, consecutive_absent, attendance_trend
    )

    recommendation = generate_smart_recommendation(
        attendance=attendance,
        homework=homework,
        quiz=quiz,
        exam=exam,
        level=level,
        predicted_score=predicted_score,
        attendance_trend=attendance_trend,
        consecutive_absent=consecutive_absent,
        hw_streak=hw_streak,
        quiz_improvement=quiz_improvement,
    )

    return {
        'predicted_score': predicted_score,
        'level':           level,
        'risk_percentage': risk_percentage,
        'recommendation':  recommendation,
    }


def try_ml_model_prediction(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
    attendance_trend: float = 0.0,
    consecutive_absent: int = 0,
    hw_streak: int = 0,
    quiz_improvement: float = 0.0,
) -> Optional[dict]:
    """
    Agar sklearn ML model (.pkl) mavjud bo'lsa, u orqali prognoz qilish.
    Model 8 ta feature bilan ishlaydi (4 asosiy + 4 trend).
    Eski 4-feature model bo'lsa — ham ishlaydi (xato bo'lsa weighted formula ishlatiladi).
    """
    try:
        import joblib
        import numpy as np
        from django.conf import settings

        model_path = getattr(settings, 'ML_MODEL_PATH', None)
        if not model_path or not os.path.exists(model_path):
            return None

        model = joblib.load(model_path)

        # 8-feature model sinab ko'rish, eski bo'lsa 4-feature
        features_8 = [[attendance, homework, quiz, exam,
                        attendance_trend, consecutive_absent, hw_streak, quiz_improvement]]
        features_4 = [[attendance, homework, quiz, exam]]

        try:
            prediction = model.predict(features_8)[0]
            proba      = model.predict_proba(features_8)[0] if hasattr(model, 'predict_proba') else None
        except ValueError:
            # Eski model (4 feature)
            prediction = model.predict(features_4)[0]
            proba      = model.predict_proba(features_4)[0] if hasattr(model, 'predict_proba') else None

        level_map = {0: 'Low Performance', 1: 'Medium Performance', 2: 'High Performance'}
        level     = level_map.get(int(prediction), 'Medium Performance')

        # Ball weighted formula bilan, daraja ML dan
        result          = calculate_prediction(
            attendance, homework, quiz, exam,
            attendance_trend, consecutive_absent, hw_streak, quiz_improvement
        )
        result['level'] = level

        if proba is not None:
            result['risk_percentage'] = _calculate_risk(
                result['predicted_score'], level, consecutive_absent, attendance_trend
            )
            # ML ning "xavf" ehtimolini ham hisobga olish
            ml_risk = round((1 - proba[2]) * 100, 1)
            result['risk_percentage'] = round(
                (result['risk_percentage'] + ml_risk) / 2, 1
            )

        result['recommendation'] = generate_smart_recommendation(
            attendance=attendance, homework=homework, quiz=quiz, exam=exam,
            level=level, predicted_score=result['predicted_score'],
            attendance_trend=attendance_trend, consecutive_absent=consecutive_absent,
            hw_streak=hw_streak, quiz_improvement=quiz_improvement,
        )

        return result

    except Exception as e:
        logger.warning(f"ML model xatosi: {e}. Weighted formula ishlatiladi.")
        return None


def get_prediction(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
) -> dict:
    """
    Oddiy prognoz (trend ma'lumotlarsiz).
    Eski Signal va PredictView bilan moslik uchun saqlanadi.
    """
    return get_prediction_with_trends(attendance, homework, quiz, exam)


def get_prediction_with_trends(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
    attendance_trend: float = 0.0,
    consecutive_absent: int = 0,
    hw_streak: int = 0,
    quiz_improvement: float = 0.0,
) -> dict:
    """
    Asosiy prognoz funksiyasi — trend ma'lumotlar bilan.
    Avval sklearn ML modelni sinab ko'radi.
    Model yo'q yoki xato bo'lsa — weighted formula + trend korreksiyasi ishlatiladi.
    """
    result = try_ml_model_prediction(
        attendance, homework, quiz, exam,
        attendance_trend, consecutive_absent, hw_streak, quiz_improvement
    )
    if result is None:
        result = calculate_prediction(
            attendance, homework, quiz, exam,
            attendance_trend, consecutive_absent, hw_streak, quiz_improvement
        )
    return result
