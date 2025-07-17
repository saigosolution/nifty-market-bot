import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re

class MarketDataScraper:
    def __init__(self):
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_nifty_pe_data(self):
        """Scrape NIFTY 50 PE data from Trendlyne"""
        try:
            url = "https://trendlyne.com/equity/PE/NIFTY/1887/nifty-50-price-to-earning-ratios/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for NIFTY 50 price and PE ratio
            # This is a simplified approach - you might need to adjust selectors
            nifty_data = {
                'price': 'N/A',
                'pe_ratio': 'N/A',
                'status': 'Data extraction in progress...'
            }
            
            # Try to find price and PE data from the page
            # Note: Website structure may change, so this might need updates
            price_elements = soup.find_all(text=re.compile(r'[\d,]+\.\d+'))
            if price_elements:
                # Extract numerical values that look like prices/ratios
                for element in price_elements[:5]:  # Check first 5 matches
                    try:
                        clean_text = re.sub(r'[^\d.]', '', str(element))
                        if '.' in clean_text and len(clean_text) > 3:
                            if nifty_data['price'] == 'N/A':
                                nifty_data['price'] = clean_text
                            elif nifty_data['pe_ratio'] == 'N/A':
                                nifty_data['pe_ratio'] = clean_text
                                break
                    except:
                        continue
            
            return nifty_data
            
        except Exception as e:
            print(f"Error scraping NIFTY PE data: {e}")
            return {
                'price': 'Error',
                'pe_ratio': 'Error',
                'status': f'Failed to fetch data: {str(e)[:50]}...'
            }

    def scrape_mmi_data(self):
        """Scrape Market Mood Index from TickerTape"""
        try:
            url = "https://www.tickertape.in/market-mood-index"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for MMI value
            mmi_data = {
                'value': 'N/A',
                'status': 'N/A',
                'description': 'Market Mood Index data'
            }
            
            # Try to find MMI value
            # This is a simplified approach - you might need to adjust selectors
            mmi_elements = soup.find_all(text=re.compile(r'\d+'))
            if mmi_elements:
                for element in mmi_elements:
                    try:
                        value = int(re.sub(r'[^\d]', '', str(element)))
                        if 0 <= value <= 100:
                            mmi_data['value'] = value
                            mmi_data['status'] = self.get_mmi_status(value)
                            break
                    except:
                        continue
            
            return mmi_data
            
        except Exception as e:
            print(f"Error scraping MMI data: {e}")
            return {
                'value': 'Error',
                'status': 'Error',
                'description': f'Failed to fetch MMI: {str(e)[:50]}...'
            }

    def get_mmi_status(self, mmi_value):
        """Determine market status based on MMI value"""
        if isinstance(mmi_value, str) or mmi_value == 'N/A':
            return 'Unknown'
        
        if mmi_value >= 75:
            return 'Extreme Greed'
        elif mmi_value >= 60:
            return 'Greed'
        elif mmi_value >= 40:
            return 'Neutral'
        elif mmi_value >= 25:
            return 'Fear'
        else:
            return 'Extreme Fear'

    def generate_market_insights(self, nifty_data, mmi_data):
        """Generate market insights and recommendations"""
        insights = []
        
        # PE Ratio Analysis
        try:
            pe_ratio = float(nifty_data['pe_ratio']) if nifty_data['pe_ratio'] != 'N/A' else None
            if pe_ratio:
                if pe_ratio > 25:
                    insights.append("🔴 High PE Ratio - Market may be overvalued")
                elif pe_ratio > 20:
                    insights.append("🟡 Moderate PE Ratio - Fair valuation")
                else:
                    insights.append("🟢 Low PE Ratio - Potential undervaluation")
        except:
            insights.append("⚠️ PE Ratio analysis unavailable")
        
        # MMI Analysis
        mmi_status = mmi_data['status']
        if mmi_status == 'Extreme Greed':
            insights.append("🔴 Extreme Greed - Consider booking profits")
        elif mmi_status == 'Greed':
            insights.append("🟡 Greed - Be cautious, consider partial booking")
        elif mmi_status == 'Neutral':
            insights.append("🟢 Neutral sentiment - Good time for SIP")
        elif mmi_status == 'Fear':
            insights.append("🟢 Fear - Good buying opportunity")
        elif mmi_status == 'Extreme Fear':
            insights.append("🟢 Extreme Fear - Excellent buying opportunity")
        
        # Investment Recommendations
        recommendations = []
        
        if mmi_status in ['Fear', 'Extreme Fear']:
            recommendations.append("📈 **Equity**: High allocation recommended")
            recommendations.append("📊 **Debt**: Low allocation")
            recommendations.append("🎯 **Action**: BUY equities gradually")
        elif mmi_status == 'Neutral':
            recommendations.append("📈 **Equity**: Moderate allocation")
            recommendations.append("📊 **Debt**: Moderate allocation")
            recommendations.append("🎯 **Action**: Continue SIP")
        else:  # Greed or Extreme Greed
            recommendations.append("📈 **Equity**: Reduce allocation")
            recommendations.append("📊 **Debt**: Increase allocation")
            recommendations.append("🎯 **Action**: Book profits, avoid new purchases")
        
        return insights, recommendations

    def format_message(self, nifty_data, mmi_data):
        """Format the complete message for Telegram"""
        current_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
        
        insights, recommendations = self.generate_market_insights(nifty_data, mmi_data)
        
        message = f"""📊 **Daily Market Report**
📅 {current_time}

**NIFTY 50 Data:**
💰 Price: {nifty_data['price']}
📊 PE Ratio: {nifty_data['pe_ratio']}

**Market Mood Index:**
🎯 MMI Value: {mmi_data['value']}
🔮 Status: {mmi_data['status']}

**Market Insights:**
{chr(10).join(insights)}

**Investment Recommendations:**
{chr(10).join(recommendations)}

**Disclaimer:** This is automated analysis for educational purposes. Please consult financial advisor for investment decisions.
"""
        
        return message

    def send_telegram_message(self, message):
        """Send message to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            print("Message sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def run(self):
        """Main execution function"""
        print("Starting market data scraping...")
        
        # Scrape data
        nifty_data = self.scrape_nifty_pe_data()
        time.sleep(2)  # Be respectful to servers
        mmi_data = self.scrape_mmi_data()
        
        # Format and send message
        message = self.format_message(nifty_data, mmi_data)
        success = self.send_telegram_message(message)
        
        if success:
            print("Daily market report sent successfully!")
        else:
            print("Failed to send daily market report.")

if __name__ == "__main__":
    scraper = MarketDataScraper()
    scraper.run()
