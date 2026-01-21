from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from recommender import carregar_dados_grafo, construir_grafo, recomendar_filmes, buscar_info_filmes, get_db_connection

app = FastAPI()

# Configuração do CORS (Crucial para o React funcionar) 
origins = [
    "http://localhost:5173", # O porto padrão do Vite/React
    "http://localhost:3000", # Create React App
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga dos Dados no Arranque
# Carregamos o grafo uma única vez quando o servidor liga para ser rápido
grafo = None

@app.on_event("startup")
def startup_event():
    global grafo
    print("A iniciar servidor... Carregando grafo...")
    try:
        atores, generos, diretores, keywords = carregar_dados_grafo()
        grafo = construir_grafo(atores, generos, diretores, keywords)
        print("Grafo carregado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar grafo: {e}")

# Rotas da API (Endpoints) 

@app.get("/")
def read_root():
    return {"message": "API do CineGraph está online!"}

@app.get("/api/recommend/{movie_id}")
def recommend(movie_id: int):
    
    #Recebe um ID, calcula recomendações e devolve JSON completo com imagens.
    if grafo is None:
        raise HTTPException(status_code=500, detail="Grafo não carregado")
    
    # 1. Obter IDs recomendados (Lógica do grafo)
    recomendacoes_raw = recomendar_filmes(grafo, movie_id)
    
    if not recomendacoes_raw:
        return {"results": []}
    
    # Separa apenas os IDs para buscar no banco
    # recomendacoes_raw é [(id, score), (id, score)...]
    ids_apenas = [rec[0] for rec in recomendacoes_raw]
    
    # 2. Obter Detalhes (Foto, Título) do PostgreSQL
    detalhes = buscar_info_filmes(ids_apenas)
    
    # 3. Montar a resposta final bonita
    resposta_final = []
    for rec_id, score in recomendacoes_raw:
        info = detalhes.get(rec_id, {})
        resposta_final.append({
            "id": rec_id,
            "titulo": info.get("titulo", "Desconhecido"),
            "poster": info.get("poster", ""),
            "ano": info.get("ano", ""),
            "score_similaridade": score
        })
        
    return {"results": resposta_final}