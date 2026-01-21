# No topo do cli_cinegraph.py
from recommender import carregar_dados_grafo, construir_grafo, recomendar_filmes
0
# BLOCO DE INTERFACE INTERATIVA
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