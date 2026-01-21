import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def criar_tabelas():
    # Conecta no 127.0.0.1 para compatibilidade total
    conn = psycopg2.connect(
        dbname="cinegraph_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port="5432"
    )
    cur = conn.cursor()
    
    # 1. Tabela Principal
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

    # 2. Entidades Secundárias
    cur.execute("CREATE TABLE actors (actor_id INTEGER PRIMARY KEY, name VARCHAR(255));")
    cur.execute("CREATE TABLE genres (genre_id INTEGER PRIMARY KEY, name VARCHAR(100));")
    
    # NOVAS TABELAS
    cur.execute("CREATE TABLE directors (director_id INTEGER PRIMARY KEY, name VARCHAR(255));")
    cur.execute("CREATE TABLE keywords (keyword_id INTEGER PRIMARY KEY, name VARCHAR(255));")

    # 3. Tabelas de Relacionamento (Links)
    cur.execute("""
        CREATE TABLE movie_actors (
            movie_id INTEGER REFERENCES movies(movie_id),
            actor_id INTEGER REFERENCES actors(actor_id),
            character_name VARCHAR(255),    
            PRIMARY KEY (movie_id, actor_id)
        );
    """)

    cur.execute("""
        CREATE TABLE movie_genres (
            movie_id INTEGER REFERENCES movies(movie_id),
            genre_id INTEGER REFERENCES genres(genre_id),
            PRIMARY KEY (movie_id, genre_id)
        );
    """)
    
    # Novos links
    cur.execute("""
        CREATE TABLE movie_directors (
            movie_id INTEGER REFERENCES movies(movie_id),
            director_id INTEGER REFERENCES directors(director_id),
            PRIMARY KEY (movie_id, director_id)
        );
    """)
    
    cur.execute("""
        CREATE TABLE movie_keywords (
            movie_id INTEGER REFERENCES movies(movie_id),
            keyword_id INTEGER REFERENCES keywords(keyword_id),
            PRIMARY KEY (movie_id, keyword_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Banco de dados criado!")

if __name__ == "__main__":
    criar_tabelas()