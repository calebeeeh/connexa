# src/app.py

import sqlite3
import os 
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Dict, Any 
from fastapi.middleware.cors import CORSMiddleware

# --- IMPORTS CORRIGIDOS DE OUTROS MÓDULOS ---
from src.llm_processor import gerar_plano_connexa 
from src.database_utils import get_db_connection, executar_query_dinamica, DynamicQuery


# --- INICIALIZAÇÃO E CONFIGURAÇÃO ---
app = FastAPI(
    title="Connexa Data API", 
    description="API de dados e IA para o modelo Connexa."
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- MODELAGEM DE DADOS (Pydantic: TODAS as classes antes das rotas) ---

# Modelo para requisição da LLM (PlanoRequest)
class PlanoRequest(BaseModel):
    meta_usuario: str
    prazo_meses: int
    membro_foco: str
    categoria_foco: str

# Modelo para dados de transação (retorno de /transacoes)
class Transacao(BaseModel):
    data: str
    valor: float
    membro_id: str
    categoria: str
    descricao: str

# Modelo para dados de série temporal (retorno de /serie_temporal)
class SerieTemporalItem(BaseModel):
    data_referencia: str
    total_gasto: float
    total_receita: float
    saldo_liquido: float


# --- ROTAS DE DADOS (Consomem get_db_connection) ---

@app.get("/transacoes", response_model=List[Transacao])
def listar_transacoes():
    """Retorna todas as transações detalhadas (dados brutos/limpos)."""
    try:
        with get_db_connection() as conn: 
            transacoes = conn.execute("SELECT * FROM connexa_financas").fetchall()
            return [Transacao(**dict(t)) for t in transacoes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar o banco de dados: {e}")


@app.get("/serie_temporal", response_model=List[SerieTemporalItem])
def obter_dados_serie_temporal():
    """Retorna o fluxo de caixa agregado mensalmente para o modelo preditivo."""
    query = """
    SELECT 
        STRFTIME('%Y-%m', data) as data_referencia,
        SUM(CASE WHEN valor < 0 THEN valor * -1 ELSE 0 END) as total_gasto,
        SUM(CASE WHEN valor > 0 THEN valor ELSE 0 END) as total_receita,
        SUM(valor) as saldo_liquido
    FROM connexa_financas
    GROUP BY data_referencia
    ORDER BY data_referencia;
    """
    try:
        with get_db_connection() as conn:
            resultados = conn.execute(query).fetchall()
            return [SerieTemporalItem(**dict(r)) for r in resultados]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar série temporal: {e}")


@app.get("/transacoes/{membro_id}", response_model=List[Transacao])
def buscar_transacoes_por_membro(
    membro_id: str = Path(..., description="ID do membro (Calebe, Felipe ou Rafael)", 
                          pattern="^(Calebe|Felipe|Rafael)$")
):
    """Retorna as transações filtradas por um membro específico."""
    try:
        with get_db_connection() as conn:
            query = "SELECT * FROM connexa_financas WHERE membro_id = ?"
            transacoes = conn.execute(query, (membro_id,)).fetchall()
            
            if not transacoes:
                raise HTTPException(status_code=404, detail=f"Nenhuma transação encontrada para o membro: {membro_id}")
            
            return [Transacao(**dict(t)) for t in transacoes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transações por membro: {e}")


# --- ROTA DE IA FINAL (Chama o Processador da LLM) ---

@app.post("/executar_query_dinamica", response_model=Dict[str, Any])
def executar_query_dinamica_route(request: DynamicQuery):
    """Endpoint para executar queries dinâmicas SQL (usado pela LLM internamente)."""
    return executar_query_dinamica(request) 

@app.post("/gerar_plano", response_model=str)
def gerar_plano_de_acao_ia(request: PlanoRequest): # Agora PlanoRequest está definido!
    """
    Rota principal de IA: Recebe a meta do usuário e dispara o processamento da LLM.
    """
    try:
        # Usa a função de processamento da LLM (importada)
        plano_final = gerar_plano_connexa(
            meta_usuario=request.meta_usuario,
            prazo_meses=request.prazo_meses,
            membro_foco=request.membro_foco,
            categoria_foco=request.categoria_foco
        )
        return plano_final
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na geração do plano de IA: {e}")