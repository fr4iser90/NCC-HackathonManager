import os
import sys
import uuid
# from getpass import getpass # No longer needed for non-interactive

# Adjust path to allow imports from the 'app' directory
# This assumes the script is run from /app/scripts/ inside the container
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base # Assuming Base might be needed if models are not yet created
from app.models.user import User
from app.auth import get_password_hash # Use your existing password hashing

def ensure_admin_user():
    print("Ensuring initial admin user...")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_full_name = os.getenv("ADMIN_FULL_NAME") # Optional

    if not all([admin_email, admin_username, admin_password]):
        print("Error: ADMIN_EMAIL, ADMIN_USERNAME, and ADMIN_PASSWORD environment variables must be set.")
        sys.exit(1) # Exit with error code if critical env vars are missing

    db = SessionLocal()
    try:
        # Check if user exists by email or username
        existing_user = db.query(User).filter((User.email == admin_email) | (User.username == admin_username)).first()

        if existing_user:
            print(f"Admin user with email '{admin_email}' or username '{admin_username}' already exists.")
            updated = False
            if existing_user.role != "admin":
                print(f"Updating role for user '{existing_user.email}' to 'admin'.")
                existing_user.role = "admin"
                updated = True
            
            # Optionally, update password if a specific env var is set, e.g., ADMIN_FORCE_PASSWORD_UPDATE=true
            # For simplicity, we are not doing that here, just ensuring the role.
            # If you want to update the password, you'd add logic similar to the old script
            # but triggered by an environment variable.

            if updated:
                db.commit()
                print("User details updated.")
            else:
                print("No changes made to existing admin user.")
            return # Exit if user exists

        # If user does not exist, create new one
        print(f"Creating new admin user: Email='{admin_email}', Username='{admin_username}'")

        hashed_password = get_password_hash(admin_password)
        
        new_admin_user = User(
            id=uuid.uuid4(),
            email=admin_email,
            username=admin_username,
            full_name=admin_full_name if admin_full_name else None,
            hashed_password=hashed_password,
            role="admin"
        )
        db.add(new_admin_user)
        db.commit()
        print(f"Admin user '{admin_email}' / '{admin_username}' created successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        sys.exit(1) # Exit with error code on failure
    finally:
        db.close()

if __name__ == "__main__":
    # Optional: Create tables if they don't exist. 
    # This is often handled by Alembic migrations or at application startup.
    # If your User model (and others) are defined using Base.metadata, 
    # you might want to ensure tables are created before trying to add data.
    # For example:
    # print("Ensuring database tables are created (if not already by Alembic/app startup)...")
    # Base.metadata.create_all(bind=engine) 
    # print("Table check/creation complete.")

    ensure_admin_user() 