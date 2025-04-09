import pyodbc
import json
from datetime import datetime
from decimal import Decimal

def custom_serializer(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)  # Convert decimal instances to string
    raise TypeError(f"Type {type(obj)} not serializable")


def fetch_related_data(connection, table_name, column_name, column_value, visited=None, depth=0, max_depth=3):
    if visited is None:
        visited = set()

    if depth > max_depth or (table_name, column_name, column_value) in visited:
        return {}

    visited.add((table_name, column_name, column_value))

    cursor = connection.cursor()

    # Fetch the row corresponding to column_name and column_value from table_name
    cursor.execute(f"SELECT * FROM {table_name} WHERE {column_name} = ?", column_value)
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()

    if not row:
        return {}

    data_row = dict(zip(columns, row))

    # Look for primary and foreign key relationships for each column in this row
    related_data = {}
    for col, val in data_row.items():
        # Skip non-integer fields for foreign key checks
        if not isinstance(val, int):
            continue

        # Find all tables where this column is a primary key or foreign key
        cursor.execute(f"""
            SELECT fk.TABLE_NAME, fk.COLUMN_NAME, 'Child' AS Relation
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS fk ON fk.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            WHERE fk.COLUMN_NAME = '{col}'
            UNION
            SELECT pk.TABLE_NAME, pk.COLUMN_NAME, 'Parent'
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS pk ON pk.CONSTRAINT_NAME = rc.UNIQUE_CONSTRAINT_NAME
            WHERE pk.COLUMN_NAME = '{col}';
        """)

        for related_table, related_column, relation_type in cursor.fetchall():
            # Fetch related data recursively
            nested_data = fetch_related_data(connection, related_table, related_column, val, visited, depth+1, max_depth)
            if nested_data:
                related_data.setdefault(related_table, []).append(nested_data)

    return {**data_row, "related_data": related_data}

# Example usage
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=atigroai.database.windows.net;DATABASE=logistics_new;UID=logistic;PWD=4$P)K0]Ti|Rv5n98')
result = fetch_related_data(conn, 'WorkOrders', 'WorkOrderID', 17)
print(json.dumps(result, indent=4, default=custom_serializer))
conn.close()