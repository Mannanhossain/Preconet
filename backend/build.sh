#!/usr/bin/env bash
echo "🚀 Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Initialize and migrate database
python -c "
from app import create_app
from app.models import db, SuperAdmin
from flask_migrate import upgrade

app = create_app()
with app.app_context():
    print('⚙️ Running database migrations...')
    upgrade()

    print('✅ Checking SuperAdmin...')
    if not SuperAdmin.query.first():
        super_admin = SuperAdmin(
            name='Super Admin',
            email='super@callmanager.com'
        )
        super_admin.set_password('admin123')
        db.session.add(super_admin)
        db.session.commit()
        print('✅ Default super admin created: super@callmanager.com / admin123')
    else:
        print('ℹ️ Super admin already exists.')
"

echo "✅ Build completed successfully!"
