import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def criar_tabelas():
    # Conecta no Localhost (Linux)
    conn = psycopg2.connect(
        dbname="cinegraph_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port="5432"
    )
    cur = conn.cursor()

    print("--- 1. Resetando o banco (Apagando tabelas antigas)...")
    cur.execute("DROP TABLE IF EXISTS movie_genres CASCADE;")
    cur.execute("DROP TABLE IF EXISTS movie_actors CASCADE;")
    cur.execute("DROP TABLE IF EXISTS genres CASCADE;")
    cur.execute("DROP TABLE IF EXISTS actors CASCADE;")
    cur.execute("DROP TABLE IF EXISTS movies CASCADE;")

    print("--- 2. Criando tabelas NOVAS (Com colunas extras)...")
    
    # 1. Tabela de Filmes
    cur.execute("""
        CREATE TABLE movies (
            movie_id INTEGER PRIMARY KEY,
            title VARCHAR(255),
            overview TEXT,                
            release_date DATE,
            poster_path VARCHAR(255),     
            vote_average FLOAT
        );
    """)

    # 2. Tabela de Atores
    cur.execute("""
        CREATE TABLE actors (
            actor_id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
    """)

    # 3. Tabela de Gêneros
    cur.execute("""
        CREATE TABLE genres (
            genre_id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
    """)

    # 4. Ligação Filme <-> Ator 
    cur.execute("""
        CREATE TABLE movie_actors (
            movie_id INTEGER REFERENCES movies(movie_id),
            actor_id INTEGER REFERENCES actors(actor_id),
            character_name VARCHAR(255),    
            PRIMARY KEY (movie_id, actor_id)
        );
    """)

    # 5. Ligação Filme <-> Gênero
    cur.execute("""
        CREATE TABLE movie_genres (
            movie_id INTEGER REFERENCES movies(movie_id),
            genre_id INTEGER REFERENCES genres(genre_id),
            PRIMARY KEY (movie_id, genre_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("SUCESSO!")

if __name__ == "__main__":
    criar_tabelas()