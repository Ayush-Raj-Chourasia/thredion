"""
Thredion Engine — API Route Tests
Covers every REST endpoint with success, error, and edge-case scenarios.
Run:  cd thredion-engine && python -m pytest tests/test_api.py -v
"""

import pytest
from tests.conftest import make_memory


# ── Root ────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_metadata(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Thredion Engine"
        assert data["status"] == "running"
        assert "endpoints" in data

    def test_docs_accessible(self, client):
        r = client.get("/docs")
        assert r.status_code == 200


# ── GET /api/memories ──────────────────────────────────────────

class TestListMemories:
    def test_empty_database(self, client):
        r = client.get("/api/memories")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_inserted_memory(self, client, db_session):
        make_memory(db_session, title="My First", url="https://example.com/1")
        r = client.get("/api/memories")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "My First"

    def test_search_filters_by_title(self, client, db_session):
        make_memory(db_session, title="Python Tips", url="https://a.com/1")
        make_memory(db_session, title="Cooking Tricks", url="https://a.com/2")
        r = client.get("/api/memories", params={"search": "python"})
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "Python Tips"

    def test_filter_by_category(self, client, db_session):
        make_memory(db_session, category="Fitness", url="https://a.com/1")
        make_memory(db_session, category="Coding", url="https://a.com/2")
        r = client.get("/api/memories", params={"category": "Fitness"})
        assert len(r.json()) == 1

    def test_sort_importance(self, client, db_session):
        make_memory(db_session, importance_score=30, url="https://a.com/lo")
        make_memory(db_session, importance_score=90, url="https://a.com/hi")
        r = client.get("/api/memories", params={"sort": "importance"})
        scores = [m["importance_score"] for m in r.json()]
        assert scores == sorted(scores, reverse=True)

    def test_limit_parameter(self, client, db_session):
        for i in range(5):
            make_memory(db_session, url=f"https://a.com/{i}")
        r = client.get("/api/memories", params={"limit": 2})
        assert len(r.json()) == 2


# ── GET /api/memories/{id} ────────────────────────────────────

class TestGetMemory:
    def test_existing(self, client, db_session):
        m = make_memory(db_session)
        r = client.get(f"/api/memories/{m.id}")
        assert r.status_code == 200
        assert r.json()["id"] == m.id

    def test_not_found(self, client):
        r = client.get("/api/memories/99999")
        assert r.status_code == 404


# ── DELETE /api/memories/{id} ─────────────────────────────────

class TestDeleteMemory:
    def test_delete_existing(self, client, db_session):
        m = make_memory(db_session)
        r = client.delete(f"/api/memories/{m.id}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Memory deleted"
        # Verify gone
        r2 = client.get(f"/api/memories/{m.id}")
        assert r2.status_code == 404

    def test_delete_nonexistent(self, client):
        r = client.delete("/api/memories/99999")
        assert r.status_code == 404


# ── POST /api/process ─────────────────────────────────────────

class TestProcessEndpoint:
    def test_invalid_url_rejected(self, client):
        r = client.post("/api/process", params={"url": "not-a-url"})
        assert r.status_code == 400

    def test_empty_url_rejected(self, client):
        r = client.post("/api/process", params={"url": "   "})
        assert r.status_code == 400


# ── GET /api/graph ────────────────────────────────────────────

class TestKnowledgeGraph:
    def test_empty_graph(self, client):
        r = client.get("/api/graph")
        assert r.status_code == 200
        data = r.json()
        assert data["nodes"] == []
        assert data["edges"] == []

    def test_graph_reflects_memories(self, client, db_session):
        make_memory(db_session, title="Node A", url="https://a.com/a")
        make_memory(db_session, title="Node B", url="https://a.com/b")
        r = client.get("/api/graph")
        assert len(r.json()["nodes"]) == 2


# ── GET /api/stats ────────────────────────────────────────────

class TestStats:
    def test_stats_empty(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        s = r.json()
        assert s["total_memories"] == 0
        assert s["total_connections"] == 0

    def test_stats_counts(self, client, db_session):
        make_memory(db_session, category="Coding", url="https://a.com/1")
        make_memory(db_session, category="Coding", url="https://a.com/2")
        make_memory(db_session, category="Fitness", url="https://a.com/3")
        r = client.get("/api/stats")
        s = r.json()
        assert s["total_memories"] == 3
        assert s["categories"]["Coding"] == 2
        assert s["top_category"] == "Coding"


# ── GET /api/categories ──────────────────────────────────────

class TestCategories:
    def test_empty(self, client):
        r = client.get("/api/categories")
        assert r.json() == []

    def test_returns_counts(self, client, db_session):
        make_memory(db_session, category="Design", url="https://a.com/1")
        make_memory(db_session, category="Design", url="https://a.com/2")
        make_memory(db_session, category="Music", url="https://a.com/3")
        cats = client.get("/api/categories").json()
        names = [c["category"] for c in cats]
        assert "Design" in names
        # Design should be first (count 2 > 1)
        assert cats[0]["category"] == "Design"
        assert cats[0]["count"] == 2


# ── GET /api/random ──────────────────────────────────────────

class TestRandomMemory:
    def test_empty_db(self, client):
        assert client.get("/api/random").status_code == 404

    def test_returns_a_memory(self, client, db_session):
        make_memory(db_session)
        r = client.get("/api/random")
        assert r.status_code == 200
        assert "id" in r.json()


# ── GET /api/resurfaced ──────────────────────────────────────

class TestResurfaced:
    def test_empty(self, client):
        r = client.get("/api/resurfaced")
        assert r.status_code == 200
        assert r.json() == []
