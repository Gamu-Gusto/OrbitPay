#!/usr/bin/env python3
"""
Script to fix the payroll_records table structure
"""

from sqlalchemy import text
from db import engine, SessionLocal
from orm_models import PayrollRecord

def fix_payroll_table():
    """Drop and recreate the payroll_records table with correct structure"""
    
    with engine.begin() as conn:
        # Drop the existing table if it exists
        print("Dropping existing payroll_records table...")
        conn.execute(text("DROP TABLE IF EXISTS payroll_records"))
        
    # Create the new table with correct structure
    print("Creating new payroll_records table...")
    PayrollRecord.__table__.create(engine, checkfirst=True)
    
    print("✅ PayrollRecord table fixed successfully!")
    print("The table now includes monthly payrun tracking:")
    print("- payrun_month (1-12)")
    print("- payrun_year (e.g., 2025)")
    print("- payrun_period (e.g., '2025-10')")

if __name__ == "__main__":
    fix_payroll_table()
