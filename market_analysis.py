import os
import sys
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import traceback

def check_environment():
    """Check if required environment variables are set"""
    missing_vars = []
    for var in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def get_nifty_data():
    try:
        print("Fetching Nifty 50 data...")
        # Get Nifty 50 data using yfinance
        nifty = yf.Ticker("^NSEI")
        current_price = nifty.info['regularMarketPrice']
        print(f"Nifty 50 price: {current_price}")
        
        # Get PE Ratio from NSE website
        print("Fetching PE Ratio...")
        nse_url = "https://www.nseindia.com/market-data/live-market-indices"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        session = requests.Session()
        response = session.get(nse_url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching PE ratio. Status code: {response.status_code}")
            pe_ratio = "N/A"
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            pe_ratio = soup.find('td', {'data-name': 'pe'})
            pe_ratio = pe_ratio.text.strip() if pe_ratio else "N/A"
        print(f"PE Ratio: {pe_ratio}")
        
        # Get VIX data
        print("Fetching VIX data...")
        vix = yf.Ticker("^INDIAVIX")
        vix_value = vix.info['regularMarketPrice']
        print(f"VIX value: {vix_value}")
        
        return current_price, pe_ratio, vix_value
    except Exception as e:
        print(f"Error in get_nifty_data: {str(e)}")
        print(traceback.format_exc())
        return None, "N/A", None

def get_mmi_data():
    try:
        print("Fetching MMI data...")
        url = "https://www.tickertape.in/market-mood-index"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching MMI data. Status code: {response.status_code}")
            return "N/A"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        mmi_value = soup.find('div', {'class': 'mmi-value'})
        if mmi_value:
            mmi_value = mmi_value.text.strip()
            print(f"MMI value: {mmi_value}")
            return mmi_value
        else:
            print("MMI value not found in the page")
            return "N/A"
    except Exception as e:
        print(f"Error in get_mmi_data: {str(e)}")
        print(traceback.format_exc())
        return "N/A"

def analyze_market(nifty_price, pe_ratio, vix_value, mmi_value):
    analysis = []
    
    # VIX Analysis
    if vix_value and isinstance(vix_value, (int, float)) and vix_value > 20:
        analysis.append("🔴 High market volatility (VIX > 20). Exercise caution.")
    elif vix_value and isinstance(vix_value, (int, float)):
        analysis.append("🟢 Market volatility is normal.")
    else:
        analysis.append("⚪ VIX data unavailable.")
    
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
    try:
        print("Sending Telegram message...")
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Error sending message. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        print("Message sent successfully!")
        return response.json()
    except Exception as e:
        print(f"Error in send_telegram_message: {str(e)}")
        print(traceback.format_exc())
        return None

def main():
    try:
        # Check environment variables
        check_environment()
        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f"Current time: {current_time}")
        
        # Get market data
        nifty_price, pe_ratio, vix_value = get_nifty_data()
        if nifty_price is None:
            raise Exception("Failed to fetch Nifty data")
            
        mmi_value = get_mmi_data()
        
        # Analyze market conditions
        market_analysis = analyze_market(nifty_price, pe_ratio, vix_value, mmi_value)
        investment_advice = get_investment_advice(pe_ratio, vix_value, mmi_value)
        
        # Format message
        message = f"""🔔 <b>Daily Market Update</b> ({current_time})

📈 <b>Market Indicators:</b>
• Nifty 50: ₹{nifty_price:,.2f}
• PE Ratio: {pe_ratio}
• VIX: {vix_value:.2f if isinstance(vix_value, (int, float)) else 'N/A'}
• Market Mood Index: {mmi_value}

📊 <b>Market Analysis:</b>
{market_analysis}

{investment_advice}

🔍 <i>Note: This is automated analysis. Please consult financial advisor for personalized advice.</i>"""
        
        # Send message
        if not send_telegram_message(message):
            raise Exception("Failed to send Telegram message")
            
        print("Script completed successfully!")
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
