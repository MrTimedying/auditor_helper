#!/usr/bin/env python3
"""
Unit tests for the chart constraints and data aggregation for tapered flexibility refactor.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_module.chart_constraints import (
    get_allowed_x_variables, get_allowed_y_variables, get_allowed_chart_types,
    get_compatible_chart_types, validate_variable_combination,
    categorize_time_to_range, get_time_range_display_name
)

class TestChartConstraints(unittest.TestCase):
    
    def test_get_allowed_variables(self):
        """Test that allowed variables are returned correctly"""
        x_vars = get_allowed_x_variables()
        y_vars = get_allowed_y_variables()
        chart_types = get_allowed_chart_types()
        
        # Check that we have the expected X variables
        expected_x = ['time_day', 'time_week', 'time_month', 'projects', 'claim_time_ranges']
        self.assertEqual(set(x_vars.keys()), set(expected_x))
        
        # Check that we have the expected Y variables
        expected_y = ['duration_average', 'claim_datetime_average', 'money_made_total', 
                     'money_made_average', 'time_usage_percent', 'fail_rate_percent', 'average_rating']
        self.assertEqual(set(y_vars.keys()), set(expected_y))
        
        # Check that we have the expected chart types
        expected_charts = ['line', 'bar']
        self.assertEqual(set(chart_types.keys()), set(expected_charts))
    
    def test_get_compatible_chart_types(self):
        """Test chart type compatibility with X variables"""
        # Time variables should be compatible with both line and bar
        self.assertIn('line', get_compatible_chart_types('time_day'))
        self.assertIn('bar', get_compatible_chart_types('time_day'))
        
        # Projects should only be compatible with bar
        compatible = get_compatible_chart_types('projects')
        self.assertIn('bar', compatible)
        self.assertNotIn('line', compatible)
        
        # Claim time ranges should only be compatible with bar
        compatible = get_compatible_chart_types('claim_time_ranges')
        self.assertIn('bar', compatible)
        self.assertNotIn('line', compatible)
    
    def test_validate_variable_combination(self):
        """Test validation of variable combinations"""
        # Valid combinations
        valid_result = validate_variable_combination('time_day', 'duration_average', 'line')
        self.assertTrue(valid_result[0])
        
        valid_result = validate_variable_combination('projects', 'money_made_total', 'bar')
        self.assertTrue(valid_result[0])
        
        # Invalid X variable
        invalid_result = validate_variable_combination('invalid_x', 'duration_average', 'bar')
        self.assertFalse(invalid_result[0])
        
        # Invalid Y variable
        invalid_result = validate_variable_combination('time_day', 'invalid_y', 'bar')
        self.assertFalse(invalid_result[0])
        
        # Invalid chart type
        invalid_result = validate_variable_combination('time_day', 'duration_average', 'invalid_chart')
        self.assertFalse(invalid_result[0])
        
        # Incompatible combination (line chart with categorical X)
        invalid_result = validate_variable_combination('projects', 'duration_average', 'line')
        self.assertFalse(invalid_result[0])
    
    def test_categorize_time_to_range(self):
        """Test time categorization to ranges"""
        # Morning
        self.assertEqual(categorize_time_to_range('2024-01-01 08:30:00'), 'morning')
        
        # Noon
        self.assertEqual(categorize_time_to_range('2024-01-01 13:15:00'), 'noon')
        
        # Afternoon
        self.assertEqual(categorize_time_to_range('2024-01-01 16:45:00'), 'afternoon')
        
        # Night
        self.assertEqual(categorize_time_to_range('2024-01-01 20:00:00'), 'night')
        self.assertEqual(categorize_time_to_range('2024-01-01 02:00:00'), 'night')
        
        # Invalid/empty input
        self.assertEqual(categorize_time_to_range(''), 'unknown')
        self.assertEqual(categorize_time_to_range(None), 'unknown')
        self.assertEqual(categorize_time_to_range('invalid'), 'unknown')
    
    def test_get_time_range_display_name(self):
        """Test time range display name retrieval"""
        self.assertIn('Morning', get_time_range_display_name('morning'))
        self.assertIn('Noon', get_time_range_display_name('noon'))
        self.assertIn('Afternoon', get_time_range_display_name('afternoon'))
        self.assertIn('Night', get_time_range_display_name('night'))
        self.assertEqual(get_time_range_display_name('invalid'), 'Unknown')


class TestDataAggregationMethods(unittest.TestCase):
    """
    Test the data aggregation methods (these would require a test database or mocked data)
    For now, just test that the methods can be imported and called without errors
    """
    
    def test_import_data_manager(self):
        """Test that DataManager can be imported with new methods"""
        try:
            from analysis_module.data_manager import DataManager
            dm = DataManager()
            
            # Check that new methods exist
            self.assertTrue(hasattr(dm, 'get_constrained_chart_data'))
            self.assertTrue(hasattr(dm, '_aggregate_constrained_data'))
            self.assertTrue(hasattr(dm, '_calculate_duration_average'))
            self.assertTrue(hasattr(dm, '_calculate_money_total'))
            self.assertTrue(hasattr(dm, '_calculate_fail_rate_percent'))
            
        except ImportError as e:
            self.fail(f"Failed to import DataManager: {e}")
    
    def test_time_parsing_methods(self):
        """Test time parsing functionality"""
        from analysis_module.data_manager import DataManager
        dm = DataManager()
        
        # Test basic time parsing
        seconds = dm._parse_time_to_seconds('01:30:45')
        expected = 1 * 3600 + 30 * 60 + 45  # 5445 seconds
        self.assertEqual(seconds, expected)
        
        # Test edge cases
        self.assertEqual(dm._parse_time_to_seconds(''), 0)
        self.assertEqual(dm._parse_time_to_seconds(None), 0)
        self.assertEqual(dm._parse_time_to_seconds('invalid'), 0)


if __name__ == '__main__':
    unittest.main() 