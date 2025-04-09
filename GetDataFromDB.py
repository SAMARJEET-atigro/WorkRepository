# import pyodbc

# def fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value):
#     # Connect to MSSQL (Azure SQL Server in this case)
#     conn = pyodbc.connect(
#         'DRIVER={ODBC Driver 17 for SQL Server};'
#         'SERVER=atigroai.database.windows.net;'
#         'DATABASE=' + dbname + ';'
#         'UID=logistic;'  # Your database username
#         'PWD=4$P)K0]Ti|Rv5n98'  # Your database password
#     )
#     cursor = conn.cursor()

#     # Check if the table exists in the schema info
#     if table_name not in schema_info:
#         print(f"Table {table_name} not found in schema information.")
#         return None

#     # Get the actual primary key column name from schema
#     primary_key_column = schema_info[table_name]['primary_key'][0]  # Assuming primary_key has one column

#     # Fetch the fields of the given table using the primary key
#     cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key_column} = ?", primary_key_value)
#     record = cursor.fetchone()
    
#     if not record:
#         print(f"No record found for {table_name} with primary key value {primary_key_value}.")
#         return None

#     # Convert record to dictionary
#     column_names = [column[0] for column in cursor.description]
#     record_dict = dict(zip(column_names, record))

#     # Process foreign keys based on schema
#     if table_name in schema_info:
#         for field, fk_relations in schema_info[table_name].get('foreign_keys', {}).items():
#             for fk_relation in fk_relations:
#                 related_table = fk_relation['table']
#                 related_column = fk_relation['foreign_column']
                
#                 # Fetch the related data using the foreign key value
#                 fk_value = record_dict.get(field)
#                 if fk_value:
#                     cursor.execute(f"SELECT * FROM {related_table} WHERE {related_column} = ?", fk_value)
#                     related_record = cursor.fetchone()
#                     if related_record:
#                         # Convert related record to dictionary
#                         related_record_dict = dict(zip([column[0] for column in cursor.description], related_record))
                        
#                         # Rename the key to match the specific format (e.g., Equipment_Related)
#                         related_key_name = f"{related_table}_Related"
#                         record_dict[related_key_name] = related_record_dict
#                     else:
#                         record_dict[f"{related_table}_Related"] = None

#     # Close the cursor and connection
#     cursor.close()
#     conn.close()

#     return record_dict


# # Example usage
# dbname = 'logistics_new'  # The database name
# table_name = 'WorkOrders'  # Example table
# primary_key_value = 1  # Example primary key value

# # Sample schema info as the one you provided earlier
# schema_info = {'WorkOrders': {'fields': {'WorkOrderID': {'type': 'int', 'default': None, 'nullable': False}, 'EquipmentID': {'type': 'int', 'default': None, 'nullable': True}, 'Status': {'type': 'nvarchar', 'default': None, 'nullable': True}, 'DateCreated': {'type': 'datetime', 'default': None, 'nullable': True}, 'DateClosed': {'type': 'datetime', 'default': None, 'nullable': True}, 'ClosingStateofEquipment': {'type': 'nvarchar', 'default': None, 'nullable': True}, 'SupervisingEmployeeID': {'type': 'int', 'default': None, 'nullable': True}}, 'primary_key': ['WorkOrderID'], 'foreign_keys': {'SupervisingEmployeeID': [{'table': 'WorkOrders', 'foreign_column': 'SupervisingEmployeeID', 'column': 'SupervisingEmployeeID'}], 'EquipmentID': [{'table': 'WorkOrders', 'foreign_column': 'EquipmentID', 'column': 'EquipmentID'}]}, 'constraints': {'unique': {}}}}

# record_with_fks = fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value)

# # Print the result
# if record_with_fks:
#     print(record_with_fks)
import pyodbc

def fetch_related_data(cursor, table_name, primary_key_column, primary_key_value):
    cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key_column} = ?", primary_key_value)
    related_record = cursor.fetchone()
    if related_record:
        column_names = [column[0] for column in cursor.description]
        related_record_dict = dict(zip(column_names, related_record))
        return related_record_dict
    return None

def fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value):
    # Connect to MSSQL (Azure SQL Server in this case)
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE=' + dbname + ';'
        'UID=logistic;'
        'PWD=4$P)K0]Ti|Rv5n98'
    )
    cursor = conn.cursor()

    # Check if the table exists in the schema info
    if table_name not in schema_info:
        print(f"Table {table_name} not found in schema information.")
        return None

    # Get the actual primary key column name from schema
    primary_key_column = schema_info[table_name]['primary_key'][0]  # Assuming primary_key has one column

    # Fetch the main record
    main_record = fetch_related_data(cursor, table_name, primary_key_column, primary_key_value)
    if not main_record:
        print(f"No record found for {table_name} with primary key value {primary_key_value}.")
        return None

    # Process foreign keys and related primary keys
    if 'foreign_keys' in schema_info[table_name]:
        for field, fk_relations in schema_info[table_name]['foreign_keys'].items():
            for fk_relation in fk_relations:
                related_table = fk_relation['table']
                related_column = fk_relation['foreign_column']
                fk_value = main_record.get(field)
                if fk_value:
                    related_record_dict = fetch_related_data(cursor, related_table, related_column, fk_value)
                    if related_record_dict:
                        main_record[f"{related_table}_Related"] = related_record_dict

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return main_record

# Example usage
dbname = 'logistics_new'  # The database name
table_name = 'WorkOrders'  # Example table
primary_key_value = 1  # Example primary key value

# Sample schema info
schema_info =  {'WorkOrders': {'fields': {'WorkOrderID': {'type': 'int', 'default': None, 'nullable': False}, 'EquipmentID': {'type': 'int', 'default': None, 'nullable': True}, 'Status': {'type': 'nvarchar', 'default': None, 'nullable': True}, 'DateCreated': {'type': 'datetime', 'default': None, 'nullable': True}, 'DateClosed': {'type': 'datetime', 'default': None, 'nullable': True}, 'ClosingStateofEquipment': {'type': 'nvarchar', 'default': None, 'nullable': True}, 'SupervisingEmployeeID': {'type': 'int', 'default': None, 'nullable': True}}, 'primary_key': ['WorkOrderID'], 'foreign_keys': {'SupervisingEmployeeID': [{'table': 'Employees', 'foreign_column': 'EmployeeID'}], 'EquipmentID': [{'table': 'EquipmentInventory', 'foreign_column': 'EquipmentID'}]}, 'constraints': {'unique': []}}}
record_with_fks = fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value)
if record_with_fks:
    print(record_with_fks)
