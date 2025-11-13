# src/llm_processor.py

import sys
import requests 
from src.database_utils import executar_query_dinamica, DynamicQuery 
from openai import OpenAI 

# --- INICIALIZAÇÃO GLOBAL ---
try:
    # A biblioteca OpenAI busca a chave de ambiente 'OPENAI_API_KEY'
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    LLM_MODEL = 'gpt-3.5-turbo' # Modelo rápido e estável
except Exception as e:
    print(f"ERRO DE CLIENTE LLM: Falha ao iniciar o OpenAI Client. Detalhes: {e}")
    sys.exit(1)


def gerar_plano_connexa(meta_usuario: str, prazo_meses: int, membro_foco: str, categoria_foco: str):
    # ... (código anterior - Geração de Prompt Mestre) ...
    
    # 4. CHAMADA FINAL DA LLM (Onde o texto é gerado)
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL, 
            messages=[
                {"role": "system", "content": "Você é o Consultor Financeiro Connexa, focado em planos motivacionais."},
                {"role": "user", "content": prompt_mestre}
            ]
        )
        # Retorna o texto gerado
        return response.choices[0].message.content
        
    except Exception as e:
        # Se a chave da OpenAI não for válida, o erro será capturado aqui.
        return f"\n❌ ERRO NA CHAMADA DA LLM: Falha ao gerar conteúdo. Verifique sua chave da OpenAI. Detalhes: {e}"


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