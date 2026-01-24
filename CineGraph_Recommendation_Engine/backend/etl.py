import requests
import psycopg2
import os
import time
import concurrent.futures
import threading
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações Globais
API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "cinegraph_db"
BASE_URL = "https://api.themoviedb.org/3"
PARAMS_BASE = {"api_key": API_KEY, "language": "pt-BR"}
MAX_WORKERS = 5

# Cadeado para controlar o acesso de escrita ao banco de dados
# Isso evita o erro de deadlock mantendo a integridade dos dados
lock_banco = threading.Lock()

def get_db_connection():
    # Estabelece conexão com o banco PostgreSQL
    return psycopg2.connect(
        dbname="cinegraph_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port="5432"
    )

# Funções de Persistência

def salvar_filme(cursor, movie_data):
    # Insere dados básicos do filme
    sql = """
        INSERT INTO movies (movie_id, title, overview, release_date, poster_path, vote_average)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (movie_id) DO NOTHING;
    """
    data_lancamento = movie_data.get('release_date')
    if not data_lancamento: 
        data_lancamento = None

    valores = (
        movie_data['id'],
        movie_data['title'],
        movie_data['overview'],
        data_lancamento,
        movie_data['poster_path'],
        movie_data['vote_average']
    )
    cursor.execute(sql, valores)

def salvar_generos(cursor, movie_id, genres_list):
    # Salva gêneros e cria relacionamento
    for genre in genres_list:
        cursor.execute("INSERT INTO genres (genre_id, name) VALUES (%s, %s) ON CONFLICT (genre_id) DO NOTHING;", (genre['id'], genre['name']))
        cursor.execute("INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s) ON CONFLICT (movie_id, genre_id) DO NOTHING;", (movie_id, genre['id']))

def salvar_atores(cursor, movie_id, cast_list):
    # Salva atores (limitado aos 10 primeiros) e cria relacionamento
    for actor in cast_list[:10]: 
        cursor.execute("INSERT INTO actors (actor_id, name) VALUES (%s, %s) ON CONFLICT (actor_id) DO NOTHING;", (actor['id'], actor['name']))
        character = actor.get('character', '')
        cursor.execute("INSERT INTO movie_actors (movie_id, actor_id, character_name) VALUES (%s, %s, %s) ON CONFLICT (movie_id, actor_id) DO NOTHING;", (movie_id, actor['id'], character))

def salvar_diretores(cursor, movie_id, crew_list):
    # Filtra e salva apenas diretores
    for crew_member in crew_list:
        if crew_member['job'] == 'Director':
            cursor.execute("INSERT INTO directors (director_id, name) VALUES (%s, %s) ON CONFLICT (director_id) DO NOTHING;", (crew_member['id'], crew_member['name']))
            cursor.execute("INSERT INTO movie_directors (movie_id, director_id) VALUES (%s, %s) ON CONFLICT (movie_id, director_id) DO NOTHING;", (movie_id, crew_member['id']))

def salvar_keywords(cursor, movie_id, keywords_list):
    # Salva palavras-chave e cria relacionamento
    for kw in keywords_list:
        cursor.execute("INSERT INTO keywords (keyword_id, name) VALUES (%s, %s) ON CONFLICT (keyword_id) DO NOTHING;", (kw['id'], kw['name']))
        cursor.execute("INSERT INTO movie_keywords (movie_id, keyword_id) VALUES (%s, %s) ON CONFLICT (movie_id, keyword_id) DO NOTHING;", (movie_id, kw['id']))

# Lógica Principal com Proteção de Concorrência

def processar_pagina(pagina):
    print(f"Iniciando download da página {pagina}...")
    
    # Conexão independente para esta thread
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Etapa 1: Rede (Executa em paralelo)
        # Baixa a lista de filmes sem bloquear o banco
        url = f"{BASE_URL}/movie/top_rated"
        params = PARAMS_BASE.copy()
        params['page'] = pagina
        
        response = requests.get(url, params=params)
        data = response.json()
        lista_filmes = data.get('results', [])
        
        for filme in lista_filmes:
            movie_id = filme['id']
            
            # Baixa detalhes adicionais em paralelo
            url_detalhes = f"{BASE_URL}/movie/{movie_id}"
            params_detalhes = PARAMS_BASE.copy()
            params_detalhes['append_to_response'] = 'credits,keywords'
            
            resp_detalhes = requests.get(url_detalhes, params=params_detalhes)
            detalhes = {}
            
            if resp_detalhes.status_code == 200:
                detalhes = resp_detalhes.json()

            # Etapa 2: Banco de Dados (Executa em série)
            # O bloco 'with lock_banco' garante que apenas UM processo grave por vez
            with lock_banco:
                salvar_filme(cur, filme)
                
                if detalhes:
                    salvar_generos(cur, movie_id, detalhes.get('genres', []))
                    salvar_atores(cur, movie_id, detalhes.get('credits', {}).get('cast', []))
                    salvar_diretores(cur, movie_id, detalhes.get('credits', {}).get('crew', []))
                    salvar_keywords(cur, movie_id, detalhes.get('keywords', {}).get('keywords', []))
                
                # Commit a cada filme para garantir persistência gradual
                conn.commit()

        return f"Página {pagina} processada com sucesso!"
        
    except Exception as e:
        conn.rollback()
        return f"Erro na página {pagina}: {e}"
    finally:
        cur.close()
        conn.close()

def run_etl():
    print(f"INICIANDO ETL HÍBRIDO ({MAX_WORKERS} workers simultâneos)")
    tempo_inicio = time.time()
    
    # Define o intervalo de páginas (1 a 50 = 1000 filmes)
    paginas_para_baixar = range(1, 51) 
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = executor.map(processar_pagina, paginas_para_baixar)
        
        for msg in resultados:
            print(msg)
            
    tempo_total = time.time() - tempo_inicio
    print(f"FIM! Tempo total: {tempo_total:.2f} segundos")

if __name__ == "__main__":
    run_etl()