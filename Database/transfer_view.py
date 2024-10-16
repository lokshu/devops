import compare_db_config
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Create database engines for both databases
engine_db1 = create_engine(compare_db_config.db1_url)
engine_db2 = create_engine(compare_db_config.db2_url)

# Create session factories for both databases
SessionDB1 = sessionmaker(bind=engine_db1)
SessionDB2 = sessionmaker(bind=engine_db2)

session_db1 = SessionDB1()
session_db2 = SessionDB2()

def list_views():
    """List all the views in the source database (db1)"""
    inspector = inspect(engine_db1)  # Correct method to get inspector
    views = inspector.get_view_names()

    print("Available views in db1:")
    for idx, view_name in enumerate(views, start=1):
        print(f"{idx}. {view_name} (View)")
    
    return views

def select_views(views):
    """Allow user to select views to transfer"""
    selected_indices = input("Enter the numbers of the views you want to transfer (comma-separated, e.g., 1,2,3): ")
    selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(',')]
    selected_views = [views[i] for i in selected_indices]
    
    return selected_views

def transfer_view(view_name):
    """Transfer a view by extracting its definition and creating it in db2."""
    inspector = inspect(engine_db1)
    view_definition = inspector.get_view_definition(view_name)
    
    # Strip out 'DEFINER' and 'SQL SECURITY' and any extra 'CREATE' keywords
    cleaned_view_definition = view_definition.replace('DEFINER=`root`@`%`', '').replace('SQL SECURITY DEFINER', '')
    cleaned_view_definition = cleaned_view_definition.replace('CREATE ALGORITHM=UNDEFINED', '')
    cleaned_view_definition = cleaned_view_definition.replace('CREATE VIEW', '').strip()
    cleaned_view_definition = cleaned_view_definition.replace('VIEW', '').strip()
    cleaned_view_definition = cleaned_view_definition.replace(f'`{view_name}` AS', '').strip()

    # Generate the final view creation SQL
    create_view_sql = f"CREATE VIEW {view_name} AS {cleaned_view_definition}"

    print(f"Creating view in db2: {view_name}")
    print(f"View definition: {create_view_sql}")
    
    try:
        with engine_db2.connect() as conn_db2:
            conn_db2.execute(text(create_view_sql))
            print(f"Successfully created view: {view_name}")
    except Exception as e:
        print(f"Failed to create view {view_name}: {e}")

def transfer_views(selected_views):
    """Transfer all selected views to db2"""
    for view_name in selected_views:
        transfer_view(view_name)

    print("\nView transfer complete.")

if __name__ == "__main__":
    # List all views from db1
    available_views = list_views()

    # Let the user select which views to transfer
    selected_views = select_views(available_views)

    # Transfer the selected views
    transfer_views(selected_views)
