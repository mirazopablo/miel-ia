import os
import sys
import subprocess

# Add project root to path so we can import 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from app.core.db import get_db_session
from app.infrastructure.repositories.role_repo import RoleRepo
from app.infrastructure.repositories.user_repo import UserRepo
from app.infrastructure.repositories.user_role_repo import UserRoleRepo
from app.services.role_service import RoleService
from app.services.user_service import UserService
from app.services.user_role_service import UserRoleService
from app.infrastructure.db.DTOs.user_dto import UserCreateInternal
from app.infrastructure.db.DTOs.user_role_dto import UserRoleCreateDTO


def init_project():
    print("========================================")
    print("   Project Initialization Wizard")
    print("========================================\n")
    
    # 1. Alembic
    print("--> Updating database schema...")
    try:
        # Siempre conviene hacer upgrade head primero por si hay migraciones pendientes
        subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=project_root)
        print("--> Database upgraded to head successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Alembic upgrade failed: {e}")
        print("Proceeding, but you might have database schema issues.\n")

    run_alembic = input("\nDo you want to create a NEW Alembic migration (autogenerate)? (y/n) [n]: ") or "n"
    if run_alembic.lower() == "y":
        msg = input("Alembic revision message [Initial revision]: ") or "Initial revision"
        print("\n--> Running Alembic autogenerate...")
        try:
            subprocess.run(["alembic", "revision", "--autogenerate", "-m", msg], check=True, cwd=project_root)
            subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=project_root)
            print("--> New migration created and applied successfully.\n")
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Alembic new migration failed: {e}")
            print("Proceeding with the rest of the initialization...\n")
    
    # 2. Open DB session
    print("--> Connecting to the database...")
    db_gen = get_db_session()
    db = next(db_gen)
    
    try:
        # Repositories
        role_repo = RoleRepo(db)
        user_repo = UserRepo(db)
        user_role_repo = UserRoleRepo(db)
        
        # Services
        role_service = RoleService(role_repo)
        user_service = UserService(user_repo)
        user_role_service = UserRoleService(user_role_repo, user_repo, role_repo)
        
        # 3. Roles
        print("\n--- Role Creation ---")
        
        roles = role_service.get_all_roles()
        if len(roles) >= 3:
            print("[INFO] 3 or more roles already exist. Skipping manual role creation.")
            role_admin = next((r for r in roles if r.name == "admin"), None)
            if not role_admin:
                raise Exception("The 'admin' role was not found among the existing roles.")
        else:
            print("The 'admin' role will be created automatically.")
            admin_role_name = "admin"
            
            try:
                role_admin = role_service.create_role(name=admin_role_name)
                print(f"Role '{admin_role_name}' created successfully.")
            except Exception as e:
                db.rollback()
                print(f"[INFO] Role '{admin_role_name}' might already exist. Attempting to fetch it...")
                roles = role_service.get_all_roles()
                role_admin = next((r for r in roles if r.name == admin_role_name), None)
                if not role_admin:
                    raise Exception(f"Failed to create or find '{admin_role_name}' role.")
                
            role2_name = input("\nEnter the name of the second role: ")
            try:
                role_service.create_role(name=role2_name)
            except Exception:
                db.rollback()
                print(f"[INFO] '{role2_name}' might already exist.")
            
            role3_name = input("Enter the name of the third role: ")
            try:
                role_service.create_role(name=role3_name)
            except Exception:
                db.rollback()
                print(f"[INFO] '{role3_name}' might already exist.")
        
        # 4. Admin User
        print("\n--- Admin User Creation ---")
        print("RECORDATORIO: ¡El NOMBRE y el APELLIDO son campos SEPARADOS!")
        print("  - Name: (ej. Pablo)")
        print("  - Last Name: (ej. Mirazo)")
        print("------------------------------------------------------------")
        admin_name = input("Name [admin]: ") or "admin"
        admin_last_name = input("Last Name [admin]: ") or "admin"
        admin_email = input("Email [admin@example.com]: ") or "admin@example.com"
        admin_dni = input("DNI [00000000]: ") or "00000000"
        admin_password = input("Password [admin123]: ") or "admin123"
        
        user_create = UserCreateInternal(
            name=admin_name,
            last_name=admin_last_name,
            email=admin_email,
            dni=admin_dni,
            password=admin_password
        )
        
        admin_user = user_service.create_user(db, user_create)
        print(f"--> Admin user '{admin_user.name}' created successfully.")
        
        # 5. Assign Role
        print("--> Assigning 'admin' role to the user...")
        user_role_dto = UserRoleCreateDTO(user_id=admin_user.id, role_id=role_admin.id)
        user_role_service.create_user_role(db, user_role_dto)
        print("--> Role assigned successfully.")
        
        # 6. Report
        print("\n========================================")
        print("   Initialization Complete")
        print("========================================")
        print("\nRoles (copy the UUIDs for frontend/environment use):")
        all_roles = role_service.get_all_roles()
        for idx, r in enumerate(all_roles, 1):
            print(f"  {idx}. {r.name:<15} : {r.id}")
            
        print("\nAdmin user details:")
        print(f"  Email: {admin_user.email}")
        print(f"  ID:    {admin_user.id}")
        print("========================================\n")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_project()
