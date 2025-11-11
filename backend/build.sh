#!/usr/bin/env bash
echo "🚀 Starting build process..."

# ✅ Install all dependencies from the backend folder
pip install -r backend/requirements.txt

# ✅ Initialize the database and create tables
python - <<'EOF'
from backend.app import create_app
from backend.app.models import db, SuperAdmin

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully on Render!")

    # ✅ Create default super admin if not exists
    if not SuperAdmin.query.first():
        admin = SuperAdmin(
            name="Super Admin",
            email="super@callmanager.com"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✅ Default Super Admin created: super@callmanager.com / admin123")
EOF

echo "✅ Build completed successfully!"
