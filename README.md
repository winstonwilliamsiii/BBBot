# Bentley Bot: Fiscal Budget Dashboard

This is a Streamlit-based web application that:

- Ingests 36 months of personal and small-business income/expense data from Google Sheets.
- Syncs bank and billing transactions via QuickBooks API (or alternative financial aggregators).
- Stores and transforms data in MySQL (self-hosted or Silobase BaaS) using Airbyte.
- Orchestrates notifications and AI workflows with n8n.
- Presents an interactive dashboard with charts for spending categories (Shopping, Bank Fees, Miscellaneous, etc.) and upcoming-bill email alerts.
- Embeds a chatbot for macro-economic forecasts, US demographic comparisons, and global scenario analysis.

# Process Flow Image

![FBB_Process_Flow-FBB](https://github.com/user-attachments/assets/e2f6667d-1d81-4742-bf27-a479b2898fb9)
