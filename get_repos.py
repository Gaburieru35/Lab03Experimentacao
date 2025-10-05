import requests
import pandas as pd
from datetime import datetime
import time

# ================================
# CONFIGURAÇÕES
# ================================
TOKEN = "" 
HEADERS = {"Authorization": f"token {TOKEN}"}
LIMITE_REPOS = 200
LIMITE_PRS_POR_REPO = 100

# ================================
# ETAPA 1: BUSCAR REPOSITÓRIOS POPULARES
# ================================
print("\n🔍 Buscando repositórios populares com >=100 PRs...")

repositorios_validos = []
pagina = 1

while len(repositorios_validos) < LIMITE_REPOS:
    print(f"➡️  Página {pagina}...")
    url = f"https://api.github.com/search/repositories?q=stars:>1000&sort=stars&order=desc&per_page=100&page={pagina}"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()

    if "items" not in data:
        print("❌ Erro ao buscar repositórios:", data)
        break

    for item in data["items"]:
        repo_nome = item["full_name"]
        # Conta PRs fechados
        pr_url = f"https://api.github.com/search/issues?q=repo:{repo_nome}+type:pr+state:closed"
        pr_resp = requests.get(pr_url, headers=HEADERS)
        if pr_resp.status_code != 200:
            continue
        total_prs = pr_resp.json().get("total_count", 0)
        time.sleep(1)  # evita rate limit

        if total_prs >= 100:
            repositorios_validos.append({
                "nome": repo_nome,
                "url": item["html_url"],
                "estrelas": item["stargazers_count"],
                "forks": item["forks_count"],
                "linguagem": item.get("language"),
                "total_prs": total_prs
            })
            print(f"✅ {repo_nome} ({total_prs} PRs)")

        if len(repositorios_validos) >= LIMITE_REPOS:
            break

    if len(data["items"]) < 100:
        break  # acabou os resultados
    pagina += 1
    time.sleep(2)

# Salva repositórios filtrados
repos_df = pd.DataFrame(repositorios_validos)
repos_df.to_csv("repositorios_filtrados.csv", index=False, encoding="utf-8")
print(f"\n✅ {len(repos_df)} repositórios com >=100 PRs salvos em repositorios_filtrados.csv")