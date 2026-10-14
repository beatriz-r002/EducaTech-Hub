import json
import os

ARQUIVO_JSON = "produtos.json"

def carregar_produtos():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_produtos(produtos):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

def listar_produtos(produtos):
    if not produtos:
        print("\n📭 Nenhum produto cadastrado no momento.")
        return
    print("\n--- 📋 LISTA DE PRODUTOS ATUAIS NO SITE ---")
    for i, p in enumerate(produtos):
        print(f"[{i}] {p['titulo']} | Atual: R$ {p['precoAtual']} | Antigo: R$ {p['precoAntigo']}")
    print("-" * 45)

def adicionar_produto():
    print("\n--- 🛒 ADICIONAR NOVO PRODUTO ---")
    titulo = input("Título do produto: ").strip()
    if not titulo:
        print("Operação cancelada: O título não pode estar vazio.")
        return

    try:
        preco_antigo = float(input("Preço antigo (ex: 65.90): ").replace(',', '.'))
        preco_atual = float(input("Preço atual / oferta (ex: 58.07): ").replace(',', '.'))
    except ValueError:
        print("Erro: Digite valores numéricos válidos para os preços.")
        return

    imagem = input("Caminho ou URL da imagem (ex: img/esp32.webp ou link): ").strip()
    link = input("Seu Link de Afiliado do Mercado Livre: ").strip()
    
    print("\nCategorias disponíveis: quentes, recentes, xadrez, papelaria")
    categoria = input("Categorias separadas por espaço (ex: quentes recentes): ").strip()

    novo_produto = {
        "titulo": titulo,
        "precoAntigo": preco_antigo,
        "precoAtual": preco_atual,
        "imagem": imagem,
        "link": link,
        "categoria": categoria if categoria else "quentes recentes"
    }

    produtos = carregar_produtos()
    
    # Verifica duplicidade
    for p in produtos:
        if p["titulo"].lower() == novo_produto["titulo"].lower():
            print("\n⚠️ Já existe um produto com este título. Use a opção de editar ou apagar.")
            return

    produtos.append(novo_produto)
    salvar_produtos(produtos)
    print(f"\n🚀 Produto '{titulo}' adicionado com sucesso!")

def remover_produto():
    produtos = carregar_produtos()
    listar_produtos(produtos)
    if not produtos:
        return

    try:
        indice = int(input("\nDigite o número [ID] do produto que deseja EXCLUIR: "))
        if 0 <= indice < len(produtos):
            removido = produtos.pop(indice)
            salvar_produtos(produtos)
            print(f"\n🗑️ Produto '{removido['titulo']}' removido com sucesso!")
        else:
            print("Erro: Número inválido.")
    except ValueError:
        print("Erro: Digite um número inteiro válido.")

def menu():
    while True:
        print("\n=== 🛠️ GERENCIADOR DO EDUCATECH HUB ===")
        print("1. Listar produtos atuais")
        print("2. Adicionar novo produto")
        print("3. Excluir um produto")
        print("4. Sair")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == '1':
            produtos = carregar_produtos()
            listar_produtos(produtos)
        elif opcao == '2':
            adicionar_produto()
        elif opcao == '3':
            remover_produto()
        elif opcao == '4':
            print("\nEncerrando o painel. Até logo!")
            break
        else:
            print("Opção inválida! Escolha entre 1 e 4.")

if __name__ == "__main__":
    menu()