import pytest
from services.text_to_sql_service import convert_text_to_sql


def test_convert_text_to_sql_users_query():
    """
    Tests that a simple query for users returns the correct SQL.
    """
    natural_language_query = "show me all users"
    expected_sql = "SELECT * FROM users;"
    result_sql = convert_text_to_sql(natural_language_query)
    assert result_sql == expected_sql


def test_convert_text_to_sql_products_count_query():
    """
    Tests that a query for the count of products returns the correct SQL.
    """
    natural_language_query = "count products"
    expected_sql = "SELECT COUNT(*) FROM products;"
    result_sql = convert_text_to_sql(natural_language_query)
    assert result_sql == expected_sql


def test_convert_text_to_sql_default_query():
    """
    Tests that a query that doesn't match any specific rule returns the default SQL.
    """
    natural_language_query = "what is the meaning of life"
    expected_sql = "SELECT name, price FROM products WHERE category = 'electronics' ORDER BY price DESC;"
    result_sql = convert_text_to_sql(natural_language_query)
    assert result_sql == expected_sql


def test_convert_text_to_sql_case_insensitivity():
    """
    Tests that the query matching is case-insensitive.
    """
    natural_language_query = "Show me all USERS"
    expected_sql = "SELECT * FROM users;"
    result_sql = convert_text_to_sql(natural_language_query)
    assert result_sql == expected_sql
