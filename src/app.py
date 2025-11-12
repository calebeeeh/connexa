import sqlite3
import os 
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List 
from fastapi.middleware.cors import CORSMiddleware

# --- 1. CONFIGURAÇÃO DE ACESSO AO BANCO DE DADOS ---

# Lógica de Portabilidade: Determina o caminho absoluto para o connexa.db dentro de src/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.path.join(BASE_DIR, "connexa.db")

# Função que abre e configura a conexão
def get_db_connection():
    """Conecta ao SQLite e configura o acesso a colunas por nome."""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as e:
        # Se houver um erro de DB (ex: arquivo não encontrado), levantamos um erro Python.
        print(f"Erro de Conexão com o DB: {e}")
        raise HTTPException(status_code=500, detail="Falha ao conectar ao banco de dados.")

# Inicializa o aplicativo FastAPI
app = FastAPI(
    title="Connexa Data API", 
    description="API de dados para o modelo Connexa AI."
)

# --- 2. CONFIGURAÇÃO CORS ---
# Permite que o front-end (o app Lovable) acesse esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- 3. MODELAGEM DE DADOS (Pydantic) ---

# Modelo para uma transação detalhada
class Transacao(BaseModel):
    data: str
    valor: float
    membro_id: str
    categoria: str
    descricao: str

# Modelo para o dado agregado mensal (Série Temporal)
class SerieTemporalItem(BaseModel):
    data_referencia: str
    total_gasto: float
    total_receita: float
    saldo_liquido: float

# --- 4. ENDPOINTS (ROTAS) ---

@app.get("/transacoes", response_model=List[Transacao])
def listar_transacoes():
    """Retorna todas as transações detalhadas (dados brutos/limpos)."""
    try:
        with get_db_connection() as conn:
            # *CORRIGIDO:* Usando o nome correto da tabela: connexa_financas
            transacoes = conn.execute("SELECT * FROM connexa_financas").fetchall()
            return [Transacao(**dict(t)) for t in transacoes]
            
    except Exception as e:
        # Retorna erro 500 se o DB estiver inacessível ou se a tabela estiver errada
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
    FROM connexa_financas -- Nome da tabela corrigido
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
    # Valida se o 'membro_id' fornecido está na lista de IDs válidos
    membro_id: str = Path(..., description="ID do membro (Calebe, Felipe ou Rafael)", 
                          pattern="^(Calebe|Felipe|Rafael)$")
):
    """
    Retorna as transações filtradas por um membro específico.
    Essencial para a análise individual do LLM (e-mails com insights).
    """
    try:
        with get_db_connection() as conn:
            # Usamos o '?' como placeholder para evitar SQL Injection (boa prática de segurança)
            query = "SELECT * FROM connexa_financas WHERE membro_id = ?"
            transacoes = conn.execute(query, (membro_id,)).fetchall()
            
            if not transacoes:
                # Se não encontrar dados, retorna 404 Not Found
                raise HTTPException(status_code=404, detail=f"Nenhuma transação encontrada para o membro: {membro_id}")
            
            return [Transacao(**dict(t)) for t in transacoes]
            
    except Exception as e:
        # Erro genérico de DB
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transações por membro: {e}")