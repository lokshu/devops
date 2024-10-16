import os
from sqlalchemy import create_engine, inspect
from jinja2 import Template
import config  # Import the config file

# Use the values from the config.py file
db_url = config.db_url
java_project_folder = config.java_project_folder
package_name = config.package_name

# Create database connection
engine = create_engine(db_url)

# Jinja2 template for the Java entity file
java_entity_template = """
package {{ package_name }}.entity;

//replace this with javax for lower version of spring boot
import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Entity
@Data
@Table(name = "{{ table_name }}")
public class {{ class_name }} {

    {% for column in columns %}
    @Column(name = "{{ column['name'] }}"{% if column['length'] %}, length = {{ column['length'] }}{% endif %}){% if column['is_primary_key'] %}
    @Id{% if column['is_auto_increment'] %}
    @GeneratedValue(strategy = GenerationType.IDENTITY){% endif %}{% endif %}
    private {{ column['java_type'] }} {{ column['camel_case_name'] }};
    {% endfor %}
}
"""

# Jinja2 template for repository (if it's a view)
view_repository_template = """
package {{ package_name }}.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import {{ package_name }}.entity.{{ class_name }};
import org.springframework.lang.NonNull;
import org.springframework.data.repository.query.Param;

@Repository
public interface {{ class_name }}Repository extends JpaRepository<{{ class_name }}, Integer> {
    @NonNull
    Page<{{ class_name }}> findAll(@NonNull Pageable pageable);

    @Query("SELECT p FROM {{ class_name }} p WHERE LOWER(p.keyword) LIKE LOWER(CONCAT('%',:keyword,'%'))")
    Page<{{ class_name }}> searchByKeyword(@Param("keyword") String keyword, Pageable pageable);
}
"""

# Jinja2 template for repository (if it's a table)
table_repository_template = """
package {{ package_name }}.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import {{ package_name }}.entity.{{ class_name }};

@Repository
public interface {{ class_name }}Repository extends JpaRepository<{{ class_name }}, Integer> {
    
}
"""

service_template = """
package {{ package_name }}.service;

import {{ package_name }}.entity.{{ class_name }};
import {{ package_name }}.repository.{{ class_name }}Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class {{ class_name }}Service {

    @Autowired
    private {{ class_name }}Repository {{ camel_class_name }}Repository;

    public List<{{ class_name }}> getAll() {
        return {{ camel_class_name }}Repository.findAll();
    }

    public Optional<{{ class_name }}> getById(Integer id) {
        return {{ camel_class_name }}Repository.findById(id);
    }

    {% if not is_view %}
    public {{ class_name }} insert({{ class_name }} {{ camel_class_name }}) {
        return {{ camel_class_name }}Repository.save({{ camel_class_name }});
    }

    public {{ class_name }} update({{ class_name }} {{ camel_class_name }}) {
        return {{ camel_class_name }}Repository.save({{ camel_class_name }});
    }
    {% endif %}
}
"""

controller_template = """
package {{ package_name }}.controller;

import {{ package_name }}.entity.{{ class_name }};
import {{ package_name }}.service.{{ class_name }}Service;
import {{ package_name }}.repository.{{ class_name }}Repository;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/{{ camel_class_name }}")
public class {{ class_name }}Controller {

    @Autowired
    private {{ class_name }}Service {{ camel_class_name }}Service;

    @Autowired
    private {{ class_name }}Repository {{ camel_class_name }}Repository;

    @GetMapping
    public ResponseEntity<Page<{{ class_name }}>> getAll(
        @PageableDefault(size = 10) Pageable pageable,
        @RequestParam(required = false) String keyword) {

        Page<{{ class_name }}> {{ camel_class_name }} = Page.empty();
        if (keyword != null && !keyword.trim().isEmpty()) {
            // Uncomment and implement search logic in repository if needed
            // {{ camel_class_name }} = {{ camel_class_name }}Repository.searchByKeyword(keyword, pageable);
        } else {    
            {{ camel_class_name }} = {{ camel_class_name }}Repository.findAll(pageable);
        }    
        return ResponseEntity.ok({{ camel_class_name }}); 
    }

    @GetMapping("/{id}")
    public ResponseEntity<Optional<{{ class_name }}>> getById(@PathVariable Integer id) {
        Optional<{{ class_name }}> {{ camel_class_name }} = {{ camel_class_name }}Service.getById(id);
        if ({{ camel_class_name }}.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok({{ camel_class_name }});
    }
}
"""

# Mapping of MySQL types to Java types
type_mapping = {
    "INTEGER": "Integer",
    "BIGINT": "Long",
    "VARCHAR": "String",
    "TEXT": "String",
    "DATE": "LocalDateTime",
    "DATETIME": "LocalDateTime",
    "DECIMAL": "BigDecimal",
    # Add other type mappings as needed
}

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0].lower() + ''.join(x.capitalize() for x in components[1:])

# Function to generate the Java class name
def generate_class_name(table_name):
    return ''.join(word.capitalize() for word in table_name.split('_'))

def is_auto_increment_column(column):
    # Only allow auto-increment for integer-like columns
    return column['type'].__class__.__name__.upper() in ['INTEGER', 'BIGINT'] and column.get('autoincrement', False)

# Function to get column details from the table
def get_columns(table_name):
    inspector = inspect(engine)
    
    # Get primary key column(s) from the table
    pk_constraint = inspector.get_pk_constraint(table_name)
    primary_keys = pk_constraint.get('constrained_columns', [])  # List of primary key column names
    
    columns = []
    for column in inspector.get_columns(table_name):
        column_name = column['name']
        is_primary_key = column_name in primary_keys  # Check if the column is in the list of primary keys
        is_auto_increment = is_auto_increment_column(column) if is_primary_key else False  # Direct access to 'autoincrement'
        
        # Check if the column has a length (for VARCHAR, etc.)
        column_length = column['type'].length if hasattr(column['type'], 'length') else None

        columns.append({
            'name': column_name,
            'camel_case_name': to_camel_case(column_name),  # Generate camel case name
            'type': column['type'].__class__.__name__.upper(),
            'is_primary_key': is_primary_key,
            'is_auto_increment': is_auto_increment,
            'java_type': type_mapping.get(column['type'].__class__.__name__.upper(), 'String'),  # Default to String
            'length': column_length  # Add length information
        })
    return columns



# Function to check if the object is a view
def is_view(table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_view_names()

# Function to generate the entity class file
def generate_entity(table_name):
    # Get columns and generate class name
    columns = get_columns(table_name)
    class_name = generate_class_name(table_name)

    # Use Jinja2 to render the entity template
    template = Template(java_entity_template)
    rendered = template.render(
        package_name=package_name,
        table_name=table_name,
        class_name=class_name,
        columns=columns
    )

    # Save the generated file to the specified folder
    output_folder = os.path.join(java_project_folder, 'src', 'main', 'java', package_name.replace('.', os.sep), 'entity')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"{class_name}.java")

    with open(output_file, 'w') as f:
        f.write(rendered)

    print(f"Generated entity: {output_file}")

# Function to generate the service class file directly
def generate_service(table_name):
    class_name = generate_class_name(table_name)
    camel_class_name = to_camel_case(class_name)
    is_view_flag = is_view(table_name)

    # Use Jinja2 to render the service template
    template = Template(service_template)
    rendered = template.render(
        package_name=package_name,
        class_name=class_name,
        camel_class_name=camel_class_name,
        is_view=is_view_flag
    )

    # Save the generated file to the specified folder
    output_folder = os.path.join(java_project_folder, 'src', 'main', 'java', package_name.replace('.', os.sep), 'service')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"{class_name}Service.java")

    with open(output_file, 'w') as f:
        f.write(rendered)

    print(f"Generated service: {output_file}")

# Function to generate the controller class file
def generate_controller(table_name):
    class_name = generate_class_name(table_name)
    camel_class_name = to_camel_case(class_name)
    is_view_flag = is_view(table_name)

    # Use Jinja2 to render the controller template
    template = Template(controller_template)
    rendered = template.render(
        package_name=package_name,
        class_name=class_name,
        camel_class_name=camel_class_name,
        is_view=is_view_flag
    )

    # Save the generated file to the specified folder
    output_folder = os.path.join(java_project_folder, 'src', 'main', 'java', package_name.replace('.', os.sep), 'controller')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"{class_name}Controller.java")

    with open(output_file, 'w') as f:
        f.write(rendered)

    print(f"Generated controller: {output_file}")

# Function to generate the repository file
def generate_repository(table_name):
    class_name = generate_class_name(table_name)
    
    # Determine if it's a view or a table
    if is_view(table_name):
        # Use the view repository template
        template = Template(view_repository_template)
    else:
        # Use the table repository template
        template = Template(table_repository_template)

    rendered = template.render(
        package_name=package_name,
        class_name=class_name
    )

    # Save the generated file to the specified folder
    output_folder = os.path.join(java_project_folder, 'src', 'main', 'java', package_name.replace('.', os.sep), 'repository')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"{class_name}Repository.java")

    with open(output_file, 'w') as f:
        f.write(rendered)

    print(f"Generated repository: {output_file}")

# Function to list all tables and views in the database
def list_tables():
    inspector = inspect(engine)
    # Get both tables and views
    tables = inspector.get_table_names()  # Get the tables
    views = inspector.get_view_names()    # Get the views
    return tables + views  # Merge tables and views into one list


# Main code
if __name__ == "__main__":
    # List available tables and views
    tables = list_tables()
    print("Available tables/views:")
    for idx, table in enumerate(tables):
        print(f"{idx + 1}. {table}")

    # Let the user select a table
    choice = int(input("Select a table by number: ")) - 1
    selected_table = tables[choice]

    # Ask the user what to generate
    print("\nSelect what to generate:")
    print("Press Enter to generate all files (Entity, Repository, Service, Controller).")
    print("1: Entity only")
    print("2: Entity and Repository")
    print("3: Entity, Repository, and Service")
    
    user_input = input("Your choice: ").strip()

    # Generate based on the user's choice
    if user_input == "1":
        print(f"Generating entity for {selected_table}...")
        generate_entity(selected_table)

    elif user_input == "2":
        print(f"Generating entity and repository for {selected_table}...")
        generate_entity(selected_table)
        generate_repository(selected_table)

    elif user_input == "3":
        print(f"Generating entity, repository, and service for {selected_table}...")
        generate_entity(selected_table)
        generate_repository(selected_table)
        generate_service(selected_table)

    else:
        print(f"Generating all files for {selected_table} (Entity, Repository, Service, Controller)...")
        generate_entity(selected_table)
        generate_repository(selected_table)
        generate_service(selected_table)
        generate_controller(selected_table)

    print("Generation complete.")
