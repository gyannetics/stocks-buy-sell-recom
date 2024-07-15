import yfinance as yf
import gradio as gr
from datetime import datetime, timedelta
from jinja2 import Template

def fetch_fundamental_data(ticker: str):
    stock = yf.Ticker(ticker)
    info = stock.info

    fundamentals = {
        "company": info.get("longName", "N/A"),
        "mkt_cap": info.get("marketCap", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "pb_ratio": info.get("priceToBook", "N/A"),
        "industry_pe": "N/A",  # This data is not available directly from yfinance
        "debt_to_equity": info.get("debtToEquity", "N/A"),
        "roe": info.get("returnOnEquity", "N/A"),
        "eps": info.get("trailingEps", "N/A"),
        "div_yield": info.get("dividendYield", "N/A"),
        "book_value": info.get("bookValue", "N/A"),
        "face_value": "N/A"  # This data is not available directly from yfinance
    }

    # Convert values to a more readable format if necessary
    if fundamentals["mkt_cap"] != "N/A":
        fundamentals["mkt_cap"] = f"{fundamentals['mkt_cap'] / 1e7:.2f} crore"
    if fundamentals["div_yield"] != "N/A":
        fundamentals["div_yield"] = f"{fundamentals['div_yield'] * 100:.2f}%"
    if fundamentals["roe"] != "N/A":
        fundamentals["roe"] = f"{fundamentals['roe'] * 100:.2f}%"
    if fundamentals["debt_to_equity"] != "N/A":
        fundamentals["debt_to_equity"] = f"{fundamentals['debt_to_equity']:.2f}"

    return fundamentals

def fetch_stock_data(ticker: str):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

def analyze_stock_trend(stock_data):
    if stock_data.empty:
        return "No data available for the given ticker."

    closing_prices = stock_data['Close']
    initial_price = closing_prices.iloc[0]
    final_price = closing_prices.iloc[-1]
    price_change = ((final_price - initial_price) / initial_price) * 100

    trend_analysis = f"The stock price has {'increased' if price_change > 0 else 'decreased'} by {abs(price_change):.2f}% over the last 6 months."

    return trend_analysis

def generate_recommendation(fundamentals, stock_trend: str) -> str:
    try:
        pe_ratio = float(fundamentals["pe_ratio"])
        roe = float(fundamentals["roe"].strip('%'))
        eps = float(fundamentals["eps"])
        debt_to_equity = float(fundamentals["debt_to_equity"])
        pb_ratio = float(fundamentals["pb_ratio"])
    except ValueError:
        return f"Cannot generate a recommendation due to incomplete data. {stock_trend}"
    
    if pe_ratio < 0 or eps < 0 or roe < 0:
        return f"Sell. {stock_trend}"
    elif pe_ratio < 20 and roe > 0 and debt_to_equity < 1 and pb_ratio < 1:
        return f"Buy. {stock_trend}"
    else:
        return f"Hold. {stock_trend}"

def load_template(template_path):
    with open(template_path) as file:
        template = Template(file.read())
    return template

def analyze_company(ticker: str):
    fundamentals = fetch_fundamental_data(ticker)
    stock_data = fetch_stock_data(ticker)
    stock_trend = analyze_stock_trend(stock_data)
    recommendation = generate_recommendation(fundamentals, stock_trend)
    
    template = load_template("templates/analysis_template.html")
    analysis = template.render(
        company=fundamentals['company'],
        fundamentals=fundamentals,
        stock_trend=stock_trend,
        recommendation=recommendation
    )
    
    return analysis

iface = gr.Interface(
    fn=analyze_company,
    inputs=[
        gr.inputs.Textbox(label="Stock Ticker Symbol")
    ],
    outputs="html",
    title="Company Fundamental Analysis",
    description="Enter the stock ticker symbol to get an analysis and recommendation."
)

if __name__ == "__main__":
    iface.launch()
