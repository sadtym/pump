# اسکنر پتانسیل رشد ارزهای دیجیتال
import sys
import time
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class GrowthPotentialScanner:
    def __init__(self):
        self.growth_threshold = 70  # حد آستانه پتانسیل رشد (از 100)
        
    def send_telegram_alert(self, message):
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
                print("📱 پیام رشد به تلگرام ارسال شد.")
                return True
            else:
                print(f"❌ خطا در ارسال تلگرام: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ خطا در ارسال تلگرام: {e}")
            return False

    def fetch_crypto_data(self):
        """دریافت داده‌های کامل ارزها"""
        print("📡 دریافت داده‌های ارزها برای تحلیل پتانسیل رشد...")
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 50,  # تحلیل top 50
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '1h,24h,7d'
        }
        
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=20)
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
                    print(f"✅ {len(tokens)} ارز دریافت شد.")
                    return tokens
                else:
                    print(f"❌ خطا: کد {response.status_code}")
            except Exception as e:
                print(f"❌ تلاش {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(5)
        
        return None

    def calculate_growth_potential(self, token):
        """محاسبه پتانسیل رشد بر اساس عوامل مختلف"""
        score = 0
        factors = []
        
        # عامل 1: روند قیمت (40 امتیاز)
        if token['change_1h'] > 2:
            score += 15
            factors.append("روند 1ساعت مثبت")
        elif token['change_1h'] > 0:
            score += 8
            
        if token['change_24h'] > 5:
            score += 15
            factors.append("رشد 24ساعت قوی")
        elif token['change_24h'] > 1:
            score += 10
            factors.append("رشد 24ساعت متوسط")
        elif token['change_24h'] > 0:
            score += 5
            
        if token['change_7d'] > 10:
            score += 10
            factors.append("روند هفتگی مثبت")
        elif token['change_7d'] > 0:
            score += 5
            
        # عامل 2: حجم معاملات (25 امتیاز)
        if token['volume_to_cap'] > 20:  # حجم بالا نسبت به ارزش بازار
            score += 15
            factors.append("حجم معاملات بالا")
        elif token['volume_to_cap'] > 10:
            score += 10
            factors.append("حجم معاملات خوب")
        elif token['volume_to_cap'] > 5:
            score += 5
            
        # عامل 3: رتبه بازار (15 امتیاز)
        if token['rank'] <= 20:
            score += 15
            factors.append("ارز برتر")
        elif token['rank'] <= 50:
            score += 10
            factors.append("ارز معتبر")
        elif token['rank'] <= 100:
            score += 5
            
        # عامل 4: پتانسیل breakout (20 امتیاز)
        # اگر تغییر 1 ساعت خیلی بیشتر از 24 ساعت باشد (momentum جدید)
        if token['change_1h'] > token['change_24h'] / 24 * 2:
            score += 10
            factors.append("momentum جدید")
            
        # اگر حجم خیلی بالا باشد (whale activity)
        if token['volume'] > 100000000:  # بیش از 100 میلیون دلار
            score += 10
            factors.append("فعالیت نهنگ‌ها")
        elif token['volume'] > 50000000:
            score += 5
            
        return min(score, 100), factors  # حداکثر 100 امتیاز

    def analyze_growth_potential(self, tokens):
        """تحلیل پتانسیل رشد همه ارزها"""
        growth_coins = []
        
        for token in tokens:
            # فیلتر اولیه: حداقل حجم و قیمت
            if token['volume'] < 1000000 or token['price'] <= 0:
                continue
                
            score, factors = self.calculate_growth_potential(token)
            
            if score >= self.growth_threshold:
                growth_coins.append({
                    'token': token,
                    'score': score,
                    'factors': factors,
                    'timestamp': datetime.now()
                })
        
        # مرتب‌سازی بر اساس امتیاز
        growth_coins.sort(key=lambda x: x['score'], reverse=True)
        return growth_coins

    def format_growth_message(self, growth_coins):
        """فرمت کردن پیام پتانسیل رشد"""
        if not growth_coins:
            return None
            
        message = f"🚀 <b>ارزهای با پتانسیل رشد بالا</b>\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        for i, coin_data in enumerate(growth_coins[:5], 1):  # top 5
            token = coin_data['token']
            score = coin_data['score']
            factors = coin_data['factors']
            
            price_str = f"${token['price']:,.4f}" if token['price'] < 1 else f"${token['price']:,.2f}"
            
            # انتخاب emoji بر اساس امتیاز
            if score >= 90:
                emoji = "🔥"
            elif score >= 80:
                emoji = "⚡"
            else:
                emoji = "💎"
                
            message += f"{emoji} <b>{i}. {token['name']}</b> ({token['symbol']})\n"
            message += f"   💰 قیمت: {price_str}\n"
            message += f"   📊 امتیاز رشد: {score}/100\n"
            message += f"   📈 تغییرات: 1س:{token['change_1h']:+.1f}% | 24س:{token['change_24h']:+.1f}% | 7روز:{token['change_7d']:+.1f}%\n"
            message += f"   💧 حجم: ${token['volume']:,.0f}\n"
            message += f"   🎯 عوامل: {', '.join(factors[:3])}\n\n"
        
        message += f"💡 <i>تحلیل شده: {len(growth_coins)} ارز با پتانسیل بالا</i>"
        return message

    def run_scan(self):
        """اجرای یک دور اسکن پتانسیل رشد"""
        print(f"\n{'='*60}")
        print(f"🚀 شروع تحلیل پتانسیل رشد - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # دریافت داده‌ها
        tokens = self.fetch_crypto_data()
        if not tokens:
            print("❌ نتوانستم داده‌ای دریافت کنم.")
            return
        
        # تحلیل پتانسیل رشد
        growth_coins = self.analyze_growth_potential(tokens)
        
        print(f"\n📊 نتایج تحلیل پتانسیل رشد:")
        print(f"   🔍 ارزهای بررسی شده: {len(tokens)}")
        print(f"   🚀 ارزهای با پتانسیل بالا: {len(growth_coins)}")
        
        if growth_coins:
            # نمایش در کنسول
            print(f"\n🏆 برترین ارزها:")
            for i, coin_data in enumerate(growth_coins[:3], 1):
                token = coin_data['token']
                score = coin_data['score']
                print(f"   {i}. {token['name']} ({token['symbol']}) - امتیاز: {score}/100")
            
            # ارسال به تلگرام
            message = self.format_growth_message(growth_coins)
            if message:
                self.send_telegram_alert(message)
                print("✅ پتانسیل‌های رشد به تلگرام ارسال شد!")
        else:
            print("⚪ هیچ ارزی با پتانسیل رشد بالا پیدا نشد.")
        
        print(f"✅ تحلیل تمام شد - بعدی در 10 دقیقه")

    def run_auto(self):
        """اجرای خودکار"""
        print("🔥 شروع اسکنر پتانسیل رشد خودکار")
        print("💡 برای توقف: Ctrl+C")
        
        while True:
            try:
                self.run_scan()
                time.sleep(600)  # 10 دقیقه
            except KeyboardInterrupt:
                print("\n⏹️ اسکنر توسط کاربر متوقف شد.")
                break
            except Exception as e:
                print(f"\n❌ خطا در اسکن: {e}")
                print("🔄 ادامه در 2 دقیقه...")
                time.sleep(120)

if __name__ == "__main__":
    scanner = GrowthPotentialScanner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # اجرای یک‌بار
        scanner.run_scan()
    else:
        # اجرای خودکار
        scanner.run_auto()
