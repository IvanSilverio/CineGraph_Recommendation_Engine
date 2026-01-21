import psycopg2
import networkx as nx
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    # Copie a mesma função de conexão do seu etl.py
    return psycopg2.connect(
        dbname="cinegraph_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="192.168.0.154",
        port="5432"
    )

def carregar_dados_grafo():
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # QUERY 1: Busque todos os pares de Filme e Ator.
    # DICA: Faça um JOIN entre movies, movie_actors e actors.
    # Retorne algo como: [(ID_Filme, Nome_Ator), (ID_Filme, Nome_Ator)...]
    
    cur.execute("""
    SELECT m.movie_id, a.name
    FROM movies m
    JOIN movie_actors ma ON m.movie_id = ma.movie_id
    JOIN actors a ON ma.actor_id = a.actor_id
    """
    ) 
    
    filmes_atores = cur.fetchall()

    # QUERY 2: Busque todos os pares de Filme e Gênero.
    # DICA: JOIN entre movies, movie_genres e genres.
    cur.execute("""
    SELECT m.movie_id, g.name
    FROM movies m
    JOIN movie_genres mg ON m.movie_id = mg.movie_id
    JOIN genres g ON mg.genres_id = g.actor_id
    """)
    filmes_generos = cur.fetchall()
    
    conn.close()
    
    print (filmes_atores, filmes_generos)
    return filmes_atores, filmes_generos

def construir_grafo(filmes_atores, filmes_generos):
    """
    Recebe os dados brutos e cria o objeto Grafo do NetworkX.
    """
    G = nx.Graph() # Inicializa um grafo não-direcionado

    print("Construindo o grafo...")

    # PARTE 1: Adicionar arestas de Atores
    for movie_id, actor_name in filmes_atores:
        # No NetworkX, você adiciona uma aresta assim: G.add_edge(no1, no2)
        # O 'no1' será o ID do filme (ex: 550)
        # O 'no2' será o nome do ator (ex: "Brad Pitt")
        
        # SEU CODIGO AQUI: Adicione a aresta entre filme e ator
        pass

    # PARTE 2: Adicionar arestas de Gêneros
    for movie_id, genre_name in filmes_generos:
        # SEU CODIGO AQUI: Adicione a aresta entre filme e gênero
        pass
    
    return G

def recomendar_filmes(G, movie_id_alvo, top_n=5):
    """
    A mágica acontece aqui.
    Dado um movie_id, quais outros movie_ids compartilham mais vizinhos?
    """
    
    if not G.has_node(movie_id_alvo):
        return "Filme não encontrado no grafo."

    # 1. Pegar os vizinhos do filme alvo (Atores e Gêneros)
    # DICA: Use list(G.neighbors(no))
    vizinhos_do_alvo = [] # Preencha isso

    # 2. Encontrar filmes candidatos
    # Para cada vizinho (ex: 'Brad Pitt'), pegue os filmes que ele fez.
    candidatos = []
    
    for vizinho in vizinhos_do_alvo:
        # Pegue os vizinhos do vizinho (os outros filmes)
        vizinhos_de_segundo_grau = [] # Preencha isso
        candidatos.extend(vizinhos_de_segundo_grau)

    # 3. Contar frequência (Ranking simples)
    # Se o filme X aparece 5 vezes na lista de candidatos, ele tem 5 conexões em comum.
    # DICA: Use a classe Counter do python (from collections import Counter)
    
    # SEU CODIGO AQUI para contar e ordenar
    
    return [] # Retorne o top N

if __name__ == "__main__":
    # 1. Carrega dados
    dados_atores, dados_generos = carregar_dados_grafo()
    
    # 2. Cria Grafo
    grafo = construir_grafo(dados_atores, dados_generos)
    
    print(f"Grafo criado com {grafo.number_of_nodes()} nós e {grafo.number_of_edges()} conexões.")
    
    # 3. Testa recomendação
    # Escolha um ID de filme que você sabe que existe no seu banco (ex: O Poderoso Chefão)
    filme_teste = 238 # Verifique se esse ID existe no seu banco
    recomendacoes = recomendar_filmes(grafo, filme_teste)
    
    print(f"Recomendações para o filme {filme_teste}: {recomendacoes}")