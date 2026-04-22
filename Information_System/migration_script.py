# Information_System/migration_script.py
import os
import django
from django.utils import timezone
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from Information_System.models import User
from Information_System.admin_models import Admin, AdminAuthorization, AdminLoginHistory

def migrate_admins():
    print("=" * 60)
    print("MIGRATING ADMIN USERS TO NEW ADMIN MODEL")
    print("=" * 60)
    
    admin_users = User.objects.filter(
        Q(user_type__in=['admin', 'faculty', 'program_chair'])
    ).distinct()
    
    print(f"Found {admin_users.count()} admin/faculty users to migrate.")
    
    migrated_count = 0
    skipped_count = 0
    
    for old_user in admin_users:
        try:
            if Admin.objects.filter(username=old_user.username).exists():
                print(f"Skipping {old_user.username} - already exists")
                skipped_count += 1
                continue
            
            # Role mapping: program_chair = super_admin, admin = admin, faculty = faculty
            if old_user.user_type == 'program_chair':
                role = 'super_admin'
            elif old_user.user_type == 'admin':
                role = 'admin'
            elif old_user.user_type == 'faculty':
                role = 'faculty'
            else:
                role = 'admin'
            
            new_admin = Admin.objects.create(
                username=old_user.username,
                email=old_user.email,
                password_hash=old_user.password,
                first_name=old_user.first_name,
                last_name=old_user.last_name,
                profile_picture=old_user.profile_picture,
                phone_number=old_user.phone_number,
                role=role,
                is_active=old_user.is_active,
                last_login=old_user.last_login,
                date_joined=old_user.date_joined,
                last_login_ip=old_user.last_login_ip,
                department=getattr(old_user, 'department', ''),
                auth_code=getattr(old_user, 'admin_authorization_code', '')
            )
            
            if old_user.approved_by:
                try:
                    approver = Admin.objects.get(username=old_user.approved_by.username)
                    new_admin.approved_by = approver
                    new_admin.save()
                except Admin.DoesNotExist:
                    pass
            
            print(f"Migrated: {old_user.username} -> {role}")
            migrated_count += 1
            
        except Exception as e:
            print(f"Error migrating {old_user.username}: {e}")
    
    print("=" * 60)
    print(f"SUMMARY: {migrated_count} migrated, {skipped_count} skipped")
    print("=" + "=" * 60)

def migrate_admin_auth_codes():
    print("\n" + "=" * 60)
    print("MIGRATING ADMIN AUTHORIZATION CODES")
    print("=" * 60)
    
    try:
        from Information_System.models import AdminAuthorization as OldAdminAuth
        old_auth_codes = OldAdminAuth.objects.all()
        print(f"Found {old_auth_codes.count()} authorization codes to migrate.")
        
        migrated = 0
        for old_auth in old_auth_codes:
            try:
                if AdminAuthorization.objects.filter(code=old_auth.code).exists():
                    print(f"Code {old_auth.code} already exists")
                    continue
                
                created_by = None
                if old_auth.created_by:
                    try:
                        created_by = Admin.objects.get(username=old_auth.created_by.username)
                    except Admin.DoesNotExist:
                        pass
                
                used_by = None
                if old_auth.used_by:
                    try:
                        used_by = Admin.objects.get(username=old_auth.used_by.username)
                    except Admin.DoesNotExist:
                        pass
                
                new_auth = AdminAuthorization.objects.create(
                    code=old_auth.code,
                    description=old_auth.description,
                    created_by=created_by,
                    created_at=old_auth.created_at,
                    expires_at=old_auth.expires_at,
                    is_used=old_auth.is_used,
                    used_by=used_by,
                    used_at=old_auth.used_at
                )
                print(f"Migrated auth code: {old_auth.code}")
                migrated += 1
                
            except Exception as e:
                print(f"Error migrating auth code {old_auth.code}: {e}")
        
        print(f"SUMMARY: {migrated} auth codes migrated")
        
    except Exception as e:
        print(f"No old AdminAuthorization model found: {e}")

def migrate_login_history():
    print("\n" + "=" * 60)
    print("MIGRATING LOGIN HISTORY")
    print("=" * 60)
    
    try:
        from Information_System.models import LoginHistory as OldLoginHistory
        old_logins = OldLoginHistory.objects.all()
        print(f"Found {old_logins.count()} login records to migrate.")
        
        migrated = 0
        for old_login in old_logins:
            try:
                if AdminLoginHistory.objects.filter(
                    login_time=old_login.login_time,
                    ip_address=old_login.ip_address
                ).exists():
                    continue
                
                admin = None
                if old_login.user:
                    try:
                        admin = Admin.objects.get(username=old_login.user.username)
                    except Admin.DoesNotExist:
                        pass
                
                if admin:
                    AdminLoginHistory.objects.create(
                        admin=admin,
                        login_time=old_login.login_time,
                        ip_address=old_login.ip_address,
                        user_agent=old_login.user_agent,
                        login_successful=old_login.login_successful
                    )
                    migrated += 1
                
            except Exception as e:
                print(f"Error migrating login record: {e}")
        
        print(f"Migrated {migrated} login records")
        
    except Exception as e:
        print(f"No old LoginHistory model found: {e}")

if __name__ == '__main__':
    migrate_admins()
    migrate_admin_auth_codes()
    migrate_login_history()
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify that all admin users were migrated")
    print("2. Test login with existing admin credentials")
    print("3. If everything works, you can safely delete the old User model")