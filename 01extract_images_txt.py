import os
import re
import pdfplumber
import fitz

def limpar_texto(texto):
    padroes_remover = [
        r'Centro Avançado de Diagnóstico e Imagem',
        r'Paciente',
        r'Médico solicitante',
        r'Espécie\s*\|\s*Raça',
        r'Rua Luis do Paco 60, Tatuapé.',
        r'https://www.medcloud.co',
        r'Use o QR Code para ter acesso digital', 
        r'ao laudo e imagens do seu exame.',
        r'Laudo de Telerradiologia',
        r'Descrição:',
        r'EXAME DE TELERRADIOLOGIA',
        r'VIA TELERRADIOLOGIA',
        r'LAUDO RADIOGRÁFICO',
        r'LAUDO RADIOGRÁFICO VIA TELERRADIOLOGIA',
        r'PET Tutor Idade ID Data do exame',
        r'Exame Veterinário\(a\) Solicitante',
        r'Página:\s*\d+\s*de\s*\d+',
    ]

    for padrao in padroes_remover:
        texto = re.sub(padrao, '', texto, flags=re.IGNORECASE | re.MULTILINE)

    # Remove linhas vazias restantes e bloco assinado
    texto = re.sub(r'Assinado por:.*', '', texto, flags=re.IGNORECASE | re.DOTALL)
    linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
    return '\n'.join(linhas)

def extrair_texto_pdfplumber(pdf_path):
    texto_final = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto = limpar_texto(texto)
                texto_final.append(texto)

    texto_final = '\n\n'.join(texto_final)
    return texto_final

def salvar_txt_e_obter_nome_base(texto, contador, pasta_txt):
    linhas = texto.split('\n')
    if len(linhas) < 2:
        raise ValueError("Texto não possui segunda linha para extrair nome base")

    dados_segunda_linha = linhas[1].strip()
    dados_segunda_linha = re.sub(r'[\\/*?:"<>|]', '_', dados_segunda_linha)  # caracteres inválidos substituídos por _

    nome_base = f"{contador:03d}_{dados_segunda_linha}"[:100]  # limita 100 chars só por segurança
    nome_txt = f"{nome_base}.txt"
    caminho_txt = os.path.join(pasta_txt, nome_txt)

    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write(texto)

    print(f'Texto extraído e salvo como: {nome_txt}')
    return nome_base

def renomear_pdf(pdf_path_antigo, pasta_saida, nome_base):
    novo_nome_pdf = f"{nome_base}.pdf"
    pdf_path_novo = os.path.join(pasta_saida, novo_nome_pdf)

    try:
        os.rename(pdf_path_antigo, pdf_path_novo)
        return pdf_path_novo
    except Exception as e:
        print(f"❌ Erro ao renomear PDF: {e}")
        return pdf_path_antigo

def eh_imagem_valida(imagem_bytes, largura, altura, min_kb=10):
    tamanho_kb = len(imagem_bytes) / 1024
    if largura == 2092 and altura == 766:
        return False
    if tamanho_kb < min_kb:
        return False
    return True

def extrair_imagens_raiox_precisas(pdf_path, pasta_imagens, nome_base):
    doc = fitz.open(pdf_path)
    total_paginas = len(doc)

    if not os.path.exists(pasta_imagens):
        os.makedirs(pasta_imagens)

    imagens_salvas = 0
    for i in range(1, total_paginas):
        pagina = doc[i]
        imagens = pagina.get_images(full=True)

        for img_index, img in enumerate(imagens):
            xref = img[0]
            base_img = doc.extract_image(xref)
            imagem_bytes = base_img["image"]
            extensao = base_img["ext"]
            largura = base_img.get("width", 0)
            altura = base_img.get("height", 0)

            if eh_imagem_valida(imagem_bytes, largura, altura):
                nome_img = f"{nome_base}_pg{i+1}_img{img_index+1}.{extensao}"
                caminho_img = os.path.join(pasta_imagens, nome_img)

                with open(caminho_img, "wb") as f:
                    f.write(imagem_bytes)
                imagens_salvas += 1

    if imagens_salvas == 0:
        print(f"⚠️ Nenhuma imagem válida extraída de {pdf_path}")
    return imagens_salvas

def processar_tudo(pasta_pdfs, pasta_txt, pasta_imagens):
    arquivos_pdf = [f for f in os.listdir(pasta_pdfs) if f.lower().endswith('.pdf')]
    if not arquivos_pdf:
        print("❌ Nenhum PDF encontrado.")
        return

    if not os.path.exists(pasta_txt):
        os.makedirs(pasta_txt)

    contador = 1
    for arquivo in arquivos_pdf:
        pdf_path_antigo = os.path.join(pasta_pdfs, arquivo)

        try:
            texto = extrair_texto_pdfplumber(pdf_path_antigo)
            nome_base = salvar_txt_e_obter_nome_base(texto, contador, pasta_txt)
            pdf_path_novo = renomear_pdf(pdf_path_antigo, pasta_pdfs, nome_base)
            extrair_imagens_raiox_precisas(pdf_path_novo, pasta_imagens, nome_base)
            contador += 1
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")

    print("Processamento finalizado!")

if __name__ == "__main__":
    pasta_pdfs = r".\data\raw"
    pasta_txt = r".\data\extracted_texts"
    pasta_imagens = r".\data\extracted_images"

    processar_tudo(pasta_pdfs, pasta_txt, pasta_imagens)
