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
        # Iniciamos com headless=False para você ver o navegador abrindo
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print(f"Acessando a página e aguardando carregamento...")
            page.goto(URL_MINHA_LISTA, timeout=60000, wait_until="networkidle")
            
            print("Página aberta com sucesso! Buscando produtos na tela...")
            page.wait_for_timeout(3000)
            
            cards = page.locator(".poly-card, .ui-search-layout__item, .andes-card").all()
            
            if not cards:
                print("⚠️ Nenhum card padrão encontrado. Tirando print para diagnóstico...")
                page.screenshot(path="erro_pagina.png")
                print("Um print 'erro_pagina.png' foi salvo na pasta.")
                return

            print(f"Encontrados {len(cards)} produtos. Extraindo dados...")
            
            for card in cards:
                try:
                    titulo = card.locator("h2, .poly-component__title, .ui-search-item__title").inner_text()
                    
                    # No Mercado Livre, o preço atual (promocional/destacado) geralmente fica dentro de .poly-price__current
                    # Vamos buscar especificamente o bloco de preço atual
                    bloco_preco_atual = card.locator(".poly-price__current, .ui-search-price__second-line").first
                    
                    parte_inteira_atual = bloco_preco_atual.locator(".andes-money-amount__fraction").inner_text().replace(".", "")
                    try:
                        centavos_atual = bloco_preco_atual.locator(".andes-money-amount__cents").inner_text()
                    except:
                        centavos_atual = "00"
                    preco_atual = float(f"{parte_inteira_atual}.{centavos_atual}")

                    # Tenta capturar o preço antigo (riscado) que costuma vir acima do preço atual na listagem
                    try:
                        bloco_preco_antigo = card.locator("s.andes-money-amount, .ui-search-price__original-value").first
                        parte_inteira_antigo = bloco_preco_antigo.locator(".andes-money-amount__fraction").inner_text().replace(".", "")
                        try:
                            centavos_antigo = bloco_preco_antigo.locator(".andes-money-amount__cents").inner_text()
                        except:
                            centavos_antigo = "00"
                        preco_antigo = float(f"{parte_inteira_antigo}.{centavos_antigo}")
                    except:
                        # Se não houver preço riscado oficial na listagem, calcula uma margem de 15% acima
                        preco_antigo = round(preco_atual * 1.15, 2)

                    # Garante que se por acaso inverter, o preço antigo seja sempre maior que o atual
                    if preco_antigo <= preco_atual:
                        preco_antigo = round(preco_atual * 1.15, 2)

                    # Captura o link e a imagem
                    link = card.locator("a").first.get_attribute("href")
                    imagem = card.locator("img").first.get_attribute("src")
                    if not imagem:
                        imagem = card.locator("img").first.get_attribute("data-src")

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
    # Sobrescreve o JSON garantindo que só fiquem os itens atuais da sua lista
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(novos, f, ensure_ascii=False, indent=4)
    
    print(f"✨ Sucesso! O arquivo produtos.json foi sincronizado com {len(novos)} produtos da sua lista.")

if __name__ == "__main__":
    extrair_lista_afiliado()