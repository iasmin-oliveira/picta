from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_global_typography_layer_exists_and_has_accessibility_tokens():
    css = (ROOT / "assets" / "picta_typography_accessibility.css").read_text(encoding="utf-8")

    required_tokens = (
        "--picta-font-body",
        "--picta-font-label",
        "--picta-font-control",
        "--picta-touch-min",
        "--picta-touch-preferred",
    )
    for token in required_tokens:
        assert token in css

    assert "font-size: 1rem !important" in css
    assert "min-height: 48px !important" in css
    assert ".pc-picto-name" in css


def test_global_typography_layer_has_explicit_responsive_rules():
    css = (ROOT / "assets" / "picta_typography_accessibility.css").read_text(encoding="utf-8")

    assert "@media (min-width: 721px) and (max-width: 1199px)" in css
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 560px)" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr)) !important" in css
    assert "grid-template-columns: 1fr !important" in css


def test_final_ui_overrides_preserve_logo_size_and_compact_return_button():
    css = (ROOT / "assets" / "picta_ui_final_overrides.css").read_text(encoding="utf-8")

    assert ".picta-logo h1" in css
    assert "font-size: 3.2rem !important" in css
    assert "picta-return-button" in css
    assert "height: 44px !important" in css


def test_css_loader_registers_global_and_final_ui_layers_in_order():
    loader = (ROOT / "utils" / "css_loader.py").read_text(encoding="utf-8")

    assert 'GLOBAL_CSS = "picta_typography_accessibility.css"' in loader
    assert 'FINAL_CSS = "picta_ui_final_overrides.css"' in loader
    assert "global_css_path" in loader
    assert "final_css_path" in loader
    assert loader.index("global_css_path") < loader.index("final_css_path")


def test_navigation_and_user_guide_are_documented():
    navigation = ROOT / "docs" / "MAPA_NAVEGACAO.md"
    guide = ROOT / "docs" / "GUIA_DE_USO.md"

    assert navigation.exists()
    assert guide.exists()

    nav_text = navigation.read_text(encoding="utf-8")
    guide_text = guide.read_text(encoding="utf-8")

    for label in ("Criança", "Responsável / Cuidador", "Profissional de Saúde", "Coleta TCC"):
        assert label in nav_text
        assert label in guide_text


def test_known_ui_spelling_issues_are_absent():
    files = (
        ROOT / "views" / "login.py",
        ROOT / "views" / "cadastro.py",
        ROOT / "views" / "dashboard_cuidador" / "_perfil.py",
        ROOT / "views" / "dashboard_profissional" / "_perfil.py",
    )
    forbidden_phrases = (
        "Nome de utilizador",
        "Email de recuperacao",
        "Obrigatorio para",
        "Username do responsável",
        "Username da criança",
        "Senha da crianca",
        "Nova senha da crianca",
        "Confirmar senha da crianca",
        "Atualizar senha da crianca",
        "As senhas nao coincidem",
        "Minimo 6 caracteres",
        "Senha da crianca atualizada",
        "Enviar senha temporaria",
    )

    for path in files:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in text, f"Encontrado texto não revisado em {path}: {phrase}"


def test_ui_round_is_frontend_only():
    changed_targets = {
        "assets/picta_typography_accessibility.css",
        "assets/picta_ui_final_overrides.css",
        "utils/css_loader.py",
        "docs/MAPA_NAVEGACAO.md",
        "docs/GUIA_DE_USO.md",
        "tests/test_ui_typography.py",
        "views/login.py",
        "views/cadastro.py",
        "views/dashboard_cuidador/_perfil.py",
        "views/dashboard_profissional/_perfil.py",
    }
    forbidden_prefixes = ("database/", "modules/", "controllers/")

    assert all(not path.startswith(forbidden_prefixes) for path in changed_targets)
