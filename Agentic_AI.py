from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from Tools import TOOLS, tool_dispatcher

#Configure model client

load_dotenv()
client = OpenAI(
    base_url=os.getenv("OPENROUTER_ENDPOINT"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
model_name = "inclusionai/ling-3.0-flash-fin"

#make the system prompt

system_prompt = """
Role: You are a professional business analyst who has wide experience of handling analysis requests from customers.
Task: You take a company's recorded sales for the last couple of months then make any type of analysis the user asks for.
Constraints:
    - Your task is just to pick the right tool for the right situation. You never make calculations on your own.
    - You only calculate the following values (total revenue, top products, customer behavior, monthly sales,
      period comparison) using the provided tools for them.
    - Don't pick one tool in situations that need more than one tool. Don't pick many tools for one simple situation.
    - If a tool reports that no data has been uploaded yet, politely ask the user to upload a CSV — don't guess or apologize excessively.
    - If the available data cannot answer the specific question asked, say so clearly instead of guessing.
    - For plain greetings or general questions unrelated to data analysis, respond naturally without trying to call a tool.
Tone: Formal, polite, careful and nice.
Audience: Your customer is a start-up that needs a quick, reliable answer.
"""

#getting the tools from Tool.py file

tools = TOOLS

#main workflow of the agent giving the model the ability to make ReAct loop

def chat(message, history, df):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    response = client.chat.completions.create(model=model_name, messages=messages, tools=tools)

    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        responses = tool_call_router(message, df)
        messages.append(message)
        messages.extend(responses)
        response = client.chat.completions.create(model=model_name, messages=messages, tools=tools)

    return response.choices[0].message.content, messages

#finally handle configure tool call allocating and executing process

def tool_call_router(message, df):
    """
    Executes every tool call the model requested and returns one 'tool' role
    message per call, matching each call's tool_call_id.

    The 'no data yet' check lives HERE, not in respond()/GradioUI.py, so plain
    conversation (greetings, questions unrelated to data) always reaches
    the model. Only an actual attempt to call a tool without data produces
    a graceful error the model can explain to the user.
    """
    responses = []

    for tool in message.tool_calls:
        name = tool.function.name
        args = json.loads(tool.function.arguments)

        if df is None:
            result = {"error": "No data has been uploaded yet. Ask the user to upload a CSV before requesting analysis."}
        else:
            func = tool_dispatcher.get(name)
            if func is None:
                result = {"error": f"Unknown tool name: {name}"}
            else:
                try:
                    result = func(df, **args)
                except Exception as e:
                    # Safety net only — each tool already handles its own expected
                    # errors internally and returns {"error": ...} instead of raising.
                    result = {"error": f"Tool '{name}' failed unexpectedly: {e}"}

        responses.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool.id,
        })

    return responses

