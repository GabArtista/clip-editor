import sys
import types

try:
    from metrics import reset_registry as _reset_metrics_registry
except Exception:  # pragma: no cover - fallback when metrics not available
    _reset_metrics_registry = None


def reset_app_modules() -> None:
    """
    Remove módulos 'app' e 'jobs' do cache do Python para que possam ser importados
    novamente com o ambiente configurado para cada teste.
    """
    if _reset_metrics_registry is not None:
        _reset_metrics_registry()

    db_module = sys.modules.get("app.database")
    if db_module is not None:
        base = getattr(db_module, "Base", None)
        if base is not None:
            base.metadata.clear()
            if hasattr(base, "registry"):
                base.registry.dispose()

    prefixes = ("app", "jobs", "api")
    for name in list(sys.modules.keys()):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def ensure_multipart_stub() -> None:
    if "multipart" in sys.modules and "multipart.multipart" in sys.modules:
        return

    multipart_module = types.ModuleType("multipart")
    multipart_module.__version__ = "0.0-test"
    submodule = types.ModuleType("multipart.multipart")

    def parse_options_header(value):  # noqa: ANN001,D401 - comportamento mínimo para testes
        """Stub que imita a assinatura esperada."""
        return {}

    submodule.parse_options_header = parse_options_header
    sys.modules.setdefault("multipart", multipart_module)
    sys.modules.setdefault("multipart.multipart", submodule)
