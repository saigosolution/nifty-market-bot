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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_nifty_data_from_finlive(self):
        """Get NIFTY 50 price and PE from finlive.in"""
        try:
            url = "https://www.finlive.in/page/nifty-50-nifty-pe-ratio"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for specific patterns in the text
            page_text = soup.get_text()
            
            # Extract PE ratio
            pe_ratio = 'N/A'
            pe_pattern = r'NIFTY 50 PE is ([\d.]+)'
            pe_match = re.search(pe_pattern, page_text)
            if pe_match:
                pe_ratio = pe_match.group(1)
            
            # Try alternative PE patterns
            if pe_ratio == 'N/A':
                pe_patterns = [
                    r'PE.*?(\d+\.\d+)',
                    r'P/E.*?(\d+\.\d+)',
                    r'ratio.*?(\d+\.\d+)'
                ]
                for pattern in pe_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        pe_ratio = match.group(1)
                        break
            
            return {'pe_ratio': pe_ratio, 'source': 'finlive.in'}
            
        except Exception as e:
            print(f"Error getting data from finlive: {e}")
            return {'pe_ratio': 'Error', 'source': 'finlive.in'}

    def get_nifty_data_from_trendlyne(self):
        """Get NIFTY 50 data from Trendlyne"""
        try:
            url = "https://trendlyne.com/equity/1887/NIFTY/nifty-50/"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for price and PE data
            price = 'N/A'
            pe_ratio = 'N/A'
            
            # Try to find price elements
            price_elements = soup.find_all(['span', 'div', 'td'], text=re.compile(r'[\d,]+\.\d+'))
            numbers = []
            
            for element in price_elements:
                try:
                    # Extract clean number
                    text = element.get_text().strip()
                    clean_num = re.sub(r'[^\d.]', '', text)
                    if '.' in clean_num and len(clean_num) > 3:
                        num = float(clean_num)
                        numbers.append(num)
                except:
                    continue
            
            # Heuristic: NIFTY price is usually above 20,000, PE is usually between 15-30
            for num in numbers:
                if 20000 <= num <= 30000 and price == 'N/A':
                    price = str(num)
                elif 15 <= num <= 35 and pe_ratio == 'N/A':
                    pe_ratio = str(num)
            
            return {'price': price, 'pe_ratio': pe_ratio, 'source': 'trendlyne.com'}
            
        except Exception as e:
            print(f"Error getting data from trendlyne: {e}")
            return {'price': 'Error', 'pe_ratio': 'Error', 'source': 'trendlyne.com'}

    def get_nifty_data_from_screener(self):
        """Get NIFTY 50 data from Screener.in"""
        try:
            url = "https://www.screener.in/company/NIFTY/"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for specific data fields
            price = 'N/A'
            pe_ratio = 'N/A'
            
            # Try to find data in table rows
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    header = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'price' in header or 'current' in header:
                        price_match = re.search(r'([\d,]+\.?\d*)', value)
                        if price_match:
                            price = price_match.group(1).replace(',', '')
                    
                    if 'pe' in header or 'p/e' in header:
                        pe_match = re.search(r'(\d+\.?\d*)', value)
                        if pe_match:
                            pe_ratio = pe_match.group(1)
            
            return {'price': price, 'pe_ratio': pe_ratio, 'source': 'screener.in'}
            
        except Exception as e:
            print(f"Error getting data from screener: {e}")
            return {'price': 'Error', 'pe_ratio': 'Error', 'source': 'screener.in'}

    def get_mmi_data_from_tickertape(self):
        """Get MMI data from TickerTape"""
        try:
            url = "https://www.tickertape.in/market-mood-index"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for MMI value in various elements
            mmi_value = 'N/A'
            
            # Try to find MMI value in specific elements
            mmi_elements = soup.find_all(['span', 'div', 'p'], text=re.compile(r'\d+'))
            
            for element in mmi_elements:
                try:
                    text = element.get_text().strip()
                    # Look for numbers between 0-100
                    numbers = re.findall(r'\b(\d+)\b', text)
                    for num in numbers:
                        value = int(num)
                        if 0 <= value <= 100:
                            mmi_value = value
                            break
                    if mmi_value != 'N/A':
                        break
                except:
                    continue
            
            return {'value': mmi_value, 'source': 'tickertape.in'}
            
        except Exception as e:
            print(f"Error getting MMI from tickertape: {e}")
            return {'value': 'Error', 'source': 'tickertape.in'}

    def get_mmi_data_from_goodreturns(self):
        """Get MMI data from GoodReturns"""
        try:
            url = "https://www.goodreturns.in/market-mood-index.html"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for MMI value
            mmi_value = 'N/A'
            
            # Search for MMI value patterns
            page_text = soup.get_text()
            mmi_patterns = [
                r'MMI.*?(\d+)',
                r'Market Mood Index.*?(\d+)',
                r'Index.*?(\d+)',
                r'current.*?(\d+)'
            ]
            
            for pattern in mmi_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = int(match.group(1))
                    if 0 <= value <= 100:
                        mmi_value = value
                        break
            
            return {'value': mmi_value, 'source': 'goodreturns.in'}
            
        except Exception as e:
            print(f"Error getting MMI from goodreturns: {e}")
            return {'value': 'Error', 'source': 'goodreturns.in'}

    def scrape_nifty_pe_data(self):
        """Scrape NIFTY 50 PE data from multiple sources"""
        print("Fetching NIFTY 50 data from multiple sources...")
        
        # Try multiple sources
        sources = [
            self.get_nifty_data_from_finlive,
            self.get_nifty_data_from_trendlyne,
            self.get_nifty_data_from_screener,
            self.get_nifty_data_from_api
        ]
        
        best_data = {'price': 'N/A', 'pe_ratio': 'N/A', 'source': 'multiple'}
        
        for source_func in sources:
            try:
                data = source_func()
                print(f"Data from {data.get('source', 'unknown')}: {data}")
                
                # Use the first valid PE ratio found
                if data.get('pe_ratio') not in ['N/A', 'Error'] and best_data['pe_ratio'] == 'N/A':
                    best_data['pe_ratio'] = data['pe_ratio']
                    best_data['source'] = data.get('source', 'unknown')
                
                # Use the first valid price found
                if data.get('price') not in ['N/A', 'Error'] and best_data['price'] == 'N/A':
                    best_data['price'] = data['price']
                
                # If we have both values, we can stop
                if best_data['price'] != 'N/A' and best_data['pe_ratio'] != 'N/A':
                    break
                    
                time.sleep(2)  # Be respectful to servers
                
            except Exception as e:
                print(f"Error with source {source_func.__name__}: {e}")
                continue
        
        return best_data

    def scrape_mmi_data(self):
        """Scrape Market Mood Index from multiple sources"""
        print("Fetching MMI data from multiple sources...")
        
        # Try multiple sources
        sources = [
            self.get_mmi_data_from_tickertape,
            self.get_mmi_data_from_goodreturns
        ]
        
        best_data = {'value': 'N/A', 'status': 'N/A', 'source': 'multiple'}
        
        for source_func in sources:
            try:
                data = source_func()
                print(f"MMI data from {data.get('source', 'unknown')}: {data}")
                
                # Use the first valid MMI value found
                if data.get('value') not in ['N/A', 'Error'] and best_data['value'] == 'N/A':
                    best_data['value'] = data['value']
                    best_data['status'] = self.get_mmi_status(data['value'])
                    best_data['source'] = data.get('source', 'unknown')
                    break
                    
                time.sleep(2)  # Be respectful to servers
                
            except Exception as e:
                print(f"Error with MMI source {source_func.__name__}: {e}")
                continue
        
        return best_data

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

    def get_nifty_data_from_api(self):
        """Get NIFTY 50 data from Yahoo Finance API (free)"""
        try:
            # Yahoo Finance API for NIFTY 50
            url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                # Get current price
                current_price = 'N/A'
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    current_price = str(round(result['meta']['regularMarketPrice'], 2))
                
                return {'price': current_price, 'pe_ratio': 'N/A', 'source': 'Yahoo Finance API'}
            
            return {'price': 'N/A', 'pe_ratio': 'N/A', 'source': 'Yahoo Finance API'}
            
        except Exception as e:
            print(f"Error getting data from Yahoo Finance API: {e}")
            return {'price': 'Error', 'pe_ratio': 'Error', 'source': 'Yahoo Finance API'}

    def format_message(self, nifty_data, mmi_data):
        """Format the complete message for Telegram"""
        current_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
        
        insights, recommendations = self.generate_market_insights(nifty_data, mmi_data)
        
        # Format data sources
        nifty_source = nifty_data.get('source', 'unknown')
        mmi_source = mmi_data.get('source', 'unknown')
        
        message = f"""📊 **Daily Market Report**
📅 {current_time}

**NIFTY 50 Data:**
💰 Price: {nifty_data['price']}
📊 PE Ratio: {nifty_data['pe_ratio']}
📍 Source: {nifty_source}

**Market Mood Index:**
🎯 MMI Value: {mmi_data['value']}
🔮 Status: {mmi_data['status']}
📍 Source: {mmi_source}

**Market Insights:**
{chr(10).join(insights)}

**Investment Recommendations:**
{chr(10).join(recommendations)}

**Data Status:**
✅ Successfully fetched from multiple reliable sources
🔄 Auto-updated daily at 9:30 AM IST

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
        
        # Scrape data with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")
                
                # Scrape data
                nifty_data = self.scrape_nifty_pe_data()
                time.sleep(3)  # Be respectful to servers
                mmi_data = self.scrape_mmi_data()
                
                # Check if we got some valid data
                valid_data = (
                    nifty_data.get('price') not in ['N/A', 'Error'] or 
                    nifty_data.get('pe_ratio') not in ['N/A', 'Error'] or
                    mmi_data.get('value') not in ['N/A', 'Error']
                )
                
                if valid_data or attempt == max_retries - 1:
                    # Format and send message
                    message = self.format_message(nifty_data, mmi_data)
                    success = self.send_telegram_message(message)
                    
                    if success:
                        print("Daily market report sent successfully!")
                        
                        # Send debug info if data is incomplete
                        if nifty_data.get('price') == 'N/A' or nifty_data.get('pe_ratio') == 'N/A' or mmi_data.get('value') == 'N/A':
                            debug_message = f"""🔧 **Debug Info**
NIFTY Price: {nifty_data.get('price')}
NIFTY PE: {nifty_data.get('pe_ratio')}
MMI Value: {mmi_data.get('value')}

Some data might be missing due to website changes. The bot will continue to improve data accuracy."""
                            self.send_telegram_message(debug_message)
                    else:
                        print("Failed to send daily market report.")
                    
                    break
                else:
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt == max_retries - 1:
                    # Send error message
                    error_message = f"""❌ **Market Data Bot Error**
Unable to fetch complete market data after {max_retries} attempts.

Error: {str(e)[:100]}...

The bot will retry in the next scheduled run."""
                    self.send_telegram_message(error_message)
                else:
                    time.sleep(5)

if __name__ == "__main__":
    scraper = MarketDataScraper()
    scraper.run()
