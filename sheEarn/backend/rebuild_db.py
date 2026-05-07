import os
from app import create_app, db
from seed import seed
from update_schemes import main as update_schemes

app = create_app("development")

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()

# Seed the initial users
seed()

# Update the government schemes
update_schemes()

print("\nDatabase completely rebuilt successfully!")
