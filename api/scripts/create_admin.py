import os
import sys
import uuid
import logging
# from getpass import getpass # No longer needed for non-interactive

# Adjust path to allow imports from the 'app' directory
# This assumes the script is run from /app/scripts/ inside the container
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base # Assuming Base might be needed if models are not yet created
from app.models.user import User, UserRole
from app.auth import get_password_hash # Use your existing password hashing

logger = logging.getLogger("create_admin")

def ensure_admin_user():
    logger.info("Ensuring initial admin user...")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_full_name = os.getenv("ADMIN_FULL_NAME")
    admin_github_id = os.getenv("ADMIN_GITHUB_ID")

    if not all([admin_email, admin_username, admin_password]):
        logger.error("Error: ADMIN_EMAIL, ADMIN_USERNAME, and ADMIN_PASSWORD environment variables must be set.")
        sys.exit(1) # Exit with error code if critical env vars are missing

    db = SessionLocal()
    try:
        # Check if user exists by email or username
        existing_user = db.query(User).filter((User.email == admin_email) | (User.username == admin_username)).first()

        if existing_user:
            logger.info(f"Admin user with email '{admin_email}' or username '{admin_username}' already exists.")
            updated = False
            if existing_user.role != UserRole.ADMIN:
                logger.info(f"Updating role for user '{existing_user.email}' to 'admin'.")
                existing_user.role = UserRole.ADMIN
                updated = True
            
            if admin_github_id and existing_user.github_id != admin_github_id:
                logger.info(f"Updating GitHub ID for user '{existing_user.email}'.")
                existing_user.github_id = admin_github_id
                updated = True

            if updated:
                db.commit()
                logger.info("User details updated.")
            else:
                logger.info("No changes made to existing admin user.")
            return # Exit if user exists

        # If user does not exist, create new one
        logger.info(f"Creating new admin user: Email='{admin_email}', Username='{admin_username}'")

        hashed_password = get_password_hash(admin_password)
        
        new_admin_user = User(
            id=uuid.uuid4(),
            email=admin_email,
            username=admin_username,
            full_name=admin_full_name if admin_full_name else None,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            github_id=admin_github_id,
            is_active=True
        )
        db.add(new_admin_user)
        db.commit()
        logger.info(f"Admin user '{admin_email}' / '{admin_username}' created successfully!")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
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