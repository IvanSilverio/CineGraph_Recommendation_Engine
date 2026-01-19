import requests
import psycopg2
import os
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações globais
API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "cinegraph_db"
BASE_URL = "https://api.themoviedb.org/3"
PARAMS_BASE = {"api_key": API_KEY, "language": "pt-BR"}

def get_db_connection():
    return psycopg2.connect(
        dbname="cinegraph_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port="5432"
    )

def salvar_filme(cursor, movie_data):
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
    for genre in genres_list:
        # Garante gênero
        cursor.execute("""
            INSERT INTO genres (genre_id, name) VALUES (%s, %s)
            ON CONFLICT (genre_id) DO NOTHING;
        """, (genre['id'], genre['name']))
        
        # Link Filme-Gênero
        cursor.execute("""
            INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)
            ON CONFLICT (movie_id, genre_id) DO NOTHING;
        """, (movie_id, genre['id']))

#Função para salvar atores e o relacionamento
def salvar_atores(cursor, movie_id, cast_list):
    """
    Recebe a lista de elenco, salva o ator na tabela 'actors'
    e cria o vínculo na tabela 'movie_actors'.
    """
    # Vamos pegar apenas os top 10 atores para não poluir demais o banco
    for actor in cast_list[:10]: 
        
        # 1. Garante que o ator exista na tabela de atores
        sql_actor = """
            INSERT INTO actors (actor_id, name) VALUES (%s, %s)
            ON CONFLICT (actor_id) DO NOTHING;
        """
        cursor.execute(sql_actor, (actor['id'], actor['name']))

        # 2. Cria o relacionamento Filme-Ator com o nome do personagem
        sql_link = """
            INSERT INTO movie_actors (movie_id, actor_id, character_name) 
            VALUES (%s, %s, %s)
            ON CONFLICT (movie_id, actor_id) DO NOTHING;
        """
        # A API pode não trazer o personagem, então usamos .get
        character = actor.get('character', '')
        
        cursor.execute(sql_link, (movie_id, actor['id'], character))

def run_etl():
    print("Iniciando carga de dados...")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        for pagina in range(1, 4):
            print(f"Processando página {pagina}...")
            
            url = f"{BASE_URL}/movie/top_rated"
            params = PARAMS_BASE.copy()
            params['page'] = pagina
            
            response = requests.get(url, params=params)
            data = response.json()
            lista_filmes = data.get('results', [])
            
            for filme in lista_filmes:
                movie_id = filme['id']
                
                # 1. Salva Filme
                salvar_filme(cur, filme)
                
                # ### ALTERADO: Busca Detalhes + Créditos (Atores) numa única chamada ###
                url_detalhes = f"{BASE_URL}/movie/{movie_id}"
                
                # Prepara parâmetros para trazer os créditos juntos (append_to_response)
                params_detalhes = PARAMS_BASE.copy()
                params_detalhes['append_to_response'] = 'credits'
                
                resp_detalhes = requests.get(url_detalhes, params=params_detalhes)
                
                if resp_detalhes.status_code == 200:
                    detalhes = resp_detalhes.json()
                    
                    # 2. Salva Gêneros
                    salvar_generos(cur, movie_id, detalhes.get('genres', []))
                    
                    # 3. Salva Atores (Extraindo do nó 'credits' -> 'cast')
                    credits = detalhes.get('credits', {})
                    cast = credits.get('cast', [])
                    salvar_atores(cur, movie_id, cast)
                
                time.sleep(0.1)
                
            conn.commit() 
            print(f"Página {pagina} finalizada.")

    except Exception as e:
        print(f"Erro na execução: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        print("Conexão encerrada.")
        

if __name__ == "__main__":
    run_etl()