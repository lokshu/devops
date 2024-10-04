from sqlalchemy import create_engine, inspect, text
from sqlalchemy.sql.sqltypes import Integer, String
import compare_db_config

# Create engine connections to both databases
db1_engine = create_engine(compare_db_config.db1_url)
db2_engine = create_engine(compare_db_config.db2_url)

# Create inspectors for both databases
db1_inspector = inspect(db1_engine)
db2_inspector = inspect(db2_engine)

# Function to normalize SQLAlchemy types to their base types
def normalize_type(column_type):
    # Check for common types like Integer, String, etc.
    if isinstance(column_type, Integer):
        return 'INTEGER'
    elif isinstance(column_type, String):
        # If it's a String, include the length in the comparison
        return f'VARCHAR({column_type.length})'
    else:
        # Return the type's string representation for other types
        return str(column_type)

# Function to compare table structures and log the differences
def compare_table_structure(db1_inspector, db2_inspector, table_name, log):
    db1_columns = db1_inspector.get_columns(table_name)
    db2_columns = db2_inspector.get_columns(table_name)

    db1_column_map = {col['name']: col['type'] for col in db1_columns}
    db2_column_map = {col['name']: col['type'] for col in db2_columns}

    log.append(f"\nComparing table: {table_name}")
    
    # Columns only in DB1
    only_in_db1 = set(db1_column_map.keys()) - set(db2_column_map.keys())
    if only_in_db1:
        log.append(f"  Columns only in DB1: {only_in_db1}")

    # Columns only in DB2
    only_in_db2 = set(db2_column_map.keys()) - set(db1_column_map.keys())
    if only_in_db2:
        log.append(f"  Columns only in DB2: {only_in_db2}")

    # Columns with different types
    for col in db1_column_map.keys() & db2_column_map.keys():
        db1_col_type = normalize_type(db1_column_map[col])
        db2_col_type = normalize_type(db2_column_map[col])
        if db1_col_type != db2_col_type:
            log.append(f"  Column type difference in '{col}': DB1 ({db1_col_type}) vs DB2 ({db2_col_type})")

# Function to compare views and log the differences
def compare_views(db1_engine, db2_engine, log):
    with db1_engine.connect() as db1_conn, db2_engine.connect() as db2_conn:
        db1_views = db1_conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'VIEW'")).fetchall()
        db2_views = db2_conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'VIEW'")).fetchall()

        db1_view_names = {view[0] for view in db1_views}
        db2_view_names = {view[0] for view in db2_views}

        log.append("\nComparing views:")

        # Views only in DB1
        only_in_db1 = db1_view_names - db2_view_names
        if only_in_db1:
            log.append(f"  Views only in DB1: {only_in_db1}")

        # Views only in DB2
        only_in_db2 = db2_view_names - db1_view_names
        if only_in_db2:
            log.append(f"  Views only in DB2: {only_in_db2}")

        # Views in both DBs but different definitions
        for view_name in db1_view_names & db2_view_names:
            db1_view_sql = db1_conn.execute(text(f"SHOW CREATE VIEW {view_name}")).fetchone()[1]
            db2_view_sql = db2_conn.execute(text(f"SHOW CREATE VIEW {view_name}")).fetchone()[1]
            if db1_view_sql != db2_view_sql:
                log.append(f"  Difference in view definition for '{view_name}'.")

# Function to compare stored procedures and log the differences
def compare_stored_procedures(db1_engine, db2_engine, log):
    with db1_engine.connect() as db1_conn, db2_engine.connect() as db2_conn:
        db1_sps = db1_conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")).fetchall()
        db2_sps = db2_conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")).fetchall()

        db1_sp_names = {sp[1] for sp in db1_sps}
        db2_sp_names = {sp[1] for sp in db2_sps}

        log.append("\nComparing stored procedures:")

        # Stored procedures only in DB1
        only_in_db1 = db1_sp_names - db2_sp_names
        if only_in_db1:
            log.append(f"  Stored procedures only in DB1: {only_in_db1}")

        # Stored procedures only in DB2
        only_in_db2 = db2_sp_names - db1_sp_names
        if only_in_db2:
            log.append(f"  Stored procedures only in DB2: {only_in_db2}")

        # Stored procedures in both DBs but different definitions
        for sp_name in db1_sp_names & db2_sp_names:
            db1_sp_sql = db1_conn.execute(text(f"SHOW CREATE PROCEDURE {sp_name}")).fetchone()[2]
            db2_sp_sql = db2_conn.execute(text(f"SHOW CREATE PROCEDURE {sp_name}")).fetchone()[2]
            if db1_sp_sql != db2_sp_sql:
                log.append(f"  Difference in stored procedure definition for '{sp_name}'.")

# Function to compare tables, views, and stored procedures and log differences
def generate_comparison_log():
    log = []

    # Get table names from both databases
    db1_tables = set(db1_inspector.get_table_names())
    db2_tables = set(db2_inspector.get_table_names())

    log.append("Comparing tables:")

    # Tables only in DB1
    only_in_db1 = db1_tables - db2_tables
    if only_in_db1:
        log.append(f"  Tables only in DB1: {only_in_db1}")

    # Tables only in DB2
    only_in_db2 = db2_tables - db1_tables
    if only_in_db2:
        log.append(f"  Tables only in DB2: {only_in_db2}")

    # Compare structure for tables that exist in both databases
    for table_name in db1_tables & db2_tables:
        compare_table_structure(db1_inspector, db2_inspector, table_name, log)

    # Compare views
    compare_views(db1_engine, db2_engine, log)

    # Compare stored procedures
    compare_stored_procedures(db1_engine, db2_engine, log)

    return log

# Write the comparison log to a file
def write_comparison_log():
    log = generate_comparison_log()
    
    with open('db_comparison_log.txt', 'w') as f:
        f.write("\n".join(log))

    print("Comparison log generated: db_comparison_log.txt")

# Run the log generation
write_comparison_log()
