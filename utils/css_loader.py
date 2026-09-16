"""
PICTA — utils/css_loader.py
Utilitários para carregar arquivos CSS externos.
"""

import os


GLOBAL_CSS = "picta_typography_accessibility.css"
FINAL_CSS = "picta_ui_final_overrides.css"


def load_css(file_path: str) -> str:
    """
    Carrega o conteúdo de um arquivo CSS e, ao final, aplica as camadas
    globais de tipografia e de ajustes finais de interface do PICTA.

    Args:
        file_path: Caminho relativo ao diretório assets/

    Returns:
        String com o conteúdo CSS envolto em <style>
    """
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
    full_path = os.path.join(assets_dir, file_path)
    global_css_path = os.path.join(assets_dir, GLOBAL_CSS)
    final_css_path = os.path.join(assets_dir, FINAL_CSS)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # A camada global entra por último para que os limites mínimos de
        # legibilidade possam corrigir ajustes específicos das telas sem
        # exigir duplicação de regras em cada CSS.
        if os.path.normpath(full_path) != os.path.normpath(global_css_path):
            with open(global_css_path, 'r', encoding='utf-8') as f:
                css_content += f"\n\n{f.read()}"

        # Ajustes finais são aplicados depois da camada global para resolver
        # conflitos de especificidade/ordem sem reescrever os CSS existentes.
        if os.path.normpath(full_path) not in {
            os.path.normpath(global_css_path),
            os.path.normpath(final_css_path),
        }:
            with open(final_css_path, 'r', encoding='utf-8') as f:
                css_content += f"\n\n{f.read()}"

        return f"<style>{css_content}</style>"
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo CSS não encontrado: {full_path}")
    except Exception as e:
        raise Exception(f"Erro ao carregar CSS {file_path}: {e}")


def inject_css(file_path: str) -> None:
    """
    Injeta CSS diretamente no Streamlit via st.markdown.

    Args:
        file_path: Caminho relativo ao diretório assets/
    """
    import streamlit as st
    css_html = load_css(file_path)
    st.markdown(css_html, unsafe_allow_html=True)
