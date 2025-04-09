# from langchain.prompts import PromptTemplate
# from langchain.output_parsers import PydanticOutputParser
# from langchain_core.output_parsers import JsonOutputParser


# from langchain_openai import ChatOpenAI
# import json
# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict
# import pyodbc
# from datetime import datetime
# from decimal import Decimal



# class User(BaseModel):
#     user_id: int
#     user_name: str
#     user_phone: str
#     user_role: str

# class UserDataObject(BaseModel):
#     users: List[User]

# class BusinessRule(BaseModel):
#     Object_Description: str
#     Object_Business_Rules: str

# class BusinessRulesObject(BaseModel):
#     Work_Order: BusinessRule

# class WorkOrderDetail(BaseModel):
#     WorkOrderDetailID: int
#     WorkOrderID: int
#     MaintenanceTaskID: int
#     TechnicianID: int
#     HoursWorked: float
#     PartID: int
#     related_data: dict

# class EquipmentInventory(BaseModel):
#     EquipmentID: int
#     EquipmentModelID: int
#     WarehouseID: int
#     JobID: int
#     InventoryQty: float
#     DateofPurchase: str
#     PurchasePrice: str
#     related_data: dict

# # class DataObject(BaseModel):
# #     WorkOrderID: int
# #     EquipmentID: int
# #     Status: str
# #     DateCreated: str
# #     DateClosed: str
# #     ClosingStateofEquipment: str
# #     SupervisingEmployeeID: int
# #     related_data: dict  
# class DataObject(BaseModel):
#     WorkOrderID: int
#     EquipmentID: Optional[int]
#     Status: str
#     DateCreated: str
#     DateClosed: Optional[str]
#     ClosingStateofEquipment: Optional[str]
#     SupervisingEmployeeID: Optional[int]
#     related_data: Dict[str, Optional[Dict]]

# class CustomData(BaseModel):
#     field1: UserDataObject
#     field2: BusinessRulesObject
#     field3: DataObject
#     user_input: str
#     response: str
    
    
# def decimal_default(obj):
#     if isinstance(obj, Decimal):
#         return float(obj)  # or use str(obj) if you want to avoid floating point precision issues
#     raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)
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
#     for field in schema_info[table_name]['fields']:
#         if schema_info[table_name]['fields'][field]['type'] == 'datetime' and record_dict[field]:
#             record_dict[field] = record_dict[field].strftime('%Y-%m-%d %H:%M:%S')

    

#     related_data = {}
#     for field, fk_relations in schema_info[table_name].get('foreign_keys', {}).items():
#         for fk_relation in fk_relations:
#             related_table = fk_relation['table']
#             related_column = fk_relation['foreign_column']
#             fk_value = record_dict.get(field)
#             if fk_value:
#                 cursor.execute(f"SELECT * FROM {related_table} WHERE {related_column} = ?", fk_value)
#                 related_record = cursor.fetchone()
#                 if related_record:
#                     related_record_dict = dict(zip([column[0] for column in cursor.description], related_record))
#                     for rel_field in schema_info[related_table]['fields']:
#                         if schema_info[related_table]['fields'][rel_field]['type'] == 'datetime' and related_record_dict[rel_field]:
#                             related_record_dict[rel_field] = related_record_dict[rel_field].strftime('%Y-%m-%d %H:%M:%S')
#                     related_data[related_table] = related_record_dict
#                 else:
#                     related_data[related_table] = None
    
#     record_dict['related_data'] = related_data

#     # Close the cursor and connection
#     cursor.close()
#     conn.close()

#     return record_dict


# def get_llm_response(data: CustomData):
#     prompt_template = """
#     Analyze the following data:
#     User Data: {user_data}
#     Business Rules: {business_rules}
#     Work Order Details: {work_order_details}
#     User Query: {user_input}
#     Provide a comprehensive response to User Query based on the above information.
#     """
#     #Provide a comprehensive response to User Query based on the above information in JSON format, like {{'response': 'Your answer here'}}.
#     #Provide a comprehensive response to User Query based on the above information.
    

#     prompt = PromptTemplate.from_template(prompt_template)
#     #parser = PydanticOutputParser(pydantic_object=CustomData)
#     llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key = "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")

#     chain = prompt | llm

#     formatted_data = {
#         "user_data": json.dumps(data.field1.model_dump(), indent=2, default=decimal_default),
#         "business_rules": json.dumps(data.field2.model_dump(), indent=2, default=decimal_default),
#         "work_order_details": json.dumps(data.field3.model_dump(), indent=2,default=decimal_default),
#         "user_input": data.user_input
#     }
#     try:
#         structured_response = chain.invoke(formatted_data)
#         return structured_response.content
#     except Exception as e:
#          print("An unexpected error occurred:", str(e))
#          return {"error": "Unexpected error", "details": str(e)}



# def main():
#     user_data = {
#         "users": [
#             {
#                 "user_id": 1,
#                 "user_name": "John Doe",
#                 "user_phone": "123-456-7890",
#                 "user_role": "Manager"
#             },
#             {
#                 "user_id": 2,
#                 "user_name": "Jane Smith",
#                 "user_phone": "098-765-4321",
#                 "user_role": "Technician"
#             }
#         ]
#     }
#     business_rules ={
#         "Work Order": {
#             "Object Description": "Details about a Work Order, including origination and context specific to the business.",
#             "Object Business Rules": "1. Work Order ID must be unique."
#             "2. Status progresses from Open, to In Progress, to Completed, or occasionally Canceled."
#             "3. Creation only by a Work Order Manager; status changes need Manager approval."
#             "4. Viewable by any user, modifiable only by the manager or assigned user."
#             "5. Cannot be canceled once completed."
#             "6. Status cannot change to Completed until all tasks are completed or canceled."
#             "7. WorkOrder can be re-Opened only by a Manager"
#         }
#     }
#     dbname = 'logistics_new'  # The database name
#     table_name = 'WorkOrders'  # Example table
#     primary_key_value = 17  # WorkOrderID example primary key value
#     schema_info = {
#     'WorkOrders': {
#         'fields': {
#             'WorkOrderID': {'type': 'int', 'default': None, 'nullable': False},
#             'EquipmentID': {'type': 'int', 'default': None, 'nullable': True},
#             'Status': {'type': 'nvarchar', 'default': None, 'nullable': True},
#             'DateCreated': {'type': 'datetime', 'default': None, 'nullable': True},
#             'DateClosed': {'type': 'datetime', 'default': None, 'nullable': True},
#             'ClosingStateofEquipment': {'type': 'nvarchar', 'default': None, 'nullable': True},
#             'SupervisingEmployeeID': {'type': 'int', 'default': None, 'nullable': True}
#         },
#         'primary_key': ['WorkOrderID'],
#         'foreign_keys': {
#             'SupervisingEmployeeID': [{'table': 'Employees', 'foreign_column': 'EmployeeID', 'column': 'SupervisingEmployeeID'}],
#             'EquipmentID': [{'table': 'EquipmentInventory', 'foreign_column': 'EquipmentID', 'column': 'EquipmentID'}]
#         },
#         'constraints': {}
#     },
#     'Employees': {
#         'fields': {
#             'EmployeeID': {'type': 'int', 'default': None, 'nullable': False},
#             'EmployeeFirstName': {'type': 'nvarchar', 'default': None, 'nullable': True},
#             'EmployeeLastName': {'type': 'nvarchar', 'default': None, 'nullable': True},
#             'EmployeeTypeID': {'type': 'int', 'default': None, 'nullable': True},
#             'WarehouseID': {'type': 'int', 'default': None, 'nullable': True},
#             'HourlyRate': {'type': 'money', 'default': None, 'nullable': True}
#         },
#         'primary_key': ['EmployeeID'],
#         'foreign_keys': {},
#         'constraints': {}
#     },
#     'EquipmentInventory': {
#         'fields': {
#             'EquipmentID': {'type': 'int', 'default': None, 'nullable': False},
#             'EquipmentModelID': {'type': 'int', 'default': None, 'nullable': True},
#             'WarehouseID': {'type': 'int', 'default': None, 'nullable': True},
#             'JobID': {'type': 'int', 'default': None, 'nullable': True},
#             'InventoryQty': {'type': 'float', 'default': None, 'nullable': True},
#             'DateofPurchase': {'type': 'datetime', 'default': None, 'nullable': True},
#             'PurchasePrice': {'type': 'money', 'default': None, 'nullable': True}
#         },
#         'primary_key': ['EquipmentID'],
#         'foreign_keys': {
#             'EquipmentModelID': [{'table': 'EquipmentModels', 'foreign_column': 'EquipmentModelID', 'column': 'EquipmentModelID'}]
#         },
#         'constraints': {}
#     },
#     'EquipmentModels': {
#         'fields': {
#             'EquipmentModelID': {'type': 'int', 'default': None, 'nullable': False},
#             'ModelName': {'type': 'nvarchar', 'default': None, 'nullable': True},
#             'Manufacturer': {'type': 'nvarchar', 'default': None, 'nullable': True}
#         },
#         'primary_key': ['EquipmentModelID'],
#         'foreign_keys': {},
#         'constraints': {}
#     }
#     }
#     data_object = fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value)
#     print("Fetched Data Object:", data_object)
#     user_data_model = UserDataObject(users=[User(**user) for user in user_data['users']])
#     #user_data_model = user_data['users'][0]
#     business_rules_model = BusinessRulesObject(Work_Order=BusinessRule(
#     Object_Description=business_rules['Work Order']['Object Description'],
#     Object_Business_Rules=business_rules['Work Order']['Object Business Rules']
# ))

#     data_object_model = DataObject(**data_object)
#     user_input = input("Please enter your input for the prompt: ")

#     custom_data_instance = CustomData(
#         field1=user_data_model,
#         field2=business_rules_model,
#         field3=data_object_model,
#         user_input=user_input,
#         response="Initial response pending"
#     )

#     response = get_llm_response(custom_data_instance)
#     if response:
#         print("Response from LLM:", response)
#     else:
#         print("No response received or an error occurred.")

# if __name__ == "__main__":
#     main()
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser


from langchain_openai import ChatOpenAI
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import pyodbc
from datetime import datetime
from decimal import Decimal
      
def get_schema_of_database(db_name):
    pass

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # or use str(obj) if you want to avoid floating point precision issues
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)
def fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value):
    # Connect to MSSQL (Azure SQL Server in this case)
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE=' + dbname + ';'
        'UID=logistic;'  # Your database username
        'PWD=4$P)K0]Ti|Rv5n98'  # Your database password
    )
    cursor = conn.cursor()

    # Check if the table exists in the schema info
    if table_name not in schema_info:
        print(f"Table {table_name} not found in schema information.")
        return None

    # Get the actual primary key column name from schema
    primary_key_column = schema_info[table_name]['primary_key'][0]  # Assuming primary_key has one column

    # Fetch the fields of the given table using the primary key
    cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key_column} = ?", primary_key_value)
    record = cursor.fetchone()
    
    if not record:
        print(f"No record found for {table_name} with primary key value {primary_key_value}.")
        return None

    # Convert record to dictionary
    column_names = [column[0] for column in cursor.description]
    record_dict = dict(zip(column_names, record))
    for field in schema_info[table_name]['fields']:
        if schema_info[table_name]['fields'][field]['type'] == 'datetime' and record_dict[field]:
            record_dict[field] = record_dict[field].strftime('%Y-%m-%d %H:%M:%S')

    

    related_data = {}
    for field, fk_relations in schema_info[table_name].get('foreign_keys', {}).items():
        for fk_relation in fk_relations:
            related_table = fk_relation['column']
            related_column = fk_relation['foreign_column']
            fk_value = record_dict.get(field)
            if fk_value:
                cursor.execute(f"SELECT * FROM {related_table} WHERE {related_column} = ?", fk_value)
                related_record = cursor.fetchone()
                if related_record:
                    related_record_dict = dict(zip([column[0] for column in cursor.description], related_record))
                    for rel_field in schema_info[related_table]['fields']:
                        if schema_info[related_table]['fields'][rel_field]['type'] == 'datetime' and related_record_dict[rel_field]:
                            related_record_dict[rel_field] = related_record_dict[rel_field].strftime('%Y-%m-%d %H:%M:%S')
                    related_data[related_table] = related_record_dict
                else:
                    related_data[related_table] = None
    
    record_dict['related_data'] = related_data

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return record_dict
def get_filtered_schema_info_for_primary_tables(dbname, primary_tables, secondary_tables):
    # Establish connection to MSSQL
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE=' + dbname + ';'
        'UID=logistic;'  # Your database username
        'PWD=4$P)K0]Ti|Rv5n98'  # Your database password
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
                    schemas[table_name]["foreign_keys"][fk[1]] = []
                schemas[table_name]["foreign_keys"][fk[1]].append({
                    "column": fk[0],
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

def get_llm_response(input_data):
    
    prompt_template = """
    Analyze the following data:
    User Data: {user_data}
    Business Rules: {business_rule}
    Schema Information : {schema_info}
    Work Order Details: {data_object}
    User Query: {user_input}
    Provide a comprehensive response to User Query based on the above information.
    """

    prompt = PromptTemplate.from_template(prompt_template)
    #parser = PydanticOutputParser(pydantic_object=CustomData)
    llm = ChatOpenAI(model="gpt-4", temperature=0,openai_api_key = "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")

    chain = prompt | llm

    try:
        structured_response = chain.invoke(input_data)
        return structured_response.content
    except Exception as e:
         print("An unexpected error occurred:", str(e))
         return {"error": "Unexpected error", "details": str(e)}

business_object_primary_table_map = {"Work Order" : ["WorkOrders"],
                                     "Service Order" : ["ServiceOrder", "ServiceOrderDetails"]}


def main():
    # Sample users data fetched from Django Table
    users_data = {
            1 : {
                "user_name": "John Doe",
                "user_phone": "123-456-7890",
                "user_role": "Manager"
            },
            2 : {
                "user_name": "Jane Smith",
                "user_phone": "098-765-4321",
                "user_role": "Technician"
            }
            }
    
    user_id = 2 # Comes dynamically from the UI
    user_data = users_data[user_id]
    
    business_rules = {
        "Work Order": {
            "Object Description": "Details about a Work Order, including origination and context specific to the business.",
            "Object Business Rules": "1. Work Order ID must be unique."
            "2. Status progresses from Open, to In Progress, to Completed, or occasionally Canceled."
            "3. Creation only by a Work Order Manager; status changes need Manager approval."
            "4. Viewable by any user, modifiable only by the manager or assigned user."
            "5. Cannot be canceled once completed."
            "6. Status cannot change to Completed until all tasks are completed or canceled."
            "7. WorkOrder can be re-Opened only by a Manager"
        }
    }
    business_object = "Work Order" # Static now, will come based on the selected assistant
    business_rule = business_rules[business_object]
    
    primary_tables = business_object_primary_table_map[business_object]
    dbname = 'logistics_new'  
    
    #specific_schema_info = get_filtered_schema_info_for_primary_tables(schema_info_of_entire_database, primary_tables)
    specific_schema_info =get_filtered_schema_info_for_primary_tables(dbname, primary_tables,[])
    
    # The database name
    
    primary_key_value = 17  # Static right now, later we build a cell for detecting the concerned key
    data_object = fetch_record_with_fks(dbname, specific_schema_info, primary_tables[0], primary_key_value)
    
    
    print("Fetched Data Object:", data_object)

    user_input = input("Please enter your input for the prompt: ")

    input_data = {"user_data" :user_data,
                "business_rule" : business_rule,
                "schema_info" : specific_schema_info,
                "data_object" : data_object,
                "user_input" : user_input}

    response = get_llm_response(input_data)
    if response:
        print("Response from LLM:", response)
    else:
        print("No response received or an error occurred.")

if __name__ == "__main__":
    main()
