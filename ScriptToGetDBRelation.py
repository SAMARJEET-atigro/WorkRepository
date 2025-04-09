import pyodbc
import json

def fetch_metadata(server, database, username, password):
    # Connection string
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    # Establish connection
    conn = pyodbc.connect(conn_str)
    
    # Query to get table and column details from the information schema
    query = """
    SELECT 
        TABLE_NAME, 
        COLUMN_NAME, 
        DATA_TYPE, 
        IS_NULLABLE, 
        CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """
    
    # Execute query
    cursor = conn.cursor()
    cursor.execute(query)
    
    # Construct metadata dictionary
    metadata = {}
    for row in cursor.fetchall():
        table_name = row.TABLE_NAME
        column_details = {
            "COLUMN_NAME": row.COLUMN_NAME,
            "DATA_TYPE": row.DATA_TYPE,
            "IS_NULLABLE": row.IS_NULLABLE,
            "MAX_LENGTH": row.CHARACTER_MAXIMUM_LENGTH
        }
        
        if table_name not in metadata:
            metadata[table_name] = {
                "table_description": f"Description of {table_name}",
                "columns": []
            }
        
        metadata[table_name]["columns"].append(column_details)
    
    # Close connection
    conn.close()
    
    return metadata

# Database credentials
server = 'atigroai.database.windows.net'
database = 'logistics_new'
username = 'logistic'
password = '4$P)K0]Ti|Rv5n98'

# Fetch metadata
db_metadata = fetch_metadata(server, database, username, password)

# Convert to JSON
json_output = json.dumps(db_metadata, indent=4)

# Print or save the JSON
#print(json_output)
with open('D:/DBMap.json', 'w') as f:
    f.write(json_output)
print("DBMap.json file created successfully.")
