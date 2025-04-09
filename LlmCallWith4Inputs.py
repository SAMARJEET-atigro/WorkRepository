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



class User(BaseModel):
    user_id: int
    user_name: str
    user_phone: str
    user_role: str

class UserDataObject(BaseModel):
    users: List[User]

class BusinessRule(BaseModel):
    Object_Description: str
    Object_Business_Rules: str

class BusinessRulesObject(BaseModel):
    Work_Order: BusinessRule

class WorkOrderDetail(BaseModel):
    WorkOrderDetailID: int
    WorkOrderID: int
    MaintenanceTaskID: int
    TechnicianID: int
    HoursWorked: float
    PartID: int
    related_data: dict

class EquipmentInventory(BaseModel):
    EquipmentID: int
    EquipmentModelID: int
    WarehouseID: int
    JobID: int
    InventoryQty: float
    DateofPurchase: str
    PurchasePrice: str
    related_data: dict

# class DataObject(BaseModel):
#     WorkOrderID: int
#     EquipmentID: int
#     Status: str
#     DateCreated: str
#     DateClosed: str
#     ClosingStateofEquipment: str
#     SupervisingEmployeeID: int
#     related_data: dict  
class DataObject(BaseModel):
    WorkOrderID: int
    EquipmentID: Optional[int]
    Status: str
    DateCreated: str
    DateClosed: Optional[str]
    ClosingStateofEquipment: Optional[str]
    SupervisingEmployeeID: Optional[int]
    related_data: Dict[str, Optional[Dict]]

class CustomData(BaseModel):
    field1: UserDataObject
    field2: BusinessRulesObject
    field3: DataObject
    user_input: str
    response: str
    
    
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
            related_table = fk_relation['table']
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


def get_llm_response(data: CustomData):
    prompt_template = """
    Analyze the following data:
    User Data: {user_data}
    Business Rules: {business_rules}
    Work Order Details: {work_order_details}
    User Query: {user_input}
    Provide a comprehensive response to User Query based on the above information.
    """
    #Provide a comprehensive response to User Query based on the above information in JSON format, like {{'response': 'Your answer here'}}.
    #Provide a comprehensive response to User Query based on the above information.
    

    prompt = PromptTemplate.from_template(prompt_template)
    #parser = PydanticOutputParser(pydantic_object=CustomData)
    llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key = "")

    chain = prompt | llm

    formatted_data = {
        "user_data": json.dumps(data.field1.model_dump(), indent=2, default=decimal_default),
        "business_rules": json.dumps(data.field2.model_dump(), indent=2, default=decimal_default),
        "work_order_details": json.dumps(data.field3.model_dump(), indent=2,default=decimal_default),
        "user_input": data.user_input
    }
    try:
        structured_response = chain.invoke(formatted_data)
        return structured_response.content
    except Exception as e:
         print("An unexpected error occurred:", str(e))
         return {"error": "Unexpected error", "details": str(e)}



def main():
    user_data = {
        "users": [
            {
                "user_id": 1,
                "user_name": "John Doe",
                "user_phone": "123-456-7890",
                "user_role": "Manager"
            },
            {
                "user_id": 2,
                "user_name": "Jane Smith",
                "user_phone": "098-765-4321",
                "user_role": "Technician"
            }
        ]
    }
    business_rules ={
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
    dbname = 'logistics_new'  # The database name
    table_name = 'WorkOrders'  # Example table
    primary_key_value = 17  # WorkOrderID example primary key value
    schema_info = {
    'WorkOrders': {
        'fields': {
            'WorkOrderID': {'type': 'int', 'default': None, 'nullable': False},
            'EquipmentID': {'type': 'int', 'default': None, 'nullable': True},
            'Status': {'type': 'nvarchar', 'default': None, 'nullable': True},
            'DateCreated': {'type': 'datetime', 'default': None, 'nullable': True},
            'DateClosed': {'type': 'datetime', 'default': None, 'nullable': True},
            'ClosingStateofEquipment': {'type': 'nvarchar', 'default': None, 'nullable': True},
            'SupervisingEmployeeID': {'type': 'int', 'default': None, 'nullable': True}
        },
        'primary_key': ['WorkOrderID'],
        'foreign_keys': {
            'SupervisingEmployeeID': [{'table': 'Employees', 'foreign_column': 'EmployeeID', 'column': 'SupervisingEmployeeID'}],
            'EquipmentID': [{'table': 'EquipmentInventory', 'foreign_column': 'EquipmentID', 'column': 'EquipmentID'}]
        },
        'constraints': {}
    },
    'Employees': {
        'fields': {
            'EmployeeID': {'type': 'int', 'default': None, 'nullable': False},
            'EmployeeFirstName': {'type': 'nvarchar', 'default': None, 'nullable': True},
            'EmployeeLastName': {'type': 'nvarchar', 'default': None, 'nullable': True},
            'EmployeeTypeID': {'type': 'int', 'default': None, 'nullable': True},
            'WarehouseID': {'type': 'int', 'default': None, 'nullable': True},
            'HourlyRate': {'type': 'money', 'default': None, 'nullable': True}
        },
        'primary_key': ['EmployeeID'],
        'foreign_keys': {},
        'constraints': {}
    },
    'EquipmentInventory': {
        'fields': {
            'EquipmentID': {'type': 'int', 'default': None, 'nullable': False},
            'EquipmentModelID': {'type': 'int', 'default': None, 'nullable': True},
            'WarehouseID': {'type': 'int', 'default': None, 'nullable': True},
            'JobID': {'type': 'int', 'default': None, 'nullable': True},
            'InventoryQty': {'type': 'float', 'default': None, 'nullable': True},
            'DateofPurchase': {'type': 'datetime', 'default': None, 'nullable': True},
            'PurchasePrice': {'type': 'money', 'default': None, 'nullable': True}
        },
        'primary_key': ['EquipmentID'],
        'foreign_keys': {
            'EquipmentModelID': [{'table': 'EquipmentModels', 'foreign_column': 'EquipmentModelID', 'column': 'EquipmentModelID'}]
        },
        'constraints': {}
    },
    'EquipmentModels': {
        'fields': {
            'EquipmentModelID': {'type': 'int', 'default': None, 'nullable': False},
            'ModelName': {'type': 'nvarchar', 'default': None, 'nullable': True},
            'Manufacturer': {'type': 'nvarchar', 'default': None, 'nullable': True}
        },
        'primary_key': ['EquipmentModelID'],
        'foreign_keys': {},
        'constraints': {}
    }
    }
    data_object = fetch_record_with_fks(dbname, schema_info, table_name, primary_key_value)
    print("Fetched Data Object:", data_object)
    #user_data_model = UserDataObject(users=[User(**user) for user in user_data['users']])
    user_data_model = user_data['users'][0]
    business_rules_model = BusinessRulesObject(Work_Order=BusinessRule(
    Object_Description=business_rules['Work Order']['Object Description'],
    Object_Business_Rules=business_rules['Work Order']['Object Business Rules']
))

    data_object_model = DataObject(**data_object)
    user_input = input("Please enter your input for the prompt: ")

    custom_data_instance = CustomData(
        field1=user_data_model,
        field2=business_rules_model,
        field3=data_object_model,
        user_input=user_input,
        response="Initial response pending"
    )

    response = get_llm_response(custom_data_instance)
    if response:
        print("Response from LLM:", response)
    else:
        print("No response received or an error occurred.")

if __name__ == "__main__":
    main()
