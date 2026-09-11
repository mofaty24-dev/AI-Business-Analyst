import pandas as pd
from LLM import run_business_analyst_agent

if __name__ == "__main__":
    # 1. Load dataset
    dataset_path = "data.csv"
    df = pd.read_csv("D:\\HARD\\AI_Business_Analyst\\data.csv")

    # Initialize empty chat history
    chat_history = []

    # -------------------------------------------------------------
    # Question 1: Initial query about top products
    # -------------------------------------------------------------
    query_1 = "What are our top 3 best-selling products by sales?"
    print(f"User Question 1: {query_1}\n")

    insight_1, chat_history = run_business_analyst_agent(
        user_query=query_1, 
        df=df, 
        history=chat_history, 
        model="qwen2.5:3b"
    )

    print("=== AGENT RESPONSE 1 ===")
    print(insight_1)
    print("\n" + "="*50 + "\n")

    # -------------------------------------------------------------
    # Question 2: Follow-up query relying on chat history
    # -------------------------------------------------------------
    query_2 = "How many units were sold in total for the first product you mentioned?"
    print(f"User Question 2: {query_2}\n")

    insight_2, chat_history = run_business_analyst_agent(
        user_query=query_2, 
        df=df, 
        history=chat_history, 
        model="qwen2.5:3b"
    )

    print("=== AGENT RESPONSE 2 ===")
    print(insight_2)