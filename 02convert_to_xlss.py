import os
import pandas as pd
import re

def processar_txt_para_excel_com_imagens(pasta_txts, pasta_imagens, arquivo_excel_saida):
    dados = []

    for arquivo in os.listdir(pasta_txts):
        if arquivo.lower().endswith('.txt'):
            caminho_txt = os.path.join(pasta_txts, arquivo)
            with open(caminho_txt, 'r', encoding='utf-8') as f:
                linhas = [linha.strip() for linha in f if linha.strip()]

            if len(linhas) < 5:
                print(f"Arquivo {arquivo} ignorado: menos de 5 linhas úteis.")
                continue

            paciente = linhas[0]

            # Linha 2: tutor e idade
            linha2 = linhas[1]
            linha2_sem_paciente = linha2.replace(paciente, '', 1).strip()

            match_tutor = re.match(r'(.+?)\s+(\d+)\s+(meses|anos)', linha2_sem_paciente, re.IGNORECASE)
            if match_tutor:
                tutor = match_tutor.group(1).strip()
                idade = f"{match_tutor.group(2)} {match_tutor.group(3)}"
            else:
                tutor = ''
                idade = ''

            # Linha 3: espécie e raça
            linha3 = linhas[2]
            partes = [p.strip() for p in linha3.split('|')]
            especie = partes[0] if len(partes) > 0 else ''
            raca = partes[1] if len(partes) > 1 else ''

            # Linha 4: Região
            linha4 = linhas[3]
            regiao = linha4.replace('Região:', '').strip()

            # Linha 5: Posicionamentos
            linha5 = linhas[4]
            posicionamentos = linha5.replace('Projeções:', '').strip()

            # Laudo: tudo até "PET: {paciente}"
            laudo_linhas = []
            for linha in linhas[5:]:
                if linha.startswith(f'PET: {paciente}'):
                    break
                laudo_linhas.append(linha)
            laudo = ' '.join(laudo_linhas)

            # Pegar exame e data
            exame_completo = ''
            data = ''
            for linha in linhas:
                if linha.upper().startswith('EXAME:'):
                    exame_completo = linha.split(':', 1)[1].strip()
                if linha.upper().startswith('DATA:'):
                    data = linha.split(':', 1)[1].strip()

            # Limpa "- SILVESTRE"
            exame_completo = re.sub(r'\s*-\s*SILVESTRE', '', exame_completo, flags=re.IGNORECASE).strip()

            # Separa exame e numero de projeções
            match_exame = re.match(r'(.+?)\s+(\d+P)$', exame_completo)
            if match_exame:
                exame = match_exame.group(1).strip()
                num_projecoes = match_exame.group(2).strip()
            else:
                exame = exame_completo
                num_projecoes = ''

            # Limpar raca se contiver nome do exame
            idx = raca.find(exame)
            if idx != -1:
                raca = raca[:idx].strip()

            # Procurar imagens associadas
            nome_base = os.path.splitext(arquivo)[0]
            imagens_relacionadas = sorted([
                img for img in os.listdir(pasta_imagens)
                if img.startswith(nome_base)
            ])
            imagens_str = ', '.join(imagens_relacionadas)

            # Montar dicionário
            registro = {
                'Nome do Paciente': paciente,
                'Nome do Tutor': tutor,
                'Idade': idade,
                'Espécie': especie,
                'Raça': raca,
                'Regiao': regiao,
                'Posicionamentos': posicionamentos,
                'Laudo': laudo,
                'Exame': exame,
                'Numero de Projeções': num_projecoes,
                'Data do Exame': data,
                'Imagens': imagens_str
            }

            dados.append(registro)

    # Criar DataFrame
    df = pd.DataFrame(dados)

    # Salvar como Excel
    df.insert(0, 'ID', [f"{i:03d}" for i in range(1, len(df) + 1)])
    df.to_excel(arquivo_excel_saida, index=False)
    print(f"Arquivo Excel gerado em: {arquivo_excel_saida}")

pasta_txts = r".\data\extracted_texts"
pasta_imagens = r".\data\extracted_images"
arquivo_excel_saida = r"notebooks\laudos_piloto.xlsx"

processar_txt_para_excel_com_imagens(pasta_txts, pasta_imagens, arquivo_excel_saida)
