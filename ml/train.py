"""
EduAnalytics — ML Model O'qitish Skripti v2.0
Ishlatish: python ml/train.py

Yangiliklar (v2.0):
    - 8 ta feature: 4 asosiy + 4 trend
    - Trend feature'lar: attendance_trend, consecutive_absent, hw_streak, quiz_improvement
    - Realistic demo data: o'quvchi xulq-atvor patternlari simulatsiya qilinadi
    - Model evaluation: confusion matrix va feature importance
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

FEATURE_NAMES = [
    'attendance',        # Davomat foizi (0-100)
    'homework',          # Uy vazifasi foizi (0-100)
    'quiz',              # Quiz/sinf ishi foizi (0-100)
    'exam',              # Imtihon foizi (0-100)
    'attendance_trend',  # Oxirgi hafta trendi (-100 dan +100)
    'consecutive_absent',# Maksimal ketma-ket kelmaslik (0-30)
    'hw_streak',         # Maksimal ketma-ket topshirish (0-30)
    'quiz_improvement',  # Quiz yaxshilanish trendi (-50 dan +50)
]


def generate_student_profile(rng: np.random.Generator, profile_type: str) -> dict:
    """
    Haqiqiy o'quvchi xulq-atvorini simulatsiya qiluvchi profil generatsiya.

    Profile types:
        'high'    — yuqori darajali o'quvchi
        'medium'  — o'rta darajali o'quvchi
        'low'     — qiynalayotgan o'quvchi
        'mixed'   — aralash (masalan: davomat yaxshi, imtihon yomon)
        'dropout' — tushib ketish xavfidagi o'quvchi
    """
    if profile_type == 'high':
        att = rng.uniform(75, 100)
        hw  = rng.uniform(70, 100)
        q   = rng.uniform(68, 100)
        e   = rng.uniform(65, 100)
        trend  = rng.uniform(-5, 20)
        absent = int(rng.integers(0, 2))
        streak = int(rng.integers(5, 20))
        q_imp  = rng.uniform(-5, 20)

    elif profile_type == 'medium':
        att = rng.uniform(50, 80)
        hw  = rng.uniform(45, 75)
        q   = rng.uniform(40, 72)
        e   = rng.uniform(38, 70)
        trend  = rng.uniform(-10, 10)
        absent = int(rng.integers(0, 4))
        streak = int(rng.integers(2, 10))
        q_imp  = rng.uniform(-8, 15)

    elif profile_type == 'low':
        att = rng.uniform(10, 50)
        hw  = rng.uniform(5, 45)
        q   = rng.uniform(5, 42)
        e   = rng.uniform(5, 40)
        trend  = rng.uniform(-20, 5)
        absent = int(rng.integers(3, 15))
        streak = int(rng.integers(0, 3))
        q_imp  = rng.uniform(-15, 5)

    elif profile_type == 'mixed':
        # Davomat yaxshi, lekin o'zlashtirish yomon — diqqat muammo
        att = rng.uniform(70, 95)
        hw  = rng.uniform(30, 60)
        q   = rng.uniform(25, 55)
        e   = rng.uniform(20, 45)
        trend  = rng.uniform(-5, 5)
        absent = int(rng.integers(0, 3))
        streak = int(rng.integers(1, 5))
        q_imp  = rng.uniform(-10, 10)

    else:  # 'dropout' — tushib ketish xavfida
        att = rng.uniform(0, 35)
        hw  = rng.uniform(0, 30)
        q   = rng.uniform(0, 35)
        e   = rng.uniform(0, 30)
        trend  = rng.uniform(-30, -5)
        absent = int(rng.integers(5, 20))
        streak = int(rng.integers(0, 2))
        q_imp  = rng.uniform(-20, -5)

    return {
        'attendance':         np.clip(att, 0, 100),
        'homework':           np.clip(hw,  0, 100),
        'quiz':               np.clip(q,   0, 100),
        'exam':               np.clip(e,   0, 100),
        'attendance_trend':   float(trend),
        'consecutive_absent': float(absent),
        'hw_streak':          float(streak),
        'quiz_improvement':   float(q_imp),
    }


def generate_demo_data(n_samples: int = 1500, seed: int = 42):
    """
    Realistic demo ma'lumotlari yaratish.

    Taqsimot:
        High:   35%
        Medium: 40%
        Low:    25% (shundan 10% dropout)
    """
    rng     = np.random.default_rng(seed)
    n_high  = int(n_samples * 0.35)
    n_med   = int(n_samples * 0.40)
    n_low   = int(n_samples * 0.15)
    n_mixed = int(n_samples * 0.05)
    n_drop  = n_samples - n_high - n_med - n_low - n_mixed

    profiles = (
        [('high',    2)] * n_high  +
        [('medium',  1)] * n_med   +
        [('low',     0)] * n_low   +
        [('mixed',   1)] * n_mixed +   # Mixed → Medium label
        [('dropout', 0)] * n_drop
    )
    rng.shuffle(profiles)

    rows   = []
    labels = []
    for ptype, label in profiles:
        p = generate_student_profile(rng, ptype)
        rows.append([
            p['attendance'], p['homework'], p['quiz'], p['exam'],
            p['attendance_trend'], p['consecutive_absent'],
            p['hw_streak'], p['quiz_improvement'],
        ])
        # Label ni weighted formula bilan ham tekshir (consistency)
        score = (p['attendance'] * 0.2 + p['homework'] * 0.2 +
                 p['quiz'] * 0.3 + p['exam'] * 0.3)
        if score >= 70:
            label = max(label, 1)
            if score >= 70:
                label = 2
        elif score < 40:
            label = 0
        labels.append(label)

    X = np.array(rows,   dtype=float)
    y = np.array(labels, dtype=int)
    return X, y


def train_and_save():
    try:
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        import joblib
    except ImportError:
        print("❌ scikit-learn o'rnatilmagan: pip install scikit-learn joblib")
        return

    print("📊 Demo data yaratilmoqda (1500 ta namuna, 8 feature)...")
    X, y = generate_demo_data(n_samples=1500)

    print(f"   High Performance  (2): {(y == 2).sum()} ta")
    print(f"   Medium Performance(1): {(y == 1).sum()} ta")
    print(f"   Low Performance   (0): {(y == 0).sum()} ta")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Gradient Boosting — trend feature'lar bilan yaxshi ishlaydi
    print("\n🤖 Gradient Boosting Classifier o'qitilmoqda...")
    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model aniqligi: {accuracy:.2%}")

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"📊 Cross-validation (5-fold): {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")

    print("\n📈 Batafsil hisobot:")
    print(classification_report(
        y_test, y_pred,
        target_names=['Low Performance', 'Medium Performance', 'High Performance']
    ))

    print("🔀 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    for row in cm:
        print("   ", row)

    print("\n🎯 Feature ahamiyati (muhimlik tartibi):")
    importances = model.feature_importances_
    feature_importance_pairs = sorted(
        zip(FEATURE_NAMES, importances),
        key=lambda x: x[1], reverse=True
    )
    for fname, imp in feature_importance_pairs:
        bar = '█' * int(imp * 50)
        print(f"   {fname:<22}: {imp:.3f}  {bar}")

    # Model saqlash
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'model_v2.pkl')
    joblib.dump(model, model_path)
    print(f"\n💾 Model saqlandi: {model_path}")
    print(f"⚙️  Model {len(FEATURE_NAMES)} feature ishlatadi: {FEATURE_NAMES}")
    print("\n📝 settings.py da MODEL_PATH ni yangilang:")
    print(f"   ML_MODEL_PATH = '{model_path}'")


if __name__ == '__main__':
    train_and_save()
