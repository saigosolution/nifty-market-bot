import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re

def scrape_nifty_data():
    """Scrape NIFTY 50 data from screener.in"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = "https://www.screener.in/company/NIFTY/"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract current price
        price_element = soup.find('span', class_='number')
        current_price = price_element.text.strip() if price_element else "N/A"
        
        # Extract PE ratio
        pe_ratio = "N/A"
        ratios_section = soup.find('div', id='ratios')
        if ratios_section:
            pe_element = ratios_section.find('span', string=re.compile(r'PE'))
            if pe_element:
                pe_value = pe_element.find_next('span', class_='number')
                if pe_value:
                    pe_ratio = pe_value.text.strip()
        
        # Extract change percentage
        change_element = soup.find('span', class_='percentage')
        change_percent = change_element.text.strip() if change_element else "N/A"
        
        # Extract market cap
        market_cap = "N/A"
        market_cap_element = soup.find('span', string=re.compile(r'Market Cap'))
        if market_cap_element:
            market_cap_value = market_cap_element.find_next('span', class_='number')
            if market_cap_value:
                market_cap = market_cap_value.text.strip()
        
        return {
            'current_price': current_price,
            'pe_ratio': pe_ratio,
            'change_percent': change_percent,
            'market_cap': market_cap,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error scraping NIFTY data: {e}")
        return None

def scrape_mmi_data():
    """Scrape Market Mood Index from tickertape.in"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = "https://www.tickertape.in/market-mood-index"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract MMI value
        mmi_value = "N/A"
        mmi_status = "N/A"
        
        # Look for MMI value
        mmi_element = soup.find('div', class_='mmi-value') or soup.find('span', class_='mmi-number')
        if mmi_element:
            mmi_value = mmi_element.text.strip()
        
        # Look for MMI status
        status_element = soup.find('div', class_='mmi-status') or soup.find('span', class_='mmi-status')
        if status_element:
            mmi_status = status_element.text.strip()
        
        return {
            'mmi_value': mmi_value,
            'mmi_status': mmi_status,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error scraping MMI data: {e}")
        return None

def analyze_market_condition(nifty_data, mmi_data):
    """Analyze market condition and provide insights"""
    
    insights = {
        'market_condition': 'Neutral',
        'recommendation': 'Hold',
        'asset_allocation': 'Balanced (50% Equity, 50% Debt)',
        'reasoning': []
    }
    
    try:
        # Analyze NIFTY change
        if nifty_data and nifty_data['change_percent'] != 'N/A':
            change_str = nifty_data['change_percent'].replace('%', '').replace('+', '')
            change_float = float(change_str)
            
            if change_float > 1:
                insights['market_condition'] = 'Bullish'
                insights['recommendation'] = 'Buy'
                insights['asset_allocation'] = 'Equity Heavy (70% Equity, 30% Debt)'
                insights['reasoning'].append(f"NIFTY up {change_float}% - Strong positive momentum")
            elif change_float < -1:
                insights['market_condition'] = 'Bearish'
                insights['recommendation'] = 'Sell/Reduce'
                insights['asset_allocation'] = 'Debt Heavy (30% Equity, 70% Debt)'
                insights['reasoning'].append(f"NIFTY down {abs(change_float)}% - Negative momentum")
            else:
                insights['reasoning'].append(f"NIFTY change {change_float}% - Sideways movement")
        
        # Analyze PE ratio
        if nifty_data and nifty_data['pe_ratio'] != 'N/A':
            try:
                pe_value = float(nifty_data['pe_ratio'])
                if pe_value > 25:
                    insights['reasoning'].append("PE ratio high - Market might be overvalued")
                    if insights['recommendation'] == 'Buy':
                        insights['recommendation'] = 'Cautious Buy'
                elif pe_value < 15:
                    insights['reasoning'].append("PE ratio low - Market might be undervalued")
                    if insights['recommendation'] == 'Sell/Reduce':
                        insights['recommendation'] = 'Hold'
                else:
                    insights['reasoning'].append("PE ratio in normal range")
            except:
                pass
        
        # Analyze MMI
        if mmi_data and mmi_data['mmi_status'] != 'N/A':
            mmi_status = mmi_data['mmi_status'].lower()
            if 'extreme greed' in mmi_status or 'greed' in mmi_status:
                insights['reasoning'].append("MMI shows greed - Consider reducing exposure")
                if insights['recommendation'] == 'Buy':
                    insights['recommendation'] = 'Cautious Buy'
            elif 'extreme fear' in mmi_status or 'fear' in mmi_status:
                insights['reasoning'].append("MMI shows fear - Good buying opportunity")
                if insights['recommendation'] == 'Sell/Reduce':
                    insights['recommendation'] = 'Buy'
    
    except Exception as e:
        print(f"Error in market analysis: {e}")
        insights['reasoning'].append("Analysis incomplete due to data parsing issues")
    
    return insights

def format_message(nifty_data, mmi_data, insights):
    """Format the data into a nice Telegram message"""
    
    current_time = datetime.now().strftime('%d %B %Y, %I:%M %p')
    
    message = f"""🚀 **NIFTY Market Update**
📅 {current_time}

📊 **NIFTY 50 Data:**
💰 Current Price: {nifty_data['current_price'] if nifty_data else 'N/A'}
📈 Change: {nifty_data['change_percent'] if nifty_data else 'N/A'}
🏢 PE Ratio: {nifty_data['pe_ratio'] if nifty_data else 'N/A'}
💎 Market Cap: {nifty_data['market_cap'] if nifty_data else 'N/A'}

🌡️ **Market Mood Index:**
🎯 MMI Value: {mmi_data['mmi_value'] if mmi_data else 'N/A'}
😊 Status: {mmi_data['mmi_status'] if mmi_data else 'N/A'}

🔍 **Market Analysis:**
📊 Condition: {insights['market_condition']}
💡 Recommendation: {insights['recommendation']}
⚖️ Asset Allocation: {insights['asset_allocation']}

💭 **Key Insights:**"""

    for reason in insights['reasoning']:
        message += f"\n• {reason}"
    
    message += f"""

⚠️ **Disclaimer:** This is automated analysis for educational purposes only. Please consult a financial advisor for investment decisions.

#NIFTY #MarketUpdate #StockMarket"""
    
    return message

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("Error: Telegram credentials not found")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print("Message sent successfully!")
            return True
        else:
            print(f"Error sending message: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def main():
    """Main function to run the bot"""
    print("Starting NIFTY Market Bot...")
    
    # Scrape data
    print("Scraping NIFTY data...")
    nifty_data = scrape_nifty_data()
    
    print("Scraping MMI data...")
    mmi_data = scrape_mmi_data()
    
    # Analyze market
    print("Analyzing market condition...")
    insights = analyze_market_condition(nifty_data, mmi_data)
    
    # Format message
    print("Formatting message...")
    message = format_message(nifty_data, mmi_data, insights)
    
    # Send message
    print("Sending message...")
    success = send_telegram_message(message)
    
    if success:
        print("Bot completed successfully!")
    else:
        print("Bot completed with errors.")

if __name__ == "__main__":
    main()
