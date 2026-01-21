import os
import psycopg2
import networkx as nx
from dotenv import load_dotenv
from collections import Counter

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Banco de Dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cinegraph_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD")

def get_db_connection():
    """Conecta ao banco de dados."""
    try:
        return psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port="5432"
        )
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco: {e}")
        exit(1)

def carregar_dados_grafo():
    """Busca dados brutos do PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()
    print("... Carregando dados (Atores e Gêneros) ...")
    
    cur.execute("SELECT m.movie_id, a.name FROM movies m JOIN movie_actors ma ON m.movie_id = ma.movie_id JOIN actors a ON ma.actor_id = a.actor_id")
    filmes_atores = cur.fetchall()

    cur.execute("SELECT m.movie_id, g.name FROM movies m JOIN movie_genres mg ON m.movie_id = mg.movie_id JOIN genres g ON mg.genre_id = g.genre_id")
    filmes_generos = cur.fetchall()
    
    cur.close()
    conn.close()
    return filmes_atores, filmes_generos

def construir_grafo(filmes_atores, filmes_generos):
    """Monta o grafo NetworkX."""
    G = nx.Graph()
    for movie_id, actor_name in filmes_atores:
        G.add_edge(movie_id, actor_name)
    for movie_id, genre_name in filmes_generos:
        G.add_edge(movie_id, genre_name)
    return G

def recomendar_filmes(G, movie_id_alvo, top_n=5):
    """Lógica de recomendação."""
    if not G.has_node(movie_id_alvo):
        return []
    
    # 1. Vizinhos diretos (Atores/Gêneros)
    vizinhos_do_alvo = list(G.neighbors(movie_id_alvo))
    candidatos = []
    
    # 2. Vizinhos de segundo grau (Filmes)
    for vizinho in vizinhos_do_alvo:
        candidatos.extend(list(G.neighbors(vizinho)))
        
    # 3. Filtros e Contagem
    candidatos_validos = [c for c in candidatos if c != movie_id_alvo and isinstance(c, int)]
    return Counter(candidatos_validos).most_common(top_n)

# --- BLOCO DE INTERFACE INTERATIVA ---
if __name__ == "__main__":
    print("\n=== CINEGRAPH: SISTEMA DE RECOMENDAÇÃO (CLI) ===")
    
    # 1. Preparação
    dados_atores, dados_generos = carregar_dados_grafo()
    if not dados_atores:
        print("Erro: Banco vazio. Rode o ETL primeiro.")
        exit()
        
    grafo = construir_grafo(dados_atores, dados_generos)
    print(f"-> Sistema pronto! {grafo.number_of_nodes()} nós conectados.\n")
    
    # 2. Loop Infinito (Menu)
    while True:
        print("-" * 50)
        entrada = input("Digite o ID do filme (ou 'sair' para fechar, '0' para exemplos): ").strip().lower()
        
        if entrada in ['sair', 'exit', 'q']:
            print("Encerrando... Até logo!")
            break
            
        if entrada == '0':
            print("\nExemplos de IDs no seu banco:")
            exemplos = [n for n in list(grafo.nodes()) if isinstance(n, int)][:5]
            print(exemplos)
            continue

        if not entrada.isdigit():
            print("Erro: Digite apenas números.")
            continue
            
        movie_id = int(entrada)
        print(f"\nBuscando recomendações para o filme {movie_id}...")
        
        resultados = recomendar_filmes(grafo, movie_id)
        
        if not resultados:
            print(f"Ops! Filme ID {movie_id} não encontrado ou sem conexões suficientes.")
        else:
            print("\n🎬 TOP RECOMENDAÇÕES:")
            for i, (rec_id, score) in enumerate(resultados, 1):
                print(f"{i}. Filme ID {rec_id} (Score: {score})")
        print("\n")