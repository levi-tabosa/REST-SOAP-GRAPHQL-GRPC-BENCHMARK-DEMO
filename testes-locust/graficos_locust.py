import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =====================================================================
# ARQUIVOS DE ENTRADA
# =====================================================================
CSV_FILES = [
    "rest-50.csv", "soap-50.csv", "graphql-50.csv", "grpc-50.csv",
    "rest-200.csv", "soap-200.csv", "graphql-200.csv", "grpc-200.csv",
    "rest-500.csv", "soap-500.csv", "graphql-500.csv", "grpc-500.csv",
]

TECH_LABEL = {
    "rest": "REST",
    "soap": "SOAP",
    "graphql": "GraphQL",
    "grpc": "gRPC",
}

# pasta do script
BASE_DIR = os.path.dirname(__file__)

# subpasta para salvar TUDO
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
print("Saída será salva em:", OUTPUT_DIR)


# =====================================================================
# FUNÇÃO PARA RESUMIR UM CSV DO LOCUST
# =====================================================================
def summarize_locust_csv(path, tech, users):
    df = pd.read_csv(path)

    # Se tiver linha "Aggregated", usa ela
    if "Name" in df.columns and (df["Name"] == "Aggregated").any():
        row = df[df["Name"] == "Aggregated"].iloc[0]

        col_avg = next(c for c in df.columns if "Average" in c and "Time" in c)
        col_rps = next(c for c in df.columns if "Requests/s" in c)
        col_fail = next(c for c in df.columns if "Failure" in c)

        return {
            "tech": TECH_LABEL.get(tech, tech),
            "users": users,
            "avg_ms": float(row[col_avg]),
            "p50_ms": float(row["50%"]),
            "p95_ms": float(row["95%"]),
            "p99_ms": float(row["99%"]),
            "rps": float(row[col_rps]),
            "failures": int(row[col_fail]),
        }

    # Senão, faz média ponderada
    col_req = next(c for c in df.columns if "Request Count" in c or "# Requests" in c)
    col_avg = next(c for c in df.columns if "Average" in c and "Time" in c)
    col_rps = next(c for c in df.columns if "Requests/s" in c)
    col_fail = next(c for c in df.columns if "Failure" in c)

    total_req = df[col_req].sum()

    return {
        "tech": TECH_LABEL.get(tech, tech),
        "users": users,
        "avg_ms": (df[col_avg] * df[col_req]).sum() / total_req,
        "p50_ms": (df["50%"] * df[col_req]).sum() / total_req,
        "p95_ms": (df["95%"] * df[col_req]).sum() / total_req,
        "p99_ms": (df["99%"] * df[col_req]).sum() / total_req,
        "rps": df[col_rps].sum(),
        "failures": int(df[col_fail].sum()),
    }


# =====================================================================
# CARREGAR TODOS OS CSV E MONTAR RESUMO
# =====================================================================
rows = []

for fname in CSV_FILES:
    path = os.path.join(BASE_DIR, fname)
    if not os.path.exists(path):
        print("[AVISO] Arquivo não encontrado:", fname)
        continue

    m = re.match(r"([a-zA-Z]+)-(\d+)\.csv", fname)
    if not m:
        print("[AVISO] Nome inesperado:", fname)
        continue

    tech = m.group(1).lower()
    users = int(m.group(2))
    rows.append(summarize_locust_csv(path, tech, users))

summary_df = pd.DataFrame(rows)
summary_df = summary_df.sort_values(["tech", "users"]).reset_index(drop=True)

print("\n==== RESUMO GERAL ====")
print(summary_df)
print()

# salva resumo em CSV
summary_df.to_csv(os.path.join(OUTPUT_DIR, "resumo_geral.csv"), index=False)
print("Resumo geral salvo em resumo_geral.csv")


# =====================================================================
# 1) GRÁFICOS INDIVIDUAIS POR TECNOLOGIA (50/200/500)
# =====================================================================
def plot_metric_per_tech(df, tech_label, metric_col, ylabel, filename):
    subset = df[df["tech"] == tech_label].sort_values("users")
    if subset.empty:
        print(f"[AVISO] Sem dados para {tech_label}")
        return

    x_users = subset["users"].values
    y_values = subset[metric_col].values

    plt.figure(figsize=(8, 5))
    plt.plot(x_users, y_values, marker="o")
    plt.xticks(x_users, [str(u) for u in x_users])
    plt.xlabel("Número de usuários")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} - {tech_label}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print("Gráfico salvo em:", output_path)


for tech_label in summary_df["tech"].unique():
    tech_key = tech_label.lower()

    plot_metric_per_tech(
        summary_df, tech_label,
        "avg_ms", "Latência média (ms)",
        f"{tech_key}_latencia_media.png"
    )
    plot_metric_per_tech(
        summary_df, tech_label,
        "p95_ms", "Latência p95 (ms)",
        f"{tech_key}_latencia_p95.png"
    )
    plot_metric_per_tech(
        summary_df, tech_label,
        "rps", "RPS",
        f"{tech_key}_rps.png"
    )


# =====================================================================
# 2) GRÁFICOS COMPARATIVOS (todas as tecnologias juntas)
#    → “os outros gráficos que comparam os 3”
# =====================================================================

# ordem bonitinha das tecnologias no eixo X
all_techs = ["REST", "SOAP", "GraphQL", "gRPC"]
# filtra só as que realmente existem no DF
techs_present = [t for t in all_techs if t in summary_df["tech"].unique()]

# cargas (50, 200, 500)
cargas = sorted(summary_df["users"].unique())


def plot_grouped_bar(metric_col, ylabel, title, filename):
    """
    Gera gráfico de barras agrupadas:
      - eixo X: tecnologias
      - barras: cada carga (50, 200, 500)
    """
    x = np.arange(len(techs_present))
    width = 0.2

    plt.figure(figsize=(10, 6))

    for i, carga in enumerate(cargas):
        subset = summary_df[summary_df["users"] == carga]
        # garante ordem das tecnologias
        subset = subset.set_index("tech").reindex(techs_present).reset_index()
        values = subset[metric_col].values

        plt.bar(x + i * width, values, width=width, label=f"{carga} usuários")

    plt.xticks(x + width, techs_present)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print("Gráfico comparativo salvo em:", output_path)


# gráfico comparando tecnologias x cargas para cada métrica
plot_grouped_bar(
    metric_col="avg_ms",
    ylabel="Latência média (ms)",
    title="Latência média por tecnologia e carga",
    filename="comparativo_latencia_media.png",
)

plot_grouped_bar(
    metric_col="p95_ms",
    ylabel="Latência p95 (ms)",
    title="Latência p95 por tecnologia e carga",
    filename="comparativo_latencia_p95.png",
)

plot_grouped_bar(
    metric_col="rps",
    ylabel="Requests por segundo (RPS)",
    title="RPS por tecnologia e carga",
    filename="comparativo_rps.png",
)

print("\n✅ Gráficos individuais + comparativos gerados em:", OUTPUT_DIR)
