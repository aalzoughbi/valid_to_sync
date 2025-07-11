from ldap3 import Server, Connection, ALL, SIMPLE, Tls, MODIFY_REPLACE
from ldap3.utils.dn import parse_dn
import ssl
import re

tls_config = Tls(validate=ssl.CERT_OPTIONAL, version=ssl.PROTOCOL_TLSv1_2)
AD_SERVER = 'ANYACCESS.NET'
AD_USER = 'ANYACCESS\\aalzoughbi-t1'
AD_PASSWORD = 'A5$!zZ2*4L9%&()'

ACTIVE_USERS_OU = 'OU=Temp,OU=Users,OU=Nordenham,OU=Europe,DC=ANYACCESS,DC=NET'
DISABLED_USERS_OU = 'OU=Inactive Objects,OU=Nordenham,OU=Europe,DC=ANYACCESS,DC=NET'

def _connect_to_ad():
    print("[DEBUG] Connecting to AD server...")
    server = Server(AD_SERVER, use_ssl=True, get_info=ALL, tls=tls_config)
    conn = Connection(server, AD_USER, AD_PASSWORD, auto_bind=True, authentication=SIMPLE)
    print(f"[DEBUG] Connected and bound as {AD_USER}")
    return conn


def _extract_cn(dn):
    print(f"[DEBUG] Extracting CN from DN: {dn}")
    rdn_components = parse_dn(dn)
    for attr, value, _ in rdn_components:
        if attr.upper() == 'CN':
            print(f"[DEBUG] Extracted CN: {value}")
            return value
    raise ValueError(f"CN not found in DN: {dn}")

def _move_user(conn, dn, target_ou):
    try:
        print(f"[DEBUG] Moving user: {dn} to {target_ou}")
        cn = _extract_cn(dn)
        new_rdn = f"CN={cn}"
        conn.modify_dn(dn, new_rdn, new_superior=target_ou)
        print(f"[DEBUG] LDAP modify_dn result: {conn.result}")

        if conn.result['description'] != 'success':
            raise Exception(conn.result['message'])

        new_dn = f"{new_rdn},{target_ou}"
        print(f"[DEBUG] User moved successfully to {new_dn}")
        return new_dn
    except Exception as e:
        print(f"[ERROR] Error moving user: {e}")
        raise

def deactivate_user(dn):
    print(f"[DEBUG] Deactivating user: {dn}")
    conn = _connect_to_ad()
    try:
        print(f"[DEBUG] Disabling account for {dn}")
        conn.modify(dn, {'userAccountControl': [MODIFY_REPLACE, [514]]})  # 514 = disabled
        print(f"[DEBUG] LDAP modify result (disable): {conn.result}")
        if conn.result['description'] != 'success':
            raise Exception(f"Failed to disable: {conn.result}")

        print(f"[DEBUG] Moving user to Disabled OU")
        new_dn = _move_user(conn, dn, DISABLED_USERS_OU)
        return new_dn
    except Exception as e:
        print(f"[ERROR] Deactivation failed: {e}")
        raise
    finally:
        conn.unbind()
        print(f"[DEBUG] Connection unbound after deactivation")

def activate_user(dn):
    print(f"[DEBUG] Activating user: {dn}")
    conn = _connect_to_ad()
    try:
        print(f"[DEBUG] Moving user to Active OU")
        new_dn = _move_user(conn, dn, ACTIVE_USERS_OU)

        print(f"[DEBUG] Enabling account for {new_dn}")
        conn.modify(new_dn, {'userAccountControl': [MODIFY_REPLACE, [512]]})  # 512 = enabled
        print(f"[DEBUG] LDAP modify result (enable): {conn.result}")
        if conn.result['description'] != 'success':
            raise Exception(f"Failed to enable: {conn.result}")
        return new_dn
    except Exception as e:
        print(f"[ERROR] Activation failed: {e}")
        raise
    finally:
        conn.unbind()
        print(f"[DEBUG] Connection unbound after activation")
