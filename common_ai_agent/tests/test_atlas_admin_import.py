import builtins
import importlib
import sys


def test_atlas_admin_module_import_does_not_import_fastapi(monkeypatch):
    sys.modules.pop("src.atlas_admin", None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "fastapi":
            raise RuntimeError("fastapi import should be deferred")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = importlib.import_module("src.atlas_admin")

    assert module.__name__ == "src.atlas_admin"
