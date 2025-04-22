import pyodbc
from collections import defaultdict
import json

def get_full_schema_info(conn):
    schema_info = {}

    with conn.cursor() as cursor:
        # Step 1: Get all table names
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        tables = [row.TABLE_NAME for row in cursor.fetchall()]

        for table_name in tables:
            schema_info[table_name] = {
                'fields': {},
                'primary_key': [],
                'foreign_keys': {},
                'constraints': {'unique': []}
            }

            # Step 2: Get fields for each table
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
            """, (table_name,))
            for col in cursor.fetchall():
                schema_info[table_name]['fields'][col.COLUMN_NAME] = {
                    'type': col.DATA_TYPE,
                    'default': col.COLUMN_DEFAULT,
                    'nullable': (col.IS_NULLABLE == 'YES')
                }

            # Step 3: Get primary keys
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = ? AND CONSTRAINT_NAME IN (
                    SELECT CONSTRAINT_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                    WHERE TABLE_NAME = ? AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                )
            """, (table_name, table_name))
            schema_info[table_name]['primary_key'] = [row.COLUMN_NAME for row in cursor.fetchall()]

            # Step 4: Get foreign keys
            cursor.execute("""
                SELECT kcu.COLUMN_NAME, ccu.TABLE_NAME AS REFERENCED_TABLE, ccu.COLUMN_NAME AS REFERENCED_COLUMN
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS rc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
                WHERE kcu.TABLE_NAME = ?
            """, (table_name,))
            for fk in cursor.fetchall():
                schema_info[table_name]['foreign_keys'].setdefault(fk.COLUMN_NAME, []).append({
                    'table': fk.REFERENCED_TABLE,
                    'foreign_column': fk.REFERENCED_COLUMN
                })

            # Step 5: Get unique constraints
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
                JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
                ON ccu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'UNIQUE' AND tc.TABLE_NAME = ?
            """, (table_name,))
            for row in cursor.fetchall():
                schema_info[table_name]['constraints']['unique'].append(row.COLUMN_NAME)

    return schema_info


# Connect and run
if __name__ == "__main__":
    db_name="WTBackend-logistic"
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE='+db_name+';'
        'UID=logistic;'
        'PWD=4$P)K0]Ti|Rv5n98'
    )
    
    schema = get_full_schema_info(conn)
    with open(f"D:/Python Scripts/WorkRepository/{db_name}_schema_info.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=4)
    print("Schema has been written to schema_info.json")
    conn.close()
