"""
PICTA — utils/css_loader.py
Utilitários para carregar arquivos CSS externos.
"""

import os


def load_css(file_path: str) -> str:
    """
    Carrega o conteúdo de um arquivo CSS.

    Args:
        file_path: Caminho relativo ao diretório assets/

    Returns:
        String com o conteúdo CSS envolto em <style>
    """
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
    full_path = os.path.join(assets_dir, file_path)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
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