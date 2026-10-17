"""Offline tests: main.py against a local fake of the Apify API (no token or network needed)."""

from __future__ import annotations

import csv
import gzip
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import main

ITEMS = [{"name": "first", "price": 1}, {"name": "second", "price": 2}]


class FakeApify(BaseHTTPRequestHandler):
    run_status = "SUCCEEDED"
    calls: list[tuple[str, str, dict]] = []

    def log_message(self, *args):
        pass

    def _send(self, body, content_type="application/json"):
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(200 if self.command == "GET" else 201)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _run(self):
        return {
            "data": {
                "id": "run1",
                "actId": "act1",
                "userId": "user1",
                "status": self.run_status,
                "statusMessage": "Input is invalid" if self.run_status != "SUCCEEDED" else None,
                "defaultDatasetId": "ds1",
                "defaultKeyValueStoreId": "kv1",
                "defaultRequestQueueId": "rq1",
                "startedAt": "2026-01-01T00:00:00.000Z",
                "finishedAt": "2026-01-01T00:01:00.000Z",
                "buildId": "b1",
                "buildNumber": "0.1.1",
                "meta": {"origin": "API"},
                "stats": {},
                "options": {"build": "latest", "timeoutSecs": 3600, "memoryMbytes": 1024, "diskMbytes": 2048},
            }
        }

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        try:
            parsed = json.loads(body or b"null")
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = json.loads(gzip.decompress(body))
        FakeApify.calls.append(("POST", self.path, parsed))
        self._send(self._run())

    def do_GET(self):
        FakeApify.calls.append(("GET", self.path, {}))
        path = self.path.split("?")[0]
        if re.fullmatch(r"/v2/act(or)?s/[^/]+", path):
            self._send(
                {
                    "data": {
                        "id": "act1",
                        "userId": "user1",
                        "name": "actor",
                        "username": "user",
                        "isPublic": True,
                        "createdAt": "2026-01-01T00:00:00.000Z",
                        "modifiedAt": "2026-01-01T00:00:00.000Z",
                        "stats": {},
                        "versions": [],
                        "defaultRunOptions": {"build": "latest", "timeoutSecs": 3600, "memoryMbytes": 1024},
                    }
                }
            )
        elif path.endswith("/log"):
            self._send(b"", "text/plain")
        elif path.startswith("/v2/datasets/ds1/items"):
            if "format=csv" in self.path:
                self._send(b"name,price\nfirst,1\nsecond,2\n", "text/csv")
            else:
                self._send(ITEMS)
        else:
            self._send(self._run())


@pytest.fixture
def api(monkeypatch):
    FakeApify.calls = []
    FakeApify.run_status = "SUCCEEDED"
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeApify)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("APIFY_TOKEN", "test-token")
    monkeypatch.setenv("APIFY_API_URL", f"http://127.0.0.1:{server.server_port}")
    yield FakeApify
    server.shutdown()


def write_input(tmp_path: Path, data) -> str:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_success_saves_json_and_csv(api, tmp_path):
    out = tmp_path / "out"
    assert main.main([write_input(tmp_path, {"q": "x"}), "--out", str(out)]) == 0
    assert json.loads((out / "results.json").read_text()) == ITEMS
    rows = list(csv.DictReader((out / "results.csv").open()))
    assert [r["name"] for r in rows] == ["first", "second"]
    start = next(c for c in api.calls if c[0] == "POST")
    assert re.match(r"/v2/act(or)?s/" + re.escape(main.ACTOR_ID.replace("/", "~")) + "/runs", start[1])
    assert start[2] == {"q": "x"}


def test_max_charge_is_sent(api, tmp_path):
    assert main.main([write_input(tmp_path, {}), "--out", str(tmp_path), "--max-charge", "0.5"]) == 0
    start = next(c for c in api.calls if c[0] == "POST")
    assert "maxTotalChargeUsd=0.5" in start[1]


def test_failed_run_returns_nonzero(api, tmp_path, capsys):
    api.run_status = "FAILED"
    assert main.main([write_input(tmp_path, {}), "--out", str(tmp_path)]) == 1
    assert "Input is invalid" in capsys.readouterr().err
    assert not (tmp_path / "results.json").exists()


def test_missing_token_stops(monkeypatch, tmp_path):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="APIFY_TOKEN"):
        main.main([write_input(tmp_path, {})])


@pytest.mark.parametrize("content, message", [(None, "not found"), ("{oops", "not valid JSON"), ("[1]", "JSON object")])
def test_bad_input_file(monkeypatch, tmp_path, content, message):
    monkeypatch.setenv("APIFY_TOKEN", "test-token")
    path = tmp_path / "input.json"
    if content is not None:
        path.write_text(content)
    with pytest.raises(SystemExit, match=message):
        main.main([str(path)])


def test_bundled_input_is_valid_json_object():
    assert isinstance(json.loads(Path(main.__file__).with_name("input.json").read_text()), dict)
