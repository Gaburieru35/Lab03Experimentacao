import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Carrega o dataset
df = pd.read_csv("repositorios_filtrados.csv")

# Mostra informações básicas
print("Resumo dos dados:")
print(df.describe())
print("\nLinguagens disponíveis:", df["linguagem"].unique())

# Correlação entre estrelas, forks e PRs
corr = df[["estrelas", "forks", "total_prs"]].corr(method="spearman")

plt.figure(figsize=(6, 4))
sns.heatmap(corr, annot=True, cmap="YlGnBu")
plt.title("Correlação (Spearman) entre estrelas, forks e PRs")
plt.tight_layout()
plt.savefig("heatmap_correlacoes.png", dpi=300)
plt.close()

# Gráfico de violino — distribuição de PRs por linguagem
plt.figure(figsize=(10, 6))
sns.violinplot(data=df, x="linguagem", y="total_prs", inner="quartile", palette="Set3")
plt.xticks(rotation=45)
plt.title("Distribuição do número total de PRs por linguagem")
plt.tight_layout()
plt.savefig("violino_prs_linguagem.png", dpi=300)
plt.close()

# Gráfico de dispersão — relação entre estrelas e PRs
plt.figure(figsize=(8, 6))
sns.scatterplot(data=df, x="estrelas", y="total_prs", hue="linguagem", alpha=0.7)
plt.title("Relação entre estrelas e número total de PRs")
plt.tight_layout()
plt.savefig("dispersao_estrelas_prs.png", dpi=300)
plt.close()

print(
    "Gráficos salvos: heatmap_correlacoes.png, violino_prs_linguagem.png, dispersao_estrelas_prs.png"
)
