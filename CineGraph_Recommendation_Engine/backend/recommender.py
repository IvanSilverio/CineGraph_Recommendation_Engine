import psycopg2
import networkx as nx
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

def get_db_connection():
    #Estabelece conexão com o banco PostgreSQL usando variáveis de ambiente.
    return psycopg2.connect(
        dbname="cinegraph_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port="5432"
    )

def carregar_dados_grafo():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Atores
    cur.execute("""SELECT m.movie_id, a.name 
        FROM movies m 
        JOIN movie_actors ma ON m.movie_id = ma.movie_id 
        JOIN actors a ON ma.actor_id = a.actor_id""")
    filmes_atores = cur.fetchall()

    # 2. Gêneros
    cur.execute("""SELECT m.movie_id, g.name 
        FROM movies m 
        JOIN movie_genres mg ON m.movie_id = mg.movie_id 
        JOIN genres g ON mg.genre_id = g.genre_id""")
    filmes_generos = cur.fetchall()
    
    # 3. Diretores
    cur.execute("""SELECT m.movie_id, d.name 
                FROM movies m 
                JOIN movie_directors md ON m.movie_id = md.movie_id 
                JOIN directors d ON md.director_id = d.director_id""")
    filmes_diretores = cur.fetchall()
    
    # 4. Keywords
    cur.execute("""SELECT m.movie_id, k.name 
                FROM movies m 
                JOIN movie_keywords mk ON m.movie_id = mk.movie_id 
                JOIN keywords k ON mk.keyword_id = k.keyword_id""")
    filmes_keywords = cur.fetchall()
    
    conn.close()
    # Retorna os 4 conjuntos de dados
    return filmes_atores, filmes_generos, filmes_diretores, filmes_keywords

def construir_grafo(filmes_atores, filmes_generos, filmes_diretores, filmes_keywords):
    G = nx.Graph()
    
    # TABELA DE PESOS
    PESO_DIRETOR = 5.0  # Muito forte!
    PESO_ATOR    = 3.0  # Forte
    PESO_KEYWORD = 2.0  # Médio (Bom para nichos)
    PESO_GENERO  = 0.5  # Fraco (Muito genérico)
    
    for movie_id, actor_name in filmes_atores:    G.add_edge(movie_id, actor_name, weight=PESO_ATOR)
    for movie_id, genre_name in filmes_generos:   G.add_edge(movie_id, genre_name, weight=PESO_GENERO)
    for movie_id, director_name in filmes_diretores: G.add_edge(movie_id, director_name, weight=PESO_DIRETOR)
    for movie_id, keyword_name in filmes_keywords:  G.add_edge(movie_id, keyword_name, weight=PESO_KEYWORD)
        
    return G

def recomendar_filmes(G, movie_id_alvo, top_n=5):
    """
    Algoritmo de Recomendação Baseado em Conteúdo (Grafo Ponderado).
    
    Como funciona:
    1. Identifica vizinhos diretos (Características do filme).
    2. Expande para vizinhos de 2º grau (Outros filmes com mesmas características).
    3. Soma os pesos dos caminhos para calcular o Score de Similaridade.
    """
    if not G.has_node(movie_id_alvo):
        return []
    
    # Dicionário acumulador de scores: {ID_Filme: Score_Total}
    scores = {}
    
    # 1. Pega as características do filme alvo (Atores, Gêneros)
    vizinhos_diretos = list(G.neighbors(movie_id_alvo))
    
    for caracteristica in vizinhos_diretos:
        # Peso da ida: Filme Alvo -> Característica
        peso_origem = G[movie_id_alvo][caracteristica]['weight']
        
        # 2. Pega os outros filmes que têm essa característica
        candidatos = list(G.neighbors(caracteristica))
        
        for filme_candidato in candidatos:
            # Pula o próprio filme alvo e nós que não são filmes (nomes de atores/generos)
            if filme_candidato == movie_id_alvo or not isinstance(filme_candidato, int):
                continue
            
            # Peso da volta: Característica -> Filme Candidato
            peso_destino = G[caracteristica][filme_candidato]['weight']
            
            # O Score é a soma dos pesos do caminho
            score_conexao = peso_origem + peso_destino
            
            if filme_candidato in scores:
                scores[filme_candidato] += score_conexao
            else:
                scores[filme_candidato] = score_conexao

    # 3. Ordena do maior para o menor score
    recomendacoes_ordenadas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return recomendacoes_ordenadas[:top_n]

def buscar_info_filmes(ids_filmes):
    """Enriquece os IDs numéricos com Título, Poster e Ano via SQL."""
    if not ids_filmes:
        return {}
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    format_strings = ','.join(['%s'] * len(ids_filmes))
    query = f"""
        SELECT movie_id, title, poster_path, release_date, vote_average
        FROM movies 
        WHERE movie_id IN ({format_strings})
    """
    
    cur.execute(query, tuple(ids_filmes))
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    
    filmes_dict = {}
    base_url_img = "https://image.tmdb.org/t/p/w500"
    
    for row in resultados:
        m_id, title, poster, date, vote = row
        filmes_dict[m_id] = {
            "titulo": title,
            "poster": f"{base_url_img}{poster}" if poster else "https://via.placeholder.com/500x750?text=Sem+Imagem",
            "ano": str(date).split('-')[0] if date else "N/A",
            "voto": vote
        }
        
    return filmes_dict

def buscar_filmes_por_nome(query_texto):
    """
    Busca filmes no banco que contenham o texto informado.
    Usa ILIKE para ignorar maiúsculas/minúsculas.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # O % envolve o texto para buscar em qualquer parte (começo, meio ou fim)
    termo_busca = f"%{query_texto}%"
    
    sql = """
        SELECT movie_id, title, release_date 
        FROM movies 
        WHERE title ILIKE %s 
        LIMIT 5;
    """
    
    cur.execute(sql, (termo_busca,))
    resultados = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Formata para JSON
    lista_filmes = []
    for row in resultados:
        lista_filmes.append({
            "id": row[0],
            "titulo": row[1],
            "ano": row[2].year if row[2] else "N/A"
        })
        
    return lista_filmes

if __name__ == "__main__":
    # Teste rápido ao rodar o arquivo diretamente
    print("Teste de Recomendação")
    dados_atores, dados_generos, dados_diretores, dados_keywords = carregar_dados_grafo()
    grafo = construir_grafo(dados_atores, dados_generos, dados_diretores, dados_keywords)
    print(recomendar_filmes(grafo, 278))