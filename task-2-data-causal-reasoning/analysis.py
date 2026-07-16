
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm


sns.set_theme(style="whitegrid", context="notebook", palette="muted")
pd.set_option("display.width", 200, "display.max_columns", 20)

TARGET = "Project Success"
FEATURES = [
    "Experience", "Team Size", "Requirements Changes", "Overtime",
    "Bugs", "Code Reviews (%)", "Customer Meetings", "Schedule Delay",
]

def banner(msg: str) -> None:
    print(f"\n{'=' * 70}\n{msg}\n{'=' * 70}")

def zscore(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return (frame[cols] - frame[cols].mean()) / frame[cols].std()

def load() -> pd.DataFrame:
    df = pd.read_csv("data/project_dataset.csv")
    return df

def eda(df: pd.DataFrame) -> None:
    def plot_distributions() -> None:
        fig, axes = plt.subplots(2, 4, figsize=(16, 7))
        for ax, col in zip(axes.ravel(), FEATURES):
            sns.histplot(data=df, x=col, hue=TARGET, ax=ax, bins=20,
                         palette={0: "#d95f5f", 1: "#4c9a6b"}, alpha=.55,
                         element="step", legend=(col == FEATURES[0]))
            ax.set_title(col, fontsize=10)
            ax.set_xlabel("")
        fig.suptitle("Distributions by outcome (red = failed, green = succeeded)", fontsize=13)
        fig.tight_layout()
        fig.savefig("figures/01_distributions.png", dpi=130)
        plt.close(fig)

    def plot_missingness() -> None:
        print("\n--- Missing values ---")
        miss = df.isna().sum()
        print(miss.to_string())

        print("\nMissingness vs Outcome:")
        for c in FEATURES:
            ind = df[c].isna().astype(int)
            tab = pd.crosstab(ind, df["Project Success"])
            chi2, p, _, _ = stats.chi2_contingency(tab)
            print(f"  {c:22s} p = {p:.3f}")

        fig, ax = plt.subplots(figsize=(9, 4))
        (miss[FEATURES] / len(df) * 100).plot.barh(ax=ax, color="#dd8452")
        ax.set_xlabel("% missing")
        ax.set_title("Missing values per column")
        fig.tight_layout()
        fig.savefig("figures/02_missingness.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    def plot_boxplots() -> None:
        z = zscore(df, FEATURES)
        fig, ax = plt.subplots(figsize=(11, 5))
        sns.boxplot(data=z.melt(var_name="variable", value_name="z"),
                    x="variable", y="z", ax=ax, fliersize=4, color="#7fa8c9")
        ax.axhline(0, color="grey", lw=.8)
        ax.set_title("Standardised values: the long tails are the planted outliers")
        ax.set_xlabel("")
        plt.xticks(rotation=30, ha="right")
        fig.tight_layout()
        fig.savefig("figures/03_outliers_boxplot.png", dpi=130)
        plt.close(fig)

    def plot_correlation() -> None:
        corr = df.corr(method="spearman")
        fig, ax = plt.subplots(figsize=(9, 7))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                    vmin=-1, vmax=1, square=True, ax=ax,
                    cbar_kws={"label": "Spearman ρ"})
        ax.set_title("Spearman correlation matrix (pairwise complete)")
        fig.tight_layout()
        fig.savefig("figures/04_correlation_heatmap.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    banner("EDA")

    print(f"Shape: {df.shape}")
    print(f"\noutcome balance:\n{df[TARGET].value_counts().rename('n')}")
    print(f"\nsummary:\n{df.describe().T.round(2)}")

    plot_distributions()
    plot_missingness()
    plot_boxplots()
    plot_correlation()

def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    # all outliers are in possible ranges, eye check

    banner("Data Cleaning")
    df_imp = df.copy()
    for c in FEATURES:
        df_imp[c] = df_imp[c].fillna(df[c].median())
    df_cc = df.dropna()
    print(f"\nComplete cases: {len(df_cc)} of {len(df)}")
    return df_cc

def hypothesis_tests(df: pd.DataFrame) -> None:
    def spearman(a, b):
        sub = df[[a, b]].dropna()
        rho, p = stats.spearmanr(sub[a], sub[b])
        return rho, p, len(sub)

    def h1_test():
        # H1: requirements changes -> schedule delay
        rho, p, n = spearman("Requirements Changes", "Schedule Delay")
        print(f"\nH1 Req. changes ↔ Schedule delay:   ρ = {rho:+.3f}, p = {p:.2e}, n = {n}")

        sns.regplot(data=df, x="Requirements Changes", y="Schedule Delay",
                    ax=axes[0][0], scatter_kws=dict(alpha=.4, s=18),
                    line_kws=dict(color="crimson"), lowess=True)
        axes[0][0].set_title(f"H1: Requirements changes vs delay (ρ={rho:.2f})")

    def h2_test():
        # H2: bugs -> failure
        sub = df[["Bugs", "Project Success"]].dropna()
        u, p2 = stats.mannwhitneyu(sub.loc[sub["Project Success"] == 1, "Bugs"],
                                   sub.loc[sub["Project Success"] == 0, "Bugs"])
        print(f"H2 Bugs (success vs failure):       "
              f"median {sub.loc[sub['Project Success'] == 1, 'Bugs'].median():.0f} vs "
              f"{sub.loc[sub['Project Success'] == 0, 'Bugs'].median():.0f}, "
              f"Mann-Whitney p = {p2:.2e}")

        sns.boxplot(data=df, x="Project Success", y="Bugs", ax=axes[0][1],
                    hue="Project Success", palette=["#c44e52", "#55a868"], legend=False)
        axes[0][1].set_title("H2: Bugs by project outcome")
        axes[0][1].set_xticks([0, 1], ["Failure", "Success"])

    def h3_test():
        # H4: delay -> overtime
        rho, p, n = spearman("Overtime", "Bugs")
        print(f"H3 Overtime ↔ Bugs: ρ = {rho:+.3f}, p = {p:.2e}")

        sns.regplot(data=df, x="Overtime", y="Bugs", ax=axes[1][0],
                    scatter_kws=dict(alpha=.4, s=18), line_kws=dict(color="crimson"))
        axes[1][0].set_title(f"H3: Overtime vs Bugs (ρ={rho:.2f})")

    def h4_test():
        # H5: customer meetings -> failure
        rho5, p5, n5 = spearman("Customer Meetings", "Project Success")
        print(f"H4 Customer meetings ↔ Success: ρ = {rho5:+.3f}, p = {p5:.2e}")

        sns.boxplot(data=df, x="Project Success", y="Customer Meetings", ax=axes[1][1],
                    hue="Project Success", palette=["#c44e52", "#55a868"], legend=False)
        axes[1][1].set_title(f"H4: Customer meetings by outcome (ρ={rho5:.2f})")
        axes[1][1].set_xticks([0, 1], ["Failure", "Success"])


    banner("Hypothesis Tests")

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    h1_test()
    h2_test()
    h3_test()
    h4_test()

    fig.tight_layout()
    fig.savefig("figures/05_hypotheses.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

def multivariate_model(df: pd.DataFrame):
    banner("Multivariate Model")
    X = df[FEATURES].copy()
    X = (X - X.mean()) / X.std()
    X = sm.add_constant(X)
    y = df[TARGET]
    model = sm.Logit(y, X).fit(disp=0)
    print(model.summary2().tables[1].round(3).to_string())

    orr = pd.DataFrame({
        "OR": np.exp(model.params),
        "lo": np.exp(model.conf_int()[0]),
        "hi": np.exp(model.conf_int()[1]),
    }).drop("const")

    fig, ax = plt.subplots(figsize=(8, 5))
    order = orr["OR"].sort_values().index
    ax.errorbar(orr.loc[order, "OR"], range(len(order)),
                xerr=[orr.loc[order, "OR"] - orr.loc[order, "lo"],
                      orr.loc[order, "hi"] - orr.loc[order, "OR"]],
                fmt="o", color="#4c72b0", capsize=4)
    ax.axvline(1, color="grey", ls="--")
    ax.set_yticks(range(len(order)), order)
    ax.set_xscale("log")
    ax.set_xlabel("Odds ratio per 1 SD (log scale, 95% CI)")
    ax.set_title("Logistic regression: adjusted association with project success")
    fig.tight_layout()
    fig.savefig("figures/06_logit_odds_ratios.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

def main():
    raw = load()
    eda(raw)
    cleaned = data_cleaning(raw)
    hypothesis_tests(cleaned)
    multivariate_model(cleaned)

if __name__ == "__main__":
    main()
