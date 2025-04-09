


import pyodbc

def get_schema(dbname, primary_tables, secondary_tables):
    # Establish connection to MSSQL
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'  # Update with your SQL Server host
        'DATABASE=' + dbname + ';'
        'UID=logistic;'  # Update with your SQL Server username
        'PWD=4$P)K0]Ti|Rv5n98'  # Update with your SQL Server password

    )

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Initialize the schema dictionary to store the result
    schemas = {}

    # Function to process tables
    def process_table(table_name, processed_tables):
        if table_name in processed_tables:
            return  # Skip if already processed
        processed_tables.add(table_name)

        schemas[table_name] = {"fields": {}, "primary_key": [], "foreign_keys": {}, "constraints": {}}

        # Columns and their types
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}';
        """)
        columns = cursor.fetchall()
        for column in columns:
            schemas[table_name]["fields"][column[0]] = {
                "type": column[1],
                "default": column[2],
                "nullable": column[3] == 'YES'
            }

        # Primary keys
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = '{table_name}' AND CONSTRAINT_NAME IN (
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_NAME = '{table_name}' AND CONSTRAINT_TYPE = 'PRIMARY KEY'
            );
        """)
        primary_keys = cursor.fetchall()
        if primary_keys:
            schemas[table_name]["primary_key"] = [pk[0] for pk in primary_keys]

        # Foreign keys
        cursor.execute(f"""
            SELECT kcu.COLUMN_NAME, ccu.TABLE_NAME AS foreign_table, ccu.COLUMN_NAME AS foreign_column
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rcc
            ON kcu.CONSTRAINT_NAME = rcc.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON rcc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            WHERE kcu.TABLE_NAME = '{table_name}' AND kcu.CONSTRAINT_NAME IN (
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_NAME = '{table_name}' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
            );
        """)
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            for fk in foreign_keys:
                # Forward flow: add the foreign table schema (if not already processed)
                if fk[1] not in schemas:
                    process_table(fk[1], processed_tables)

                # Record the foreign key relationship
                if fk[1] not in schemas[table_name]["foreign_keys"]:
                    schemas[table_name]["foreign_keys"][fk[0]] = []
                schemas[table_name]["foreign_keys"][fk[0]].append({
                    "table": fk[1],
                    "foreign_column": fk[2]
                })

        # Constraints (Unique, Check, etc.), excluding PK & FK which are handled separately
        cursor.execute(f"""
            SELECT CONSTRAINT_TYPE, COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_NAME = '{table_name}' AND tc.CONSTRAINT_TYPE != 'PRIMARY KEY' AND tc.CONSTRAINT_TYPE != 'FOREIGN KEY'
        """)
        constraints = cursor.fetchall()
        if constraints:
            for constraint in constraints:
                if constraint[0] not in schemas[table_name]["constraints"]:
                    schemas[table_name]["constraints"][constraint[0]] = []
                schemas[table_name]["constraints"][constraint[0]].append(constraint[1])

    # Set of processed tables to avoid duplicate work
    processed_tables = set()

    # Process primary tables first
    for table_name in primary_tables:
        process_table(table_name, processed_tables)

    # Process secondary tables, ensuring both forward and backward foreign key relationships
    for table_name in secondary_tables:
        process_table(table_name, processed_tables)

    # Close the connection
    cursor.close()
    conn.close()

    return schemas


# Example usage
database = 'logistics_new'
primary_tables = ["WorkOrders"]  # Primary tables
secondary_tables = []  # Secondary tables (could be FK-related)
schema = get_schema(database, primary_tables, secondary_tables)

# Output the result
print(schema)

