# 🌍 GFM-Dashboard

**Global Franchise Map Dashboard**  
Built using Python, Dash, and SQL

## 🚀 Overview

An interactive dashboard visualizing franchise brand distribution across the globe. Explore global market presence and brand relationships with dynamic filters and rich visualizations.

## 🔧 Features

- **Auto Data Cleaning:** From Excel/CSV sources  
- **Interactive Dashboard:** Built with Dash + Plotly  
- **Multi-Dimensional Filters:** Country, Product Type, Brand Origin, Group Type  
- **Visualizations:**
  - Interactive Table (Sort & Filter)
  - Global Choropleth Map
  - Charts & Graphs
  - Network Graphs
  - Treemaps & Distribution Matrices  
- **Export Filtered Data** for external analysis

## 🗃️ Data Structure

Expected fields:

- `Brand Name`
- `Franchise Group`
- `Country`
- `Product Type` *(optional)*
- `Group Type` *(optional)*
- `Brand Origin` *(optional)*

> ℹ️ If "Brand Origin" is missing, ensure your file has a **"Brand country of Origin"** column.

## 💻 Requirements

- Python 3.6+
- Libraries: `pandas`, `sqlalchemy`, `dash`, `plotly`, `networkx`, `openpyxl`

## ▶️ Usage

1. Place your dataset in the same folder as `app1.py`
2. ```bash
   pip freeze -r requirements.txt  
3. Run the app:
   ```bash
   python app1.py
