"""
EduAnalytics — ML Model O'qitish Skripti
Ishlatish: python ml/train.py

Bu skript demo data asosida model yaratadi.
Real loyihada o'z ma'lumotlaringizni ishlating.
"""
import os
import sys
import numpy as np

# Django settings qo'shish
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def generate_demo_data(n_samples=500):
    """Demo training data yaratish"""
    np.random.seed(42)

    attendance = np.random.uniform(0, 100, n_samples)
    homework   = np.random.uniform(0, 100, n_samples)
    quiz       = np.random.uniform(0, 100, n_samples)
    exam       = np.random.uniform(0, 100, n_samples)

    # Weighted formula asosida label
    scores = attendance * 0.20 + homework * 0.20 + quiz * 0.30 + exam * 0.30
    labels = np.where(scores >= 70, 2, np.where(scores >= 40, 1, 0))
    # 0: Low, 1: Medium, 2: High

    X = np.column_stack([attendance, homework, quiz, exam])
    y = labels
    return X, y


def train_and_save():
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, classification_report
        import joblib
    except ImportError:
        print("❌ scikit-learn o'rnatilmagan: pip install scikit-learn joblib")
        return

    print("📊 Demo data yaratilmoqda...")
    X, y = generate_demo_data(1000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("🤖 Random Forest model o'qitilmoqda...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model aniqligi: {accuracy:.2%}")
    print("\n📈 Batafsil hisobot:")
    print(classification_report(
        y_test, y_pred,
        target_names=['Low Performance', 'Medium Performance', 'High Performance']
    ))

    # Model saqlash
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'model_v1.pkl')
    joblib.dump(model, model_path)
    print(f"\n💾 Model saqlandi: {model_path}")


if __name__ == '__main__':
    train_and_save()
