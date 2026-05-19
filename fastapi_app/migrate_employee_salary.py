"""
Database migration script to add salary fields to Employee table
Run this script to update existing database with new salary columns
"""

from sqlalchemy import create_engine, text
from db import SQLALCHEMY_DATABASE_URL
import os

def migrate_employee_table():
    """Add new salary-related columns to the employees table"""
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # List of new columns to add
    new_columns = [
        # Employment Status
        "ALTER TABLE employees ADD COLUMN is_active BOOLEAN DEFAULT 1",
        "ALTER TABLE employees ADD COLUMN termination_date DATE",
        
        # Salary Information
        "ALTER TABLE employees ADD COLUMN basic_salary REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN hourly_rate REAL",
        "ALTER TABLE employees ADD COLUMN salary_type VARCHAR(20) DEFAULT 'monthly'",
        
        # Allowances
        "ALTER TABLE employees ADD COLUMN housing_allowance REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN transport_allowance REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN meal_allowance REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN other_allowances REAL DEFAULT 0.0",
        
        # Deductions
        "ALTER TABLE employees ADD COLUMN pension_contribution REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN medical_aid REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN union_fees REAL DEFAULT 0.0",
        "ALTER TABLE employees ADD COLUMN other_deductions REAL DEFAULT 0.0",
        
        # Tax Information
        "ALTER TABLE employees ADD COLUMN tax_number VARCHAR(100)",
        "ALTER TABLE employees ADD COLUMN tax_directive VARCHAR(100)",
        
        # Banking Information
        "ALTER TABLE employees ADD COLUMN bank_name VARCHAR(100)",
        "ALTER TABLE employees ADD COLUMN account_number VARCHAR(50)",
        "ALTER TABLE employees ADD COLUMN branch_code VARCHAR(20)",
        "ALTER TABLE employees ADD COLUMN account_type VARCHAR(20)"
    ]
    
    with engine.connect() as connection:
        # Check if migration is needed by checking if basic_salary column exists
        try:
            result = connection.execute(text("SELECT basic_salary FROM employees LIMIT 1"))
            print("Migration already completed - salary columns exist")
            return
        except Exception:
            print("Starting migration - adding salary columns to employees table")
        
        # Add each column, handling cases where column might already exist
        for sql in new_columns:
            try:
                connection.execute(text(sql))
                print(f"✓ Added column: {sql.split('ADD COLUMN')[1].split()[0]}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"- Column already exists: {sql.split('ADD COLUMN')[1].split()[0]}")
                else:
                    print(f"✗ Error adding column: {e}")
        
        connection.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    print("Employee Salary Migration Script")
    print("=" * 40)
    
    # Check if database exists
    if not os.path.exists("payroll.db"):
        print("Database file not found. Please run the main application first to create the database.")
        exit(1)
    
    migrate_employee_table()
    print("\nMigration finished. You can now restart your application.")
