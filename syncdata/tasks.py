from datetime import datetime
from celery import shared_task
from django.db import connections
from .models import SyncedRecord
from config.celery import app

def parse_int_date(date_int):
    return datetime.strptime(str(date_int), '%Y%m%d').date()

@app.task
def sync_valid_to():

    today = datetime.today().date()
    #today = datetime(2025, 6, 30).date()

    with connections['mssql'].cursor() as cursor:
        cursor.execute('''
        SELECT [FIRST_NAME]
      ,[LAST_NAME]
      ,[VALID_TO]
FROM (
    SELECT [FIRST_NAME]
      ,[LAST_NAME]
      ,[VALID_TO],
          ROW_NUMBER() OVER (PARTITION BY [FIRST_NAME], [LAST_NAME] ORDER BY [PERSON_ID]) as rn
    FROM [tisoware].[dbo].[V_EN_PERSON]
) t
WHERE rn = 1 AND CAST(CONVERT(VARCHAR(8), VALID_TO) AS DATE) < CAST(GETDATE() AS DATE)''')
        rows = cursor.fetchall()

        for row in rows:
            first_name, last_name, valid_to_int = row
            valid_to_date = parse_int_date(valid_to_int)

            if valid_to_date < today:
                SyncedRecord.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    valid_to=valid_to_date,
                )