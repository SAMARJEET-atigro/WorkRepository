from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import pyodbc
from decimal import Decimal
import os

      
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
            related_table = fk_relation['table']
            related_column = fk_relation['foreign_column']
            fk_value = record_dict.get(field)
            if fk_value and related_table != table_name:  # Ensure not to re-fetch from the same table
                cursor.execute(f"SELECT * FROM {related_table} WHERE {related_column} = ?", fk_value)
                related_record = cursor.fetchone()
                if related_record:
                    related_record_dict = dict(zip([column[0] for column in cursor.description], related_record))
                    related_data[related_table] = related_record_dict
                else:
                    related_data[related_table] = None


    #print(f"related_data: {related_data}")
    record_dict['related_data'] = related_data

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return record_dict
def get_filtered_schema_info_for_primary_tables(conn, table_name):
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
            'type': str(column.data_type),
            'default': str(column.column_default),
            'nullable': str(column.is_nullable == 'YES')
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
        schema_info[table_name]['primary_key'].append(str(row.column_name))

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
            'table': str(fk.referenced_table),
            'foreign_column': str(fk.referenced_column)
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
        schema_info[table_name]['constraints']['unique'].append(str(row.column_name))

    cursor.close()
    conn.close()
    return schema_info



def get_llm_response(input_data):
    user = input_data["user_data"]["user_name"]
    prompt_template = f"""
    As {user}, a {input_data['user_data']['user_role']}, you're asking:
    {input_data['user_input']}
    
    Considering the provided Work Order details and business rules related to your role, here's a detailed analysis:
    Business Rules: {{business_rule}}
    Schema Information: {{schema_info}}
    Work Order Details: {{data_object}}
    """
    
    # prompt_template = """
    # Analyze the following data:
    # User Data: {user_data}
    # Business Rules: {business_rule}
    # Schema Information : {schema_info}
    # Work Order Details: {data_object}
    # User Query: {user_input}
    # Provide a comprehensive response to User Query based on the above information.
    # """
    key = "" 
    prompt = PromptTemplate.from_template(prompt_template)
    llm = ChatOpenAI(model="gpt-4", temperature=0,openai_api_key = key)
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
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=atigroai.database.windows.net;'
        'DATABASE=' + dbname + ';'
        'UID=logistic;'  # Your database username
        'PWD=4$P)K0]Ti|Rv5n98'  # Your database password
    )
    specific_schema_info =get_filtered_schema_info_for_primary_tables(conn, primary_tables[0])
    print(f"Schema Information:{specific_schema_info}")
    
    # The database name
    
    primary_key_value = 17  # Static right now, later we build a cell for detecting the concerned key
    data_object = fetch_record_with_fks(dbname, specific_schema_info, primary_tables[0], primary_key_value)
    
    
    print("Fetched Data Object:", data_object)

    while True:
        user_input = input("Please enter your input for the prompt (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            print("Exiting the program.")
            break


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
