import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
from Agentic_AI import chat
from Tools import get_monthly_sales

#Making a chart which represents the monthly sales

def make_revenue_chart(df):
    """Build a matplotlib bar chart of monthly revenue. Only runs when the user asks for it."""
    if df is None:
        fig, ax = plt.subplots()
        ax.set_title("Upload a CSV first")
        return fig

    result = get_monthly_sales(df)

    if result.get("error"):
        fig, ax = plt.subplots()
        ax.set_title("Chart unavailable")
        return fig

    monthly = result["monthly_sales"]
    months = list(monthly.keys())
    revenues = [v["revenue"] for v in monthly.values()]

    fig, ax = plt.subplots()
    ax.bar(months, revenues)
    ax.set_title("Monthly Revenue")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    plt.xticks(rotation=45)
    fig.tight_layout()
    return fig

#loading the csv file which user will upload

def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.
    Returns (df, error) — df is None if loading fails.
    """
    try:
        df = pd.read_csv(file_path)
        return df, None
    except Exception as e:
        return None, f"Could not read CSV file: {e}"

#Making uploading process more reliable

def handle_upload(file):
    """Runs when the user uploads a CSV. Validates only — no chart is built here."""
    if file is None:
        return None, "No file uploaded."

    df, load_error = load_csv(file.name)
    if load_error:
        return None, load_error

    if df is None or df.empty:
        return None, "The uploaded file is empty."

    # Use get_monthly_sales as the validity check only — it runs tools.py's own
    # prepare_dataframe internally and reports a clear error if the data can't be used.
    # The chart itself is NOT built here anymore; it's only built when the user
    # explicitly asks for it via the "Show Monthly Revenue" button.
    check = get_monthly_sales(df)
    if check.get("error"):
        return None, f"Invalid CSV: {check['error']}"

    return df, f"Loaded {len(df)} rows successfully."

#Preparing the agent which the customer will communicate with

def respond(message, history, df):
    """
    Runs when the user sends a chat message. Always calls chat() — even with
    df=None — so plain conversation (e.g. a greeting) still gets a real reply.
    The 'no data uploaded' case is now handled inside tool_call_router, only
    when the model actually tries to run a tool that needs data.
    """
    reply, _ = chat(message, history, df)

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    return "", history

#reserving place for each previous function on the main UI

with gr.Blocks(title="AI Business Analyst") as demo:
    gr.Markdown("# AI Business Analyst\nUpload your sales data, then ask questions about it.")

    df_state = gr.State(None)

    with gr.Row():
        file_upload = gr.File(label="Upload sales CSV", file_types=[".csv"])
        upload_status = gr.Textbox(label="Status", interactive=False)

    revenue_button = gr.Button("Show Monthly Revenue")
    revenue_chart = gr.Plot(label="Monthly Revenue")

    chatbot = gr.Chatbot(label="Ask about your data")
    msg = gr.Textbox(label="Your question", placeholder="e.g. How did Q2 compare to Q1?")

    file_upload.upload(
        fn=handle_upload,
        inputs=file_upload,
        outputs=[df_state, upload_status],
    )

    revenue_button.click(
        fn=make_revenue_chart,
        inputs=df_state,
        outputs=revenue_chart,
    )

    msg.submit(
        fn=respond,
        inputs=[msg, chatbot, df_state],
        outputs=[msg, chatbot],
    )

#now let launch the magic

demo.launch()

