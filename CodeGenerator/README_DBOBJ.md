# Spring Boot Code Generator

This Python script is designed to generate the core components (Entities, Repositories, Services, and Controllers) for a Spring Boot application based on a MySQL database. It automatically generates CRUD operations for tables, and it skips `INSERT` and `UPDATE` endpoints for database views.

## Features

- **Entity Generation**: Generates Java entity files based on table structure in the database.
- **Repository Generation**: Generates Spring Data JPA repository interfaces for tables and views.
- **Service Generation**: Generates service classes with methods for retrieving, inserting, and updating data (skips `insert()` and `update()` for views).
- **Controller Generation**: Generates RESTful controllers with `GET`, `POST`, and `PUT` endpoints for tables (skips `POST` and `PUT` for views). It includes pagination and search functionality for views and tables.

## Prerequisites

Before you begin, ensure you have the following:

1. **Python**: Installed and available in your system's PATH.
2. **MySQL Database**: Your MySQL database must be accessible, and you must have a connection URL for it.
3. **Jinja2**: This Python package is required for rendering templates.
   
   You can install it using:
   ```bash
   pip install jinja2

## Configuration

In the same folder as the script, create a config.py file with the following parameters:

db_url = "mysql+pymysql://<user>:<password>@<host>:<port>/<database>"
java_project_folder = "C:/Project/dodomax20erp"
package_name = "com.embraiz.dodomax20"

## Usage

python generate_code.py

Once the generation is complete, you will find the following generated files inside your project folder:

Entity: Under src/main/java/com/embraiz/dodomax20/entity/
Repository: Under src/main/java/com/embraiz/dodomax20/repository/
Service: Under src/main/java/com/embraiz/dodomax20/service/
Controller: Under src/main/java/com/embraiz/dodomax20/controller/