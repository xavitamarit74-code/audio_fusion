import pytest


def test_file_path_supports_no_extension(tmp_path, monkeypatch):
    import backend.app as app

    monkeypatch.setattr(app, "FILES_DIR", tmp_path)

    file_id = "abc123"
    expected = tmp_path / file_id
    expected.write_bytes(b"data")

    assert app._file_path(file_id) == expected


def test_file_path_supports_with_extension(tmp_path, monkeypatch):
    import backend.app as app

    monkeypatch.setattr(app, "FILES_DIR", tmp_path)

    file_id = "abc123"
    expected = tmp_path / f"{file_id}.mp3"
    expected.write_bytes(b"data")

    assert app._file_path(file_id) == expected


def test_file_path_prefers_exact_match_over_extension(tmp_path, monkeypatch):
    import backend.app as app

    monkeypatch.setattr(app, "FILES_DIR", tmp_path)

    file_id = "abc123"
    exact = tmp_path / file_id
    with_ext = tmp_path / f"{file_id}.mp3"

    exact.write_bytes(b"exact")
    with_ext.write_bytes(b"ext")

    assert app._file_path(file_id) == exact


def test_file_path_raises_when_missing(tmp_path, monkeypatch):
    import backend.app as app

    monkeypatch.setattr(app, "FILES_DIR", tmp_path)

    with pytest.raises(app.HTTPException) as exc:
        app._file_path("does_not_exist")

    assert exc.value.status_code == 404
