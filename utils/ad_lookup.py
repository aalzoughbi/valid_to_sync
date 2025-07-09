from ldap3 import Server, Connection, ALL, SIMPLE, Tls, SUBTREE
from ldap3.utils.conv import escape_filter_chars
import ssl

def normalize_name(name):
    if not name:
        return ''
    return (
        name.strip().lower()
            .replace('ä', 'ae')
            .replace('ö', 'oe')
            .replace('ü', 'ue')
            .replace('ß', 'ss')
            .replace('é', 'e')
    )

def is_user_enabled(user_account_control: int) -> bool:
    return not (user_account_control & 0x2)

def find_ad_user(last_name, first_name):
    raw_sn = escape_filter_chars(last_name)
    norm_sn = escape_filter_chars(normalize_name(last_name))

    raw_gn = escape_filter_chars(first_name)
    norm_gn = escape_filter_chars(normalize_name(first_name))

    tls_config = Tls(validate=ssl.CERT_OPTIONAL, version=ssl.PROTOCOL_TLSv1_2)
    server = Server('ANYACCESS.NET', use_ssl=True, get_info=ALL, tls=tls_config)
    conn = Connection(
        server,
        user='ANYACCESS\\aalzoughbi-t1',
        password='A5$!zZ2*4L9%&()',
        authentication=SIMPLE,
        auto_bind=True
    )

    search_base = 'OU=Nordenham,OU=Europe,DC=ANYACCESS,DC=NET'
    #search_filter = '(sn=*)'
    search_filter = f'''(&
        (objectCategory=person)
        (objectClass=user)
        (|
            (sn={raw_sn})
            (sn={norm_sn})
        )
        (|
            (givenName={raw_gn})
            (givenName={norm_gn})
        )
    )'''
    attributes = ['displayName', 'sAMAccountName', 'givenName', 'sn', 'userAccountControl',]

    normalized_sn = normalize_name(last_name)
    normalized_gn = normalize_name(first_name)

    # Initial paged search
    conn.search(
        search_base=search_base,
        search_filter=search_filter,
        search_scope=SUBTREE,
        attributes=attributes,
        paged_size=1000
    )

    while True:
        for entry in conn.entries:
            ad_sn_raw = getattr(entry, 'sn', None)
            ad_gn_raw = getattr(entry, 'givenName', None)

            if not ad_sn_raw or not ad_gn_raw:
                continue  # skip if names are missing

            ad_sn = normalize_name(ad_sn_raw.value)
            ad_gn = normalize_name(ad_gn_raw.value)

            # Log for debugging
            print(f"Comparing DB: {normalized_gn} {normalized_sn} <--> AD: {ad_gn} {ad_sn} <--> {entry.userAccountControl} - {entry.userAccountControl.value}")

            if normalized_sn in ad_sn and normalized_gn in ad_gn:
                enabled = is_user_enabled(int(entry.userAccountControl.value))
                return {
                    'display_name': getattr(entry, 'displayName', None).value if getattr(entry, 'displayName', None) else '',
                    'sAMAccountName': getattr(entry, 'sAMAccountName', None).value if getattr(entry, 'sAMAccountName', None) else '',
                    'enabled': enabled
                }

        # Handle paging
        cookie = conn.result.get('controls', {}).get('1.2.840.113556.1.4.319', {}).get('value', {}).get('cookie')
        if cookie:
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                paged_size=1000,
                paged_cookie=cookie
            )
        else:
            break

    return None
