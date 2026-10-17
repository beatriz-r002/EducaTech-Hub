import json
import os
import re
import unicodedata
from playwright.sync_api import sync_playwright

ARQUIVO_JSON = "produtos.json"
# Cole aqui o link final completo da sua lista aberta no navegador
URL_MINHA_LISTA = "https://meli.la/1xpoNCD"

def normalizar_texto(texto):
    texto = unicodedata.normalize("NFD", str(texto).casefold())
    texto = "".join(caractere for caractere in texto if unicodedata.category(caractere) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto).split())


def definir_categoria(titulo):
    titulo_normalizado = normalizar_texto(titulo)
    regras = (
        ("jogos", ("jogo", "jogos", "xadrez", "cubo magico", "puzzle", "puzzles", "quebra cabeca", "quebra cabecas", "tabuleiro", "tabuleiros", "baralho")),
        ("visual", ("relogio", "relogios", "oculos", "boina", "boinas", "chapeu", "chapeus", "bolsa", "bolsas", "mochila", "mochilas", "carteira", "carteiras", "pulseira", "pulseiras", "colar", "colares")),
        ("alta performance", (
            "teclado", "teclados", "mouse", "mouses", "headset", "headsets", "fone", "fones", "ssd", "ssds", "hub", "hubs", "monitor", "monitores", "kindle",
            "ereader", "e reader", "leitor digital", "leitores digitais", "suporte para notebook", "suporte para notebooks", "webcam", "webcams",
            "microfone", "microfones", "pendrive", "pendrives", "pen drive", "cabo", "cabos", "processador", "processadores", "memoria", "tablet", "tablets", "laptop", "laptops", "notebook", "notebooks"
        )),
        ("arquitetura de mesa", (
            "estojo", "estojos", "organizador", "organizadores", "caderno", "cadernos", "suporte de mesa", "suportes de mesa", "suporte para celular", "suporte de celular",
            "fichario", "ficharios", "agenda", "agendas", "planner", "planners", "caneta", "canetas", "bloco", "blocos",
            "marca texto", "marcador", "marcadores", "lapis", "anotacao", "anotacoes", "luminaria", "luminarias", "abajur", "abajures",
            "lampada", "lampadas", "decoracao", "neon", "quadro", "quadros", "papelaria"
        )),
    )

    for categoria, palavras in regras:
        for palavra in palavras:
            palavra_normalizada = normalizar_texto(palavra)
            if f" {palavra_normalizada} " in f" {titulo_normalizado} ":
                return categoria

    return "revisar"

def extrair_lista_afiliado():
    print("🤖 Iniciando o robô para varrer a sua lista do Mercado Livre...")
    
    novos_produtos = []
    
    with sync_playwright() as p:
        # Iniciamos com headless=False para você ver o navegador abrindo
        modo_headless = os.getenv("PLAYWRIGHT_HEADLESS", "").strip().lower() in {"1", "true", "yes"}
        browser = p.chromium.launch(headless=modo_headless)
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
                    # Tenta pegar o título usando várias opções possíveis do layout do Mercado Livre
                    titulo_el = card.locator("h2, h3, a.poly-component__title, .poly-component__title, .ui-search-item__title").first
                    titulo = titulo_el.inner_text().strip() if titulo_el.count() > 0 else "Produto Mercado Livre"
                    
                    if not titulo:
                        titulo = "Produto Mercado Livre"
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
                        "categoria": definir_categoria(titulo)
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