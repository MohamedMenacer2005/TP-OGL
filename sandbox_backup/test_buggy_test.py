"""
Tests for buggy_test.py
Testing various functions to verify they work correctly
"""

import pytest
from buggy_test import (
    calculate_total_with_tax,
    greet_user,
    process_order,
    BankAccount,
    read_file_unsafe,
    parse_json_unsafe,
    divide_unsafe
)


class TestCalculations:
    """Test calculation functions"""
    
    def test_calculate_total_with_tax_basic(self):
        """Test basic tax calculation"""
        result = calculate_total_with_tax(100)
        assert result == 110  # 100 + (100 * 0.1)
    
    def test_greet_user_basic(self):
        """Test greeting function"""
        result = greet_user("Alice")
        assert result == "Hello, Alice!"


class TestBankAccount:
    """Test BankAccount class"""
    
    def test_account_initialization(self):
        """Test account creation"""
        account = BankAccount("John", 1000)
        assert account.owner == "John"
        assert account.balance == 1000
    
    def test_account_deposit(self):
        """Test depositing money"""
        account = BankAccount("Jane", 500)
        account.deposit(250)
        assert account.balance == 750
    
    def test_account_withdraw(self):
        """Test withdrawing money"""
        account = BankAccount("Bob", 1000)
        account.withdraw(300)
        assert account.balance == 700


class TestDivideFunction:
    """Test divide function"""
    
    def test_divide_positive_numbers(self):
        """Test dividing two positive numbers"""
        result = divide_unsafe(10, 2)
        assert result == 5
    
    def test_divide_with_zero_raises_error(self):
        """Test that dividing by zero raises error"""
        with pytest.raises(ValueError):
            divide_unsafe(10, 0)


class TestFileOperations:
    """Test file operation functions"""
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist"""
        result = read_file_unsafe("/nonexistent/file.txt")
        assert result is None


class TestJSONParsing:
    """Test JSON parsing functions"""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON"""
        result = parse_json_unsafe('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        result = parse_json_unsafe("not json")
        assert result is None


# Global variable (bad practice)
GLOBAL_COUNTER=0

def increment_counter():
    global GLOBAL_COUNTER
    GLOBAL_COUNTER+=1
    return GLOBAL_COUNTER