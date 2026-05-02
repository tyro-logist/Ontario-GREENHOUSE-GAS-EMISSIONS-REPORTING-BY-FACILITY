"""
Ontario GHG Emissions by Facility — Full EDA
Using: pandas, matplotlib, seaborn, scikit-learn, scipy
Data: 2010-2020 Specified GHG Activities (2557 facility-year rows)
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

warnings.filterwarnings("ignore")

# ── paths ──────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(BASE, "GHG_Data_2010_2020_data_Dec162021.csv")
OUT  = os.path.join(BASE, "figures")
os.makedirs(OUT, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 120, "figure.figsize": (10, 5)})

# ── 1. LOAD & BASIC INFO ───────────────────────────────────────────────────────
print("=" * 70)
print("1. LOADING DATA")
print("=" * 70)

df = pd.read_csv(CSV, encoding="latin-1")
df.columns = df.columns.str.strip()

# Short column aliases
GHG_COLS = [
    "Carbon dioxide (CO2) from non-biomass in CO2e (t)",
    "Carbon dioxide (CO2) from biomass in CO2e (t)",
    "Methane (CH4) in CO2e (t)",
    "Nitrous oxide (N2O) in CO2e (t)",
    "Sulphur hexafluoride (SF6) in CO2e (t)",
    "Hydrofluorocarbons (HFCs) in CO2e (t)",
    "Perfluorocarbons (PFCs) in CO2e (t)",
    "Nitrogen Trifluoride (NF3) in CO2e (t)",
]
TOTAL_COL = "Total CO2e from all sources in CO2e (t)"

# Convert numeric columns
for c in GHG_COLS + [TOTAL_COL,
                     "Reporting Amount in CO2e (t)",
                     "Verification Amount in CO2e (t)"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Short display names for GHG gases
SHORT = {
    "Carbon dioxide (CO2) from non-biomass in CO2e (t)": "CO2 (fossil)",
    "Carbon dioxide (CO2) from biomass in CO2e (t)":     "CO2 (biomass)",
    "Methane (CH4) in CO2e (t)":                         "CH4",
    "Nitrous oxide (N2O) in CO2e (t)":                   "N2O",
    "Sulphur hexafluoride (SF6) in CO2e (t)":            "SF6",
    "Hydrofluorocarbons (HFCs) in CO2e (t)":             "HFCs",
    "Perfluorocarbons (PFCs) in CO2e (t)":               "PFCs",
    "Nitrogen Trifluoride (NF3) in CO2e (t)":            "NF3",
}

print(f"Shape : {df.shape}")
print(f"Years : {sorted(df['Year'].unique())}")
print(f"Unique facilities : {df['Ontario GHG ID'].nunique()}")
print(f"Unique owners     : {df['Facility Owner'].nunique()}")
print(f"Unique cities     : {df['Facility City'].nunique()}")

# ── 2. MISSING VALUES ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("2. MISSING VALUES")
print("=" * 70)

missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(1)
mv = pd.DataFrame({"missing": missing, "pct": missing_pct})
mv = mv[mv["missing"] > 0].sort_values("pct", ascending=False)
print(mv.to_string())

# ── 3. SUMMARY STATISTICS ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("3. SUMMARY STATISTICS  (Total CO2e, tonnes)")
print("=" * 70)

desc = df[TOTAL_COL].describe()
print(desc.apply(lambda x: f"{x:,.0f}"))
print(f"\nSkewness : {df[TOTAL_COL].skew():.2f}")
print(f"Kurtosis : {df[TOTAL_COL].kurt():.2f}")

# per-gas share
gas_totals = df[GHG_COLS].sum()
gas_pct    = (gas_totals / gas_totals.sum() * 100).rename(SHORT)
print("\nGas-mix (% of total CO2e across all years):")
print(gas_pct.sort_values(ascending=False).apply(lambda x: f"{x:.2f}%"))

# ── 4. TREND OVER TIME ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. ANNUAL TOTAL EMISSIONS (Mt CO2e)")
print("=" * 70)

annual = (df.groupby("Year")[TOTAL_COL].sum() / 1e6).rename("Mt CO2e")
print(annual.apply(lambda x: f"{x:.2f}"))

# regression
slope, intercept, r, p, se = stats.linregress(annual.index, annual.values)
print(f"\nLinear trend: slope={slope:.3f} Mt/yr, R²={r**2:.3f}, p={p:.4f}")

fig, ax = plt.subplots()
annual.plot(ax=ax, marker="o", color="steelblue", linewidth=2, label="Annual total")
x = np.array(annual.index)
ax.plot(x, intercept + slope * x, "--", color="tomato", label=f"Trend (slope={slope:.3f} Mt/yr)")
ax.set_title("Annual Total GHG Emissions (2010–2020)")
ax.set_ylabel("Mt CO2e")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}"))
ax.legend()
plt.tight_layout()
fig.savefig(os.path.join(OUT, "01_annual_trend.png"))
plt.close(fig)

# ── 5. TOP EMITTERS ───────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("5. TOP 10 FACILITIES (cumulative 2010-2020, Mt CO2e)")
print("=" * 70)

by_fac = (df.groupby(["Ontario GHG ID", "Facility Name", "Facility Owner"])[TOTAL_COL]
            .sum()
            .sort_values(ascending=False))
top10 = by_fac.head(10) / 1e6
print(top10.apply(lambda x: f"{x:.2f} Mt").to_string())

fig, ax = plt.subplots(figsize=(11, 5))
labels = [name for _, name, _ in top10.index]
ax.barh(labels[::-1], top10.values[::-1], color=sns.color_palette("Blues_r", 10))
ax.set_xlabel("Total CO2e (Mt, 2010–2020)")
ax.set_title("Top 10 Facilities by Cumulative GHG Emissions")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "02_top10_facilities.png"))
plt.close(fig)

# ── 6. TOP OWNERS ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("6. TOP 10 FACILITY OWNERS (cumulative Mt CO2e)")
print("=" * 70)

by_owner = (df.groupby("Facility Owner")[TOTAL_COL]
              .sum()
              .sort_values(ascending=False)
              .head(10) / 1e6)
print(by_owner.apply(lambda x: f"{x:.2f} Mt").to_string())

fig, ax = plt.subplots(figsize=(11, 5))
ax.barh(by_owner.index[::-1], by_owner.values[::-1],
        color=sns.color_palette("Oranges_r", 10))
ax.set_xlabel("Total CO2e (Mt, 2010–2020)")
ax.set_title("Top 10 Facility Owners by Cumulative GHG Emissions")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "03_top10_owners.png"))
plt.close(fig)

# ── 7. EMISSIONS BY CITY ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("7. TOP 10 CITIES (cumulative Mt CO2e)")
print("=" * 70)

by_city = (df.groupby("Facility City")[TOTAL_COL]
             .sum()
             .sort_values(ascending=False)
             .head(10) / 1e6)
print(by_city.apply(lambda x: f"{x:.2f} Mt").to_string())

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(by_city.index, by_city.values, color=sns.color_palette("Greens_r", 10))
ax.set_ylabel("Total CO2e (Mt, 2010–2020)")
ax.set_title("Top 10 Cities by Cumulative GHG Emissions")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "04_top10_cities.png"))
plt.close(fig)

# ── 8. NAICS SECTOR BREAKDOWN ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("8. TOP 10 PRIMARY NAICS CODES")
print("=" * 70)

# Map NAICS 6-digit codes to 2-digit sector descriptions (partial list)
NAICS_DESC = {
    "11": "Agriculture", "21": "Mining & Oil/Gas", "22": "Utilities",
    "23": "Construction", "31": "Food/Beverage/Textile Mfg",
    "32": "Paper/Chemical/Plastics Mfg", "33": "Metal/Machinery/Transport Mfg",
    "41": "Wholesale Trade", "44": "Retail Trade", "48": "Transportation",
    "49": "Warehousing", "51": "Information", "52": "Finance",
    "53": "Real Estate", "54": "Professional Services",
    "55": "Management", "56": "Admin/Waste Services",
    "61": "Educational Services", "62": "Health Care",
    "71": "Arts/Recreation", "72": "Accommodation/Food",
    "81": "Other Services", "91": "Public Administration",
}

df["NAICS2"] = df["Facility Primary NAICS Code"].astype(str).str[:2]
df["Sector"] = df["NAICS2"].map(NAICS_DESC).fillna("Other")

by_naics = (df.groupby(["Facility Primary NAICS Code", "Sector"])[TOTAL_COL]
              .sum()
              .sort_values(ascending=False)
              .head(10) / 1e6)
print(by_naics.apply(lambda x: f"{x:.2f} Mt").to_string())

by_sector = (df.groupby("Sector")[TOTAL_COL]
               .sum()
               .sort_values(ascending=False) / 1e6)
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(by_sector.index, by_sector.values,
       color=sns.color_palette("tab10", len(by_sector)))
ax.set_ylabel("Total CO2e (Mt, 2010–2020)")
ax.set_title("GHG Emissions by NAICS Sector (2010–2020)")
plt.xticks(rotation=40, ha="right")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "05_sector_emissions.png"))
plt.close(fig)

# ── 9. GAS COMPOSITION ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("9. GAS COMPOSITION")
print("=" * 70)

gas_yr = df.groupby("Year")[GHG_COLS].sum().rename(columns=SHORT)
print(gas_yr.map(lambda x: f"{x/1e6:.2f}").to_string())

fig, ax = plt.subplots(figsize=(11, 5))
gas_yr.plot(kind="bar", stacked=True, ax=ax, colormap="tab10")
ax.set_title("Annual GHG Emissions by Gas (Mt CO2e)")
ax.set_ylabel("Mt CO2e")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.0f}"))
ax.legend(loc="upper right", fontsize=8)
plt.xticks(rotation=0)
plt.tight_layout()
fig.savefig(os.path.join(OUT, "06_gas_composition.png"))
plt.close(fig)

# Pie chart of overall gas mix
fig, ax = plt.subplots(figsize=(7, 7))
gas_pie = gas_totals.rename(SHORT)
wedges, texts, autotexts = ax.pie(
    gas_pie.values, labels=gas_pie.index,
    autopct=lambda p: f"{p:.1f}%" if p > 0.5 else "",
    startangle=140, pctdistance=0.8,
    colors=sns.color_palette("tab10", len(gas_pie)),
)
ax.set_title("Overall Gas Mix (2010–2020)")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "07_gas_pie.png"))
plt.close(fig)

# ── 10. DISTRIBUTION / OUTLIERS ───────────────────────────────────────────────
print("\n" + "=" * 70)
print("10. OUTLIER ANALYSIS (Total CO2e per facility-year)")
print("=" * 70)

q1, q3 = df[TOTAL_COL].quantile([0.25, 0.75])
iqr = q3 - q1
outlier_thresh = q3 + 1.5 * iqr
outliers = df[df[TOTAL_COL] > outlier_thresh]
print(f"IQR fence (upper): {outlier_thresh:,.0f} t CO2e")
print(f"Outlier rows      : {len(outliers)} of {len(df)}")
print("\nTop outlier facility-years:")
print(outliers.nlargest(10, TOTAL_COL)[
    ["Year", "Facility Name", "Facility City", TOTAL_COL]
].to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
df[TOTAL_COL].plot(kind="hist", bins=60, ax=axes[0], color="steelblue",
                   edgecolor="white", logy=True)
axes[0].set_title("Distribution of Annual Facility Emissions (log scale)")
axes[0].set_xlabel("CO2e (t)")

df.boxplot(column=TOTAL_COL, by="Year", ax=axes[1], showfliers=False)
axes[1].set_title("Box Plot by Year (outliers hidden)")
axes[1].set_xlabel("Year")
axes[1].set_ylabel("CO2e (t)")
plt.suptitle("")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "08_distribution.png"))
plt.close(fig)

# ── 11. CORRELATION MATRIX ────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("11. CORRELATION MATRIX (GHG gas columns)")
print("=" * 70)

corr = df[GHG_COLS].rename(columns=SHORT).corr()
print(corr.map(lambda x: f"{x:.2f}").to_string())

fig, ax = plt.subplots(figsize=(8, 7))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, annot=True, fmt=".2f", mask=mask, ax=ax,
            cmap="RdYlGn", vmin=-1, vmax=1, linewidths=0.5)
ax.set_title("Correlation Matrix of GHG Gases")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "09_correlation.png"))
plt.close(fig)

# ── 12. VERIFICATION vs REPORTING GAP ─────────────────────────────────────────
print("\n" + "=" * 70)
print("12. REPORTING vs VERIFICATION AMOUNT")
print("=" * 70)

dv = df.dropna(subset=["Reporting Amount in CO2e (t)",
                        "Verification Amount in CO2e (t)"])
dv = dv[dv["Verification Amount in CO2e (t)"] > 0].copy()
dv["gap_pct"] = ((dv["Reporting Amount in CO2e (t)"] -
                  dv["Verification Amount in CO2e (t)"]) /
                 dv["Verification Amount in CO2e (t)"]) * 100
print(f"Records with verification: {len(dv)}")
print(f"Mean gap %  : {dv['gap_pct'].mean():.2f}%")
print(f"Median gap %: {dv['gap_pct'].median():.2f}%")
print(f"Max gap %   : {dv['gap_pct'].max():.2f}%")
print(f"Min gap %   : {dv['gap_pct'].min():.2f}%")

fig, ax = plt.subplots(figsize=(8, 4))
dv["gap_pct"].clip(-5, 5).plot(kind="hist", bins=50, ax=ax,
                                color="mediumpurple", edgecolor="white")
ax.axvline(0, color="red", linestyle="--")
ax.set_title("Reporting vs Verification Gap (clipped ±5%)")
ax.set_xlabel("Gap %  (positive = reported > verified)")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "10_verification_gap.png"))
plt.close(fig)

# ── 13. FACILITY COUNT TREND ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("13. REPORTING FACILITY COUNT PER YEAR")
print("=" * 70)

count_yr = df.groupby("Year")["Ontario GHG ID"].nunique()
print(count_yr.to_string())

fig, ax = plt.subplots(figsize=(8, 4))
count_yr.plot(ax=ax, marker="s", color="darkorange", linewidth=2)
ax.set_title("Number of Reporting Facilities per Year")
ax.set_ylabel("Facility count")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "11_facility_count.png"))
plt.close(fig)

# ── 14. PCA + K-MEANS CLUSTERING ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("14. PCA + K-MEANS CLUSTERING OF FACILITIES")
print("=" * 70)

# Aggregate per facility (mean across years they reported)
fac_agg = df.groupby("Ontario GHG ID")[GHG_COLS].mean().dropna()
scaler  = StandardScaler()
X_scaled = scaler.fit_transform(fac_agg)

pca = PCA(n_components=2, random_state=42)
pcs = pca.fit_transform(X_scaled)
print(f"Explained variance (PC1+PC2): "
      f"{pca.explained_variance_ratio_.sum()*100:.1f}%")

# Elbow method to choose k
inertias = []
K_range  = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].plot(list(K_range), inertias, marker="o", color="steelblue")
axes[0].set_title("K-Means Elbow Curve")
axes[0].set_xlabel("k (clusters)")
axes[0].set_ylabel("Inertia")

km_final = KMeans(n_clusters=4, random_state=42, n_init=10)
labels   = km_final.fit_predict(X_scaled)
sc = axes[1].scatter(pcs[:, 0], pcs[:, 1], c=labels,
                     cmap="tab10", alpha=0.6, s=25)
axes[1].set_title("PCA of Facilities (k=4 clusters)")
axes[1].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
axes[1].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
plt.colorbar(sc, ax=axes[1], label="Cluster")
plt.tight_layout()
fig.savefig(os.path.join(OUT, "12_pca_clusters.png"))
plt.close(fig)

# Cluster profiles
fac_agg["cluster"] = labels
cluster_profile = (fac_agg.groupby("cluster")[GHG_COLS]
                          .mean()
                          .rename(columns=SHORT))
print("\nCluster mean emissions (t CO2e):")
print(cluster_profile.map(lambda x: f"{x:,.0f}").to_string())

# ── 15. PER-FACILITY EMISSION INTENSITY CHANGE ────────────────────────────────
print("\n" + "=" * 70)
print("15. FACILITIES THAT IMPROVED vs WORSENED (2010 → most recent year)")
print("=" * 70)

first_last = (df.sort_values("Year")
                .groupby("Ontario GHG ID")
                .apply(lambda g: pd.Series({
                    "first_year": g["Year"].min(),
                    "last_year":  g["Year"].max(),
                    "first_co2e": g.loc[g["Year"].idxmin(), TOTAL_COL],
                    "last_co2e":  g.loc[g["Year"].idxmax(), TOTAL_COL],
                    "Facility Name": g["Facility Name"].iloc[0],
                }))
                .dropna())

# Keep facilities that reported in both 2010 and 2020 (or their last year)
fl = first_last[first_last["first_year"] == 2010].copy()
fl["change_pct"] = ((fl["last_co2e"] - fl["first_co2e"]) /
                    fl["first_co2e"] * 100)
fl = fl.replace([np.inf, -np.inf], np.nan).dropna(subset=["change_pct"])

improved  = fl[fl["change_pct"] < 0].sort_values("change_pct").head(10)
worsened  = fl[fl["change_pct"] > 0].sort_values("change_pct", ascending=False).head(10)
print("Most improved facilities (% reduction):")
print(improved[["Facility Name", "change_pct"]].to_string(index=False))
print("\nMost worsened facilities (% increase):")
print(worsened[["Facility Name", "change_pct"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(fl["change_pct"].clip(-100, 200), bins=40, color="teal", edgecolor="white")
ax.axvline(0, color="red", linestyle="--", label="No change")
ax.set_title("Distribution of % Change in Emissions per Facility (2010 → last year)")
ax.set_xlabel("% change in CO2e")
ax.legend()
plt.tight_layout()
fig.savefig(os.path.join(OUT, "13_facility_change.png"))
plt.close(fig)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print(f"Figures saved to: {OUT}")
print("=" * 70)
