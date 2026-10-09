from novamarket.work import find, load_incidents, load_tickets, visible_tickets


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_and_find_ticket(tmp_path):
    _write(tmp_path / "tickets" / "NM-001.yaml", "title: Ingestão\nstatus: READY\n")
    tickets = load_tickets(tmp_path)
    assert find(tickets, "nm-001")["title"] == "Ingestão"
    assert find(tickets, "NM-999") is None


def test_ready_ticket_with_open_dependency_is_blocked(tmp_path):
    _write(tmp_path / "tickets" / "NM-001.yaml", "status: IN_PROGRESS\n")
    _write(tmp_path / "tickets" / "NM-002.yaml", "status: READY\ndepends_on: [NM-001]\n")
    by_id = {t["id"]: t["status"] for t in visible_tickets(load_tickets(tmp_path))}
    assert by_id == {"NM-001": "IN_PROGRESS", "NM-002": "BLOCKED"}


def test_dependency_done_unblocks(tmp_path):
    _write(tmp_path / "tickets" / "NM-001.yaml", "status: DONE\n")
    _write(tmp_path / "tickets" / "NM-002.yaml", "status: READY\ndepends_on: [NM-001]\n")
    assert {t["id"]: t["status"] for t in visible_tickets(load_tickets(tmp_path))}["NM-002"] == "READY"


def test_missing_dirs_return_empty(tmp_path):
    assert load_tickets(tmp_path) == [] and load_incidents(tmp_path) == []


def test_real_backlog_is_consistent():
    from novamarket.work import ROOT

    tickets = load_tickets(ROOT)
    ids = {t["id"] for t in tickets}
    assert len(tickets) == 12
    assert {t["level"] for t in tickets} == {1, 2, 3, 4, 5, 6}
    for t in tickets:
        assert set(t.get("depends_on") or []) <= ids
        assert t["acceptance_criteria"]
    assert [t["id"] for t in tickets if t["status"] == "READY"] == ["NM-001"]
    incident_ids = {i["id"] for i in load_incidents(ROOT)}
    assert {t["incident"] for t in tickets if t.get("incident")} <= incident_ids
