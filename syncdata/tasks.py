from datetime import datetime
from celery import shared_task
from django.db import connections
from .models import SyncedRecord
from config.celery import app
from utils.ad_lookup import find_ad_user

def parse_int_date(date_int):
    return datetime.strptime(str(date_int), '%Y%m%d').date()

@app.task
def sync_valid_to():

    today = datetime.today().date()
    # today = datetime(2025, 6, 26).date()

    with connections['mssql'].cursor() as cursor:
        cursor.execute('''
            WITH RANKED_PERSON AS (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY [PERSON_ID] ORDER BY [VALID_TO] DESC) AS rn
                FROM [tisoware].[dbo].[V_EN_PERSON]
            ),
            ROW_PER_PERSON AS (
                SELECT * FROM RANKED_PERSON
                WHERE rn = 1
            ),
            NORMALIZED AS (
                SELECT *,
                    REPLACE(LOWER([LAST_NAME]), 'é', 'e') AS NORMALIZED_LAST_NAME,
                    REPLACE(LOWER([FIRST_NAME]), 'é', 'e') AS NORMALIZED_FIRST_NAME
                FROM ROW_PER_PERSON
                ),
            RANKED AS (
                SELECT *, 
                    ROW_NUMBER() OVER (PARTITION BY NORMALIZED_FIRST_NAME, NORMALIZED_LAST_NAME ORDER BY [VALID_TO] DESC) AS rn2
                FROM NORMALIZED
            )
            SELECT [FIRST_NAME], [LAST_NAME], [VALID_TO] 
            FROM RANKED 
            WHERE rn2 = 1 AND CAST(CONVERT(VARCHAR(8), [VALID_TO]) AS DATE) < CAST(GETDATE() AS DATE) AND FIRST_NAME = 'Amer'
            
        ''')
        rows = cursor.fetchall()

        for row in rows:
            first_name, last_name, valid_to_int = row
            valid_to_date = parse_int_date(valid_to_int)

            if valid_to_date < today:
                record, created = SyncedRecord.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    valid_to=valid_to_date,

                )

                ad_user = find_ad_user(last_name, first_name)
                if ad_user:
                    record.ad_display_name = ad_user['display_name']
                    record.ad_samaccountname = ad_user['sAMAccountName']
                    record.ad_enabled = ad_user['enabled']
                    record.distinguished_name = ad_user['distinguishedName']
                    record.save()
