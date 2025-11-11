#!/usr/bin/env bash
echo "🚀 Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Initialize database and create tables
python - <<'PYCODE'
from app import create_app
from app.models import db, SuperAdmin

app = create_app()
with app.app_context():
    print("⚙️ Checking database tables...")
    db.create_all()

    print("✅ Checking for default Super Admin...")
    if not SuperAdmin.query.first():
        super_admin = SuperAdmin(
            name="Super Admin",
            email="super@callmanager.com"
        )
        super_admin.set_password("admin123")
        db.session.add(super_admin)
        db.session.commit()
        print("✅ Default Super Admin created: super@callmanager.com / admin123")
    else:
        print("ℹ️ Super Admin already exists.")
PYCODE

echo "✅ Build completed successfully!"
