import pyodbc
import json
from datetime import datetime

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()

def fetch_table_relationships(conn, table_name):
    query = f"""
    SELECT 
        fk.name AS FK_name,
        tp.name AS parent_table,
        tr.name AS referenced_table,
        cp.name AS parent_column,
        cr.name AS referenced_column
    FROM 
        sys.foreign_keys AS fk
    INNER JOIN 
        sys.tables AS tp ON fk.parent_object_id = tp.object_id
    INNER JOIN 
        sys.tables AS tr ON fk.referenced_object_id = tr.object_id
    INNER JOIN 
        sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
    INNER JOIN 
        sys.columns AS cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
    INNER JOIN 
        sys.columns AS cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
    WHERE 
        tp.name = '{table_name}'
    """
    cursor = conn.cursor()
    cursor.execute(query)
    relationships = []
    for row in cursor.fetchall():
        relationships.append({
            "foreign_key_name": row.FK_name,
            "parent_table": row.parent_table,
            "referenced_table": row.referenced_table,
            "parent_column": row.parent_column,
            "referenced_column": row.referenced_column
        })
    return relationships

def fetch_related_data(conn, table_name, relationships):
    data = {}
    cursor = conn.cursor()
    for rel in relationships:
        query = f"SELECT * FROM {rel['referenced_table']}"
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        related_data = [dict(zip(columns, [datetime_converter(val) if isinstance(val, datetime) else val for val in row])) for row in cursor.fetchall()]
        data[rel['referenced_table']] = related_data
    return data

def main():
    server = 'atigroai.database.windows.net'
    database = 'logistics_new'
    username = 'logistic'
    password = '4$P)K0]Ti|Rv5n98'
    table_name = "WorkOrders"  # Example table

    # Connection string
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    # Establish connection
    conn = pyodbc.connect(conn_str)

    # Fetch relationships
    relationships = fetch_table_relationships(conn, table_name)

    # Fetch data based on relationships
    related_data = fetch_related_data(conn, table_name, relationships)

    # Optionally include data from the main table as well
    query = f"SELECT * FROM {table_name}"
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    main_data = [dict(zip(columns, [datetime_converter(val) if isinstance(val, datetime) else val for val in row])) for row in cursor.fetchall()]

    # Combine data
    combined_data = {
        "main_table": table_name,
        "main_data": main_data,
        "related_data": related_data
    }

    # Serialize to JSON
    json_output = json.dumps(combined_data, indent=4, default=datetime_converter)

    # Optionally: Save to a file or print it out
    print(json_output)
    with open(f'D:/{table_name}_data.json', 'w') as f:
        f.write(json_output)
    print(f"Data for {table_name} and its relationships saved to D:/{table_name}_data.json")

    # Closing the connection
    conn.close()

if __name__ == "__main__":
    main()


# #import psycopg2
# import pyodbc


# # Connect to your PostgreSQL database using credentials from Django's settings
# server = 'atigroai.database.windows.net'
# database = 'logistics_new'
# username = 'logistic'
# password = '4$P)K0]Ti|Rv5n98'

# conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
# conn = pyodbc.connect(conn_str)
# # conn = psycopg2.connect(
# #     server = 'atigroai.database.windows',
# #     username = 'logistic',
# #     password = '4$P)K0]Ti|Rv5n98',
# #     table_name = "WorkOrders" 
# # )

# # Create a cursor object to interact with the database
# cursor = conn.cursor()

# # Get list of tables
# cursor.execute("""
#     SELECT table_name
#     FROM information_schema.tables
#     WHERE table_schema = 'public';
# """)
# tables = cursor.fetchall()
# print("Tables:", tables)

# # Get schema for each table (columns, types, primary keys, foreign keys, etc.)
# for table in tables:
#     table_name = table[0]
#     print(f"\nSchema for {table_name}:")

#     # Columns and their types
#     cursor.execute(f"""
#         SELECT column_name, data_type, column_default, is_nullable
#         FROM information_schema.columns
#         WHERE table_name = '{table_name}';
#     """)
#     columns = cursor.fetchall()
#     for column in columns:
#         print(f"  {column[0]} ({column[1]}) - Default: {column[2]} - Nullable: {column[3]}")

#     # Primary keys
#     cursor.execute(f"""
#         SELECT column_name
#         FROM information_schema.key_column_usage
#         WHERE table_name = '{table_name}' AND constraint_name IN (
#             SELECT constraint_name
#             FROM information_schema.table_constraints
#             WHERE table_name = '{table_name}' AND constraint_type = 'PRIMARY KEY'
#         );
#     """)
#     primary_keys = cursor.fetchall()
#     if primary_keys:
#         print("  Primary Key(s):", [pk[0] for pk in primary_keys])

#     # Foreign keys
#     cursor.execute(f"""
#         SELECT kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
#         FROM information_schema.key_column_usage kcu
#         JOIN information_schema.constraint_column_usage ccu
#         ON kcu.constraint_name = ccu.constraint_name
#         WHERE kcu.table_name = '{table_name}' AND kcu.constraint_name IN (
#             SELECT constraint_name
#             FROM information_schema.table_constraints
#             WHERE table_name = '{table_name}' AND constraint_type = 'FOREIGN KEY'
#         );
#     """)
#     foreign_keys = cursor.fetchall()
#     if foreign_keys:
#         print("  Foreign Key(s):")
#         for fk in foreign_keys:
#             print(f"    {fk[0]} -> {fk[1]}.{fk[2]}")

#     # Constraints (Unique, Check, etc.)
#     cursor.execute(f"""
#         SELECT constraint_type, column_name
#         FROM information_schema.table_constraints tc
#         JOIN information_schema.key_column_usage kcu
#         ON tc.constraint_name = kcu.constraint_name
#         WHERE tc.table_name = '{table_name}'
#     """)
#     constraints = cursor.fetchall()
#     if constraints:
#         print("  Constraints:")
#         for constraint in constraints:
#             print(f"    {constraint[0]} on {constraint[1]}")

# # Close the connection
# cursor.close()
# conn.close()
