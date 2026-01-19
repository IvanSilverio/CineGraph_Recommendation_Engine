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
    
    #Estabelece conexão com o banco de dados PostgreSQL
    
    try:
        return psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port="5432"
        )
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        exit(1)

def carregar_dados_grafo():
    """
    Busca os relacionamentos (Filme-Ator e Filme-Gênero) no banco de dados.
    Retorna duas listas de tuplas.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"[INFO] Carregando dados do banco {DB_NAME}...")

    # Busca relacionamentos Filme <-> Ator
    cur.execute("""
        SELECT m.movie_id, a.name
        FROM movies m
        JOIN movie_actors ma ON m.movie_id = ma.movie_id
        JOIN actors a ON ma.actor_id = a.actor_id
    """)
    filmes_atores = cur.fetchall()

    # Busca relacionamentos Filme <-> Gênero
    cur.execute("""
        SELECT m.movie_id, g.name
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
    """)
    filmes_generos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    print(f"[INFO] Dados carregados: {len(filmes_atores)} atores vinculados e {len(filmes_generos)} gêneros vinculados.")
    return filmes_atores, filmes_generos

def construir_grafo(filmes_atores, filmes_generos):
    """
    Constrói um grafo usando NetworkX.
    Nós: Filmes (int), Atores (str), Gêneros (str).
    Arestas: Conexões entre Filmes e suas propriedades.
    """
    G = nx.Graph()
    print("[INFO] Construindo estrutura do grafo...")

    # Adiciona arestas Filme <-> Ator
    for movie_id, actor_name in filmes_atores:
        G.add_edge(movie_id, actor_name)

    # Adiciona arestas Filme <-> Gênero
    for movie_id, genre_name in filmes_generos:
        G.add_edge(movie_id, genre_name)
    
    return G

def recomendar_filmes(G, movie_id_alvo, top_n=5):
    """
    Realiza recomendação baseada em filtragem colaborativa (vizinhos de segundo grau)
    
        G: O grafo NetworkX.
        movie_id_alvo: ID do filme base.
        top_n: Quantidade de recomendações desejadas.
        
    Returns:
        Lista de tuplas (movie_id, pontuação).
    """
    if not G.has_node(movie_id_alvo):
        print(f"[AVISO] O filme ID {movie_id_alvo} não foi encontrado no grafo.")
        return []

    # 1. Identifica características do filme (Atores e Gêneros)
    # Primeiro Grau: Filme -> [Ator A, Gênero B, ...]
    vizinhos_do_alvo = list(G.neighbors(movie_id_alvo))

    candidatos = []
    
    # 2. Busca filmes que compartilham essas características
    # Segundo Grau: [Ator A] -> Filme X, Filme Y
    for vizinho in vizinhos_do_alvo:
        vizinhos_de_segundo_grau = list(G.neighbors(vizinho))
        candidatos.extend(vizinhos_de_segundo_grau)
        
    # 3. Filtra a lista
    # Remove o próprio filme alvo e garante que retornamos apenas IDs de filmes (int)
    candidatos_validos = [
        c for c in candidatos 
        if c != movie_id_alvo and isinstance(c, int)
    ]

    # 4. Classifica por frequência (similaridade)
    contagem = Counter(candidatos_validos)
    
    return contagem.most_common(top_n)

if __name__ == "__main__":
    # --- Execução Principal ---
    
    # 1. Carregamento e Construção
    dados_atores, dados_generos = carregar_dados_grafo()
    
    if not dados_atores:
        print("[ERRO] Nenhum dado encontrado. Verifique se o ETL foi executado.")
        exit(1)

    grafo = construir_grafo(dados_atores, dados_generos)
    print(f"[INFO] Grafo pronto com {grafo.number_of_nodes()} nós e {grafo.number_of_edges()} conexões.")
    
    # 2. Exemplo de Uso (Teste)
    # ID 278: Um Sonho de Liberdade (Shawshank Redemption)
    id_teste = 278 
    
    print(f"\n--- Gerando recomendações para o filme ID: {id_teste} ---")
    recomendacoes = recomendar_filmes(grafo, id_teste)
    
    if recomendacoes:
        print(f"Top recomendações encontradas:")
        for i, (filme_id, score) in enumerate(recomendacoes, 1):
            print(f"{i}. Filme ID {filme_id} (Score de similaridade: {score})")
    else:
        print("Nenhuma recomendação encontrada ou filme inexistente.")