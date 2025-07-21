# تست ساده برای بررسی خروجی
print("=== شروع تست ساده ===")

# داده نمونه
sample_tokens = [
    {"name": "Bitcoin", "price": 45000, "volume": 1000000, "change": 2.5},
    {"name": "Ethereum", "price": 3000, "volume": 800000, "change": -1.2},
    {"name": "Solana", "price": 100, "volume": 500000, "change": 5.1}
]

print("\nتوکن‌های نمونه:")
for token in sample_tokens:
    print(f"نام: {token['name']}, قیمت: ${token['price']}, تغییر: {token['change']}%")

# تست سیگنال ساده
print("\n=== تحلیل سیگنال ===")
for token in sample_tokens:
    if token['change'] > 2:
        print(f"🟢 سیگنال خرید: {token['name']} (تغییر: +{token['change']}%)")
    elif token['change'] < -1:
        print(f"🔴 سیگنال فروش: {token['name']} (تغییر: {token['change']}%)")
    else:
        print(f"⚪ بدون سیگنال: {token['name']}")

print("\n=== پایان تست ===")
