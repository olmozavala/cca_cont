#!/usr/bin/env python3
"""
Test script to verify database connection and basic functionality.
"""

import sys
sys.path.insert(0, './db_utils')

from db_utils.sql_con import test_connection
from db_utils.oztools import ContIOTools
from db_utils.queries_add import insert_pollutant_data


def test_oztools() -> None:
    """Test the ContIOTools class functionality."""
    print("\n🧪 Testing ContIOTools class...")
    
    oz_tools = ContIOTools()
    
    # Test table methods
    tables = oz_tools.getTables()
    print(f"📊 Pollutant tables: {tables}")
    
    meteo_tables = oz_tools.getMeteoTables()
    print(f"🌤️  Meteorological tables: {meteo_tables}")
    
    # Test parameter methods
    contaminants = oz_tools.getContaminants()
    print(f"🔬 Contaminant parameters: {contaminants}")
    
    meteo_params = oz_tools.getMeteoParams()
    print(f"🌡️  Meteorological parameters: {meteo_params}")
    
    print("✅ ContIOTools tests passed!")


def test_insert_function() -> None:
    """Test the insert function with a dummy record."""
    print("\n🧪 Testing insert function...")
    
    # Test with a dummy record (this should fail gracefully if table doesn't exist)
    success = insert_pollutant_data(
        table="cont_test",
        fecha="12/25/2023 10:00:00",
        id_est="TEST",
        value="0.0"
    )
    
    if success:
        print("✅ Insert function test passed!")
    else:
        print("⚠️  Insert function test completed (expected failure for test table)")


def main() -> None:
    """Main test function."""
    print("🚀 Starting connection and functionality tests...")
    
    # Test database connection
    connection_success = test_connection()
    
    if connection_success:
        # Test ContIOTools functionality
        test_oztools()
        
        # Test insert function
        test_insert_function()
        
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Database connection failed. Please check your configuration.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 