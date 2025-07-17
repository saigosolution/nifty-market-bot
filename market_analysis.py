import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import traceback

def get_nifty_data():
    try:
        print("Fetching Nifty data from screener.in...")
        url = "https://www.screener.in/company/NIFTY/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching Nifty data. Status code: {response.status_code}")
            return None, None, None, None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract current price
        try:
            current_price = float(soup.select_one('.current-price').text.replace('₹', '').replace(',', '').strip())
            print(f"Current Price: {current_price}")
        except:
            current_price = None
            print("Failed to extract current price")
        
        # Extract P/E
        try:
            pe_ratio = float(soup.find('text', text='P/E').find_next('b').text.strip())
            print(f"P/E Ratio: {pe_ratio}")
        except:
            try:
                # Alternative way to find P/E
                ratios = soup.find_all('li', class_='flex flex-space-between')
                for ratio in ratios:
                    if 'P/E' in ratio.text:
                        pe_ratio = float(ratio.text.split('P/E')[-1].strip())
                        break
            except:
                pe_ratio = None
            print("Failed to extract P/E ratio")
        
        # Extract Price to Book value
        try:
            pb_ratio = float(soup.find('text', text='Price to Book value').find_next('b').text.strip())
            print(f"P/B Ratio: {pb_ratio}")
        except:
            try:
                # Alternative way to find P/B
                ratios = soup.find_all('li', class_='flex flex-space-between')
                for ratio in ratios:
                    if 'Price to Book value' in ratio.text:
                        pb_ratio = float(ratio.text.split('Price to Book value')[-1].strip())
                        break
            except:
                pb_ratio = None
            print("Failed to extract P/B ratio")
        
        return current_price, pe_ratio, pb_ratio
    except Exception as e:
        print(f"Error in get_nifty_data: {str(e)}")
        print(traceback.format_exc())
        return None, None, None

def get_mmi_data():
    try:
        print("Fetching MMI data...")
        url = "https://www.tickertape.in/market-mood-index"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
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

def analyze_market(current_price, pe_ratio, pb_ratio, mmi_value):
    analysis = []
    
    # P/E Analysis
    if pe_ratio:
        if pe_ratio > 25:
            analysis.append("🔴 Market is expensive based on P/E ratio (>25)")
        elif pe_ratio < 15:
            analysis.append("🟢 Market is relatively cheap based on P/E ratio (<15)")
        else:
            analysis.append("🟡 Market valuation is neutral based on P/E ratio (15-25)")
    else:
        analysis.append("⚪ P/E ratio data unavailable")
    
    # P/B Analysis
    if pb_ratio:
        if pb_ratio > 4:
            analysis.append("🔴 High Price to Book ratio (>4) indicates expensive valuations")
        elif pb_ratio < 2:
            analysis.append("🟢 Low Price to Book ratio (<2) indicates potential value")
        else:
            analysis.append("🟡 Price to Book ratio is in moderate range (2-4)")
    else:
        analysis.append("⚪ Price to Book ratio data unavailable")
    
    # MMI Analysis
    try:
        mmi_float = float(mmi_value)
        if mmi_float > 70:
            analysis.append("🔴 Market is in Extreme Greed zone (MMI > 70)")
        elif mmi_float < 30:
            analysis.append("🟢 Market is in Extreme Fear zone (MMI < 30)")
        else:
            analysis.append("🟡 Market sentiment is neutral (MMI between 30-70)")
    except:
        analysis.append("⚪ MMI data unavailable")
    
    return "\n".join(analysis)

def get_investment_advice(pe_ratio, pb_ratio, mmi_value):
    try:
        advice = []
        risk_score = 0  # 0 = neutral, positive = risky, negative = conservative
        
        # P/E based analysis
        if pe_ratio:
            if pe_ratio > 25:
                risk_score += 2
                advice.append("• High P/E ratio suggests market is expensive")
            elif pe_ratio < 15:
                risk_score -= 2
                advice.append("• Low P/E ratio indicates potential value opportunities")
        
        # P/B based analysis
        if pb_ratio:
            if pb_ratio > 4:
                risk_score += 1
                advice.append("• High P/B ratio indicates rich valuations")
            elif pb_ratio < 2:
                risk_score -= 1
                advice.append("• Low P/B ratio suggests possible undervaluation")
        
        # MMI based analysis
        try:
            mmi_float = float(mmi_value)
            if mmi_float > 70:
                risk_score += 2
                advice.append("• High market sentiment (greed) suggests caution")
            elif mmi_float < 30:
                risk_score -= 2
                advice.append("• Low market sentiment (fear) might present opportunities")
        except:
            pass
        
        # Final recommendation based on risk score
        if risk_score >= 2:
            advice.append("\n📊 Recommendation: Consider reducing equity exposure and increasing allocation to debt/fixed income.")
        elif risk_score <= -2:
            advice.append("\n📊 Recommendation: Consider increasing equity exposure as market valuations appear favorable.")
        else:
            advice.append("\n📊 Recommendation: Maintain balanced allocation between equity and debt as per your financial goals.")
        
        return "\n".join(advice)
    except:
        return "📊 Recommendation: Insufficient data for investment advice. Stick to your asset allocation strategy."

def send_telegram_message(message):
    try:
        print("Sending Telegram message...")
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError("Telegram bot token or chat ID not found in environment variables")
        
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
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f"Current time: {current_time}")
        
        # Get market data
        current_price, pe_ratio, pb_ratio = get_nifty_data()
        if current_price is None:
            raise Exception("Failed to fetch Nifty data")
            
        mmi_value = get_mmi_data()
        
        # Analyze market conditions
        market_analysis = analyze_market(current_price, pe_ratio, pb_ratio, mmi_value)
        investment_advice = get_investment_advice(pe_ratio, pb_ratio, mmi_value)
        
        # Format message
        message = f"""🔔 <b>Daily Market Update</b> ({current_time})

📈 <b>Market Indicators:</b>
• Nifty 50: ₹{current_price:,.2f if current_price else 'N/A'}
• P/E Ratio: {pe_ratio:.2f if pe_ratio else 'N/A'}
• Price to Book: {pb_ratio:.2f if pb_ratio else 'N/A'}
• Market Mood Index: {mmi_value}

📊 <b>Market Analysis:</b>
{market_analysis}

📈 <b>Investment Insights:</b>
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
