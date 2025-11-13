# src/database_utils.py

import sqlite3
import os
from pydantic import BaseModel, Field
from fastapi import HTTPException
from typing import Dict, Any

# --- CONFIGURAÇÃO DE ACESSO AO BANCO DE DADOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.path.join(BASE_DIR, "connexa.db") 

# Modelo para a Query Dinâmica (Usado pelo FastAPI e pela LLM)
class DynamicQuery(BaseModel):
    query: str = Field(..., description="A query SQL gerada pela LLM a ser executada.")

# Função que abre e configura a conexão
def get_db_connection():
    """Conecta ao SQLite e configura o acesso a colunas por nome."""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        print(f"Erro de Conexão com o DB: {e}")
        raise HTTPException(status_code=500, detail="Falha ao conectar ao banco de dados.")

# Função que o FastAPI e a LLM usam para rodar consultas dinâmicas
def executar_query_dinamica(request: DynamicQuery) -> Dict[str, Any]:
    """
    Executa uma query SQL dinâmica no banco de dados.
    """
    sql_query = request.query.strip()
    
    # 1. Validação Simples (Prevenção contra SQL Injection de comandos maliciosos)
    if sql_query.lower().startswith(("delete", "drop", "update", "insert")):
        raise HTTPException(
            status_code=400,
            detail="Comandos de modificação de dados (DELETE, DROP, UPDATE) não são permitidos."
        )

    try:
        with get_db_connection() as conn:
            resultado = conn.execute(sql_query).fetchone()
            
            if resultado:
                return {"status": "sucesso", "resultado": dict(resultado)}
            else:
                return {"status": "sucesso", "resultado": "Nenhum dado retornado pela query."}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na execução da Query SQL: {e}")