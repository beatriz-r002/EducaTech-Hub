import json
import os
from playwright.sync_api import sync_playwright

ARQUIVO_JSON = "produtos.json"
# Cole aqui o link final completo da sua lista aberta no navegador
URL_MINHA_LISTA = "https://meli.la/1xpoNCD"

def extrair_lista_afiliado():
    print("🤖 Iniciando o robô para varrer a sua lista do Mercado Livre...")
    
    novos_produtos = []
    
    with sync_playwright() as p:
        # Iniciamos com headless=False para você ver o navegador abrindo e acompanhando o que acontece
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print(f"Acessando a página e aguardando carregamento...")
            # Usa 'networkidle' para garantir que a página terminou de carregar os redirecionamentos e scripts
            page.goto(URL_MINHA_LISTA, timeout=60000, wait_until="networkidle")
            
            print("Página aberta com sucesso! Buscando produtos na tela...")
            
            # Dá um tempinho extra para garantir que os cards renderizaram
            page.wait_for_timeout(3000)
            
            # Vamos tentar capturar os cards usando seletores genéricos robustos do Mercado Livre
            # O ML costuma usar tags como .ui-search-layout__item ou .poly-card
            cards = page.locator(".poly-card, .ui-search-layout__item, .andes-card").all()
            
            if not cards:
                print("⚠️ Nenhum card padrão encontrado. Tirando print para diagnóstico...")
                page.screenshot(path="erro_pagina.png")
                print("Um print 'erro_pagina.png' foi salvo na pasta para você ver o que o robô enxergou.")
                return

            print(f"Encontrados {len(cards)} produtos. Extraindo dados...")
            
            for card in cards:
                try:
                    titulo = card.locator("h2, .poly-component__title, .ui-search-item__title").inner_text()
                    
                    # Captura correta de preço com centavos
                    parte_inteira = card.locator(".andes-money-amount__fraction").first.inner_text().replace(".", "")
                    try:
                        centavos = card.locator(".andes-money-amount__cents").first.inner_text()
                    except:
                        centavos = "00"
                    
                    preco_atual = float(f"{parte_inteira}.{centavos}")
                    
                    link = card.locator("a").first.get_attribute("href")
                    
                    imagem = card.locator("img").first.get_attribute("src")
                    if not imagem:
                        imagem = card.locator("img").first.get_attribute("data-src")
                        
                    preco_antigo = round(preco_atual * 1.15, 2)
                    
                    produto = {
                        "titulo": titulo,
                        "precoAntigo": preco_antigo,
                        "precoAtual": preco_atual,
                        "imagem": imagem if imagem else "",
                        "link": link if link else "",
                        "categoria": "quentes recentes"
                    }
                    novos_produtos.append(produto)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao acessar ou raspar a página: {e}")
        finally:
            browser.close()

    if novos_produtos:
        atualizar_json(novos_produtos)
    else:
        print("⚠️ Nenhum produto foi extraído com sucesso.")

def atualizar_json(novos):
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            atuais = json.load(f)
    else:
        atuais = []

    for novo in novos:
        existe = False
        for p in atuais:
            if p["titulo"] == novo["titulo"]:
                p["precoAtual"] = novo["precoAtual"]
                p["link"] = novo["link"]
                existe = True
                break
        if not existe:
            atuais.append(novo)

    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(atuais, f, ensure_ascii=False, indent=4)
    
    print("✨ Arquivo produtos.json atualizado com sucesso pelo robô!")

if __name__ == "__main__":
    extrair_lista_afiliado()

def atualizar_json(novos):
    # Em vez de ler o antigo e mesclar, nós salvamos DIRETAMENTE a nova lista 
    # garantindo que só exista no site o que está na sua lista oficial do Mercado Livre agora!
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(novos, f, ensure_ascii=False, indent=4)
    
    print(f"✨ Sucesso! O arquivo produtos.json foi sincronizado com {len(novos)} produtos da sua lista.")