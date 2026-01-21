import requests
import psycopg2
import os
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Configurações Globais
API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "cinegraph_db"
BASE_URL = "https://api.themoviedb.org/3"
PARAMS_BASE = {"api_key": API_KEY, "language": "pt-BR"}

def get_db_connection():
    """
    Estabelece a conexão com o banco PostgreSQL.
    Usa 127.0.0.1 para evitar problemas de resolução de DNS no WSL/Linux.
    """
    return psycopg2.connect(
        dbname="cinegraph_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port="5432"
    )

def salvar_filme(cursor, movie_data):
    """
    Insere dados na tabela 'movies'.
    Usa ON CONFLICT DO NOTHING para garantir idempotência (não duplica se rodar 2x).
    """
    sql = """
        INSERT INTO movies (movie_id, title, overview, release_date, poster_path, vote_average)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (movie_id) DO NOTHING;
    """
    
    # Tratamento para datas vazias na API
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
    """
    Salva os gêneros e cria o relacionamento N:N na tabela 'movie_genres'.
    """
    for genre in genres_list:
        # 1. Garante que o gênero existe na tabela de domínio
        cursor.execute("""
            INSERT INTO genres (genre_id, name) VALUES (%s, %s)
            ON CONFLICT (genre_id) DO NOTHING;
        """, (genre['id'], genre['name']))
        
        # 2. Cria o link Filme <-> Gênero
        cursor.execute("""
            INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)
            ON CONFLICT (movie_id, genre_id) DO NOTHING;
        """, (movie_id, genre['id']))

def salvar_atores(cursor, movie_id, cast_list):
    """
    Salva os atores e cria o relacionamento na tabela 'movie_actors'.
    NOTA: Limitamos aos TOP 10 atores para evitar poluição do grafo com figurantes.
    """
    # Itera apenas os 10 primeiros creditados (Otimização de Grafo)
    for actor in cast_list[:10]: 
        
        # 1. Garante que o ator existe na tabela de atores
        sql_actor = """
            INSERT INTO actors (actor_id, name) VALUES (%s, %s)
            ON CONFLICT (actor_id) DO NOTHING;
        """
        cursor.execute(sql_actor, (actor['id'], actor['name']))

        # 2. Cria o link Filme <-> Ator incluindo o nome do personagem
        sql_link = """
            INSERT INTO movie_actors (movie_id, actor_id, character_name) 
            VALUES (%s, %s, %s)
            ON CONFLICT (movie_id, actor_id) DO NOTHING;
        """
        # .get evita erro caso a API não mande o campo character
        character = actor.get('character', '')
        
        cursor.execute(sql_link, (movie_id, actor['id'], character))

def salvar_diretores(cursor, movie_id, crew_list):
    """Filtra a lista da equipe técnica para pegar apenas o Diretor."""
    for crew_member in crew_list:
        if crew_member['job'] == 'Director':
            # 1. Salva Diretor
            cursor.execute("""
                INSERT INTO directors (director_id, name) VALUES (%s, %s)
                ON CONFLICT (director_id) DO NOTHING;
            """, (crew_member['id'], crew_member['name']))
            
            # 2. Link Filme-Diretor
            cursor.execute("""
                INSERT INTO movie_directors (movie_id, director_id) VALUES (%s, %s)
                ON CONFLICT (movie_id, director_id) DO NOTHING;
            """, (movie_id, crew_member['id']))

def salvar_keywords(cursor, movie_id, keywords_list):
    """Salva as palavras-chave do filme."""
    for kw in keywords_list:
        # 1. Salva Keyword
        cursor.execute("""
            INSERT INTO keywords (keyword_id, name) VALUES (%s, %s)
            ON CONFLICT (keyword_id) DO NOTHING;
        """, (kw['id'], kw['name']))
        
        # 2. Link Filme-Keyword
        cursor.execute("""
            INSERT INTO movie_keywords (movie_id, keyword_id) VALUES (%s, %s)
            ON CONFLICT (movie_id, keyword_id) DO NOTHING;
        """, (movie_id, kw['id']))

def run_etl():
    """
    Função Principal do Pipeline ETL (Extract, Transform, Load).
    Percorre a API do TMDB e popula o banco local.
    """
    print("INICIANDO PROCESSO ETL")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Loop para pegar múltiplas páginas de filmes populares
        for pagina in range(1, 4):
            print(f"Baixando página {pagina} de dados...")
            
            url = f"{BASE_URL}/movie/top_rated"
            params = PARAMS_BASE.copy()
            params['page'] = pagina
            
            response = requests.get(url, params=params)
            data = response.json()
            lista_filmes = data.get('results', [])
            
            for filme in lista_filmes:
                movie_id = filme['id']
                
                # Passo 1: Salvar Dados Básicos
                salvar_filme(cur, filme)
                
                # Passo 2: Buscar Detalhes Estendidos (Atores e Gêneros)
                # Usamos 'append_to_response' para economizar requisições
                url_detalhes = f"{BASE_URL}/movie/{movie_id}"
                params_detalhes = PARAMS_BASE.copy()
                params_detalhes['append_to_response'] = 'credits'
                
                resp_detalhes = requests.get(url_detalhes, params=params_detalhes)
                
                if resp_detalhes.status_code == 200:
                    detalhes = resp_detalhes.json()
                    
                    # Salva relacionamentos
                    salvar_generos(cur, movie_id, detalhes.get('genres', []))
                    
                    # Extrai elenco do nó 'credits' -> 'cast'
                    credits = detalhes.get('credits', {})
                    cast = credits.get('cast', [])
                    salvar_atores(cur, movie_id, cast)
                
                # Rate Limiting: Pausa para não bloquear a API Key
                time.sleep(0.1)
                
            # Commit a cada página para salvar o progresso
            conn.commit() 
            print(f" Página {pagina} processada e salva.")

    except Exception as e:
        print(f"Erro crítico na execução: {e}")
        conn.rollback() # Desfaz alterações parciais em caso de erro
    finally:
        cur.close()
        conn.close()
        print("CONEXÃO ENCERRADA")
        
if __name__ == "__main__":
    run_etl()