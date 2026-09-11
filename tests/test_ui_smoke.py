from pathlib import Path


def test_research_ui_and_dashboard_modules_import():
    import views.dashboard_profissional as dashboard
    from views.dashboard_profissional import _pesquisa

    assert callable(dashboard.render)
    assert callable(_pesquisa.render)


def test_all_python_sources_compile():
    sources = list(Path(".").rglob("*.py"))
    ignored = {".git", ".venv", "venv", "__pycache__"}
    checked = 0
    for source in sources:
        if any(part in ignored for part in source.parts):
            continue
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
        checked += 1
    assert checked > 0
