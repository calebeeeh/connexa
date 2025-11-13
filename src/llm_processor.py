# src/llm_processor.py

import sys
import os # Necessário para ler a variável de ambiente da OpenAI
import requests

# --- CLIENTE E FERRAMENTAS ---
from openai import OpenAI # Cliente oficial da OpenAI
from src.database_utils import executar_query_dinamica, DynamicQuery 
from src.database_utils import get_db_connection # Necessário para o main block (se for usado)


# --- 1. INICIALIZAÇÃO GLOBAL (AGORA USANDO OPENAI) ---
try:
    # 🚨 CRÍTICO: O cliente busca a chave na variável de ambiente 'OPENAI_API_KEY'
    # O valor da chave deve ser configurado no painel da Render.
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 
    LLM_MODEL = 'gpt-3.5-turbo' # Modelo estável e rápido para raciocínio
except Exception as e:
    print(f"ERRO DE CLIENTE LLM: Falha ao iniciar o OpenAI Client. Verifique a chave de API. Detalhes: {e}")
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
        # Executando a query no Backend
        resultado_gasto = executar_query_dinamica(query_object)
        gasto_critico_total = resultado_gasto['resultado']['total_gasto_foco'] * -1
        
    except Exception as e:
        # Captura erros de DB ou de cálculo no Backend
        return f"Falha na busca de dados para {membro_foco} em {categoria_foco}. Erro: {e}"

    # 2. INJEÇÃO DE CONTEXTO E CÁLCULO DE METAS
    baseline_poupanca = 2703.11 
    meta_mensal_requerida = 10000 / prazo_meses 
    
    # CRIAÇÃO DO PROMPT MESTRE (Onde o NLP e o Dado se encontram)
    prompt_mestre = f"""
    Você é o Consultor Financeiro Connexa, focado em planos motivacionais.

    --- CONTEXTO ANALÍTICO ---
    Meta do Usuário: {meta_usuario}. Prazo: {prazo_meses} meses.
    Poupança Média Atual (Baseline): R$ {baseline_poupanca:.2f}/mês.
    Meta de Poupança Mensal Requerida: R$ {meta_mensal_requerida:.2f}/mês.
    Gasto Crítico de Foco ({membro_foco} em {categoria_foco}): R$ {gasto_critico_total:.2f} (em 18 meses).

    --- TAREFAS ---
    1. Calcule a porcentagem de corte (máximo 20% e mínimo 1%) que {membro_foco} deve fazer no gasto de {categoria_foco} para cobrir um déficit mensal de R$ 500,00 e trace o plano.
    2. Gere a resposta em três seções claras: "Status da Meta", "Plano de Ação Connexa" e "Dica Comportamental".
    """
    
    # 3. CHAMADA FINAL DA LLM (Onde o texto é gerado)
    try:
        # 🚨 CHAMADA DA API OPENAI
        response = client.chat.completions.create(
            model=LLM_MODEL, 
            messages=[
                {"role": "system", "content": "Você é um assistente financeiro especialista em análise comportamental."},
                {"role": "user", "content": prompt_mestre}
            ]
        )
        # Retorna o texto gerado pela LLM
        return response.choices[0].message.content
        
    except Exception as e:
        # Se a chave da OpenAI não for válida ou o servidor falhar
        return f"\n❌ ERRO NA CHAMADA DA LLM: Falha ao gerar conteúdo. Verifique sua chave da OpenAI. Detalhes: {e}"


if __name__ == "__main__":
    # Teste de Simulação Local (A chave de API deve ser definida no terminal)
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