"""
ماژول multi_api.py
تجمیع داده و سیگنال از چندین API: CoinGecko, Ethereum, BSC, CoinMarketCap
"""
import requests
from typing import List, Dict, Optional

class MultiAPIScanner:
    def __init__(self, coingecko_key: Optional[str]=None, cmc_key: Optional[str]=None, eth_key: Optional[str]=None, bsc_key: Optional[str]=None):
        self.coingecko_key = coingecko_key
        self.cmc_key = cmc_key
        self.eth_key = eth_key
        self.bsc_key = bsc_key

    def fetch_coingecko(self, symbol: str) -> Dict:
        import time
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
        tries = 3
        for attempt in range(tries):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    return r.json()
                else:
                    print(f"[CoinGecko] خطا: وضعیت {r.status_code} برای {symbol}")
            except requests.exceptions.SSLError as e:
                print(f"[CoinGecko] خطای SSL برای {symbol}: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"[CoinGecko] خطای اتصال برای {symbol}: {e}")
            except Exception as e:
                print(f"[CoinGecko] خطا در دریافت داده برای {symbol}: {e}")
            if attempt < tries-1:
                print("دوباره تلاش می‌شود...")
                time.sleep(10)  # افزایش تاخیر برای اتصال بهتر به سرور
        print(f"[CoinGecko] شکست در دریافت داده برای {symbol} بعد از {tries} تلاش.")
        return {}

    def fetch_top_coins(self, limit: int = 10) -> list:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1&sparkline=false"
        headers = {"x-cg-pro-api-key": self.coingecko_key} if self.coingecko_key else {}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        return []

    def detect_newly_listed(self, days: int = 7, min_volume: float = 1e5, min_change: float = 5) -> list:
        ... # (existing code)

    def detect_holder_growth(self, days: int = 7, min_growth: int = 50) -> list:
        """
        شناسایی کوین‌های جدید با رشد سریع هولدرها (ورود زودهنگام)
        days: تعداد روز از لیست شدن
        min_growth: حداقل رشد تعداد هولدر در ۲۴ ساعت اخیر
        """
        import datetime
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false"
        headers = {"x-cg-pro-api-key": self.coingecko_key} if self.coingecko_key else {}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return []
        coins = r.json()
        now = datetime.datetime.utcnow()
        result = []
        for coin in coins:
            coin_detail = self.fetch_coingecko(coin['id'])
            gen_date = coin_detail.get('genesis_date')
            if not gen_date:
                continue
            try:
                listed_dt = datetime.datetime.strptime(gen_date, "%Y-%m-%d")
            except Exception:
                continue
            days_since = (now - listed_dt).days
            if days_since > days:
                continue
            # فقط توکن‌های دارای قرارداد اتریوم یا BSC
            eth_contract = None
            bsc_contract = None
            platforms = coin_detail.get('platforms', {})
            if 'ethereum' in platforms and platforms['ethereum']:
                eth_contract = platforms['ethereum']
            if 'binance-smart-chain' in platforms and platforms['binance-smart-chain']:
                bsc_contract = platforms['binance-smart-chain']
            holders_now = None
            holders_24h_ago = None
            # فقط یکی را چک کن (اولویت با اتریوم)
            if eth_contract:
                holders_now = self._get_eth_holder_count(eth_contract)
                holders_24h_ago = self._get_eth_holder_count(eth_contract, days_ago=1)
            elif bsc_contract:
                holders_now = self._get_bsc_holder_count(bsc_contract)
                holders_24h_ago = self._get_bsc_holder_count(bsc_contract, days_ago=1)
            if holders_now is not None and holders_24h_ago is not None:
                growth = holders_now - holders_24h_ago
                if growth >= min_growth:
                    result.append({
                        'name': coin.get('name'),
                        'symbol': coin.get('symbol'),
                        'price': coin.get('current_price'),
                        'holder_growth': growth,
                        'holders_now': holders_now,
                        'listed_days_ago': days_since
                    })
        return result

    def _get_eth_holder_count(self, contract, days_ago=0):
        import time
        # Etherscan API: https://api.etherscan.io/api?module=token&action=tokenholderlist&contractaddress=... (pro API)
        # اما API رایگان فقط تعداد هولدر را نمی‌دهد، پس از token/tokeninfo استفاده می‌کنیم
        url = f"https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={contract}&apikey={self.eth_key}"
        r = requests.get(url)
        if r.status_code != 200:
            return None
        data = r.json()
        try:
            holders = int(data['result'][0]['tokenHolder'])
        except Exception:
            holders = None
        # اگر days_ago>0 داده تاریخی نداریم، مقدار فعلی را برمی‌گردانیم (بهتر است تاریخچه را ذخیره کنیم)
        return holders

    def _get_bsc_holder_count(self, contract, days_ago=0):
        url = f"https://api.bscscan.com/api?module=token&action=tokeninfo&contractaddress={contract}&apikey={self.bsc_key}"
        r = requests.get(url)
        if r.status_code != 200:
            return None
        data = r.json()
        try:
            holders = int(data['result'][0]['tokenHolder'])
        except Exception:
            holders = None
        return holders

        """
        شناسایی کوین‌های تازه لیست‌شده با پتانسیل رشد بالا
        days: تعداد روز از لیست شدن
        min_volume: حداقل حجم معاملات
        min_change: حداقل درصد رشد قیمت
        """
        import datetime
        import time
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
        headers = {"x-cg-pro-api-key": self.coingecko_key} if self.coingecko_key else {}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return []
        coins = r.json()
        now = datetime.datetime.utcnow()
        result = []
        for coin in coins:
            # گرفتن تاریخ لیست شدن از API اصلی کوین‌گکو (ممکن است کند باشد)
            coin_detail = self.fetch_coingecko(coin['id'])
            gen_date = coin_detail.get('genesis_date')
            if not gen_date:
                continue
            try:
                listed_dt = datetime.datetime.strptime(gen_date, "%Y-%m-%d")
            except Exception:
                continue
            days_since = (now - listed_dt).days
            if days_since > days:
                continue
            volume = coin.get('total_volume', 0)
            price_change = coin.get('price_change_percentage_24h', 0)
            if volume >= min_volume and price_change >= min_change:
                result.append({
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'price': coin.get('current_price'),
                    'volume': volume,
                    'price_change_24h': price_change,
                    'listed_days_ago': days_since
                })
        return result

    def best_coin_signal(self, limit: int = 10) -> dict:
        coins = self.fetch_top_coins(limit)
        best = None
        best_score = float('-inf')
        results = []
        for coin in coins:
            symbol = coin['id']
            cg = self.fetch_coingecko(symbol)
            cg_price = cg.get('market_data', {}).get('current_price', {}).get('usd')
            cg_change = cg.get('market_data', {}).get('price_change_percentage_24h')
            volume = cg.get('market_data', {}).get('total_volume', {}).get('usd')
            cmc = self.fetch_coinmarketcap(coin.get('symbol', '').upper())
            cmc_price = None
            cmc_change = None
            cmc_volume = None
            try:
                data = cmc.get('data', {})
                for k in data:
                    cmc_price = data[k]['quote']['USD']['price']
                    cmc_change = data[k]['quote']['USD']['percent_change_24h']
                    cmc_volume = data[k]['quote']['USD']['volume_24h']
                    break
            except Exception:
                pass
            # آنچین: اگر contract address داشت، بگیر
            eth_contract = cg.get('contract_address') if cg.get('asset_platform_id') == 'ethereum' else None
            bsc_contract = cg.get('contract_address') if cg.get('asset_platform_id') == 'binance-smart-chain' else None
            eth_data = self.fetch_ethereum(eth_contract) if eth_contract else None
            bsc_data = self.fetch_bsc(bsc_contract) if bsc_contract else None
            # مثال ساده: تعداد تراکنش آنچین (در حالت واقعی باید پارس شود)
            eth_tx = len(eth_data['result']) if eth_data and 'result' in eth_data else 0
            bsc_tx = len(bsc_data['result']) if bsc_data and 'result' in bsc_data else 0
            # امتیازدهی: رشد ۲۴ ساعت + حجم + log(تراکنش آنچین+1)
            try:
                score = ((cg_change or 0) + (cmc_change or 0))/2 + ((volume or 0)+(cmc_volume or 0))/2/1e7 + (eth_tx + bsc_tx)**0.3
            except Exception:
                score = 0
            results.append({
                'name': coin.get('name'),
                'symbol': symbol,
                'price': cg_price,
                'cg_change_24h': cg_change,
                'cg_volume': volume,
                'cmc_price': cmc_price,
                'cmc_change_24h': cmc_change,
                'cmc_volume': cmc_volume,
                'eth_tx': eth_tx,
                'bsc_tx': bsc_tx,
                'score': round(score,3)
            })
            if score > best_score:
                best_score = score
                best = results[-1]
        return {'best': best, 'all': results}

    def fetch_coinmarketcap(self, symbol: str) -> Dict:
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
        headers = {"X-CMC_PRO_API_KEY": self.cmc_key} if self.cmc_key else {}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        return {}

    def fetch_ethereum(self, contract: str) -> Dict:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract}&apikey={self.eth_key}"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        return {}

    def fetch_bsc(self, contract: str) -> Dict:
        url = f"https://api.bscscan.com/api?module=account&action=tokentx&contractaddress={contract}&apikey={self.bsc_key}"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        return {}

    def aggregate_signals(self, symbol: str, eth_contract: Optional[str]=None, bsc_contract: Optional[str]=None) -> Dict:
        """
        داده‌های چند API را جمع می‌کند و سیگنال نهایی تولید می‌کند
        """
        cg = self.fetch_coingecko(symbol)
        cmc = self.fetch_coinmarketcap(symbol)
        eth = self.fetch_ethereum(eth_contract) if eth_contract else None
        bsc = self.fetch_bsc(bsc_contract) if bsc_contract else None
        # نمونه منطق: اگر قیمت در هر دو API رشد مثبت داشت و حجم بالا بود، سیگنال خرید
        try:
            cg_price = float(cg['market_data']['current_price']['usd']) if cg else None
            cmc_price = float(cmc['data'][symbol]['quote']['USD']['price']) if cmc else None
            cg_change = float(cg['market_data']['price_change_percentage_24h']) if cg else None
            cmc_change = float(cmc['data'][symbol]['quote']['USD']['percent_change_24h']) if cmc else None
            volume = float(cg['market_data']['total_volume']['usd']) if cg else None
        except Exception:
            cg_price = cmc_price = cg_change = cmc_change = volume = None
        signal = None
        if cg_change and cmc_change and cg_change > 2 and cmc_change > 2 and volume and volume > 1000000:
            signal = 'خرید قوی'
        elif cg_change and cmc_change and cg_change < -2 and cmc_change < -2:
            signal = 'فروش قوی'
        else:
            signal = 'خنثی/نیاز به بررسی بیشتر'
        return {
            'cg_price': cg_price,
            'cmc_price': cmc_price,
            'cg_change': cg_change,
            'cmc_change': cmc_change,
            'volume': volume,
            'signal': signal,
            'coingecko': cg,
            'coinmarketcap': cmc,
            'ethereum': eth,
            'bsc': bsc
        }
