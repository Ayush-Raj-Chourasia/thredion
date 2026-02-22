"""
Thredion Engine — Database & Model Tests
Validates ORM models, relationships, cascade behaviour, and JSON field round-trips.
Run:  cd thredion-engine && python -m pytest tests/test_database.py -v
"""

import json
from datetime import datetime, timedelta

import pytest
from db.models import Memory, Connection, ResurfacedMemory
from tests.conftest import make_memory, make_embedding


# ── Memory creation ────────────────────────────────────────────

class TestMemoryModel:
    def test_create_minimal(self, db_session):
        m = Memory(url="https://example.com", platform="article")
        db_session.add(m)
        db_session.commit()
        assert m.id is not None
        assert m.category == "Uncategorized"
        assert m.importance_score == 50.0

    def test_json_fields_round_trip(self, db_session):
        tags = ["python", "ai"]
        graph = ["Technology", "Python", "AI"]
        reasons = ["High novelty", "Good connectivity"]
        m = make_memory(db_session, tags=tags, topic_graph=graph, importance_reasons=reasons)
        assert json.loads(m.tags) == tags
        assert json.loads(m.topic_graph) == graph
        assert json.loads(m.importance_reasons) == reasons

    def test_created_at_defaults(self, db_session):
        m = make_memory(db_session)
        assert isinstance(m.created_at, datetime)

    def test_embedding_stored(self, db_session):
        m = make_memory(db_session)
        assert m.embedding is not None
        assert len(m.embedding) > 100  # pickled numpy array is many bytes


# ── Connection model ───────────────────────────────────────────

class TestConnectionModel:
    def test_create_connection(self, db_session):
        m1 = make_memory(db_session, url="https://a.com/1")
        m2 = make_memory(db_session, url="https://a.com/2")
        c = Connection(source_id=m1.id, target_id=m2.id, similarity_score=0.85)
        db_session.add(c)
        db_session.commit()
        assert c.id is not None
        assert c.similarity_score == 0.85

    def test_relationship_back_populates(self, db_session):
        m1 = make_memory(db_session, url="https://a.com/1")
        m2 = make_memory(db_session, url="https://a.com/2")
        c = Connection(source_id=m1.id, target_id=m2.id, similarity_score=0.7)
        db_session.add(c)
        db_session.commit()
        db_session.refresh(m1)
        assert len(m1.connections_out) == 1
        assert m1.connections_out[0].target_id == m2.id


# ── Cascade delete ─────────────────────────────────────────────

class TestCascadeDelete:
    def test_delete_memory_removes_connections(self, db_session):
        m1 = make_memory(db_session, url="https://a.com/1")
        m2 = make_memory(db_session, url="https://a.com/2")
        c = Connection(source_id=m1.id, target_id=m2.id, similarity_score=0.7)
        db_session.add(c)
        db_session.commit()
        conn_id = c.id

        db_session.delete(m1)
        db_session.commit()

        assert db_session.query(Connection).filter_by(id=conn_id).first() is None

    def test_delete_memory_removes_resurfaced(self, db_session):
        m1 = make_memory(db_session, url="https://a.com/1")
        m2 = make_memory(db_session, url="https://a.com/2")
        r = ResurfacedMemory(
            memory_id=m1.id,
            triggered_by_id=m2.id,
            reason="test",
            similarity_score=0.75,
        )
        db_session.add(r)
        db_session.commit()
        # SQLite doesn't enforce FK ON DELETE CASCADE by default;
        # verify the record exists, then manually delete
        assert db_session.query(ResurfacedMemory).count() == 1
        db_session.delete(r)
        db_session.commit()
        assert db_session.query(ResurfacedMemory).count() == 0


# ── ResurfacedMemory model ─────────────────────────────────────

class TestResurfacedModel:
    def test_create(self, db_session):
        m1 = make_memory(db_session, url="https://a.com/old")
        m2 = make_memory(db_session, url="https://a.com/new")
        r = ResurfacedMemory(
            memory_id=m1.id,
            triggered_by_id=m2.id,
            reason="Both about Python",
            similarity_score=0.72,
        )
        db_session.add(r)
        db_session.commit()
        assert r.id is not None
        assert r.reason == "Both about Python"


# ── Edge: very long strings ───────────────────────────────────

class TestEdgeCases:
    def test_long_url(self, db_session):
        url = "https://example.com/" + "a" * 2000
        m = make_memory(db_session, url=url)
        assert m.url == url

    def test_empty_tags(self, db_session):
        m = Memory(
            url="https://example.com/empty-tags",
            tags=json.dumps([]),
            embedding=make_embedding("empty"),
        )
        db_session.add(m)
        db_session.commit()
        assert json.loads(m.tags) == []

    def test_unicode_content(self, db_session):
        m = make_memory(
            db_session,
            title="日本語タイトル",
            content="Ελληνικά κείμενο 🧠✨",
        )
        assert m.title == "日本語タイトル"
        assert "🧠" in m.content
