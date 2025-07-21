# تست ساده اتصال به CoinGecko
import requests

print("🔍 تست اتصال به CoinGecko...")

try:
    # تست ساده ping
    response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ اتصال موفق! پاسخ: {data}")
    else:
        print(f"❌ خطا: کد {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ خطای اتصال - احتمالاً فیلترشکن لازم است")
except requests.exceptions.Timeout:
    print("❌ خطای timeout - سرور پاسخ نداد")
except Exception as e:
    print(f"❌ خطا: {e}")

print("\n🔍 تست دریافت قیمت Bitcoin...")
try:
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ قیمت Bitcoin: ${data['bitcoin']['usd']:,}")
    else:
        print(f"❌ خطا: کد {response.status_code}")
except Exception as e:
    print(f"❌ خطا: {e}")
