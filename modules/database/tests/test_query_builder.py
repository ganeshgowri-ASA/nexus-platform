"""
Tests for Query Builder
"""

import pytest
from ..query_builder import (
    Query, QueryBuilder, Column, TableRef, Filter,
    JoinType, OperatorType, SortOrder
)


class TestQuery:
    """Test Query class"""

    def test_simple_select(self):
        """Test simple SELECT query"""
        query = Query()
        query.select("id", "name").from_("users")

        sql, params = query.to_sql(use_params=False)

        assert "SELECT id, name" in sql
        assert "FROM users" in sql

    def test_select_with_where(self):
        """Test SELECT with WHERE clause"""
        query = Query()
        query.select("id", "name").from_("users").where("id", OperatorType.EQUALS, 1)

        sql, params = query.to_sql()

        assert "WHERE" in sql
        assert len(params) > 0

    def test_select_with_join(self):
        """Test SELECT with JOIN"""
        query = Query()
        query.select("u.name", "o.total").from_("users", alias="u")
        query.join("orders", Column("u.id"), Column("o.user_id"), JoinType.INNER)

        sql, params = query.to_sql(use_params=False)

        assert "INNER JOIN" in sql

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY"""
        query = Query()
        query.select("name").from_("users").order("name", SortOrder.DESC)

        sql, params = query.to_sql(use_params=False)

        assert "ORDER BY" in sql
        assert "DESC" in sql

    def test_select_with_limit(self):
        """Test SELECT with LIMIT"""
        query = Query()
        query.select("*").from_("users").limit_offset(limit=10, offset=20)

        sql, params = query.to_sql(use_params=False)

        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql

    def test_select_distinct(self):
        """Test SELECT DISTINCT"""
        query = Query()
        query.select("category").from_("products").set_distinct(True)

        sql, params = query.to_sql(use_params=False)

        assert "SELECT DISTINCT" in sql


class TestQueryBuilder:
    """Test QueryBuilder class"""

    def test_create_query(self):
        """Test creating query"""
        builder = QueryBuilder()
        query = builder.create_query("test_query")

        assert "test_query" in builder.queries
        assert isinstance(query, Query)

    def test_save_and_get_query(self):
        """Test saving and retrieving query"""
        builder = QueryBuilder()
        query = Query().select("*").from_("users")

        builder.save_query("my_query", query)

        retrieved = builder.get_query("my_query")
        assert retrieved is query

    def test_list_queries(self):
        """Test listing queries"""
        builder = QueryBuilder()

        builder.save_query("query1", Query())
        builder.save_query("query2", Query())

        queries = builder.list_queries()
        assert len(queries) == 2
        assert "query1" in queries
        assert "query2" in queries

    def test_delete_query(self):
        """Test deleting query"""
        builder = QueryBuilder()
        builder.save_query("to_delete", Query())

        builder.delete_query("to_delete")

        assert "to_delete" not in builder.queries
