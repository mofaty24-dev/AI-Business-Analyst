import pandas as pd
import json

# ==============================================================================
# 1. DATA PREPROCESSING HELPER
# ==============================================================================

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans data, ensures required columns exist, converts types,
    and calculates revenue if missing.
    """
    if df.empty:
        raise ValueError("Uploaded DataFrame is completely empty.")
        
    data = df.copy()
    
    # 1. Map columns if dataset uses non-standard names (like E-Commerce dataset)
    column_mapping = {
        'InvoiceNo': 'order_id',
        'InvoiceDate': 'date',
        'Description': 'product',
        'CustomerID': 'customer',
        'Quantity': 'quantity',
        'UnitPrice': 'price',
        'Sale_Date': 'date',
        'Product_ID': 'product',
        'Sales_Amount': 'revenue'
    }
    data = data.rename(columns={k: v for k, v in column_mapping.items() if k in data.columns})
    
    # 2. Convert Date column
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        
    # 3. Calculate Revenue if missing
    if 'revenue' not in data.columns:
        if 'quantity' in data.columns and 'price' in data.columns:
            data['revenue'] = data['quantity'] * data['price']
        else:
            raise KeyError("Dataset must contain 'revenue' or both 'quantity' and 'price' columns.")
            
    return data

# ==============================================================================
# 2. THE 5 CORE BUSINESS ANALYST TOOLS
# ==============================================================================

def get_total_revenue(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> dict:
    """Calculates total revenue across the dataset, optionally filtered by date range."""
    try:
        data = prepare_dataframe(df)
        
        if start_date:
            data = data[data['date'] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data['date'] <= pd.to_datetime(end_date)]
            
        total_rev = round(float(data['revenue'].sum()), 2)
        order_count = int(data['order_id'].nunique()) if 'order_id' in data.columns else len(data)
        
        return {
            "total_revenue": total_rev,
            "order_count": order_count,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "error": None
        }
    except Exception as e:
        return {
            "total_revenue": 0.0,
            "order_count": 0,
            "start_date": start_date,
            "end_date": end_date,
            "error": str(e)
        }


def get_monthly_sales(df: pd.DataFrame) -> dict:
    """Groups dataset by month and returns total revenue and order counts per month."""
    try:
        data = prepare_dataframe(df)
        data['month'] = data['date'].dt.strftime('%Y-%m')
        
        agg_rules = {'revenue': 'sum'}
        if 'order_id' in data.columns:
            agg_rules['order_id'] = 'nunique'
            
        grouped = data.groupby('month').agg(agg_rules).reset_index()
        
        monthly_sales = {}
        for _, row in grouped.iterrows():
            m = str(row['month'])
            rev = round(float(row['revenue']), 2)
            orders = int(row['order_id']) if 'order_id' in row else len(data[data['month'] == m])
            monthly_sales[m] = {"revenue": rev, "orders": orders}
            
        return {
            "monthly_sales": monthly_sales,
            "error": None
        }
    except Exception as e:
        return {
            "monthly_sales": {},
            "error": str(e)
        }


def get_top_products(df: pd.DataFrame, by: str = "revenue", direction: str = "top", limit: int = 5) -> dict:
    """Returns top or bottom products ranked by revenue or units sold."""
    try:
        data = prepare_dataframe(df)
        
        metric_col = 'revenue' if by == 'revenue' else 'quantity'
        if metric_col not in data.columns:
            return {"by": by, "direction": direction, "limit": limit, "products": [], "error": f"Column '{metric_col}' not found."}
            
        is_ascending = True if direction.lower() == "bottom" else False
        
        agg_rules = {'revenue': 'sum'}
        if 'quantity' in data.columns:
            agg_rules['quantity'] = 'sum'
            
        grouped = data.groupby('product').agg(agg_rules).reset_index()
        sorted_df = grouped.sort_values(by=metric_col, ascending=is_ascending).head(limit)
        
        products_list = []
        for _, row in sorted_df.iterrows():
            products_list.append({
                "product": str(row['product']),
                "total_revenue": round(float(row['revenue']), 2),
                "units_sold": int(row['quantity']) if 'quantity' in row else None
            })
            
        return {
            "by": by,
            "direction": direction,
            "limit": limit,
            "products": products_list,
            "error": None
        }
    except Exception as e:
        return {
            "by": by,
            "direction": direction,
            "limit": limit,
            "products": [],
            "error": str(e)
        }


def get_customer_statistics(df: pd.DataFrame, customer_id: str = None) -> dict:
    """Calculates customer spend, order count, and repeat purchase rate globally or per customer ID."""
    try:
        data = prepare_dataframe(df)
        
        if customer_id:
            # Handle specific customer logic
            cust_data = data[data['customer'].astype(str) == str(customer_id)]
            if cust_data.empty:
                return {
                    "customer_id": customer_id,
                    "order_count": 0,
                    "total_spend": 0.0,
                    "repeat_purchase_rate": None,
                    "error": f"Customer ID '{customer_id}' not found."
                }
                
            orders = int(cust_data['order_id'].nunique()) if 'order_id' in cust_data.columns else len(cust_data)
            spend = round(float(cust_data['revenue'].sum()), 2)
            
            return {
                "customer_id": str(customer_id),
                "order_count": orders,
                "total_spend": spend,
                "repeat_purchase_rate": None,
                "error": None
            }
        else:
            # Handle overall dataset customer statistics
            agg_rules = {'revenue': 'sum'}
            if 'order_id' in data.columns:
                agg_rules['order_id'] = 'nunique'
                
            cust_grouped = data.groupby('customer').agg(agg_rules)
            total_customers = len(cust_grouped)
            
            orders_col = cust_grouped['order_id'] if 'order_id' in cust_grouped.columns else cust_grouped['revenue']
            repeat_customers = (orders_col > 1).sum()
            repeat_rate = round(float(repeat_customers / total_customers), 4) if total_customers > 0 else 0.0
            
            return {
                "customer_id": None,
                "total_unique_customers": total_customers,
                "total_spend": round(float(data['revenue'].sum()), 2),
                "repeat_purchase_rate": repeat_rate,
                "error": None
            }
    except Exception as e:
        return {
            "customer_id": customer_id,
            "order_count": 0,
            "total_spend": 0.0,
            "repeat_purchase_rate": 0.0,
            "error": str(e)
        }


def compare_periods(df: pd.DataFrame, period1_start: str, period1_end: str, period2_start: str, period2_end: str) -> dict:
    """Compares revenue between two date ranges and identifies top product drivers of change."""
    try:
        data = prepare_dataframe(df)
        
        p1 = data[(data['date'] >= pd.to_datetime(period1_start)) & (data['date'] <= pd.to_datetime(period1_end))]
        p2 = data[(data['date'] >= pd.to_datetime(period2_start)) & (data['date'] <= pd.to_datetime(period2_end))]
        
        p1_rev = round(float(p1['revenue'].sum()), 2)
        p2_rev = round(float(p2['revenue'].sum()), 2)
        
        abs_change = round(p2_rev - p1_rev, 2)
        pct_change = round((abs_change / p1_rev * 100), 2) if p1_rev != 0 else 0.0
        
        # Product impact analysis
        p1_prod = p1.groupby('product')['revenue'].sum()
        p2_prod = p2.groupby('product')['revenue'].sum()
        
        diff = (p2_prod.sub(p1_prod, fill_value=0)).reset_index()
        diff.columns = ['product', 'revenue_change']
        
        top_growth = diff.sort_values(by='revenue_change', ascending=False).head(3).to_dict('records')
        top_decline = diff.sort_values(by='revenue_change', ascending=True).head(3).to_dict('records')
        
        for item in top_growth + top_decline:
            item['revenue_change'] = round(float(item['revenue_change']), 2)

        return {
            "period1": {"start": period1_start, "end": period1_end, "revenue": p1_rev},
            "period2": {"start": period2_start, "end": period2_end, "revenue": p2_rev},
            "metrics": {
                "absolute_change": abs_change,
                "percentage_change": pct_change
            },
            "top_growth_contributors": top_growth,
            "top_decline_contributors": top_decline,
            "error": None
        }
    except Exception as e:
        return {
            "period1": {"start": period1_start, "end": period1_end, "revenue": 0.0},
            "period2": {"start": period2_start, "end": period2_end, "revenue": 0.0},
            "metrics": {"absolute_change": 0.0, "percentage_change": 0.0},
            "top_growth_contributors": [],
            "top_decline_contributors": [],
            "error": str(e)
        }

# ==============================================================================
# 3. OLLAMA TOOL SCHEMAS (OpenAI-compatible)
# ==============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_total_revenue",
            "description": "Calculates total sales revenue across the dataset, optionally filtered by start and end dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Filter start date in YYYY-MM-DD format."},
                    "end_date": {"type": "string", "description": "Filter end date in YYYY-MM-DD format."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_sales",
            "description": "Aggregates revenue and order count per month to analyze sales trends.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_products",
            "description": "Retrieves the highest or lowest selling products ranked by revenue or quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "by": {"type": "string", "enum": ["revenue", "quantity"], "description": "Metric to rank products by."},
                    "direction": {"type": "string", "enum": ["top", "bottom"], "description": "Whether to get top or bottom performers."},
                    "limit": {"type": "integer", "description": "Number of products to return (e.g. 5)."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_statistics",
            "description": "Calculates order count, spend, and repeat purchase rate globally or for a specific customer ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Optional customer ID to inspect."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_periods",
            "description": "Compares revenue between two date ranges and identifies top products causing the change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period1_start": {"type": "string", "description": "First period start date (YYYY-MM-DD)."},
                    "period1_end": {"type": "string", "description": "First period end date (YYYY-MM-DD)."},
                    "period2_start": {"type": "string", "description": "Second period start date (YYYY-MM-DD)."},
                    "period2_end": {"type": "string", "description": "Second period end date (YYYY-MM-DD)."}
                },
                "required": ["period1_start", "period1_end", "period2_start", "period2_end"]
            }
        }
    }
]

# ==============================================================================
# 4. TOOL DISPATCHER MAP
# ==============================================================================

tool_dispatcher = {
    "get_total_revenue": get_total_revenue,
    "get_monthly_sales": get_monthly_sales,
    "get_top_products": get_top_products,
    "get_customer_statistics": get_customer_statistics,
    "compare_periods": compare_periods
}