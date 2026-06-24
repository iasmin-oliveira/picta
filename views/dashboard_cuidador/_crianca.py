"""
PICTA — views/dashboard_cuidador/_crianca.py
Seção "Minha Criança" do dashboard do cuidador.
"""

import datetime
import streamlit as st
from collections import Counter

from modules.logs import APP_TZ, obter_interacoes
from modules.auth import obter_crianca_por_id, atualizar_crianca
from utils.formatters import format_date_br
from ._constants import EMOCOES_POSITIVAS


def render_crianca(usuario_id, criancas, crianca_id, crianca_nome: str) -> None:
    st.markdown(
        '<div class="page-header">'
        '  <div class="page-title">👶 Minha Criança</div>'
        '  <div class="page-subtitle">'
        '    Visualize e edite os dados da criança, e veja dicas personalizadas.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not criancas or not crianca_id:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:2.5rem;">'
            '  <div style="font-size:3rem;margin-bottom:1rem">🧩</div>'
            '  <div style="font-weight:800;color:#1e1b4b">Nenhuma criança vinculada</div>'
            '  <div style="color:#9ca3af;font-weight:600;margin-top:.4rem">'
            '    Acesse <b>Vínculos</b> para adicionar uma criança.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    crianca_db = obter_crianca_por_id(crianca_id)
    nome_curto = crianca_nome.split()[0]

    col_info, col_edit = st.columns([1, 1])

    with col_info:
        dn      = crianca_db.get('data_nascimento') if crianca_db else None
        dn_str  = str(dn) if dn else ''
        idade_txt = ''
        if dn_str:
            try:
                hoje_local = datetime.datetime.now(APP_TZ).date()
                anos = (hoje_local - datetime.date.fromisoformat(dn_str)).days // 365
                idade_txt = f"{anos} anos"
            except Exception:
                pass
        dn_exibicao = format_date_br(dn_str) if dn_str else ""

        st.markdown(
            f'<div class="crianca-card">'
            f'  <div class="crianca-avatar">🧒</div>'
            f'  <div class="crianca-nome">{crianca_nome}</div>'
            f'  <div class="crianca-info">'
            f'    {f"Nascimento: {dn_exibicao}" if dn_exibicao else "Data de nascimento: não informada"}'
            f'    {f" · {idade_txt}" if idade_txt else ""}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        interacoes = obter_interacoes(crianca_id, limite=200)
        hoje = datetime.datetime.now(APP_TZ).date().isoformat()
        hoje_ints  = [i for i in interacoes
                      if str(i.get('registado_em', ''))[:10] == hoje]
        necs_all   = [i for i in interacoes if i.get('categoria') == 'necessidade']
        acoes_all  = [i for i in interacoes if i.get('categoria') == 'acao']
        emocs_all  = [i for i in interacoes if i.get('categoria') == 'emocao']

        st.markdown(
            f'<div class="glass-card" style="padding:1rem 1.2rem;">'
            f'  <div class="sec-header" style="margin-bottom:.6rem">📊 Resumo geral</div>'
            f'  <div class="ficha-row"><span class="ficha-label">Total de comunicações</span>'
            f'    <span class="ficha-valor">{len(interacoes)}</span></div>'
            f'  <div class="ficha-row"><span class="ficha-label">Comunicações hoje</span>'
            f'    <span class="ficha-valor">{len(hoje_ints)}</span></div>'
            f'  <div class="ficha-row"><span class="ficha-label">Pedidos registrados</span>'
            f'    <span class="ficha-valor">{len(necs_all)}</span></div>'
            f'  <div class="ficha-row"><span class="ficha-label">Emoções registradas</span>'
            f'    <span class="ficha-valor">{len(emocs_all)}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Dicas baseadas no histórico
        dicas = []
        if necs_all:
            top = Counter(i['pictograma'] for i in necs_all).most_common(1)[0]
            dicas.append(
                f'O pedido mais frequente de <b>{nome_curto}</b> é '
                f'<b>{top[0].lower()}</b> ({top[1]}×). '
                f'Garantir que este item esteja sempre acessível pode reduzir frustrações.'
            )
        if acoes_all:
            top_a = Counter(i['pictograma'] for i in acoes_all).most_common(1)[0]
            dicas.append(
                f'<b>{nome_curto}</b> demonstra interesse frequente em '
                f'<b>{top_a[0].lower()}</b> ({top_a[1]}×). '
                f'Essa atividade pode ser usada como reforço positivo.'
            )
        em_pos = [i for i in emocs_all if i['pictograma'] in EMOCOES_POSITIVAS]
        if emocs_all and len(em_pos) > len(emocs_all) * 0.5:
            dicas.append(
                f'Mais da metade das emoções registradas são positivas! '
                f'Continue com as rotinas que estão funcionando bem para {nome_curto}.'
            )
        if dicas:
            st.markdown(
                '<div class="sec-header" style="margin-top:.5rem">💡 Dicas para você</div>',
                unsafe_allow_html=True,
            )
            for d in dicas:
                st.markdown(f'<div class="tip-card">{d}</div>', unsafe_allow_html=True)

    with col_edit:
        st.markdown(
            '<div class="sec-header">✏️ Editar dados da criança</div>',
            unsafe_allow_html=True,
        )
        nome_atual = (crianca_db.get('nome', crianca_nome) if crianca_db else crianca_nome)
        dn_atual   = dn_str

        with st.form("form_editar_crianca"):
            novo_nome = st.text_input("Nome da criança", value=nome_atual)
            nova_dn   = st.text_input(
                "Data de nascimento",
                value=dn_atual, placeholder="AAAA-MM-DD  (ex: 2018-05-10)",
                help="Formato: Ano-Mês-Dia",
            )
            submitted = st.form_submit_button(
                "💾 Salvar alterações", use_container_width=True, type="primary"
            )
            if submitted:
                dn_val = nova_dn.strip()
                if dn_val:
                    try:
                        datetime.date.fromisoformat(dn_val)
                    except ValueError:
                        st.error("❌ Data inválida. Use AAAA-MM-DD.")
                        st.stop()
                erro = atualizar_crianca(crianca_id, novo_nome, dn_val)
                if erro:
                    st.error(f"❌ {erro}")
                else:
                    st.success(f"✅ Dados de {novo_nome.split()[0]} atualizados!")
                    st.rerun()
