from pathlib import Path

from pywebui import graph


def test_graph_links_lexically_related_nodes(tmp_path: Path):
    path = tmp_path / "graph.json"
    graph.update(path, {"id": "one", "title": "Launch plan", "summary": "release date", "archived": False})
    data = graph.update(path, {"id": "two", "title": "Launch review", "summary": "release date", "archived": False})
    assert len(data["edges"]) == 1
    assert data["edges"][0]["strength"] > 0


def test_graph_relation_callback_can_override_strength(tmp_path: Path):
    path = tmp_path / "graph.json"
    graph.update(path, {"id": "one", "title": "Launch plan", "summary": "release date", "archived": False})
    data = graph.update(
        path,
        {"id": "two", "title": "Launch review", "summary": "release date", "archived": False},
        relation=lambda current, previous: 0.91,
    )
    assert data["edges"][0]["strength"] == 0.91


def test_graph_keeps_lexical_score_when_relation_fails(tmp_path: Path):
    path = tmp_path / "graph.json"
    graph.update(path, {"id": "one", "title": "Launch plan", "summary": "release date", "archived": False})
    data = graph.update(
        path,
        {"id": "two", "title": "Launch review", "summary": "release date", "archived": False},
        relation=lambda current, previous: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert data["edges"][0]["strength"] > 0


def test_graph_wipe_resets_graph(tmp_path: Path):
    path = tmp_path / "graph.json"
    graph.update(path, {"id": "one", "title": "Launch plan", "summary": "release date", "archived": False})
    data = graph.wipe(path)
    assert data == {"version": 1, "nodes": [], "edges": []}
    assert path.exists()


def test_graph_rebuild_from_storage(tmp_path: Path):
    from pywebui.storage import Chunk, Metadata, Storage

    storage = Storage(tmp_path)
    rec = storage.create("rec1")
    meta = rec.read_metadata()
    meta.chunks = [
        Chunk(
            index=1,
            title="Launch plan",
            start=1,
            end=10,
            slug="launch-plan",
            completeness=80,
            quality=85,
        ),
        Chunk(
            index=2,
            title="Launch review",
            start=11,
            end=20,
            slug="launch-review",
            completeness=75,
            quality=80,
        ),
    ]
    rec.write_metadata(meta)
    rec.chunk_txt(1, "launch-plan").write_text("We are planning the launch date and release milestones.", encoding="utf-8")
    rec.chunk_summary_txt(1, "launch-plan").write_text("Launch plan and release date discussion.", encoding="utf-8")
    rec.chunk_txt(2, "launch-review").write_text("Reviewing the launch date and progress on release.", encoding="utf-8")
    rec.chunk_summary_txt(2, "launch-review").write_text("Launch review and release date summary.", encoding="utf-8")

    path = tmp_path / "graph.json"
    data = graph.rebuild_from_storage(path, storage)
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["strength"] > 0
