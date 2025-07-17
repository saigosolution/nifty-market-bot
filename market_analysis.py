import os
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

def get_nifty_data():
    # Get Nifty 50 data using yfinance
    nifty = yf.Ticker("^NSEI")
    current_price = nifty.info['regularMarketPrice']
    
    # Get PE Ratio from NSE website
    nse_url = "https://www.nseindia.com/market-data/live-market-indices"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(nse_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        pe_ratio = soup.find('td', {'data-name': 'pe'}).text.strip()
    except:
        pe_ratio = "N/A"
    
    # Get VIX data
    vix = yf.Ticker("^INDIAVIX")
    vix_value = vix.info['regularMarketPrice']
    
    return current_price, pe_ratio, vix_value

def get_mmi_data():
    url = "https://www.tickertape.in/market-mood-index"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        mmi_value = soup.find('div', {'class': 'mmi-value'}).text.strip()
        return mmi_value
    except:
        return "N/A"

def analyze_market(nifty_price, pe_ratio, vix_value, mmi_value):
    analysis = []
    
    # VIX Analysis
    if vix_value > 20:
        analysis.append("🔴 High market volatility (VIX > 20). Exercise caution.")
    else:
        analysis.append("🟢 Market volatility is normal.")
    
    # PE Ratio Analysis
    try:
        pe_float = float(pe_ratio)
        if pe_float > 25:
            analysis.append("🔴 Market is expensive based on PE ratio.")
        elif pe_float < 15:
            analysis.append("🟢 Market is relatively cheap based on PE ratio.")
        else:
            analysis.append("🟡 Market valuation is neutral based on PE ratio.")
    except:
        analysis.append("⚪ PE ratio data unavailable.")
    
    # MMI Analysis
    try:
        mmi_float = float(mmi_value)
        if mmi_float > 70:
            analysis.append("🔴 Market is in Extreme Greed zone (MMI).")
        elif mmi_float < 30:
            analysis.append("🟢 Market is in Extreme Fear zone (MMI).")
        else:
            analysis.append("🟡 Market sentiment is neutral (MMI).")
    except:
        analysis.append("⚪ MMI data unavailable.")
    
    return "\n".join(analysis)

def get_investment_advice(pe_ratio, vix_value, mmi_value):
    try:
        pe_float = float(pe_ratio)
        mmi_float = float(mmi_value)
        
        if pe_float > 25 and mmi_float > 70:
            return "📊 Recommendation: Consider increasing allocation to debt/fixed income. Market showing signs of overvaluation."
        elif pe_float < 15 and mmi_float < 30:
            return "📊 Recommendation: Consider increasing equity allocation. Market showing signs of undervaluation."
        else:
            return "📊 Recommendation: Maintain balanced allocation between equity and debt as per your financial goals."
    except:
        return "📊 Recommendation: Insufficient data for investment advice. Stick to your asset allocation strategy."

def send_telegram_message(message):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def main():
    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Get market data
    nifty_price, pe_ratio, vix_value = get_nifty_data()
    mmi_value = get_mmi_data()
    
    # Analyze market conditions
    market_analysis = analyze_market(nifty_price, pe_ratio, vix_value, mmi_value)
    investment_advice = get_investment_advice(pe_ratio, vix_value, mmi_value)
    
    # Format message
    message = f"""🔔 <b>Daily Market Update</b> ({current_time})

📈 <b>Market Indicators:</b>
• Nifty 50: ₹{nifty_price:,.2f}
• PE Ratio: {pe_ratio}
• VIX: {vix_value:.2f}
• Market Mood Index: {mmi_value}

📊 <b>Market Analysis:</b>
{market_analysis}

{investment_advice}

🔍 <i>Note: This is automated analysis. Please consult financial advisor for personalized advice.</i>"""
    
    # Send message
    send_telegram_message(message)

if __name__ == "__main__":
    main() 
