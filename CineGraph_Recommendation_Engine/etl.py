import requests
import psycopg2
import os
import time
from dotenv import load_dotenv

# Carrega variáveis de ambiente (credenciais)
load_dotenv()

# Configurações globais
API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "cinegraph_db"
BASE_URL = "https://api.themoviedb.org/3"

# Parâmetros padrão para as requisições
PARAMS_BASE = {"api_key": API_KEY, "language": "pt-BR"}

def get_db_connection():
    #Estabelece e retorna a conexão com o PostgreSQL.
    return psycopg2.connect(
        dbname=DB_NAME,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="192.168.0.154",
        port="5432"
    )

def salvar_filme(cursor, movie_data):
    """
    Insere registro na tabela 'movies'.
    Utiliza ON CONFLICT para ignorar inserção caso o ID já exista.
    """
    sql = """
        INSERT INTO movies (movie_id, title, overview, release_date, poster_path, vote_average)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (movie_id) DO NOTHING;
    """
    
    # Tratamento de dados: Converte string vazia para None (NULL no SQL)
    # A API retorna "" para datas desconhecidas, o que gera erro no tipo DATE
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
    
    #Popula tabela de domínio 'genres' e a tabela associativa 'movie_genres'.
    
    for genre in genres_list:
        # 1. Garante que o gênero exista na base
        sql_genre = """
            INSERT INTO genres (genre_id, name) VALUES (%s, %s)
            ON CONFLICT (genre_id) DO NOTHING;
        """
        cursor.execute(sql_genre, (genre['id'], genre['name']))
        
        # 2. Cria o relacionamento N:N entre filme e gênero
        sql_link = """
            INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)
            ON CONFLICT (movie_id, genre_id) DO NOTHING;
        """
        cursor.execute(sql_link, (movie_id, genre['id']))

def run_etl():
    print("Iniciando carga de dados...")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Loop para buscar múltiplas páginas da API (paginação)
        for pagina in range(1, 4):
            print(f"Processando página {pagina}...")
            
            # Endpoint: Filmes Bem Avaliados
            url = f"{BASE_URL}/movie/top_rated"
            params = PARAMS_BASE.copy()
            params['page'] = pagina
            
            response = requests.get(url, params=params)
            data = response.json()
            
            lista_filmes = data.get('results', [])
            
            for filme in lista_filmes:
                movie_id = filme['id']
                
                # Persiste dados principais do filme
                salvar_filme(cur, filme)
                
                # Data Enrichment: Busca detalhes adicionais (gêneros vêm incompletos na lista principal)
                url_detalhes = f"{BASE_URL}/movie/{movie_id}"
                resp_detalhes = requests.get(url_detalhes, params=PARAMS_BASE)
                
                if resp_detalhes.status_code == 200:
                    detalhes = resp_detalhes.json()
                    salvar_generos(cur, movie_id, detalhes.get('genres', []))
                
                # Delay para respeitar o Rate Limit da API do TMDB
                time.sleep(0.1)
                
            # Commit por página para persistência gradual
            conn.commit() 
            print(f"Página {pagina} finalizada.")

    except Exception as e:
        print(f"Erro na execução: {e}")
        conn.rollback() # Desfaz alterações pendentes em caso de erro
    finally:
        cur.close()
        conn.close()
        print("Conexão encerrada.")

if __name__ == "__main__":
    run_etl()