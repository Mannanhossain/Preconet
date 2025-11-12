# #!/usr/bin/env bash
# echo "🚀 Starting build process..."

# # Install dependencies
# pip install -r requirements.txt

# # Create all tables in the connected database
# python - <<'PYCODE'
# from app import create_app
# from app.models import db, SuperAdmin
# from sqlalchemy import inspect

# app = create_app()
# with app.app_context():
#     print("⚙️ Checking database connection and tables...")

#     inspector = inspect(db.engine)
#     existing_tables = inspector.get_table_names()
#     print(f"📋 Existing tables before creation: {existing_tables}")

#     # Create tables if not present
#     db.create_all()
#     print("✅ Tables created successfully!")

#     # Ensure default SuperAdmin exists
#     if not SuperAdmin.query.first():
#         super_admin = SuperAdmin(
#             name="Super Admin",
#             email="super@callmanager.com"
#         )
#         super_admin.set_password("admin123")
#         db.session.add(super_admin)
#         db.session.commit()
#         print("✅ Default Super Admin created: super@callmanager.com / admin123")
#     else:
#         print("ℹ️ Super Admin already exists.")
# PYCODE

# echo "✅ Build completed successfully!"


#!/usr/bin/env bash
echo "🚀 Starting build process..."

# -------------------------
# 1️⃣ Install dependencies
# -------------------------
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
    exit 1
fi

# -------------------------
# 2️⃣ Create required frontend directories
# -------------------------
echo "🗂️ Ensuring frontend directories exist..."
mkdir -p frontend/super_admin/css frontend/super_admin/js frontend/super_admin/assets
mkdir -p frontend/admin/css frontend/admin/js frontend/admin/assets

# -------------------------
# 3️⃣ Initialize database and Super Admin
# -------------------------
echo "🛠️ Initializing database..."

python - <<'PYCODE'
from app import create_app
from app.models import db, SuperAdmin
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    try:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"📋 Existing tables before creation: {existing_tables}")

        db.create_all()
        print("✅ Database tables created successfully!")

        # Ensure default SuperAdmin exists
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
            print("ℹ️ Super Admin already exists. Skipping creation.")
    except Exception as e:
        print("❌ Database initialization failed:", e)
        exit(1)
PYCODE

# -------------------------
# 4️⃣ Finish
# -------------------------
echo "✅ Build completed successfully!"
