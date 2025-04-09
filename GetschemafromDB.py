import pyodbc
def fetch_schema_info_for_table(dbname, table_name):
    # Define the connection string using secure method to handle credentials
    connection_string = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE=' + dbname + ';'
        'UID=logistic;'  # Adjust these details according to your security practices
        'PWD=4$P)K0]Ti|Rv5n98'
    )
    # Connect to the database
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    schema_info = {
        table_name: {
            'fields': {},
            'primary_key': [],
            'foreign_keys': {},
            'constraints': {'unique': []}
        }
    }

    # Fetch column details
    cursor.execute("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = ?
    """, (table_name,))
    for column in cursor.fetchall():
        schema_info[table_name]['fields'][column.column_name] = {
            'type': column.data_type,
            'default': column.column_default,
            'nullable': column.is_nullable == 'YES'
        }

    # Fetch primary keys
    cursor.execute("""
        SELECT column_name
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE table_name = ? AND constraint_name IN (
            SELECT constraint_name
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE table_name = ? AND constraint_type = 'PRIMARY KEY'
        )
    """, (table_name, table_name))
    for row in cursor.fetchall():
        schema_info[table_name]['primary_key'].append(row.column_name)

    # Fetch foreign keys
    cursor.execute("""
        SELECT kcu.column_name, ccu.table_name AS referenced_table, ccu.column_name AS referenced_column
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS kcu
        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS rc
            ON kcu.constraint_name = rc.constraint_name
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
            ON rc.unique_constraint_name = ccu.constraint_name
        WHERE kcu.table_name = ?
    """, (table_name,))
    for fk in cursor.fetchall():
        if fk.column_name not in schema_info[table_name]['foreign_keys']:
            schema_info[table_name]['foreign_keys'][fk.column_name] = []
        schema_info[table_name]['foreign_keys'][fk.column_name].append({
            'table': fk.referenced_table,
            'foreign_column': fk.referenced_column
        })

    # Fetch unique constraints
    cursor.execute("""
        SELECT column_name
        FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
        JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'UNIQUE' AND tc.table_name = ?
    """, (table_name,))
    for row in cursor.fetchall():
        schema_info[table_name]['constraints']['unique'].append(row.column_name)

    cursor.close()
    conn.close()
    return schema_info

# Example usage
dbname = 'logistics_new'
table_name = 'WorkOrders'  # Pass the table name as an argument
schema_info = fetch_schema_info_for_table(dbname, table_name)
print(schema_info)