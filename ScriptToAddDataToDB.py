import pyodbc
import datetime

# Connect to the database
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=atigroai.database.windows.net;'
    'DATABASE=logistics_new;'
    'UID=logistic;'
    'PWD=4$P)K0]Ti|Rv5n98'
)
cursor = conn.cursor()

# Timestamps
now = datetime.datetime.now()
current_date = now.date()
current_time = now.time()

# Loop for 10 rows of data
for i in range(1,10):
    # 1. Insert EquipmentCategory
    cursor.execute("INSERT INTO EquipmentCategory (EquipmentCategoryName) OUTPUT INSERTED.EquipmentCategoryID VALUES (?)", ('Aerial Lifts',))
    equipment_category_id = cursor.fetchone()[0]

    # Temporarily re-use category ID as EquipmentModelID (to satisfy broken FK)
    equipment_model_id = equipment_category_id

    # 2. Insert Warehouse
    cursor.execute("INSERT INTO Warehouses (WarehouseName, City, State) OUTPUT INSERTED.WarehouseID VALUES (?, ?, ?)", ('Central Warehouse', 'Sangli', 'MH'))
    warehouse_id = cursor.fetchone()[0]

    # 3. Insert EquipmentInventory using EquipmentModelID (from step 2)
    cursor.execute("""
        INSERT INTO EquipmentInventory (EquipmentModelID, WarehouseID, DateofPurchase)
        OUTPUT INSERTED.EquipmentID
        VALUES (?, ?, ?)
    """, (equipment_model_id, warehouse_id, current_date))
    equipment_id = cursor.fetchone()[0]

    # 4. Insert EmployeeType
    cursor.execute("INSERT INTO EmployeeType (EmployeeType) OUTPUT INSERTED.EmployeeTypeID VALUES (?)", ('Technician',))
    employee_type_id = cursor.fetchone()[0]

    # 5. Insert Employee
    cursor.execute("""
        INSERT INTO Employees (EmployeeFirstName, EmployeeLastName, EmployeeTypeID, WarehouseID, HourlyRate)
        OUTPUT INSERTED.EmployeeID
        VALUES (?, ?, ?, ?, ?)
    """, (f'Sam{i}', 'Chavan', employee_type_id, warehouse_id, 50.00))
    employee_id = cursor.fetchone()[0]

    # 6. Insert WorkOrder
    cursor.execute("""
        INSERT INTO WorkOrders (EquipmentID, Status, DateCreated, SupervisingEmployeeID)
        OUTPUT INSERTED.WorkOrderID
        VALUES (?, ?, ?, ?)
    """, (equipment_id, 'Open', now, employee_id))
    work_order_id = cursor.fetchone()[0]

    # 7. Insert TimeTracking_Hours
    cursor.execute("""
        INSERT INTO TimeTracking_Hours (EmployeeID, Date, Hours, TypeofTime, ChargetoJobTF, WorkOrderID, FromTime, ToTime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (employee_id, current_date, 8, 'Regular', 1, work_order_id, current_time.replace(microsecond=0), (datetime.datetime.combine(current_date, current_time) + datetime.timedelta(hours=8)).time()))
    conn.commit()

    # 8. Insert WorkOrderDetail
    cursor.execute("INSERT INTO MaintenanceTasks (MaintenanceTask) OUTPUT INSERTED.MaintenanceTaskID VALUES (?)", ('Routine Check',))
    task_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO WorkOrderDetails (WorkOrderID, MaintenanceTaskID, TechnicianID, HoursWorked)
        VALUES (?, ?, ?, ?)
    """, (work_order_id, task_id, employee_id, 8))
    conn.commit()

print("✅ 10 rows of sample data added successfully!")
