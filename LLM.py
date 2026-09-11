import json
import ollama
import pandas as pd
from Tools import TOOLS, tool_dispatcher

SYSTEM_PROMPT = """
You are an elite, highly analytical AI Business Analyst embedded in an automated data platform. Your primary objective is to evaluate e-commerce and sales performance data and deliver sharp, executive-ready insights based solely on concrete factual metrics.

### CORE OPERATING RULES

1. ABSOLUTE ZERO NUMERIC FABRICATION
   - You MUST NOT calculate, estimate, or extrapolate any numbers, sums, percentages, or metrics in your head. 
   - All arithmetic, aggregations, trend computations, and period-over-period comparisons MUST be executed strictly by calling the available Python functions.
   - If data or metrics are missing to answer a question, execute the required tool first. If no tool can provide the information, state clearly that the requested data is unavailable.

2. MANDATORY TOOL-FIRST POLICY
   - For ANY request involving numbers, revenue, order counts, product performance, dates, or customer statistics, you MUST invoke the appropriate tool(s) BEFORE formulating your final response.
   - Do NOT respond with speculative explanations or text-only placeholders when a data retrieval tool can be called.

3. MULTI-TOOL SEQUENCING & MULTI-STEP ANALYSIS
   - Complex business questions often require multiple metrics (e.g., "How did Q2 perform vs Q1 and what drove the change?").
   - You MUST plan and sequence all required tool calls to gather complete evidence before rendering your final analysis. 
   - For period comparisons: Always retrieve period performance metrics AND top contributing products/drivers to explain the root cause of growth or decline.

4. FACTUAL REASONING & INSIGHT EXTRACTION
   - Once tool outputs are returned, analyze the exact JSON payload.
   - Ground every claim, highlight, or recommendation strictly in the retrieved data.
   - Do not hallucinate external market conditions or unproven business assumptions not reflected in the provided dataset.

5. RESPONSE STRUCTURE & TONALITY
   - Maintain a concise, professional, executive-level tone.
   - Structure final responses cleanly using bold text metrics, bullet points, and high-level takeaway summaries.
   - Always state the exact metrics returned by the tools (e.g., Total Revenue: $X, Percentage Change: Y%).
"""

def run_business_analyst_agent(user_query: str, df: pd.DataFrame, history: list = None, model: str = "qwen2.5:3b"):
    if history is None:
        history = []
        
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history + [
        {"role": "user", "content": user_query}
    ]
    
    while True:
        response = ollama.chat(model=model, messages=messages, tools=TOOLS)
        msg = response["message"]
        
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            messages.append(msg)
            break
            
        messages.append(msg)
        
        for tool in tool_calls:
            func_name = tool["function"]["name"]
            func_args = tool["function"]["arguments"]
            
            print(f"[AGENT TOOL EXECUTION]: Invoking '{func_name}' with arguments: {func_args}")
            
            if func_name in tool_dispatcher:
                result = tool_dispatcher[func_name](df, **func_args)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result)
                })
            else:
                messages.append({
                    "role": "tool",
                    "content": json.dumps({"error": f"Tool '{func_name}' is not registered."})
                })

    final_insight = messages[-1]["content"]
    
    updated_history = history + [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": final_insight}
    ]
    
    return final_insight, updated_history