"""Node tests."""
import pytest

from pgsync.base import Base
from pgsync.exc import (
    MultipleThroughTablesError,
    NodeAttributeError,
    RelationshipAttributeError,
    RelationshipForeignKeyError,
    RelationshipTypeError,
    RelationshipVariantError,
    TableNotInNodeError,
)
from pgsync.node import ForeignKey, Node, Relationship, Tree


@pytest.mark.usefixtures("table_creator")
class TestNode(object):
    """Node tests."""

    @pytest.fixture(scope="function")
    def nodes(self):
        return {
            "schema": "public",
            "table": "book",
            "columns": ["isbn", "title", "description"],
            "children": [
                {
                    "schema": "public",
                    "table": "publisher",
                    "columns": ["name", "id"],
                    "label": "publisher_label",
                    "relationship": {
                        "variant": "object",
                        "type": "one_to_one",
                    },
                    "children": [],
                    "transform": {},
                },
                {
                    "schema": "public",
                    "table": "book_language",
                    "columns": ["book_isbn", "language_id"],
                    "label": "book_languages",
                    "relationship": {
                        "variant": "object",
                        "type": "one_to_many",
                    },
                },
                {
                    "schema": "public",
                    "table": "author",
                    "columns": ["id", "name"],
                    "label": "authors",
                    "relationship": {
                        "type": "one_to_many",
                        "variant": "object",
                        "through_tables": ["book_author"],
                    },
                    "children": [
                        {
                            "schema": "public",
                            "table": "city",
                            "columns": ["name", "id"],
                            "label": "city_label",
                            "relationship": {
                                "variant": "object",
                                "type": "one_to_one",
                            },
                            "children": [
                                {
                                    "schema": "public",
                                    "table": "country",
                                    "columns": ["name", "id"],
                                    "label": "country_label",
                                    "relationship": {
                                        "variant": "object",
                                        "type": "one_to_one",
                                    },
                                    "children": [
                                        {
                                            "schema": "public",
                                            "table": "continent",
                                            "columns": ["name"],
                                            "label": "continent_label",
                                            "relationship": {
                                                "variant": "object",
                                                "type": "one_to_one",
                                            },
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
                {
                    "schema": "public",
                    "table": "language",
                    "label": "languages",
                    "columns": ["code"],
                    "relationship": {
                        "type": "one_to_many",
                        "variant": "scalar",
                        "through_tables": ["book_language"],
                    },
                },
                {
                    "schema": "public",
                    "table": "subject",
                    "label": "subjects",
                    "columns": ["name"],
                    "relationship": {
                        "type": "one_to_many",
                        "variant": "scalar",
                        "through_tables": ["book_subject"],
                    },
                },
            ],
        }

    def test_node(self, connection):
        pg_base = Base(connection.engine.url.database)
        node = Node(
            models=pg_base.models,
            table="book",
            schema="public",
            label="book_label",
        )
        assert str(node) == "Node: public.book_label"

    def test_traverse_breadth_first(self, sync, nodes):
        root = Tree(sync.models).build(nodes)
        root.display()
        for i, node in enumerate(root.traverse_breadth_first()):
            if i == 0:
                assert node.table == "book"
            if i == 1:
                assert node.table == "publisher"
            if i == 2:
                assert node.table == "book_language"
            if i == 3:
                assert node.table == "author"
            if i == 4:
                assert node.table == "language"
            if i == 5:
                assert node.table == "subject"
            if i == 6:
                assert node.table == "city"
            if i == 7:
                assert node.table == "country"
            if i == 8:
                assert node.table == "continent"
        sync.search_client.close()

    def test_traverse_post_order(self, sync, nodes):
        root = Tree(sync.models).build(nodes)
        root.display()
        for i, node in enumerate(root.traverse_post_order()):
            if i == 0:
                assert node.table == "publisher"
            if i == 1:
                assert node.table == "book_language"
            if i == 2:
                assert node.table == "continent"
            if i == 3:
                assert node.table == "country"
            if i == 4:
                assert node.table == "city"
            if i == 5:
                assert node.table == "author"
            if i == 6:
                assert node.table == "language"
            if i == 7:
                assert node.table == "subject"
            if i == 8:
                assert node.table == "book"
        sync.search_client.close()

    def test_relationship(self, sync):
        nodes = {
            "table": "book",
            "children": [
                {
                    "table": "publisher",
                    "relationship": {
                        "xxx": "object",
                        "type": "one_to_one",
                    },
                },
            ],
        }
        with pytest.raises(RelationshipAttributeError) as excinfo:
            Tree(sync.models).build(nodes)
        assert "Relationship attribute " in str(excinfo.value)
        sync.search_client.close()

    def test_get_node(self, sync):
        nodes = {
            "table": "book",
            "children": [
                {
                    "table": "publisher",
                    "relationship": {
                        "variant": "object",
                        "type": "one_to_one",
                    },
                },
            ],
        }
        tree = Tree(sync.models)
        tree.build(nodes)
        node = tree.get_node("book", "public")
        assert str(node) == "Node: public.book"

        with pytest.raises(RuntimeError) as excinfo:
            tree.get_node("xxx", "public")
        assert "Node for public.xxx not found" in str(excinfo.value)

        sync.search_client.close()

    def test_tree_build(self, sync):
        with pytest.raises(TableNotInNodeError) as excinfo:
            Tree(sync.models).build(
                {
                    "table": None,
                }
            )

        with pytest.raises(NodeAttributeError) as excinfo:
            Tree(sync.models).build(
                {
                    "table": "book",
                    "foo": "bar",
                }
            )
        assert "Unknown node attribute(s):" in str(excinfo.value)

        with pytest.raises(NodeAttributeError) as excinfo:
            Tree(sync.models).build(
                {
                    "table": "book",
                    "children": [
                        {
                            "table": "publisher",
                            "columns": ["name", "id"],
                            "relationship": {
                                "variant": "object",
                                "type": "one_to_one",
                            },
                            "foo": "bar",
                        },
                    ],
                }
            )
        assert "Unknown node attribute(s):" in str(excinfo.value)

        with pytest.raises(TableNotInNodeError) as excinfo:
            Tree(sync.models).build(
                {
                    "table": "book",
                    "children": [
                        {
                            "columns": ["name", "id"],
                            "relationship": {
                                "variant": "object",
                                "type": "one_to_one",
                            },
                        },
                    ],
                }
            )
        assert "Table not specified in node" in str(excinfo.value)

        Tree(sync.models).build(
            {
                "table": "book",
                "columns": ["tags->0"],
            }
        )

        sync.search_client.close()


@pytest.mark.usefixtures("table_creator")
class TestForeignKey(object):
    """ForeignKey tests."""

    def test_init(self):
        foreign_key = ForeignKey({"child": ["id"], "parent": ["publisher_id"]})
        assert str(foreign_key) == "foreign_key: ['publisher_id']:['id']"
        with pytest.raises(RelationshipForeignKeyError) as excinfo:
            ForeignKey({"parent": ["publisher_id"]})
        assert (
            "ForeignKey Relationship must contain a parent and child."
            in str(excinfo.value)
        )


@pytest.mark.usefixtures("table_creator")
class TestRelationship(object):
    """Relationship tests."""

    def test_init(self):
        relationship = Relationship(
            {
                "variant": "object",
                "type": "one_to_one",
                "through_tables": ["book_author"],
            }
        )
        assert (
            str(relationship)
            == "relationship: object.one_to_one:['book_author']"
        )

        with pytest.raises(RelationshipAttributeError) as excinfo:
            Relationship(
                {
                    "foo": "bar",
                }
            )
        assert "Relationship attribute {'foo'} is invalid." in str(
            excinfo.value
        )

        with pytest.raises(RelationshipTypeError) as excinfo:
            Relationship(
                {
                    "type": "xyz",
                }
            )
        assert 'Relationship type "xyz" is invalid.' in str(excinfo.value)

        with pytest.raises(RelationshipVariantError) as excinfo:
            Relationship(
                {
                    "variant": "xyz",
                }
            )
        assert 'Relationship variant "xyz" is invalid.' in str(excinfo.value)

        with pytest.raises(MultipleThroughTablesError) as excinfo:
            Relationship(
                {
                    "variant": "object",
                    "type": "one_to_one",
                    "through_tables": ["book_author", "subject"],
                }
            )
        assert "Multiple through tables" in str(excinfo.value)
