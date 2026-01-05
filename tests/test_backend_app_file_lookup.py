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


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, "mp3"),
        ("mp3", "mp3"),
        (".mp3", "mp3"),
        (" audio_fusion.mp3 ", "mp3"),
        ("M4A", "m4a"),
        (".m4r", "m4r"),
        ("audio_fusion.m4r", "m4r"),
        ("mp4", "mp4"),
        ("aac", "aac"),
    ],
)
def test_normalize_output_format(raw, expected):
    import backend.app as app

    assert app._normalize_output_format(raw) == expected


def test_allowed_output_formats_include_aac_family():
    import backend.app as app

    for ext in {"m4a", "m4r", "mp4", "aac"}:
        assert ext in app._ALLOWED_OUTPUT_FORMATS
