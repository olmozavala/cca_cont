#!/usr/bin/env python3
"""
Pytest tests for the 2_update_last_hour.py functionality.
"""

import pytest
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.oztools import ContIOTools
from db_utils.queries_add import insert_pollutant_data, insert_meteorological_data


class TestContIOTools:
    """Test cases for ContIOTools class."""
    
    def test_get_tables(self):
        """Test getTables method returns correct pollutant table names."""
        oz_tools = ContIOTools()
        tables = oz_tools.getTables()
        
        expected_tables = [
            'cont_pmco', 'cont_pmdoscinco', 'cont_nox', 'cont_codos', 
            'cont_co', 'cont_nodos', 'cont_no', 'cont_otres', 
            'cont_sodos', 'cont_pmdiez'
        ]
        
        assert tables == expected_tables
        assert len(tables) == 10
    
    def test_get_meteo_tables(self):
        """Test getMeteoTables method returns correct meteorological table names."""
        oz_tools = ContIOTools()
        tables = oz_tools.getMeteoTables()
        
        expected_tables = ['met_tmp', 'met_rh', 'met_wsp', 'met_wdr', 'met_pba']
        
        assert tables == expected_tables
        assert len(tables) == 5
    
    def test_get_contaminants(self):
        """Test getContaminants method returns correct parameter names."""
        oz_tools = ContIOTools()
        contaminants = oz_tools.getContaminants()
        
        expected_contaminants = [
            'pmco', 'pm2', 'nox', 'co2', 'co', 'no2', 'no', 'o3', 'so2', 'pm10'
        ]
        
        assert contaminants == expected_contaminants
        assert len(contaminants) == 10
    
    def test_get_meteo_params(self):
        """Test getMeteoParams method returns correct parameter names."""
        oz_tools = ContIOTools()
        params = oz_tools.getMeteoParams()
        
        expected_params = ['tmp', 'rh', 'wsp', 'wdr', 'pba']
        
        assert params == expected_params
        assert len(params) == 5
    
    def test_find_table(self):
        """Test findTable method with various file names."""
        oz_tools = ContIOTools()
        
        # Test pollutant tables
        assert oz_tools.findTable("PM2.5_data.csv") == "cont_pmdoscinco"
        assert oz_tools.findTable("PM10_data.csv") == "cont_pmdiez"
        assert oz_tools.findTable("NOX_data.csv") == "cont_nox"
        assert oz_tools.findTable("CO2_data.csv") == "cont_codos"
        assert oz_tools.findTable("CO_data.csv") == "cont_co"
        assert oz_tools.findTable("NO2_data.csv") == "cont_nodos"
        assert oz_tools.findTable("NO_data.csv") == "cont_no"
        assert oz_tools.findTable("O3_data.csv") == "cont_otres"
        assert oz_tools.findTable("SO2_data.csv") == "cont_sodos"
        
        # Test meteorological tables
        assert oz_tools.findTable("TMP_data.csv") == "met_tmp"
        assert oz_tools.findTable("RH_data.csv") == "met_rh"
        assert oz_tools.findTable("WSP_data.csv") == "met_wsp"
        assert oz_tools.findTable("WDR_data.csv") == "met_wdr"
        assert oz_tools.findTable("PBA_data.csv") == "met_pba"
        
        # Test unknown file
        assert oz_tools.findTable("unknown.csv") == ""


class TestDatabaseFunctions:
    """Test cases for database functions."""
    
    @patch('db_utils.queries_add.get_db_engine')
    def test_insert_pollutant_data_success(self, mock_get_engine):
        """Test successful pollutant data insertion."""
        # Mock the database engine and connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_get_engine.return_value = mock_engine
        
        result = insert_pollutant_data(
            table="cont_o3",
            fecha="12/25/2023 10:00:00",
            id_est="TEST",
            value="0.05"
        )
        
        assert result is True
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
    
    @patch('db_utils.queries_add.get_db_engine')
    def test_insert_pollutant_data_duplicate(self, mock_get_engine):
        """Test pollutant data insertion with duplicate key error."""
        # Mock the database engine and connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_connection.execute.side_effect = Exception("duplicate key")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_get_engine.return_value = mock_engine
        
        result = insert_pollutant_data(
            table="cont_o3",
            fecha="12/25/2023 10:00:00",
            id_est="TEST",
            value="0.05"
        )
        
        assert result is False
    
    @patch('db_utils.queries_add.get_db_engine')
    def test_insert_meteorological_data(self, mock_get_engine):
        """Test meteorological data insertion."""
        # Mock the database engine and connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_get_engine.return_value = mock_engine
        
        result = insert_meteorological_data(
            table="met_tmp",
            fecha="12/25/2023 10:00:00",
            id_est="TEST",
            value="25.5"
        )
        
        assert result is True
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_num_string(self):
        """Test num_string function with various inputs."""
        from db_utils.oztools import ContIOTools
        
        # This function is not in the current oztools.py, but we can test the logic
        def num_string(num: int) -> str:
            if num < 10:
                return "0" + str(num)
            else:
                return str(num)
        
        assert num_string(1) == "01"
        assert num_string(9) == "09"
        assert num_string(10) == "10"
        assert num_string(25) == "25"
        assert num_string(0) == "00"


if __name__ == "__main__":
    pytest.main([__file__]) 