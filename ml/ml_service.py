"""
EduAnalytics ML Service
O'quvchining o'zlashtirish darajasini AQLLI tahlil qilish va prognozlash

Recommendation tizimi har bir ko'rsatkichni (davomat, uy vazifasi, quiz, imtihon)
alohida tahlil qilib, o'quvchining aniq zaif tomonlarini aniqlaydi va
shaxsiy tavsiyalar beradi.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  AQLLI RECOMMENDATION TIZIMI
# ═══════════════════════════════════════════════════════════════

def _analyze_weak_points(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> list[str]:
    """
    Har bir ko'rsatkichni tahlil qilib, zaif tomonlarni aniqlaydi.
    
    Darajalar:
        Yaxshi  : >= 70
        O'rtacha: 40 - 69
        Zaif    : < 40
    
    Returns:
        list of specific problem descriptions
    """
    problems = []

    # --- DAVOMAT tahlili ---
    if attendance < 40:
        problems.append(
            f"⚠️ Davomat juda past ({attendance:.0f}%) — darslarning yarmidan ko'pi o'tkazib yuborilgan"
        )
    elif attendance < 70:
        problems.append(
            f"📌 Davomat o'rtacha ({attendance:.0f}%) — darsga qatnashish muntazamligi oshirilishi kerak"
        )

    # --- UY VAZIFASI tahlili ---
    if homework < 40:
        problems.append(
            f"⚠️ Uy vazifalari juda kam bajarilgan ({homework:.0f}%) — mustaqil ishga e'tibor zarur"
        )
    elif homework < 70:
        problems.append(
            f"📌 Uy vazifasi o'rtacha ({homework:.0f}%) — uyda ko'proq takrorlash tavsiya etiladi"
        )

    # --- QUIZ tahlili ---
    if quiz < 40:
        problems.append(
            f"⚠️ Quiz natijalari juda past ({quiz:.0f}%) — mavzularni tushunishda jiddiy muammolar bor"
        )
    elif quiz < 70:
        problems.append(
            f"📌 Quiz natijalari o'rtacha ({quiz:.0f}%) — nazariy bilimlarni mustahkamlash kerak"
        )

    # --- IMTIHON tahlili ---
    if exam < 40:
        problems.append(
            f"⚠️ Imtihon natijasi juda past ({exam:.0f}%) — bilim darajasi past, tezkor yordam kerak"
        )
    elif exam < 70:
        problems.append(
            f"📌 Imtihon natijasi o'rtacha ({exam:.0f}%) — imtihonga tayyorgarlikni kuchaytirish kerak"
        )

    return problems


def _find_strongest_point(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> str:
    """O'quvchining eng kuchli tomonini topadi"""
    scores = {
        'Davomat':    attendance,
        'Uy vazifasi': homework,
        'Quiz':       quiz,
        'Imtihon':    exam,
    }
    best = max(scores, key=scores.get)
    return f"{best} ({scores[best]:.0f}%)"


def generate_smart_recommendation(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float,
    level: str,
    predicted_score: float
) -> str:
    """
    O'quvchining barcha ko'rsatkichlarini tahlil qilib,
    SHAXSIY va ANIQ tavsiya generatsiya qiladi.

    Args:
        attendance: Davomat foizi (0-100)
        homework:   Uy vazifasi foizi (0-100)
        quiz:       Quiz foizi (0-100)
        exam:       Imtihon foizi (0-100)
        level:      Prognoz darajasi
        predicted_score: Umumiy ball

    Returns:
        Shaxsiy tavsiya matni
    """
    problems    = _analyze_weak_points(attendance, homework, quiz, exam)
    best_point  = _find_strongest_point(attendance, homework, quiz, exam)
    lines       = []

    # ── HIGH PERFORMANCE ─────────────────────────────────────────
    if level == 'High Performance':
        lines.append(f"✅ Ajoyib natija! Umumiy ball: {predicted_score:.1f}/100")
        lines.append(f"🏆 Eng kuchli ko'rsatkich: {best_point}")

        if not problems:
            lines.append("📈 Barcha ko'rsatkichlar yaxshi darajada. Joriy sur'atni saqlang!")
        else:
            lines.append("📊 Kichik takomillashtirish imkoniyatlari:")
            for p in problems:
                lines.append(f"   {p}")

        # Imtihon va quiz farqi katta bo'lsa ogohlantirish
        if abs(exam - quiz) > 25:
            if exam > quiz:
                lines.append(
                    f"💡 Imtihon ({exam:.0f}%) va quiz ({quiz:.0f}%) orasida katta farq bor — "
                    f"sinf ishlarida ham yuqori natija ko'rsating"
                )
            else:
                lines.append(
                    f"💡 Quiz ({quiz:.0f}%) yaxshi, lekin imtihon ({exam:.0f}%) pastroq — "
                    f"imtihon vaziyatida ishonchni mustahkamlang"
                )

    # ── MEDIUM PERFORMANCE ───────────────────────────────────────
    elif level == 'Medium Performance':
        lines.append(f"📊 O'rta daraja. Umumiy ball: {predicted_score:.1f}/100")
        lines.append(f"🏅 Kuchli tomoni: {best_point}")

        if problems:
            lines.append(f"\n🔍 Yaxshilash kerak bo'lgan sohalar:")
            for p in problems:
                lines.append(f"   {p}")

        # Konkret maslahatlar
        action_items = _get_action_items(attendance, homework, quiz, exam)
        if action_items:
            lines.append(f"\n📋 Tavsiya etilgan harakatlar:")
            for action in action_items:
                lines.append(f"   {action}")

        lines.append(
            f"\n🎯 Maqsad: Umumiy ballni {predicted_score:.0f}→70 ga yetkazish uchun "
            f"haftalik {_calculate_needed_improvement(attendance, homework, quiz, exam)}"
        )

    # ── LOW PERFORMANCE ──────────────────────────────────────────
    else:  # Low Performance
        lines.append(f"🚨 Darhol e'tibor talab etiladi! Ball: {predicted_score:.1f}/100")

        critical = [p for p in problems if p.startswith("⚠️")]
        moderate = [p for p in problems if p.startswith("📌")]

        if critical:
            lines.append(f"\n🔴 Jiddiy muammolar ({len(critical)} ta):")
            for p in critical:
                lines.append(f"   {p}")

        if moderate:
            lines.append(f"\n🟡 O'rtacha muammolar ({len(moderate)} ta):")
            for p in moderate:
                lines.append(f"   {p}")

        # Eng past ko'rsatkich
        worst_metric = min(
            [('Davomat', attendance), ('Uy vazifasi', homework),
             ('Quiz', quiz), ('Imtihon', exam)],
            key=lambda x: x[1]
        )
        lines.append(
            f"\n🎯 BIRINCHI NAVBATDA: {worst_metric[0]} ({worst_metric[1]:.0f}%) — "
            f"shu ko'rsatkichni yaxshilash eng katta ta'sir beradi"
        )

        # Acil harakatlar
        lines.append(f"\n⚡ Zudlik bilan kerak bo'lgan yordam:")
        urgent = _get_urgent_actions(attendance, homework, quiz, exam)
        for action in urgent:
            lines.append(f"   {action}")

    return "\n".join(lines)


def _get_action_items(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> list[str]:
    """Medium Performance uchun aniq harakatlar ro'yxati"""
    actions = []

    if attendance < 70:
        missed = round((100 - attendance) / 100 * 20)  # oylik
        actions.append(f"📅 Oyiga taxminan {missed} darsni qayta ko'rib chiqing")

    if homework < 70:
        actions.append("📝 Har kuni 30-45 daqiqa uy vazifasiga vaqt ajrating")

    if quiz < 70:
        actions.append("📖 Har mavzu oxirida o'z-o'zini tekshirish testlarini yechib ko'ring")

    if exam < 70:
        actions.append("✏️ O'tgan imtihon savollarini takrorlang, sinov imtihonlar yozing")

    return actions[:3]  # eng muhim 3 tasini qaytarish


def _get_urgent_actions(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> list[str]:
    """Low Performance uchun favqulodda harakatlar"""
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


def _calculate_needed_improvement(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> str:
    """70 ballga yetish uchun taxminiy yaxshilanish hisoblash"""
    current = attendance * 0.20 + homework * 0.20 + quiz * 0.30 + exam * 0.30
    needed  = 70 - current

    if needed <= 5:
        return "kichik qo'shimcha sa'y-harakat yetarli"
    elif needed <= 15:
        return f"~{needed:.0f} ball yaxshilanish kerak (5-6 hafta intensiv ish)"
    else:
        return f"~{needed:.0f} ball yaxshilanish kerak (jiddiy rejali ish talab etiladi)"


# ═══════════════════════════════════════════════════════════════
#  ASOSIY PROGNOZ FUNKSIYASI
# ═══════════════════════════════════════════════════════════════

def calculate_prediction(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> dict:
    """
    Weighted formula asosida prognoz hisoblash + aqlli recommendation.

    Formula:
        predicted_score = attendance×0.20 + homework×0.20 + quiz×0.30 + exam×0.30

    Returns:
        dict with: predicted_score, level, risk_percentage, recommendation
    """
    predicted_score = (
        attendance * 0.20 +
        homework   * 0.20 +
        quiz       * 0.30 +
        exam       * 0.30
    )
    predicted_score = round(predicted_score, 1)

    # Daraja va xavf foizi aniqlash
    if predicted_score >= 70:
        level           = 'High Performance'
        risk_percentage = round(100 - predicted_score, 1)
    elif predicted_score >= 40:
        level           = 'Medium Performance'
        risk_percentage = round(70 - predicted_score * 0.5, 1)
    else:
        level           = 'Low Performance'
        risk_percentage = round(min(100.0, 100 - predicted_score * 0.3), 1)

    # ✅ AQLLI RECOMMENDATION — har bir o'quvchi uchun shaxsiy tavsiya
    recommendation = generate_smart_recommendation(
        attendance=attendance,
        homework=homework,
        quiz=quiz,
        exam=exam,
        level=level,
        predicted_score=predicted_score,
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
    exam: float
) -> Optional[dict]:
    """
    Agar ML model (sklearn .pkl fayl) mavjud bo'lsa, u orqali prognoz qilish.
    Aks holda None qaytaradi — weighted formula ishga tushadi.
    """
    try:
        import joblib
        from django.conf import settings

        model_path = getattr(settings, 'ML_MODEL_PATH', None)
        if not model_path or not os.path.exists(model_path):
            return None

        model      = joblib.load(model_path)
        features   = [[attendance, homework, quiz, exam]]
        prediction = model.predict(features)[0]
        proba      = model.predict_proba(features)[0] if hasattr(model, 'predict_proba') else None

        level_map = {
            0: 'Low Performance',
            1: 'Medium Performance',
            2: 'High Performance'
        }
        level = level_map.get(int(prediction), 'Medium Performance')

        # Ball hisoblash formuladan
        result        = calculate_prediction(attendance, homework, quiz, exam)
        result['level'] = level  # ML model darajasini ustiga yozish

        if proba is not None:
            result['risk_percentage'] = round((1 - proba[2]) * 100, 1)

        # Recommendation ni ML model darajasiga moslash
        result['recommendation'] = generate_smart_recommendation(
            attendance=attendance,
            homework=homework,
            quiz=quiz,
            exam=exam,
            level=level,
            predicted_score=result['predicted_score'],
        )

        return result

    except Exception as e:
        logger.warning(f"ML model xatosi: {e}. Weighted formula ishlatiladi.")
        return None


def get_prediction(
    attendance: float,
    homework: float,
    quiz: float,
    exam: float
) -> dict:
    """
    Asosiy prognoz funksiyasi.
    Avval sklearn ML modelni sinab ko'radi.
    Model yo'q yoki xato bo'lsa — weighted formula + aqlli recommendation ishlatiladi.
    """
    result = try_ml_model_prediction(attendance, homework, quiz, exam)
    if result is None:
        result = calculate_prediction(attendance, homework, quiz, exam)
    return result
