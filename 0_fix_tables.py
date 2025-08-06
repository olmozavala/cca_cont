#!/usr/bin/env python3
"""
Script to fix database tables by making their id columns auto-incrementing primary keys.
This script alters all pollutant and meteorological tables to ensure proper auto-increment behavior.
"""

import sys
from typing import List, Tuple
from sqlalchemy import text

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.sql_con import get_db_engine
from db_utils.oztools import ContIOTools


def get_all_tables() -> List[str]:
    """
    Get all pollutant and meteorological table names.
    
    Returns:
        List[str]: List of all table names
    """
    oz_tools = ContIOTools()
    pollutant_tables = oz_tools.getTables()
    meteo_tables = oz_tools.getMeteoTables()
    return pollutant_tables + meteo_tables


def check_table_schema(engine, table_name: str) -> Tuple[bool, str]:
    """
    Check if a table's id column is properly configured as auto-increment.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to check
        
    Returns:
        Tuple[bool, str]: (is_auto_increment, description)
    """
    try:
        with engine.connect() as connection:
            # Check if the table exists
            check_table_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """)
            result = connection.execute(check_table_sql, {'table_name': table_name})
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                return False, f"Table {table_name} does not exist"
            
            # Check the id column configuration
            column_info_sql = text("""
                SELECT 
                    column_name,
                    column_default,
                    is_nullable,
                    data_type,
                    is_identity,
                    identity_generation
                FROM information_schema.columns 
                WHERE table_name = :table_name AND column_name = 'id'
            """)
            result = connection.execute(column_info_sql, {'table_name': table_name})
            column_info = result.fetchone()
            
            if not column_info:
                return False, f"Column 'id' not found in table {table_name}"
            
            column_name, default, nullable, data_type, is_identity, identity_gen = column_info
            
            if is_identity == 'YES':
                return True, f"Table {table_name} has auto-incrementing id column"
            elif default and 'nextval' in default:
                return True, f"Table {table_name} has sequence-based id column"
            else:
                return False, f"Table {table_name} id column is not auto-incrementing"
                
    except Exception as e:
        return False, f"Error checking table {table_name}: {e}"


def check_table_constraints(engine, table_name: str) -> Tuple[bool, bool, bool, str]:
    """
    Check if a table has proper constraints: foreign key to cont_estaciones, 
    composite primary key (id, fecha, id_est), and unique constraint on (fecha, id_est).
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to check
        
    Returns:
        Tuple[bool, bool, bool, str]: (has_fk, has_composite_pk, has_unique, description)
    """
    try:
        with engine.connect() as connection:
            # Check foreign key to cont_estaciones
            fk_sql = text(f"""
                SELECT COUNT(*) 
                FROM pg_constraint 
                WHERE conrelid = '{table_name}'::regclass
                AND contype = 'f'
                AND pg_get_constraintdef(oid) LIKE '%REFERENCES cont_estaciones%'
            """)
            result = connection.execute(fk_sql)
            has_fk = result.fetchone()[0] > 0
            
            # Check composite primary key (id, fecha, id_est)
            pk_sql = text(f"""
                SELECT 
                    pg_get_constraintdef(oid) as pk_definition
                FROM pg_constraint 
                WHERE conrelid = '{table_name}'::regclass
                AND contype = 'p'
            """)
            result = connection.execute(pk_sql)
            pk_row = result.fetchone()
            has_composite_pk = False
            if pk_row:
                pk_definition = pk_row[0]
                has_composite_pk = 'id, fecha, id_est' in pk_definition.replace(' ', '')
            
            # Check unique constraint on (fecha, id_est)
            unique_sql = text(f"""
                SELECT COUNT(*) 
                FROM pg_constraint 
                WHERE conrelid = '{table_name}'::regclass
                AND contype = 'u'
                AND pg_get_constraintdef(oid) LIKE '%fecha, id_est%'
            """)
            result = connection.execute(unique_sql)
            has_unique = result.fetchone()[0] > 0
            
            description = f"FK: {'✅' if has_fk else '❌'}, Composite PK: {'✅' if has_composite_pk else '❌'}, Unique (fecha,id_est): {'✅' if has_unique else '❌'}"
            
            return has_fk, has_composite_pk, has_unique, description
                
    except Exception as e:
        return False, False, False, f"Error checking constraints for {table_name}: {e}"


def fix_table_id_column(engine, table_name: str) -> Tuple[bool, str]:
    """
    Fix a table's id column to be auto-incrementing.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to fix
        
    Returns:
        Tuple[bool, str]: (success, description)
    """
    try:
        with engine.connect() as connection:
            # First check if the table exists
            check_table_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """)
            result = connection.execute(check_table_sql, {'table_name': table_name})
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                return False, f"Table {table_name} does not exist"
            
            # Check if id column exists
            check_column_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name AND column_name = 'id'
                )
            """)
            result = connection.execute(check_column_sql, {'table_name': table_name})
            column_exists = result.fetchone()[0]
            
            if not column_exists:
                return False, f"Column 'id' not found in table {table_name}"
            
            # Check current configuration
            is_auto_increment, description = check_table_schema(engine, table_name)
            if is_auto_increment:
                return True, f"Table {table_name} already has auto-incrementing id column"
            
            # Try to make it auto-incrementing using GENERATED ALWAYS AS IDENTITY
            try:
                alter_sql = text(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY
                """)
                connection.execute(alter_sql)
                connection.commit()
                return True, f"Successfully made {table_name} id column auto-incrementing"
                
            except Exception as e:
                # If that fails, try the older SERIAL approach
                try:
                    # Create a sequence
                    sequence_name = f"{table_name}_id_seq"
                    create_seq_sql = text(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name}")
                    connection.execute(create_seq_sql)
                    
                    # Set the default value
                    alter_default_sql = text(f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN id SET DEFAULT nextval('{sequence_name}')
                    """)
                    connection.execute(alter_default_sql)
                    
                    # Set the sequence to the current maximum value + 1
                    set_seq_sql = text(f"""
                        SELECT setval('{sequence_name}', COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1)
                    """)
                    connection.execute(set_seq_sql)
                    
                    connection.commit()
                    return True, f"Successfully made {table_name} id column auto-incrementing using sequence"
                    
                except Exception as e2:
                    connection.rollback()
                    return False, f"Failed to fix {table_name}: {e2}"
                    
    except Exception as e:
        return False, f"Error fixing table {table_name}: {e}"


def fix_table_constraints(engine, table_name: str) -> Tuple[bool, str]:
    """
    Fix a table's constraints: add foreign key to cont_estaciones, 
    change primary key to (id, fecha, id_est), and add unique constraint on (fecha, id_est).
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to fix
        
    Returns:
        Tuple[bool, str]: (success, description)
    """
    try:
        with engine.connect() as connection:
            # Check current constraints
            has_fk, has_composite_pk, has_unique, description = check_table_constraints(engine, table_name)
            
            if has_fk and has_composite_pk and has_unique:
                return True, f"Table {table_name} already has all required constraints"
            
            # Step 1: Check for orphaned records before adding foreign key
            if not has_fk:
                # Check for orphaned records
                orphan_check_sql = text(f"""
                    SELECT DISTINCT t.id_est, COUNT(*) as count
                    FROM {table_name} t
                    LEFT JOIN cont_estaciones e ON t.id_est = e.id
                    WHERE e.id IS NULL
                    GROUP BY t.id_est
                    ORDER BY count DESC
                """)
                
                orphan_result = connection.execute(orphan_check_sql)
                orphaned_stations = orphan_result.fetchall()
                
                if orphaned_stations:
                    print(f"  ⚠️  Found orphaned records in {table_name} for stations: {[s[0] for s in orphaned_stations]}")
                    print(f"  📊 Orphaned record counts: {dict(orphaned_stations)}")
                    
                    # Ask user what to do
                    response = input(f"  Delete orphaned records from {table_name}? (y/N): ")
                    if response.lower() == 'y':
                        delete_orphaned_sql = text(f"""
                            DELETE FROM {table_name} 
                            WHERE id_est IN (
                                SELECT DISTINCT t.id_est
                                FROM {table_name} t
                                LEFT JOIN cont_estaciones e ON t.id_est = e.id
                                WHERE e.id IS NULL
                            )
                        """)
                        result = connection.execute(delete_orphaned_sql)
                        deleted_count = result.rowcount
                        print(f"  ✅ Deleted {deleted_count} orphaned records from {table_name}")
                        connection.commit()
                    else:
                        print(f"  ⚠️  Skipping foreign key constraint for {table_name} due to orphaned records")
                        return False, f"Skipped {table_name} due to orphaned records"
                
                # Now try to add foreign key
                try:
                    fk_sql = text(f"""
                        ALTER TABLE {table_name} 
                        ADD CONSTRAINT fk_{table_name}_estaciones 
                        FOREIGN KEY (id_est) REFERENCES cont_estaciones(id) ON DELETE CASCADE
                    """)
                    connection.execute(fk_sql)
                    print(f"  ✅ Added foreign key to {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not add foreign key to {table_name}: {e}")
                    connection.rollback()
                    return False, f"Failed to add foreign key to {table_name}: {e}"
            
            # Step 2: Change primary key to composite (id, fecha, id_est) if needed
            if not has_composite_pk:
                try:
                    # First, find and drop the existing primary key constraint
                    find_pk_sql = text(f"""
                        SELECT conname 
                        FROM pg_constraint 
                        WHERE conrelid = '{table_name}'::regclass 
                        AND contype = 'p'
                    """)
                    
                    pk_result = connection.execute(find_pk_sql)
                    existing_pk = pk_result.fetchone()
                    
                    if existing_pk:
                        pk_name = existing_pk[0]
                        print(f"  🔍 Found existing primary key: {pk_name}")
                        
                        # Drop the existing primary key
                        drop_pk_sql = text(f"ALTER TABLE {table_name} DROP CONSTRAINT {pk_name}")
                        connection.execute(drop_pk_sql)
                        print(f"  ✅ Dropped existing primary key: {pk_name}")
                    
                    # Add new composite primary key
                    add_pk_sql = text(f"""
                        ALTER TABLE {table_name} 
                        ADD CONSTRAINT pk_{table_name}_composite 
                        PRIMARY KEY (id, fecha, id_est)
                    """)
                    connection.execute(add_pk_sql)
                    print(f"  ✅ Changed primary key to composite for {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not change primary key for {table_name}: {e}")
                    connection.rollback()
                    return False, f"Failed to change primary key for {table_name}: {e}"
            
            # Step 3: Add unique constraint on (fecha, id_est) if missing
            if not has_unique:
                try:
                    # Check for existing duplicates before adding unique constraint
                    duplicate_check_sql = text(f"""
                        SELECT fecha, id_est, COUNT(*) as count
                        FROM {table_name}
                        GROUP BY fecha, id_est
                        HAVING COUNT(*) > 1
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    
                    duplicate_result = connection.execute(duplicate_check_sql)
                    duplicates = duplicate_result.fetchall()
                    
                    if duplicates:
                        print(f"  ⚠️  Found duplicate (fecha, id_est) combinations in {table_name}:")
                        for fecha, id_est, count in duplicates:
                            print(f"    {fecha} {id_est}: {count} records")
                        
                        response = input(f"  Remove duplicates from {table_name}? (y/N): ")
                        if response.lower() == 'y':
                            # Keep only the first record for each (fecha, id_est) combination
                            delete_duplicates_sql = text(f"""
                                DELETE FROM {table_name} 
                                WHERE id IN (
                                    SELECT id FROM (
                                        SELECT id,
                                               ROW_NUMBER() OVER (PARTITION BY fecha, id_est ORDER BY id) as rn
                                        FROM {table_name}
                                    ) ranked
                                    WHERE rn > 1
                                )
                            """)
                            result = connection.execute(delete_duplicates_sql)
                            deleted_count = result.rowcount
                            print(f"  ✅ Removed {deleted_count} duplicate records from {table_name}")
                            connection.commit()
                        else:
                            print(f"  ⚠️  Skipping unique constraint for {table_name} due to duplicates")
                            return False, f"Skipped {table_name} due to duplicate records"
                    
                    # Now try to add unique constraint
                    unique_sql = text(f"""
                        ALTER TABLE {table_name} 
                        ADD CONSTRAINT unique_{table_name}_fecha_id_est 
                        UNIQUE (fecha, id_est)
                    """)
                    connection.execute(unique_sql)
                    print(f"  ✅ Added unique constraint on (fecha, id_est) for {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not add unique constraint to {table_name}: {e}")
                    connection.rollback()
                    return False, f"Failed to add unique constraint to {table_name}: {e}"
            
            connection.commit()
            return True, f"Successfully updated constraints for {table_name}"
                    
    except Exception as e:
        return False, f"Error fixing constraints for {table_name}: {e}"


def main() -> None:
    """
    Main function to fix all tables.
    """
    print("🔧 Starting table fix process...")
    
    # Get database engine
    engine = get_db_engine()
    if engine is None:
        print("❌ Failed to create database engine")
        return
    
    # Get all tables
    tables = get_all_tables()
    print(f"📋 Found {len(tables)} tables to check/fix:")
    for table in tables:
        print(f"  - {table}")
    
    print("\n🔍 Checking current table configurations...")
    tables_to_fix_id = []
    tables_to_fix_constraints = []
    
    for table in tables:
        # Check ID column configuration
        is_auto_increment, id_description = check_table_schema(engine, table)
        print(f"  {table} ID: {id_description}")
        if not is_auto_increment:
            tables_to_fix_id.append(table)
        
        # Check constraints
        has_fk, has_composite_pk, has_unique, constraint_description = check_table_constraints(engine, table)
        print(f"  {table} Constraints: {constraint_description}")
        if not (has_fk and has_composite_pk and has_unique):
            tables_to_fix_constraints.append(table)
    
    if not tables_to_fix_id and not tables_to_fix_constraints:
        print("\n✅ All tables are already properly configured!")
        return
    
    # Show what needs to be fixed
    if tables_to_fix_id:
        print(f"\n🔧 Found {len(tables_to_fix_id)} tables that need ID column fixing:")
        for table in tables_to_fix_id:
            print(f"  - {table}")
    
    if tables_to_fix_constraints:
        print(f"\n🔧 Found {len(tables_to_fix_constraints)} tables that need constraint fixing:")
        for table in tables_to_fix_constraints:
            print(f"  - {table}")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with fixing these tables? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled by user")
        return
    
    # Fix ID columns
    if tables_to_fix_id:
        print("\n🔧 Fixing ID columns...")
        success_count = 0
        failed_count = 0
        
        for table in tables_to_fix_id:
            success, description = fix_table_id_column(engine, table)
            if success:
                print(f"  ✅ {description}")
                success_count += 1
            else:
                print(f"  ❌ {description}")
                failed_count += 1
        
        print(f"📊 ID Column Fix Summary:")
        print(f"  ✅ Successfully fixed: {success_count}")
        print(f"  ❌ Failed to fix: {failed_count}")
    
    # Fix constraints
    if tables_to_fix_constraints:
        print("\n🔧 Fixing constraints...")
        success_count = 0
        failed_count = 0
        
        for table in tables_to_fix_constraints:
            success, description = fix_table_constraints(engine, table)
            if success:
                print(f"  ✅ {description}")
                success_count += 1
            else:
                print(f"  ❌ {description}")
                failed_count += 1
        
        print(f"📊 Constraint Fix Summary:")
        print(f"  ✅ Successfully fixed: {success_count}")
        print(f"  ❌ Failed to fix: {failed_count}")
    
    print("\n🎉 Table fix process completed!")


if __name__ == "__main__":
    main()
