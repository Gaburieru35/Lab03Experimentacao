import os
import requests
import pandas as pd
from datetime import datetime
import time

# ================================
# CONFIGURAÇÕES
# ================================
GITHUB_TOKEN = "" 
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Arquivos
REPOS_CSV = "repositorios_filtrados.csv"
OUTPUT_CSV = "dataset_lab03s01.csv"


def save_pr_to_csv(record: dict, csv_path: str):
    """Salva ou atualiza um PR na planilha CSV.

    Regras:
    - Identifica linhas por (repo, pr_number).
    - Se existir, atualiza a linha com os novos valores.
    - Se não existir, anexa uma nova linha.
    """
    # Se não existe ainda, cria um DataFrame novo com a única linha
    if not os.path.exists(csv_path):
        df_new = pd.DataFrame([record])
        df_new.to_csv(csv_path, index=False, encoding="utf-8")
        return

    try:
        df_existing = pd.read_csv(csv_path)
    except Exception:
        # Se não conseguir ler (arquivo corrompido), sobrescreve com novo
        df_existing = pd.DataFrame()

    # chave única
    mask = (df_existing.get("repo") == record["repo"]) & (df_existing.get("pr_number") == record["pr_number"]) if not df_existing.empty else pd.Series(dtype=bool)

    if not df_existing.empty and mask.any():
        # atualiza a(s) linha(s) existentes
        idx = df_existing[mask].index
        for col, val in record.items():
            df_existing.loc[idx, col] = val
        df_existing.to_csv(csv_path, index=False, encoding="utf-8")
    else:
        # anexa nova linha
        df_existing = pd.concat([df_existing, pd.DataFrame([record])], ignore_index=True)
        df_existing.to_csv(csv_path, index=False, encoding="utf-8")

# ================================
# CARREGAR REPOSITÓRIOS FILTRADOS
# ================================
repos_filtrados = pd.read_csv(REPOS_CSV)
print(f"🔍 {len(repos_filtrados)} repositórios carregados para coleta de PRs.\n")

# ================================
# ETAPA 2: COLETAR PULL REQUESTS DETALHADOS
# ================================
resultados = []

for repo in repos_filtrados["nome"]:
    print(f"\n➡️  Coletando PRs de {repo}...")
    page = 1
    prs_coletados = 0  # contador por repositório

    while prs_coletados < 100:
        pr_url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=50&page={page}"
        pr_resp = requests.get(pr_url, headers=HEADERS)
        if pr_resp.status_code != 200:
            print(f"⚠️ Erro ao buscar PRs: {pr_resp.status_code}")
            break

        prs = pr_resp.json()
        if not prs:
            break  # fim das páginas

        for pr in prs:

            # Limite de PRs por repositório
            if prs_coletados >= 100:
                break
            # Verifica datas
            if not pr.get("created_at") or not pr.get("closed_at"):
                continue

            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            closed = datetime.fromisoformat(pr["closed_at"].replace("Z", "+00:00"))
            duracao_horas = (closed - created).total_seconds() / 3600
            if duracao_horas < 1:
                continue  # descarta PRs revisados automaticamente

            # Detalhes completos do PR
            detalhes_url = f"https://api.github.com/repos/{repo}/pulls/{pr['number']}"
            detalhes = requests.get(detalhes_url, headers=HEADERS).json()
            arquivos_modificados = detalhes.get("changed_files", 0)
            linhas_adicionadas = detalhes.get("additions", 0)
            linhas_removidas = detalhes.get("deletions", 0)
            descricao_len = len(detalhes.get("body") or "")

            # Revisões humanas
            reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr['number']}/reviews"
            reviews = requests.get(reviews_url, headers=HEADERS).json()
            if not isinstance(reviews, list) or len(reviews) == 0:
                continue  # descarta PRs sem revisão humana

            # Comentários gerais no PR
            comentarios_url = f"https://api.github.com/repos/{repo}/issues/{pr['number']}/comments"
            comentarios = requests.get(comentarios_url, headers=HEADERS).json()

            # Comentários inline (review comments)
            review_comments_url = f"https://api.github.com/repos/{repo}/pulls/{pr['number']}/comments"
            review_comments = requests.get(review_comments_url, headers=HEADERS).json()

            # Participantes únicos (autor + reviewers + comentadores)
            participantes = set()
            if pr.get("user") and pr["user"].get("login"):
                participantes.add(pr["user"]["login"])
            for r in reviews:
                if r.get("user") and r["user"].get("login"):
                    participantes.add(r["user"]["login"])
            for c in comentarios if isinstance(comentarios, list) else []:
                if c.get("user") and c["user"].get("login"):
                    participantes.add(c["user"]["login"])
            for c in review_comments if isinstance(review_comments, list) else []:
                if c.get("user") and c["user"].get("login"):
                    participantes.add(c["user"]["login"])

            resultados.append({
                "repo": repo,
                "pr_number": pr["number"],
                "status": "merged" if pr.get("merged_at") else "closed",
                "arquivos_modificados": arquivos_modificados,
                "linhas_adicionadas": linhas_adicionadas,
                "linhas_removidas": linhas_removidas,
                "tempo_analise_horas": round(duracao_horas, 2),
                "descricao_len": descricao_len,
                "participantes": len(participantes),
                "comentarios": len(comentarios) if isinstance(comentarios, list) else 0,
                "review_comments": len(review_comments) if isinstance(review_comments, list) else 0,
                "reviews": len(reviews)
            })
            # Salva/atualiza a planilha a cada PR coletado
            pr_record = resultados[-1]
            try:
                save_pr_to_csv(pr_record, OUTPUT_CSV)
            except Exception as e:
                print(f"⚠️ Erro ao salvar PR {pr['number']} de {repo}: {e}")

            prs_coletados += 1
            time.sleep(0.5)  # evita rate limit

        page += 1
        time.sleep(1)
        
    print(f"✅ Repositório {repo} analisado com sucesso ({prs_coletados} PRs válidos coletados).")

# ================================
# SALVAR DATASET FINAL (mescla segura)
# ================================
df = pd.DataFrame(resultados)

# Se não houver resultados nesta execução, apenas informa o que existe
if df.empty:
    if os.path.exists(OUTPUT_CSV):
        df_existing = pd.read_csv(OUTPUT_CSV)
        print(f"\nℹ️ Nenhum PR novo coletado nesta execução. {len(df_existing)} PRs já presentes em {OUTPUT_CSV}.")
    else:
        print(f"\nℹ️ Nenhum PR coletado e {OUTPUT_CSV} não existe.")
else:
    # Se já existir um CSV, mescla atualizações para evitar sobrescrever PRs de execuções anteriores
    if os.path.exists(OUTPUT_CSV):
        try:
            df_existing = pd.read_csv(OUTPUT_CSV)
            combined = pd.concat([df_existing, df], ignore_index=True)
            # remove duplicatas mantendo a versão mais recente (última linha) para cada PR
            combined.drop_duplicates(subset=["repo", "pr_number"], keep="last", inplace=True)
            combined.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
            total_count = len(combined)
            print(f"\n✅ Dataset mesclado salvo como {OUTPUT_CSV} ({len(df)} PRs novos/atualizados, total {total_count}).")
        except Exception as e:
            # Em caso de erro ao mesclar, salva apenas os resultados atuais (evita perder o que foi coletado agora)
            df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
            print(f"\n⚠️ Erro ao mesclar com {OUTPUT_CSV}: {e}. Arquivo sobrescrito com os PRs desta execução ({len(df)} itens).")
    else:
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
        print(f"\n✅ Dataset salvo como {OUTPUT_CSV} ({len(df)} PRs).")

    print(f"Total de PRs coletados nesta execução: {len(df)}")
