import requests
import pandas as pd
import time

# Configurações
GITHUB_TOKEN = ""
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

print("\n📥 Coletando Pull Requests detalhados...")

# Lê o CSV salvo na Etapa 1 e 2 (get_repos.py)
repos_filtrados = pd.read_csv("repositorios_filtrados.csv")

pulls_data = []

for repo in repos_filtrados["nome"]:
    print(f"\n➡️ Coletando PRs de {repo}...")
    page = 1

    while True:
        pr_url = f"https://api.github.com/repos/{repo}/pulls?state=all&per_page=100&page={page}"
        response = requests.get(pr_url, headers=HEADERS)

        if response.status_code != 200:
            print(f"⚠️ Erro ao buscar PRs de {repo}: {response.status_code}")
            break

        prs = response.json()
        if not prs:
            break

        for pr in prs:
            pulls_data.append({
                "repositorio": repo,
                "id": pr["id"],
                "numero": pr["number"],
                "titulo": pr["title"],
                "usuario": pr["user"]["login"] if pr.get("user") else None,
                "estado": pr["state"],
                "criado_em": pr["created_at"],
                "mergeado_em": pr.get("merged_at"),
                "fechado_em": pr.get("closed_at"),
                "commits_url": pr["commits_url"],
                "html_url": pr["html_url"]
            })

        page += 1
        time.sleep(1)

# Salvar resultado
pulls_df = pd.DataFrame(pulls_data)
pulls_df.to_csv("pull_requests.csv", index=False, encoding="utf-8")

print(f"\n✅ Dados dos PRs coletados e salvos em pull_requests.csv")
