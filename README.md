# AI Business Analyst

## Project Name and Team Members
**AI Business Analyst** — Team 4, Final Team Project (AI & Automation Engineering)

- Mohamed Mahmoud Fathy — Built the agentic workflow from model chatting to handling tool calls in addition to Gradio UI and making charts
- Ahmed Yasser Amer — Built the five main tools the model will use while handling analysis request in addition to providing data for testing process

## Problem Statement
Small businesses and start-ups often have sales data sitting in spreadsheets but no easy way to interrogate it — answering a question like "how did last quarter perform?" usually means opening the file, filtering rows, and building a pivot table by hand. This project removes that friction: the user uploads a CSV of their sales data and asks questions about it in plain language. The application performs the actual calculations in Python (never trusting the LLM to do arithmetic) and uses an LLM to decide which analysis to run and to explain the result in a clear, natural-language answer.

## Application Features
- Upload a sales CSV directly through the Gradio interface.
- Ask free-form questions about the data in a chat interface, with conversation history preserved across turns.
- The assistant automatically selects and calls the right analysis tool(s) based on the question — including chaining more than one tool when a question needs it (e.g. comparing periods and then explaining which products drove the change).
- On-demand monthly revenue chart, shown only when requested via a dedicated button (not auto-generated on upload).
- On-demand period-comparison chart, comparing revenue between two user-chosen date ranges.
- Input validation on the uploaded CSV, with clear error messages instead of a crash.
- Graceful "I don't have enough information" behavior when a question can't be answered from the uploaded data or before any data has been uploaded.

## Technologies Used
- **Python** — core application logic
- **Pandas** — all data analysis and aggregation
- **Gradio** — user interface (file upload, chat, charts)
- **Matplotlib** — chart rendering
- **OpenAI Python SDK** — used as an OpenAI-compatible client (see note below)
- **python-dotenv** — environment variable management

## Model Used and How to Run It
This project originally targeted a locally-running **Ollama** model, as required by the brief. After evaluating the options, the team made a deliberate decision to substitute **OpenRouter**, using the free model `inclusionai/ling-3.0-flash-fin`, accessed through the same OpenAI-compatible `chat.completions` interface. This is a known deviation from the brief's requirement that Ollama be the core model, made for [reason — e.g. local hardware constraints / model quality]. See **Known Limitations** below.

To run the model integration:
1. Create an OpenRouter account and generate an API key.
2. Set the following environment variables in a `.env` file in the project root:
   ```
   OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1
   OPENROUTER_API_KEY=your_key_here
   ```
3. No local model download or Ollama installation is required with this configuration.

## Installation / Setup Instructions
1. Clone the repository:
   ```
   git clone https://github.com/mofaty24-dev/AI-Business-Analyst/tree/main
   cd main
   ```
2. Install dependencies:
   ```
   pip install gradio pandas matplotlib openai python-dotenv
   ```
3. Create a `.env` file as described above.
4. Ensure `data.csv` (or your own sales CSV) is available to upload through the interface — it does not need to be preloaded, only present when you want to test.
5. Run the application:
   ```
   python Gradio_UI.py
   ```
6. Open the local URL Gradio prints in the terminal.

## Application Architecture
```
User
  → Gradio_UI.py        (upload, chat interface, on-demand charts)
    → Agentic_AI.py      (chat loop, system prompt, tool-call routing)
      → OpenRouter model  (tool selection — never performs calculations itself)
        → Tools.py        (5 pandas-based analysis functions)
          → data.csv       (uploaded sales data, held in-memory as a DataFrame)
        ← tool result (JSON)
      ← final natural-language response
    ← chat reply + on-demand chart (Matplotlib, via Gradio_UI.py only)
```

Key design points:
- **Separation of concerns**: `Gradio_UI.py` owns the interface only; `Agentic_AI.py` owns the model/tool-calling loop; `Tools.py` owns all data analysis. No component does another's job.
- **Tools return data, never charts.** Charts are built independently in `Gradio_UI.py` from the same underlying data a tool would return, and are only rendered when the user explicitly requests them (not automatically on upload).
- **Per-session state**: the uploaded DataFrame is held in Gradio's session state, not a global variable, so one user's data never leaks into another session.
- **No LangChain or agent framework** — tool calling uses the OpenAI-compatible `tools=` parameter directly, with a simple `while` loop handling sequential (multi-step) tool calls.

## Tools
| Tool | What it does |
|---|---|
| `get_total_revenue(df, start_date, end_date)` | Calculates total revenue across the dataset, optionally filtered by date range. |
| `get_monthly_sales(df)` | Groups the data by month and returns revenue and order count per month. |
| `get_top_products(df, by, direction, limit)` | Returns the best- or worst-selling products by revenue or units sold. |
| `get_customer_statistics(df, customer_id)` | Returns customer behavior metrics — order count, total spend, and repeat-purchase rate — globally or for one customer. |
| `compare_periods(df, period1_start, period1_end, period2_start, period2_end)` | Compares revenue between two chosen date ranges and identifies the top products driving the change. |

The model selects which tool(s) to call based on the user's question; it never performs the underlying calculation itself.

## Example Multi-Tool Conversations
**Example 1 — Period comparison with root-cause explanation**
> User: "How did Q2 perform compared with Q1, and which products caused the change?"
> 1. Assistant calls `compare_periods` with the Q1 and Q2 date ranges.
> 2. Result includes overall revenue change plus top growth/decline contributors.
> 3. Assistant explains the change and highlights the specific products responsible, all from the tool's own output — no additional tool call needed since `compare_periods` already returns product-level drivers.

**Example 2 — Revenue check followed by customer behavior**
> User: "What was our total revenue last month, and are most of our customers repeat buyers?"
> 1. Assistant calls `get_total_revenue` filtered to last month.
> 2. Assistant calls `get_customer_statistics` (no `customer_id`, so it returns the aggregate repeat-purchase rate).
> 3. Assistant combines both results into a single natural-language answer.

## Explanation of the Advanced Topic
[This project's assigned advanced topic — AI-driven multi-step analysis (an automatic "Analyze My Business" report combining several analyses into one insight report) — was not implemented in this submission, by team decision, in favor of ensuring the core and intermediate requirements were solid. See Known Limitations.]

## Known Limitations
- **Model substitution**: uses an OpenRouter free model instead of a locally-hosted Ollama model, which is a deviation from the brief's stated requirement.
- **Advanced topic not implemented**: the assigned advanced feature (AI-driven multi-step analysis / automatic business report) was intentionally out of scope for this submission.
- Chart interpretation depends on the uploaded CSV having a `date` column plus either a `revenue` column or both `quantity` and `price` — datasets with substantially different structures may need column mapping adjustments.
- `get_customer_statistics` returns a different set of fields depending on whether a specific `customer_id` is requested versus an aggregate view.
- No automated test suite; validation has been manual.

## Future Improvements
- Add the option to run against a genuinely local Ollama model as a fallback/comparison to the current OpenRouter setup.
- Implement the assigned advanced topic (AI-driven multi-step business report).
- Expand chart options (e.g. top-products chart, customer-spend distribution).
- Add caching for repeated identical tool calls to reduce redundant computation on large datasets.
- Add a lightweight automated test suite covering each tool with edge-case CSVs (missing columns, empty file, malformed dates).
