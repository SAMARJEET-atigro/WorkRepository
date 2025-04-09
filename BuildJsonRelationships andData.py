# ####################################### Sample User Data Object Structure #######################################

user_data = {
    "users": [
        {"user_id": 1, "user_name": "John Doe", "user_phone": "123-456-7890", "user_role": "Manager"},
        {"user_id": 2, "user_name": "Jane Smith", "user_phone": "098-765-4321", "user_role": "Technician"}
    ]
}

# ######################################## Sample Business Rules for Work Orders #######################################
business_rules = {
    "Work Order": {
        "Object Description": "Details about a Work Order, including origination and context specific to the business.",
        "Object Business Rules": """
        1. Work Order ID must be unique.
        2. Status progresses from Open, to In Progress, to Completed, or occasionally Canceled.
        3. Creation only by a Work Order Manager; status changes need Manager approval.
        4. Viewable by any user, modifiable only by the manager or assigned user.
        5. Cannot be canceled once completed.
        6. Status cannot change to Completed until all tasks are completed or canceled.
        """
    }
}
import pyodbc
import json
from datetime import datetime

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()

def fetch_metadata(conn):
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
    cursor = conn.cursor()
    cursor.execute(query)
    metadata = {}
    for row in cursor.fetchall():
        table_name = row.TABLE_NAME
        column_details = {
            "COLUMN_NAME": row.COLUMN_NAME,
            "DATA_TYPE": row.DATA_TYPE,
            "IS_NULLABLE": row.IS_NULLABLE == 'YES',
            "MAX_LENGTH": row.CHARACTER_MAXIMUM_LENGTH
        }
        if table_name not in metadata:
            metadata[table_name] = {
                "table_description": f"Description of {table_name}",
                "columns": []
            }
        metadata[table_name]["columns"].append(column_details)
    return metadata

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


def fetch_table_data(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, [datetime_converter(val) if isinstance(val, datetime) else val for val in row])) for row in cursor.fetchall()]
    return data

def main():
    try:

        server = 'atigroai.database.windows.net'
        database = 'logistics_new'
        username = 'logistic'
        password = '4$P)K0]Ti|Rv5n98'
        table_name = "WorkOrders" 

        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        conn = pyodbc.connect(conn_str)

        try:

            all_metadata = fetch_metadata(conn)
            relationships = fetch_table_relationships(conn, table_name)
            if not relationships:
                print("No relationships found for the table.")
                if table_name == "WorkOrders":
                    relationships = {
                    "table_description": "The WorkOrders table tracks all work orders within the system, detailing their management, progress, and resolution.",
                    "fields": {
                        "WorkOrderID": {
                            "description": "Unique identifier for each work order.",
                            "type": "integer",
                            "primary_key": True
                        },
                        "EquipmentID": {
                            "description": "Identifier for equipment associated with the work order.",
                            "type": "integer",
                            "lookup_table": "EquipmentInventory",
                            "lookup_table_id_field": "EquipmentID",
                        },
                        "Status": {
                            "description": "Current status of the work order, which could be Open, Closed, or Canceled.",
                            "type": "string",
                            "valid_values": ["Open", "Closed", "Canceled"]
                        },
                        "DateCreated": {
                            "description": "Date and time when the work order was created.",
                            "type": "datetime"
                        },
                        "DateClosed": {
                            "description": "Date and time when the work order was closed or canceled, if applicable.",
                            "type": "datetime",
                            "nullable": True
                        },
                        "ClosingStateofEquipment": {
                            "description": "Describes the state of the equipment at the time the work order was closed.",
                            "type": "string",
                            "nullable": True
                        },
                        "SupervisingEmployeeID": {
                            "description": "Identifier for the employee supervising the work order.",
                            "type": "integer",
                            "lookup_table": "Employees",
                            "lookup_table_id_field": "EmployeeID",
                            "lookup_table_description_field": "EmployeeFirstName"  
                        }
                    }}
                elif table_name == "ServiceOrderTickets":
                    relationships =  {
                        "table_description": "The ServiceOrderTickets table contains information related to service orders.",
                        "fields": {
                            "ServiceOrderID": {
                                "description": "ServiceOrderID column stores a unique identifier for each service order.",
                                "type": "integer",
                                "primary_key": True
                            },
                            "ServiceOrderTypeID": {
                                "description": "ServiceOrderTypeID represents the type of service order.",
                                "type": "integer",
                                "lookup_table": "ServiceOrderTypes",
                                "lookup_table_id_field": "ServiceOrderTypeID",
                                "lookup_table_description_field": "Description"
                            },
                            "Status": {
                                "description": "Status of the service order, which could be Open, Closed, or Canceled.",
                                "type": "string",
                                "valid_values": ["Open", "Closed", "Canceled"]
                            },
                            "DateCreated": {
                                "description": "DateCreated records the date and time when the service order was created.",
                                "type": "datetime"
                            },
                            "DateClosedCancelled": {
                                "description": "DateClosedCancelled Stores the date and time when the service order was closed or canceled.",
                                "type": "datetime",
                                "nullable": True
                            },
                            "FromLocationID": {
                                "description": "FromLocationID Specifies the location identifier from which the service order originates.",
                                "type": "integer",
                                "lookup_table": "Locations",
                                "lookup_table_id_field": "LocationID",
                                "lookup_table_description_field": "LocationName"
                            },
                            "ToLocationID": {
                                "description": "ToLocationID Represents the location identifier to which the service order is directed.",
                                "type": "integer",
                                "lookup_table": "Locations",
                                "lookup_table_id_field": "LocationID",
                                "lookup_table_description_field": "LocationName"
                            }
                        }
                    }


            data = fetch_table_data(conn, table_name)
        except Exception as e:
            print(f"Error fetching metadata, relationships or data: {e}")
            return

        combined_data = {
            "user_data": user_data,
            "business_rules": business_rules,
            "metadata": all_metadata.get(table_name, {}),
            "relationships": relationships,
            "data": data
        }
        

        json_output = json.dumps(combined_data, indent=4, default=datetime_converter)
        with open(f'D:/{table_name}_Details.json', 'w') as f:
            f.write(json_output)
        print(f"Data and metadata for {table_name} saved to D:/{table_name}_Details.json")

        conn.close()
    except pyodbc.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        

if __name__ == "__main__":
    main()
