"""Compat shim for pydub on Python 3.13+.

pydub imports `pyaudioop` as a drop-in replacement for the removed stdlib `audioop`.
We provide a tiny shim that re-exports whatever `audioop` module is available.

On Python 3.13, install `audioop-lts` (it provides `audioop`).
"""

try:
    from audioop import *  # type: ignore
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "No se pudo importar `audioop`. En Python 3.13 instala `audioop-lts`."
    ) from exc
