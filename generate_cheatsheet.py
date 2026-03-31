#!/usr/bin/env python3
"""Generate a one-page Azure Databricks Data Engineering cheat sheet PDF."""

from pathlib import Path

from fpdf import FPDF

# ── Colours ──────────────────────────────────────────────────────────────
DARK = (30, 30, 30)
ACCENT = (0, 120, 212)       # Azure blue
BRONZE_C = (184, 115, 51)
SILVER_C = (170, 169, 173)
GOLD_C = (212, 175, 55)
WHITE = (255, 255, 255)
LIGHT_BG = (245, 247, 250)
BOX_BORDER = (200, 200, 200)
GREEN = (16, 124, 65)


class CheatSheet(FPDF):
    def header(self):
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.set_xy(6, 3)
        self.cell(0, 12, "Azure Databricks  |  Data Engineering Cheat Sheet", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 7)
        self.set_xy(6, 12)
        self.cell(0, 5, "One-page reference - key concepts with ready-to-say sentences & architecture overview")
        self.ln(10)

    def footer(self):
        self.set_y(-8)
        self.set_font("Helvetica", "I", 6)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, "Generated from azure-databricks-platform-demo", align="C")


pdf = CheatSheet("P", "mm", "A4")
pdf.set_auto_page_break(auto=False)
pdf.add_page()

# ── Helper: concept row ─────────────────────────────────────────────────
y_cursor = 22

def concept_block(title, sentence, bullet_color=ACCENT):
    global y_cursor
    x = 5
    w = 98
    pdf.set_xy(x, y_cursor)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*bullet_color)
    pdf.cell(3, 4, "*")  # bullet
    pdf.set_text_color(*DARK)
    pdf.cell(w - 3, 4, f"  {title}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(x + 4, y_cursor + 4)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(w - 4, 3.2, sentence)
    block_h = pdf.get_y() - y_cursor
    y_cursor += max(block_h + 1.5, 9)

def right_concept_block(title, sentence, bullet_color=ACCENT):
    global y_cursor_r
    x = 107
    w = 98
    pdf.set_xy(x, y_cursor_r)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*bullet_color)
    pdf.cell(3, 4, "*")
    pdf.set_text_color(*DARK)
    pdf.cell(w - 3, 4, f"  {title}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(x + 4, y_cursor_r + 4)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(w - 4, 3.2, sentence)
    block_h = pdf.get_y() - y_cursor_r
    y_cursor_r += max(block_h + 1.5, 9)


# ── LEFT COLUMN — Core Concepts ─────────────────────────────────────────
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*ACCENT)
pdf.set_xy(5, y_cursor)
pdf.cell(98, 5, "CORE DATA ENGINEERING CONCEPTS", ln=True)
y_cursor += 6

concepts = [
    ("Lakehouse Architecture",
     "A lakehouse combines the low-cost scalability of a data lake with the structured query and ACID guarantees of a data warehouse. It lets you store raw files cheaply while still running SQL analytics directly on them."),
    ("Medallion Architecture (Bronze / Silver / Gold)",
     "Data flows through three layers: Bronze stores raw ingested data as-is, Silver is cleaned and deduplicated, and Gold holds business-level aggregates ready for dashboards and reporting."),
    ("Delta Lake",
     "Delta Lake is an open-source storage layer that adds ACID transactions, schema enforcement, and time-travel to Parquet files. It is the default table format in Databricks."),
    ("Unity Catalog",
     "Unity Catalog provides centralized governance across all Databricks workspaces, managing permissions, data lineage, and audit logging from a single control plane."),
    ("Apache Spark (Distributed Compute)",
     "Spark is the distributed engine under Databricks that parallelizes data processing across a cluster. You write transformations in Python/SQL and Spark handles partitioning and execution."),
    ("ETL / ELT Pipelines",
     "ETL extracts data, transforms it, then loads it into a target. Modern cloud pipelines often use ELT: load raw data first, then transform in-place using Spark or SQL."),
    ("Auto Loader & Structured Streaming",
     "Auto Loader incrementally ingests new files as they land in cloud storage. Structured Streaming extends this to near-real-time, processing micro-batches continuously."),
    ("Delta Live Tables (DLT)",
     "DLT is a declarative ETL framework: you define what each table should look like and Databricks handles orchestration, retries, and data quality checks automatically."),
    ("Schema Evolution",
     "Schema evolution lets pipelines adapt when source data adds or changes columns, without breaking existing downstream tables or queries."),
    ("Data Quality / Expectations",
     "Expectations are constraints applied during transformation, e.g. 'temperature must be between -50 and 80'. Rows that fail can be dropped, flagged, or quarantined."),
]

for title, sentence in concepts:
    concept_block(title, sentence)

# ── RIGHT COLUMN — Azure / Terraform Resources ──────────────────────────
y_cursor_r = 22
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*ACCENT)
pdf.set_xy(107, y_cursor_r)
pdf.cell(98, 5, "KEY AZURE + TERRAFORM RESOURCES", ln=True)
y_cursor_r += 6

tf_concepts = [
    ("azurerm_databricks_workspace",
     "The workspace is the primary Databricks resource in Azure. It provisions the managed control plane, VNet injection, and the web UI endpoint."),
    ("azurerm_storage_account + containers",
     "ADLS Gen2 storage accounts host the data lake. Containers map to medallion layers (bronze, silver, gold) and are accessed via abfss:// URIs."),
    ("azurerm_databricks_access_connector",
     "A managed identity that lets Databricks authenticate to Azure storage without storing credentials. Required for Unity Catalog external locations."),
    ("databricks_catalog + schema",
     "The catalog is the top-level namespace in Unity Catalog. Schemas (databases) sit inside catalogs and contain tables, views, and volumes."),
    ("databricks_storage_credential + external_location",
     "Storage credentials link an Azure managed identity to Unity Catalog. External locations map specific ADLS paths so they can be governed by the catalog."),
    ("databricks_cluster + cluster_policy",
     "Clusters are the compute. Policies set guardrails (max nodes, allowed instance types, auto-termination) to control cost and compliance."),
    ("databricks_job",
     "Jobs orchestrate notebooks or tasks on a schedule or trigger. They support multi-task DAGs with retries and alerting."),
    ("azurerm_key_vault + secrets",
     "Key Vault stores sensitive values (tokens, connection strings). Databricks secret scopes can back onto Key Vault for secure access from notebooks."),
    ("azurerm_role_assignment",
     "RBAC bindings grant identities (e.g. the access connector) roles like Storage Blob Data Contributor on storage accounts."),
    ("databricks_grants",
     "Fine-grained Unity Catalog permissions: grant SELECT, USE CATALOG, CREATE TABLE etc. to users or groups on catalogs, schemas, and tables."),
]

for title, sentence in tf_concepts:
    right_concept_block(title, sentence)

# ── ARCHITECTURE DIAGRAM ────────────────────────────────────────────────
diag_y = max(y_cursor, y_cursor_r) + 2
pdf.set_draw_color(*BOX_BORDER)
pdf.set_line_width(0.3)
pdf.line(5, diag_y - 1, 205, diag_y - 1)

pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*ACCENT)
pdf.set_xy(5, diag_y)
pdf.cell(200, 5, "ARCHITECTURE OVERVIEW", ln=True)
diag_y += 6

def draw_box(x, y, w, h, label, fill_color, text_color=WHITE, sub=None):
    pdf.set_fill_color(*fill_color)
    pdf.set_draw_color(*fill_color)
    r = 2
    pdf.rect(x, y, w, h, "F")
    # rounded look via small circles at corners
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*text_color)
    tw = pdf.get_string_width(label)
    pdf.set_xy(x + (w - tw) / 2, y + 2)
    pdf.cell(tw, 4, label)
    if sub:
        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(*text_color)
        sw = pdf.get_string_width(sub)
        pdf.set_xy(x + (w - sw) / 2, y + 6.5)
        pdf.cell(sw, 3, sub)

def draw_arrow(x1, y, x2, color=DARK):
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.4)
    pdf.line(x1, y, x2, y)
    # arrowhead
    pdf.line(x2 - 2, y - 1.2, x2, y)
    pdf.line(x2 - 2, y + 1.2, x2, y)

# Row 1: Sources → Bronze → Silver → Gold → Consumers
box_h = 12
row_y = diag_y

draw_box(5, row_y, 28, box_h, "Data Sources", (100, 100, 100), WHITE, "IoT / APIs / Files")
draw_arrow(33, row_y + box_h / 2, 39)

draw_box(39, row_y, 30, box_h, "Bronze", BRONZE_C, WHITE, "Raw Ingestion")
draw_arrow(69, row_y + box_h / 2, 75)

draw_box(75, row_y, 30, box_h, "Silver", SILVER_C, DARK, "Clean & Validate")
draw_arrow(105, row_y + box_h / 2, 111)

draw_box(111, row_y, 30, box_h, "Gold", GOLD_C, DARK, "Aggregations")
draw_arrow(141, row_y + box_h / 2, 147)

draw_box(147, row_y, 28, box_h, "BI / Analytics", GREEN, WHITE, "Dashboards")

# Row 2: Infra layer
row2_y = row_y + box_h + 4
infra_w = 170
pdf.set_fill_color(235, 240, 250)
pdf.set_draw_color(*ACCENT)
pdf.set_line_width(0.3)
pdf.rect(5, row2_y, infra_w, 10, "DF")

items_row2 = [
    ("Databricks Workspace", 8),
    ("Unity Catalog", 52),
    ("ADLS Gen2 Storage", 92),
    ("Key Vault", 138),
]
pdf.set_font("Helvetica", "B", 6.5)
pdf.set_text_color(*ACCENT)
for label, xp in items_row2:
    pdf.set_xy(xp, row2_y + 1)
    pdf.cell(40, 4, label)

pdf.set_font("Helvetica", "", 5.5)
pdf.set_text_color(80, 80, 80)
sub_items = [
    ("Spark Clusters + Jobs", 8),
    ("Governance & Lineage", 52),
    ("bronze/ silver/ gold/", 92),
    ("Secrets & Tokens", 138),
]
for label, xp in sub_items:
    pdf.set_xy(xp, row2_y + 5)
    pdf.cell(40, 4, label)

# Terraform label
pdf.set_fill_color(*ACCENT)
pdf.rect(178, row2_y, 27, 10, "F")
pdf.set_font("Helvetica", "B", 6.5)
pdf.set_text_color(*WHITE)
pdf.set_xy(179, row2_y + 1)
pdf.cell(25, 4, "Provisioned by")
pdf.set_xy(179, row2_y + 5)
pdf.cell(25, 4, "Terraform")

# ── Save ─────────────────────────────────────────────────────────────────
out_path = Path(__file__).parent / "databricks_cheatsheet.pdf"
pdf.output(str(out_path))
print(f"PDF saved to {out_path}")
