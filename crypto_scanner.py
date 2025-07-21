# اسکنر حرفه‌ای ارز دیجیتال با تحلیل پیشرفته
import sys
import time
import json
import numpy as np
import pandas as pd
import requests
import ta
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config import (
    TELEGRAM_BOT_TOKEN, 
    TELEGRAM_CHAT_ID,
    COINGECKO_API_KEY,
    COINMARKETCAP_API_KEY
)

SETTINGS = {
    'min_volume': 1000000,
    'min_liquidity': 5000000,
    'max_volatility': 20,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'max_drawdown': 15,
    'min_market_cap': 10000000,
    'max_market_cap': 10000000000
}

@dataclass
class TokenAnalysis:
    symbol: str
    name: str
    price: float
    volume: float
    market_cap: float
    change_1h: float
    change_24h: float
    change_7d: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bollinger_band: Optional[float] = None
    volume_ma: Optional[float] = None
    score: float = 0
    risk_level: str = "متوسط"
    signals: List[str] = None
    factors: List[str] = None
    def __post_init__(self):
        self.signals = [] if self.signals is None else self.signals
        self.factors = [] if self.factors is None else self.factors

import csv
import os

class AdvancedCryptoScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        self.historical_data = {}
        self.last_analysis = {}
        self.alert_history = set()
        self.signal_log_file = 'signals_log.csv'
        self._load_alert_history()

    def _log_signal(self, symbol, name, score, reasons, timeframe, source):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_exists = os.path.isfile(self.signal_log_file)
        with open(self.signal_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["time", "symbol", "name", "score", "reasons", "timeframe", "source"])
            writer.writerow([now, symbol, name, score, reasons, timeframe, source])
        # Add to alert history
        self.alert_history.add((symbol, timeframe, source, now[:10]))

    def _load_alert_history(self):
        self.alert_history = set()
        if os.path.exists(self.signal_log_file):
            with open(self.signal_log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.alert_history.add((row['symbol'], row['timeframe'], row['source'], row['time'][:10]))

    def _should_alert(self, symbol, timeframe, source):
        today = datetime.now().strftime('%Y-%m-%d')
        return (symbol, timeframe, source, today) not in self.alert_history

    # آماده‌سازی ساختار برای چند تایم‌فریم و چند API (در توابع بعدی تکمیل می‌شود)

    def _make_api_request(self, url: str, params: dict = None, retries: int = 3) -> Optional[dict]:
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    print(f"⏳ محدودیت نرخ. صبر می‌کنم {wait_time} ثانیه...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ خطای API: کد {response.status_code}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ خطای اتصال: {e}")
                time.sleep(5)
                continue
        return None
    def fetch_real_crypto_data(self, limit: int = 100) -> List[Dict]:
        print("\n📡 در حال دریافت داده‌های ارزهای دیجیتال...")
        cg_data = self._fetch_coingecko_data(limit)
        cmc_data = []
        if COINMARKETCAP_API_KEY and COINMARKETCAP_API_KEY != 'YOUR_COINMARKETCAP_API_KEY':
            cmc_data = self._fetch_coinmarketcap_data(limit)
        all_tokens = {}
        if cg_data:
            for token in cg_data:
                all_tokens[token['symbol']] = token
        if cmc_data:
            for token in cmc_data:
                if token['symbol'] not in all_tokens:
                    all_tokens[token['symbol']] = token
        tokens = list(all_tokens.values())
        tokens.sort(key=lambda x: x.get('volume', 0), reverse=True)
        print(f"✅ داده‌های {len(tokens)} ارز با موفقیت دریافت شد.")
        return tokens
    def _fetch_coingecko_data(self, limit: int) -> List[Dict]:
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': min(limit, 250),
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '1h,24h,7d,14d,30d',
                'x_cg_pro_api_key': COINGECKO_API_KEY if COINGECKO_API_KEY != 'YOUR_COINGECKO_API_KEY' else ''
            }
            response = self.session.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                tokens = []
                for coin in data:
                    try:
                        tokens.append({
                            'symbol': coin['symbol'].upper(),
                            'name': coin['name'],
                            'price': coin['current_price'],
                            'volume': coin['total_volume'],
                            'market_cap': coin['market_cap'],
                            'rank': coin['market_cap_rank'],
                            'change_1h': coin.get('price_change_percentage_1h', 0) or 0,
                            'change_24h': coin.get('price_change_percentage_24h', 0) or 0,
                            'change_7d': coin.get('price_change_percentage_7d', 0) or 0,
                            'change_14d': coin.get('price_change_percentage_14d', 0) or 0,
                            'change_30d': coin.get('price_change_percentage_30d', 0) or 0,
                            'ath': coin.get('ath'),
                            'ath_change_percentage': coin.get('ath_change_percentage'),
                            'ath_date': coin.get('ath_date'),
                            'last_updated': coin.get('last_updated'),
                            'source': 'CoinGecko'
                        })
                    except (KeyError, TypeError) as e:
                        print(f"⚠️ خطا در پردازش داده‌های {coin.get('symbol', 'ناشناخته')}: {e}")
                        continue
                return tokens
            else:
                print(f"❌ خطا در دریافت داده از CoinGecko: کد {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ خطا در اتصال به CoinGecko: {e}")
            return []
    def _fetch_coinmarketcap_data(self, limit: int) -> List[Dict]:
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            headers = {
                'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
                'Accept': 'application/json'
            }
            params = {
                'start': 1,
                'limit': min(limit, 100),
                'convert': 'USD'
            }
            response = self.session.get(url, headers=headers, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                tokens = []
                for coin in data.get('data', []):
                    try:
                        quote = coin.get('quote', {}).get('USD', {})
                        tokens.append({
                            'symbol': coin['symbol'],
                            'name': coin['name'],
                            'price': quote.get('price'),
                            'volume': quote.get('volume_24h', 0),
                            'market_cap': quote.get('market_cap'),
                            'rank': coin.get('cmc_rank', 9999),
                            'change_1h': quote.get('percent_change_1h', 0),
                            'change_24h': quote.get('percent_change_24h', 0),
                            'change_7d': quote.get('percent_change_7d', 0),
                            'change_30d': quote.get('percent_change_30d', 0),
                            'ath': None,
                            'ath_change_percentage': None,
                            'ath_date': None,
                            'last_updated': quote.get('last_updated'),
                            'source': 'CoinMarketCap'
                        })
                    except (KeyError, TypeError) as e:
                        print(f"⚠️ خطا در پردازش داده‌های {coin.get('symbol', 'ناشناخته')}: {e}")
                        continue
                return tokens
            else:
                error_msg = response.json().get('status', {}).get('error_message', 'خطای ناشناخته')
                print(f"❌ خطا در دریافت داده از CoinMarketCap: کد {response.status_code} - {error_msg}")
                return []
        except Exception as e:
            print(f"❌ خطا در اتصال به CoinMarketCap: {e}")
            return []
    def fetch_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        if symbol in self.historical_data:
            return self.historical_data[symbol]
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily',
                'x_cg_pro_api_key': COINGECKO_API_KEY if COINGECKO_API_KEY != 'YOUR_COINGECKO_API_KEY' else ''
            }
            response = self.session.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if 'prices' in data and len(data['prices']) > 0:
                    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
                    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('date', inplace=True)
                    df['rsi'] = ta.momentum.RSIIndicator(df['price']).rsi()
                    macd = ta.trend.MACD(df['price'])
                    df['macd'] = macd.macd()
                    df['macd_signal'] = macd.macd_signal()
                    bollinger = ta.volatility.BollingerBands(df['price'])
                    df['bb_high'] = bollinger.bollinger_hband()
                    df['bb_mid'] = bollinger.bollinger_mavg()
                    df['bb_low'] = bollinger.bollinger_lband()
                    self.historical_data[symbol] = df
                    return df
            return None
        except Exception as e:
            print(f"❌ خطا در دریافت داده‌های تاریخی {symbol}: {e}")
            return None
    def analyze_token(self, token_data: Dict) -> Optional[TokenAnalysis]:
        try:
            token = TokenAnalysis(
                symbol=token_data['symbol'],
                name=token_data['name'],
                price=token_data['price'],
                volume=token_data['volume'],
                market_cap=token_data['market_cap'],
                change_1h=token_data['change_1h'],
                change_24h=token_data['change_24h'],
                change_7d=token_data['change_7d']
            )
            if not self._validate_token(token):
                return None
            self._calculate_technical_indicators(token)
            self._calculate_final_score(token)
            self._determine_risk_level(token)
            self.last_analysis[token.symbol] = token
            return token
        except Exception as e:
            print(f"⚠️ خطا در تحلیل توکن {token_data.get('symbol', 'ناشناخته')}: {e}")
            return None
    def _validate_token(self, token: TokenAnalysis) -> bool:
        if token.volume < SETTINGS['min_volume']:
            return False
        if token.market_cap < SETTINGS['min_market_cap']:
            return False
        if token.market_cap > SETTINGS['max_market_cap']:
            return False
        if abs(token.change_24h) > SETTINGS['max_volatility']:
            token.signals.append(f"⚠️ هشدار: نوسان بالا ({token.change_24h:.2f}%)")
        return True
    def _calculate_technical_indicators(self, token: TokenAnalysis):
        df = self.fetch_historical_data(token.symbol)
        if df is not None and not df.empty:
            if 'rsi' in df.columns:
                token.rsi = df['rsi'].iloc[-1]
                if token.rsi > SETTINGS['rsi_overbought']:
                    token.signals.append(f"اشباع خرید (RSI: {token.rsi:.1f})")
                elif token.rsi < SETTINGS['rsi_oversold']:
                    token.signals.append(f"اشباع فروش (RSI: {token.rsi:.1f})")
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                macd_line = df['macd'].iloc[-1]
                signal_line = df['macd_signal'].iloc[-1]
                if macd_line > signal_line and df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2]:
                    token.signals.append("تقاطع صعودی MACD")
                elif macd_line < signal_line and df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2]:
                    token.signals.append("تقاطع نزولی MACD")
            if 'bb_high' in df.columns and 'bb_low' in df.columns:
                current_price = token.price
                bb_high = df['bb_high'].iloc[-1]
                bb_low = df['bb_low'].iloc[-1]
                if current_price >= bb_high:
                    token.signals.append("نزدیک به باند بالایی بولینگر")
                elif current_price <= bb_low:
                    token.signals.append("نزدیک به باند پایینی بولینگر")
    def _calculate_final_score(self, token: TokenAnalysis):
        score = 0
        factors = []
        price_score = 0
        if token.change_1h > 5:
            price_score += 12
            factors.append("📈 رشد قوی 1 ساعته")
        elif token.change_1h > 2:
            price_score += 8
            factors.append("📈 رشد متوسط 1 ساعته")
        elif token.change_1h > 0:
            price_score += 3
        if token.change_24h > 15:
            price_score += 12
            factors.append("🚀 رشد انفجاری 24 ساعته")
        elif token.change_24h > 7:
            price_score += 8
            factors.append("📈 رشد قوی 24 ساعته")
        elif token.change_24h > 3:
            price_score += 4
            factors.append("📊 رشد متوسط 24 ساعته")
        if token.change_7d > 30:
            price_score += 6
            factors.append("🌟 روند صعودی قوی هفتگی")
        elif token.change_7d > 15:
            price_score += 4
            factors.append("📈 روند صعودی هفتگی")
        elif token.change_7d > 0:
            price_score += 2
        score += min(price_score, 30)
        liquidity_score = 0
        volume_to_mcap = (token.volume / token.market_cap) if token.market_cap > 0 else 0
        if volume_to_mcap > 0.5:
            liquidity_score += 15
            factors.append("💎 نقدینگی فوق‌العاده")
        elif volume_to_mcap > 0.2:
            liquidity_score += 10
            factors.append("💧 نقدینگی بالا")
        elif volume_to_mcap > 0.1:
            liquidity_score += 5
            factors.append("💦 نقدینگی مناسب")
        if token.volume > 1000000000:
            liquidity_score += 10
            factors.append("💰 حجم معاملات بسیار بالا")
        elif token.volume > 100000000:
            liquidity_score += 6
            factors.append("💵 حجم معاملات بالا")
        elif token.volume > 10000000:
            liquidity_score += 3
        score += min(liquidity_score, 25)
        ta_score = 0
        if token.rsi is not None:
            if token.rsi < 30:
                ta_score += 8
                factors.append("🟢 RSI در ناحیه اشباع فروش")
            elif token.rsi > 70:
                ta_score -= 5
                factors.append("🔴 RSI اشباع خرید")
        if token.macd is not None:
            if token.macd > 0:
                ta_score += 5
                factors.append("📊 MACD مثبت")
            else:
                ta_score -= 3
        score += min(ta_score, 25)
        risk_score = 0
        if token.change_24h < -SETTINGS['max_drawdown']:
            risk_score -= 10
            factors.append("⚠️ افت شدید قیمت")
        token.score = max(0, min(score + risk_score, 100))
        token.factors = factors
    def _determine_risk_level(self, token: TokenAnalysis):
        if token.score > 80:
            token.risk_level = "کم"
        elif token.score > 50:
            token.risk_level = "متوسط"
        else:
            token.risk_level = "زیاد"
    def find_best_coins(self, tokens: List[Dict], top_n: int = 5) -> List[TokenAnalysis]:
        analyzed = []
        for token_data in tokens:
            token = self.analyze_token(token_data)
            if token and token.score >= 40:
                analyzed.append(token)
        analyzed.sort(key=lambda t: t.score, reverse=True)
        return analyzed[:top_n]
    def send_telegram_alert(self, message: str):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("📣 پیام به تلگرام ارسال شد.")
            else:
                print(f"❌ خطا در ارسال پیام تلگرام: {response.status_code}")
        except Exception as e:
            print(f"❌ خطا در ارسال پیام تلگرام: {e}")
    def format_best_coins_message(self, best_coins: List[TokenAnalysis]) -> str:
        if not best_coins:
            return "هیچ ارز مناسبی یافت نشد."
        msg = "<b>🏆 بهترین ارزهای دیجیتال امروز:</b>\n\n"
        for i, t in enumerate(best_coins, 1):
            msg += f"<b>{i}. {t.name} ({t.symbol})</b>\n"
            msg += f"قیمت: <b>${t.price:,.2f}</b>\n"
            msg += f"امتیاز: <b>{t.score:.1f}/100</b> - ریسک: <b>{t.risk_level}</b>\n"
            msg += f"تغییر 1h: {t.change_1h:+.2f}% | 24h: {t.change_24h:+.2f}% | 7d: {t.change_7d:+.2f}%\n"
            if t.signals:
                msg += "سیگنال‌ها: " + ", ".join(t.signals) + "\n"
            if t.factors:
                msg += "دلایل: " + ", ".join(t.factors) + "\n"
            msg += "---\n"
        return msg

def main():
    print("🔥 شروع اسکن حرفه‌ای ارز دیجیتال...")
    try:
        print("📡 دریافت داده‌های بازار...")
        scanner = AdvancedCryptoScanner()
        tokens = scanner.fetch_real_crypto_data(limit=100)
        print(f"✅ {len(tokens)} ارز دریافت شد.")
        if not tokens:
            print("❌ هیچ داده‌ای دریافت نشد. لطفاً اینترنت و API را بررسی کنید.")
            return
        print("🧮 در حال تحلیل و امتیازدهی...")
        best_coins = scanner.find_best_coins(tokens, top_n=5)
        print(f"✅ تحلیل تمام شد. {len(best_coins)} ارز برتر پیدا شد.")
        msg = scanner.format_best_coins_message(best_coins)
        print("\n--- نتیجه نهایی ---\n")
        print(msg)
        print("\n-------------------\n")
        if best_coins:
            print("📤 ارسال سیگنال به تلگرام...")
            scanner.send_telegram_alert(msg)
            print("✅ سیگنال به تلگرام ارسال شد.")
        else:
            print("⚠️ هیچ ارز مناسبی برای سیگنال یافت نشد.")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    print("🔚 پایان اسکن.")

if __name__ == "__main__":
    main()


def fetch_real_crypto_data():
    """دریافت داده‌های واقعی از CoinGecko API - همه ارزهای مهم"""
    print("📡 در حال اتصال به CoinGecko API برای اسکن همه ارزها...")
    
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 100,  # تحلیل top 100 ارز
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '1h,24h,7d'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            tokens = []
            for coin in data:
                tokens.append({
                    "name": coin['name'],
                    "symbol": coin['symbol'].upper(),
                    "price": coin['current_price'],
                    "volume": coin['total_volume'],
                    "change_1h": coin.get('price_change_percentage_1h', 0) or 0,
                    "change_24h": coin.get('price_change_percentage_24h', 0) or 0,
                    "change_7d": coin.get('price_change_percentage_7d', 0) or 0,
                    "market_cap": coin['market_cap'],
                    "rank": coin['market_cap_rank'],
                    "volume_to_cap": (coin['total_volume'] / coin['market_cap']) * 100 if coin['market_cap'] else 0
                })
            print(f"✅ داده‌های {len(tokens)} ارز با موفقیت دریافت شد.")
            return tokens
        else:
            print(f"❌ خطا در دریافت داده: کد {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ خطای اتصال: لطفاً فیلترشکن فعال کنید.")
        return None
    except requests.exceptions.Timeout:
        print("❌ خطای timeout: سرور پاسخ نداد.")
        return None
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return None

def calculate_coin_score(token):
    """محاسبه امتیاز هوشمند برای هر ارز (از 100)"""
    score = 0
    factors = []
    
    # عامل 1: روند قیمت (35 امتیاز)
    if token['change_1h'] > 3:
        score += 15
        factors.append("momentum قوی 1ساعت")
    elif token['change_1h'] > 1:
        score += 8
        factors.append("momentum متوسط 1ساعت")
    elif token['change_1h'] > 0:
        score += 3
        
    if token['change_24h'] > 10:
        score += 15
        factors.append("رشد فوق‌العاده 24ساعت")
    elif token['change_24h'] > 5:
        score += 10
        factors.append("رشد قوی 24ساعت")
    elif token['change_24h'] > 2:
        score += 5
        factors.append("رشد متوسط 24ساعت")
    elif token['change_24h'] > 0:
        score += 2
        
    if token['change_7d'] > 20:
        score += 5
        factors.append("روند هفتگی عالی")
    elif token['change_7d'] > 0:
        score += 2
        
    # عامل 2: حجم و نقدینگی (25 امتیاز)
    if token['volume_to_cap'] > 30:
        score += 15
        factors.append("نقدینگی فوق‌العاده")
    elif token['volume_to_cap'] > 15:
        score += 10
        factors.append("نقدینگی عالی")
    elif token['volume_to_cap'] > 5:
        score += 5
        factors.append("نقدینگی خوب")
        
    if token['volume'] > 500000000:  # بیش از 500 میلیون
        score += 10
        factors.append("حجم معاملات بالا")
    elif token['volume'] > 100000000:  # بیش از 100 میلیون
        score += 5
        
    # عامل 3: رتبه و اعتبار (20 امتیاز)
    if token['rank'] <= 10:
        score += 20
        factors.append("ارز برتر")
    elif token['rank'] <= 30:
        score += 15
        factors.append("ارز معتبر")
    elif token['rank'] <= 50:
        score += 10
        factors.append("ارز شناخته‌شده")
    elif token['rank'] <= 100:
        score += 5
        
    # عامل 4: پتانسیل breakout (20 امتیاز)
    # momentum جدید (1ساعت بهتر از میانگین 24ساعت)
    if token['change_1h'] > token['change_24h'] / 24 * 3:
        score += 10
        factors.append("breakout جدید")
        
    # whale activity (حجم خیلی بالا)
    if token['volume'] > token['market_cap'] * 0.5:  # حجم بیش از 50% ارزش بازار
        score += 10
        factors.append("فعالیت نهنگ‌ها")
    elif token['volume'] > token['market_cap'] * 0.2:
        score += 5
        
    return min(score, 100), factors

def find_best_coins(tokens, top_n=5):
    """یافتن بهترین ارزها بر اساس امتیاز"""
    scored_coins = []
    
    for token in tokens:
        # فیلتر اولیه
        if token['volume'] < 1000000 or token['price'] <= 0:
            continue
            
        score, factors = calculate_coin_score(token)
        if score >= 30:  # حداقل امتیاز برای در نظر گیری
            scored_coins.append({
                'token': token,
                'score': score,
                'factors': factors
            })
    
    # مرتب‌سازی بر اساس امتیاز
    scored_coins.sort(key=lambda x: x['score'], reverse=True)
    return scored_coins[:top_n]

def send_telegram_alert(message):
    """ارسال هشدار به تلگرام"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ تنظیمات تلگرام ناقص است.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("📱 بهترین ارزها به تلگرام ارسال شد!")
            return True
        else:
            print(f"❌ خطا در ارسال تلگرام: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطا در ارسال تلگرام: {e}")
        return False

def format_best_coins_message(best_coins):
    """فرمت کردن پیام بهترین ارزها"""
    if not best_coins:
        return None
        
    message = f"🏆 <b>بهترین ارزهای دیجیتال</b>\n"
    message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    for i, coin_data in enumerate(best_coins, 1):
        token = coin_data['token']
        score = coin_data['score']
        factors = coin_data['factors']
        
        price_str = f"${token['price']:,.4f}" if token['price'] < 1 else f"${token['price']:,.2f}"
        
        # انتخاب emoji بر اساس امتیاز
        if score >= 80:
            emoji = "🔥"
        elif score >= 60:
            emoji = "⚡"
        else:
            emoji = "💎"
            
        message += f"{emoji} <b>{i}. {token['name']}</b> ({token['symbol']})\n"
        message += f"   💰 قیمت: {price_str}\n"
        message += f"   📊 امتیاز: {score}/100\n"
        message += f"   📈 تغییرات: 1س:{token['change_1h']:+.1f}% | 24س:{token['change_24h']:+.1f}% | 7روز:{token['change_7d']:+.1f}%\n"
        message += f"   💧 حجم: ${token['volume']:,.0f}\n"
        message += f"   🎯 دلایل: {', '.join(factors[:3])}\n\n"
    
    message += f"💡 <i>از {len(best_coins)} ارز برتر انتخاب شده</i>"
    return message

def main():
    print("\n🚦 شروع اسکن حرفه‌ای چند تایم‌فریم و چند منبع...")
    scanner = AdvancedCryptoScanner()
    timeframes = [
        ("1h", 1),
        ("4h", 4),
        ("1d", 24)
    ]
    sources = ["CoinGecko", "CoinMarketCap"]
    all_best_coins = []
    for tf_name, tf_hours in timeframes:
        print(f"\n⏱ تحلیل تایم‌فریم {tf_name}...")
        tokens = scanner.fetch_real_crypto_data(limit=100)
        best_coins = scanner.find_best_coins(tokens, top_n=5)
        for coin in best_coins:
            reasons = ", ".join(coin.signals or [])
            if scanner._should_alert(coin.symbol, tf_name, coin.__dict__.get('source', 'CoinGecko')):
                scanner._log_signal(coin.symbol, coin.name, coin.score, reasons, tf_name, coin.__dict__.get('source', 'CoinGecko'))
                print(f"✅ سیگنال جدید {coin.symbol} در {tf_name} ثبت شد!")
            else:
                print(f"⏳ سیگنال {coin.symbol} قبلاً در {tf_name} ثبت شده است.")
        all_best_coins.extend([(coin, tf_name) for coin in best_coins])
    # ساخت جدول HTML حرفه‌ای برای تلگرام
    def html_table(best_coins_with_tf):
        if not best_coins_with_tf:
            return "<b>هیچ سیگنال معتبری یافت نشد.</b>"
        table = "<b>🏆 جدول بهترین ارزها (تایم‌فریم):</b>\n<table border='1' cellpadding='4'>\n<tr><th>ردیف</th><th>نماد</th><th>نام</th><th>امتیاز</th><th>ریسک</th><th>1h</th><th>24h</th><th>7d</th><th>تایم‌فریم</th><th>دلایل</th></tr>"
        for i, (t, tf) in enumerate(best_coins_with_tf, 1):
            table += f"<tr><td>{i}</td><td>{t.symbol}</td><td>{t.name}</td><td>{t.score:.1f}</td><td>{t.risk_level}</td>"
            table += f"<td>{t.change_1h:+.2f}%</td><td>{t.change_24h:+.2f}%</td><td>{t.change_7d:+.2f}%</td><td>{tf}</td>"
            table += f"<td>{'، '.join(t.signals or [])}</td></tr>"
        table += "</table>"
        return table
    html_msg = html_table(all_best_coins)
    scanner.send_telegram_alert(html_msg)
    print("\n📊 گزارش حرفه‌ای به تلگرام ارسال شد.")
    print("\n🎯 پایان اسکن حرفه‌ای.")

    return signals_found

if __name__ == "__main__":
    try:
        print("🔥 اجرای اسکنر ارز دیجیتال با داده‌های واقعی...")
        print("📡 اتصال به CoinGecko API...\n")
        result = main()
        print(f"\n🎯 نتیجه نهایی: {'✅ سیگنال‌هایی پیدا شد!' if result else '⚪ هیچ سیگنال قوی‌ای پیدا نشد.'}")
        print("\n💡 نکته: برای داده‌های به‌روز، مجدداً اجرا کنید.")
    except KeyboardInterrupt:
        print("\n⏹️ اسکنر توسط کاربر متوقف شد.")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        print("💡 اگر خطای اتصال دیدید، فیلترشکن فعال کنید.")
        sys.exit(1)
