#!/usr/bin/env bash
echo "Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "
from app import create_app
from app.models import db
import os

app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
    
    # Create default super admin if not exists
    from app.models import SuperAdmin
    if not SuperAdmin.query.first():
        super_admin = SuperAdmin(
            name='Super Admin',
            email='super@callmanager.com'
        )
        super_admin.set_password('admin123')
        db.session.add(super_admin)
        db.session.commit()
        print('Default super admin created: super@callmanager.com / admin123')
"

echo "Build completed successfully!"