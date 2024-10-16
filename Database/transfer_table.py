import compare_db_config
import json
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import sessionmaker

# Create database engines for both databases
engine_db1 = create_engine(compare_db_config.db1_url)
engine_db2 = create_engine(compare_db_config.db2_url)

# Create session factories for both databases
SessionDB1 = sessionmaker(bind=engine_db1)
SessionDB2 = sessionmaker(bind=engine_db2)

session_db1 = SessionDB1()
session_db2 = SessionDB2()

# Reflect metadata from db1 (source database)
metadata_db1 = MetaData()
metadata_db1.reflect(bind=engine_db1)

def list_tables():
    """List all the tables in the source database (db1)"""
    tables = list(metadata_db1.tables.keys())
    print("Available tables in db1:")
    for idx, table_name in enumerate(tables, start=1):
        print(f"{idx}. {table_name}")
    return tables

def select_tables(tables):
    """Allow user to select tables to transfer"""
    selected_indices = input("Enter the numbers of the tables you want to transfer (comma-separated, e.g., 1,2,3): ")
    selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    selected_tables = [tables[i] for i in selected_indices]
    return selected_tables

def convert_to_sql_values(row):
    """Converts a dictionary row to SQL value syntax, with proper escaping."""
    values = []
    
    for value in row.values():
        if isinstance(value, dict):
            # Assuming the value is JSON-like, we serialize it to a string
            json_str = json.dumps(value)  # Convert Python dict to JSON string
            escaped_value = json_str.replace("'", "''")  # Escape single quotes inside the JSON string
            values.append(f"'{escaped_value}'")
        elif isinstance(value, str):
            # Escape single quotes in regular strings
            escaped_value = value.replace("'", "''")
            values.append(f"'{escaped_value}'")
        elif value is None:
            # Handle NULL values
            values.append("NULL")
        elif isinstance(value, (int, float)):
            # Directly convert integers and floats
            values.append(str(value))
        else:
            # Fallback for other types, convert to string and escape
            escaped_value = str(value).replace("'", "''")
            values.append(f"'{escaped_value}'")
    
    # Return the formatted values as a tuple in SQL syntax
    return f"({', '.join(values)})"


def generate_insert_sql(table_name, columns, data_to_insert):
    """Generates raw SQL INSERT statements."""
    column_names = ', '.join(columns)
    values_sql = ',\n'.join([convert_to_sql_values(row) for row in data_to_insert])

    insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES\n{values_sql};"
    return insert_sql

def transfer_structure_and_data(selected_tables):
    """
    Transfer the structure (table definitions) and data for selected tables from db1 to db2.
    Generates raw SQL INSERT statements.
    """
    # Open connections for both databases
    with engine_db1.connect() as conn_db1, engine_db2.connect() as conn_db2:
        for table_name in selected_tables:
            print(f"\nProcessing table: {table_name}")

            # Get the table structure from db1
            table_db1 = metadata_db1.tables[table_name]

            # Generate the Create Table SQL for db2 (target database)
            create_table_sql = str(CreateTable(table_db1).compile(engine_db2))

            # Create the table in db2
            print(f"Creating table in db2: {table_name}")
            try:
                conn_db2.execute(text(create_table_sql))
            except Exception as e:
                print(f"Table {table_name} already exists or failed to create. Skipping creation.")
                print(e)

            # Transfer the data
            print(f"Transferring data for table: {table_name}")
            try:
                # Fetch all data from db1
                result = conn_db1.execute(table_db1.select()).fetchall()
                
                if not result:
                    print(f"No data to transfer for table: {table_name}")
                    continue

                # Convert the result into dictionaries with column names
                data_to_insert = [
                    {column.name: value for column, value in zip(table_db1.columns, row)}
                    for row in result
                ]

                # Generate raw SQL INSERT statements
                column_names = [column.name for column in table_db1.columns]
                insert_sql = generate_insert_sql(table_name, column_names, data_to_insert)

                # Print or execute the raw SQL
                print(f"Generated SQL for {table_name}:\n{insert_sql}")
                conn_db2.execute(text(insert_sql))
                conn_db2.commit()

            except Exception as e:
                print(f"Failed to transfer data for table: {table_name}")
                print(f"Error: {e}")

    print("\nData and structure transfer complete.")

if __name__ == "__main__":
    # List all tables from db1
    available_tables = list_tables()

    # Let the user select which tables to transfer
    selected_tables = select_tables(available_tables)

    # Transfer structure and data for the selected tables
    transfer_structure_and_data(selected_tables)
