# Bentley Bot: Fiscal Budget Dashboard

This is a Streamlit-based web application that:

- Ingests 36 months of personal and small-business income/expense data from Google Sheets.
- Syncs bank and billing transactions via QuickBooks API (or alternative financial aggregators).
- Stores and transforms data in MySQL (self-hosted or Appwrite BaaS) using Airbyte.
- Orchestrates notifications with Zapier and AI workflows with n8n.
- Presents an interactive dashboard with charts for spending categories (Shopping, Bank Fees, Miscellaneous, etc.) and upcoming-bill email alerts.
- Embeds a chatbot for macro-economic forecasts, US demographic comparisons, and global scenario analysis.

# Process Flow Image

https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D
<img width="460" height="373" alt="image" src="https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602" />
