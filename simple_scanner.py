import requests
from datetime import datetime

def fetch_top_coins():
    """دریافت 10 ارز برتر از کوین‌گلاس"""
    print("📡 در حال دریافت داده‌های ارزهای دیجیتال...")
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ خطا: کد {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return None

def analyze_coins(coins):
    """تحلیل ارزها و یافتن بهترین‌ها"""
    if not coins:
        return []
    
    # مرتب‌سازی بر اساس تغییر قیمت 24 ساعته (نزولی)
    sorted_coins = sorted(coins, key=lambda x: x['price_change_percentage_24h'] or 0, reverse=True)
    
    # فقط ارزهایی که حجم معاملات بالایی دارند
    good_coins = [
        coin for coin in sorted_coins 
        if coin.get('total_volume', 0) > 1000000  # حداقل 1 میلیون دلار حجم معاملات
    ]
    
    return good_coins[:5]  # برگرداندن 5 ارز برتر

def main():
    print("🚀 اسکنر ساده ارز دیجیتال")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 در حال یافتن بهترین ارزها...\n")
    
    # دریافت داده‌ها
    coins = fetch_top_coins()
    
    if not coins:
        print("⚠️ نتوانستم به داده‌ها دسترسی پیدا کنم. لطفاً اینترنت خود را بررسی کنید.")
        return
    
    # تحلیل ارزها
    best_coins = analyze_coins(coins)
    
    if not best_coins:
        print("⚪ هیچ ارز مناسبی پیدا نشد.")
        return
    
    print("🏆 بهترین ارزها برای معامله:")
    print("-" * 50)
    
    for i, coin in enumerate(best_coins, 1):
        change = coin.get('price_change_percentage_24h', 0) or 0
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        
        print(f"{i}. {emoji} {coin['name']} ({coin['symbol'].upper()})")
        print(f"   💵 قیمت: ${coin['current_price']:,.2f}")
        print(f"   📈 تغییر 24h: {change:+.2f}%")
        print(f"   💰 حجم معاملات: ${coin['total_volume']:,.0f}")
        print()
    
    print("✅ تحلیل به پایان رسید!")

if __name__ == "__main__":
    main()
