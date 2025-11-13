# src/llm_processor.py

import sys
import requests
from google import genai 
from src.database_utils import executar_query_dinamica, DynamicQuery 
from google.genai import types

# --- INICIALIZAÇÃO GLOBAL ---
try:
    client = genai.Client()
    LLM_MODEL = 'gemini-2.5-flash'
except Exception as e:
    print(f"ERRO DE CLIENTE LLM: Falha ao iniciar o Gemini Client. Detalhes: {e}")
    sys.exit(1)


def gerar_plano_connexa(meta_usuario: str, prazo_meses: int, membro_foco: str, categoria_foco: str):
    """
    Executa o ciclo completo: Geração de Feature Dinâmica -> Cálculo -> Geração de Plano pela LLM.
    """
    # 1. GERAÇÃO DINÂMICA DE FEATURE (Busca o dado crítico no Backend)
    sql_gasto_foco = (
        f"SELECT SUM(valor) AS total_gasto_foco FROM connexa_financas "
        f"WHERE membro_id = '{membro_foco}' AND categoria = '{categoria_foco}'"
    )
    
    try:
        query_object = DynamicQuery(query=sql_gasto_foco)
        resultado_gasto = executar_query_dinamica(query_object)
        gasto_critico_total = resultado_gasto['resultado']['total_gasto_foco'] * -1
        
    except Exception:
        return f"Falha na busca de dados para {membro_foco} em {categoria_foco}. Verifique a categoria."

    # 2. INJEÇÃO DE CONTEXTO E CÁLCULO DE METAS
    baseline_poupanca = 2703.11 
    meta_mensal_requerida = 10000 / prazo_meses 
    
    # 3. CRIAÇÃO DO PROMPT MESTRE (Com todas as Features injetadas)
    prompt_mestre = f"""
    Você é o Consultor Financeiro Connexa. Crie um plano de ação motivacional para a meta.

    --- CONTEXTO ANALÍTICO ---
    Meta do Usuário: {meta_usuario}. Prazo: {prazo_meses} meses.
    Poupança Média Atual (Baseline): R$ {baseline_poupanca:.2f}/mês.
    Meta de Poupança Mensal Requerida: R$ {meta_mensal_requerida:.2f}/mês.
    Gasto Crítico de Foco ({membro_foco} em {categoria_foco}): R$ {gasto_critico_total:.2f} (em 18 meses).

    --- TAREFAS ---
    1. Calcule a porcentagem de corte (máximo 20% e mínimo 1%) que {membro_foco} deve fazer no gasto de {categoria_foco} para cobrir um déficit mensal de R$ 500,00 e trace o plano.
    2. Gere a resposta em três seções claras: "Status da Meta", "Plano de Ação Connexa" e "Dica Comportamental".
    """
    
    # 4. CHAMADA FINAL DA LLM (Onde o texto é gerado)
    try:
        response = client.models.generate_content(
            model=LLM_MODEL, 
            contents=prompt_mestre
        )
        return response.text
    except Exception as e:
        return f"\n❌ ERRO NA CHAMADA DA LLM: Falha ao gerar conteúdo. Detalhes: {e}"


if __name__ == "__main__":
    # Simulação de Teste Local
    print("\n--- INÍCIO DO PROJETO CONNEXTA: GERAÇÃO DE PLANO ---")
    resultado_plano = gerar_plano_connexa(
        meta_usuario="viajar para Porto Seguro, gastando R$ 10.000", 
        prazo_meses=14,
        membro_foco="Rafael",
        categoria_foco="Lazer"
    )
    print("\n\n--- PLANO GERADO PELA IA DO CONNEXTA ---")
    print(resultado_plano)
    print("-------------------------------------------\n")