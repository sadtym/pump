# اسکنر خودکار ارز دیجیتال با فیلترهای بهبود یافته
import sys
import time
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class AutoCryptoScanner:
    def __init__(self):
        self.last_signals = {}  # ذخیره آخرین سیگنال‌ها برای جلوگیری از تکرار
        
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
                print("📱 پیام به تلگرام ارسال شد.")
                return True
            else:
                print(f"❌ خطا در ارسال تلگرام: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ خطا در ارسال تلگرام: {e}")
            return False

    def fetch_crypto_data(self):
        """دریافت داده‌های ارز با retry logic"""
        print("📡 دریافت داده‌های جدید...")
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 20,  # افزایش تعداد ارزها
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
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
                            "change_24h": coin['price_change_percentage_24h'] or 0,
                            "market_cap": coin['market_cap'],
                            "rank": coin['market_cap_rank']
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

    def analyze_signals(self, tokens):
        """تحلیل پیشرفته سیگنال‌ها با فیلترهای بهبود یافته"""
        signals = []
        
        for token in tokens:
            symbol = token['symbol']
            change = token['change_24h']
            volume = token['volume']
            price = token['price']
            rank = token.get('rank', 999)
            
            # فیلتر اولیه: فقط ارزهای معتبر
            if not volume or volume < 100000:  # حجم کمینه
                continue
            if rank > 100:  # فقط top 100
                continue
                
            signal_type = None
            strength = 0
            reason = ""
            
            # سیگنال‌های خرید
            if change > 5 and volume > 10000000:  # رشد قوی + حجم بالا
                signal_type = "خرید قوی"
                strength = 3
                reason = f"رشد {change:.1f}% با حجم بالا"
            elif change > 3 and volume > 5000000:
                signal_type = "خرید متوسط"
                strength = 2
                reason = f"رشد {change:.1f}% با حجم خوب"
            elif change > 1.5 and volume > 2000000 and rank <= 50:
                signal_type = "خرید ضعیف"
                strength = 1
                reason = f"رشد {change:.1f}% در ارز معتبر"
                
            # سیگنال‌های فروش
            elif change < -5 and volume > 5000000:
                signal_type = "فروش قوی"
                strength = 3
                reason = f"سقوط {abs(change):.1f}% با حجم بالا"
            elif change < -3 and volume > 2000000:
                signal_type = "فروش متوسط"
                strength = 2
                reason = f"کاهش {abs(change):.1f}%"
            elif change < -2 and rank <= 20:  # ارزهای top 20
                signal_type = "هشدار نزولی"
                strength = 1
                reason = f"کاهش {abs(change):.1f}% در ارز برتر"
            
            # بررسی تغییرات شدید (pump/dump)
            if abs(change) > 15:
                if change > 0:
                    signal_type = "پامپ احتمالی"
                    strength = 3
                    reason = f"رشد شدید {change:.1f}% - احتیاط!"
                else:
                    signal_type = "دامپ احتمالی"
                    strength = 3
                    reason = f"سقوط شدید {abs(change):.1f}% - فرار!"
            
            if signal_type:
                signals.append({
                    'token': token,
                    'type': signal_type,
                    'strength': strength,
                    'reason': reason,
                    'timestamp': datetime.now()
                })
        
        return signals

    def format_signal_message(self, signals):
        """فرمت کردن پیام سیگنال برای تلگرام"""
        if not signals:
            return None
            
        message = f"🚨 <b>سیگنال‌های جدید ارز دیجیتال</b>\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # دسته‌بندی بر اساس قدرت سیگنال
        strong_signals = [s for s in signals if s['strength'] == 3]
        medium_signals = [s for s in signals if s['strength'] == 2]
        weak_signals = [s for s in signals if s['strength'] == 1]
        
        for category, signals_list, emoji in [
            ("🔥 سیگنال‌های قوی", strong_signals, "🔥"),
            ("⚡ سیگنال‌های متوسط", medium_signals, "⚡"),
            ("💡 سیگنال‌های ضعیف", weak_signals, "💡")
        ]:
            if signals_list:
                message += f"<b>{category}</b>\n"
                for signal in signals_list[:3]:  # حداکثر 3 سیگنال از هر دسته
                    token = signal['token']
                    price_str = f"${token['price']:,.4f}" if token['price'] < 1 else f"${token['price']:,.2f}"
                    message += f"{emoji} <b>{token['name']}</b> ({token['symbol']})\n"
                    message += f"   💰 قیمت: {price_str}\n"
                    message += f"   📊 {signal['reason']}\n"
                    message += f"   🎯 نوع: {signal['type']}\n\n"
        
        return message

    def should_send_alert(self, signals):
        """تشخیص اینکه آیا باید هشدار ارسال شود یا نه"""
        if not signals:
            return False
            
        # ارسال فقط برای سیگنال‌های قوی یا تعداد زیاد سیگنال‌های متوسط
        strong_count = len([s for s in signals if s['strength'] == 3])
        medium_count = len([s for s in signals if s['strength'] == 2])
        
        return strong_count > 0 or medium_count >= 3

    def run_scan(self):
        """اجرای یک دور اسکن"""
        print(f"\n{'='*60}")
        print(f"🚀 شروع اسکن - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # دریافت داده‌ها
        tokens = self.fetch_crypto_data()
        if not tokens:
            print("❌ نتوانستم داده‌ای دریافت کنم.")
            return
        
        # تحلیل سیگنال‌ها
        signals = self.analyze_signals(tokens)
        
        print(f"\n📊 نتایج اسکن:")
        print(f"   🔍 ارزهای بررسی شده: {len(tokens)}")
        print(f"   🎯 سیگنال‌های یافت شده: {len(signals)}")
        
        if signals:
            # نمایش سیگنال‌ها در کنسول
            for signal in signals[:5]:  # نمایش 5 سیگنال برتر
                token = signal['token']
                print(f"   {signal['type']}: {token['name']} ({signal['reason']})")
            
            # ارسال به تلگرام در صورت نیاز
            if self.should_send_alert(signals):
                message = self.format_signal_message(signals)
                if message:
                    self.send_telegram_alert(message)
                    print("✅ سیگنال یافت شد!")
            else:
                print("📝 سیگنال‌ها ضعیف - ارسال نشد.")
        else:
            print("⚪ هیچ سیگنالی پیدا نشد.")
        
        print(f"✅ اسکن تمام شد - بعدی در 5 دقیقه")

    def run_auto(self):
        """اجرای خودکار"""
        print("🔥 شروع اسکنر خودکار ارز دیجیتال")
        print("💡 برای توقف: Ctrl+C")
        
        while True:
            try:
                self.run_scan()
                time.sleep(300)  # 5 دقیقه
            except KeyboardInterrupt:
                print("\n⏹️ اسکنر توسط کاربر متوقف شد.")
                break
            except Exception as e:
                print(f"\n❌ خطا در اسکن: {e}")
                print("🔄 ادامه در 1 دقیقه...")
                time.sleep(60)

if __name__ == "__main__":
    scanner = AutoCryptoScanner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # اجرای یک‌بار
        scanner.run_scan()
    else:
        # اجرای خودکار
        scanner.run_auto()
