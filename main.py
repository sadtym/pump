from dataclasses import dataclass
from typing import List, Optional, Callable

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

import sys

# fetcher.py حذف شده - از داده نمونه استفاده می‌شود
FETCHER_AVAILABLE = False
FetchedToken = None
fetch_top_tokens = None

# --- Multi-API Signal Integration ---
try:
    from scanner.multi_api import MultiAPIScanner
    import config
    MULTI_API_AVAILABLE = True
except Exception as e:
    MULTI_API_AVAILABLE = False
    print("خطا در وارد کردن multi_api یا config: ", e, file=sys.stderr)

@dataclass
class Token:
    name: str
    price: float
    volume: int
    price_change_24h: Optional[float] = None  # درصد تغییر قیمت ۲۴ ساعت
    moving_avg: Optional[float] = None        # میانگین متحرک فرضی

def filter_tokens(
    tokens: List[Token],
    min_price: Optional[float] = None,
    name_contains: Optional[str] = None,
    min_volume: Optional[int] = None,
    custom_filter: Optional[Callable[[Token], bool]] = None
) -> List[Token]:
    """
    فیلتر لیست توکن‌ها بر اساس قیمت، نام، حجم یا فیلتر سفارشی
    """
    result = []
    for token in tokens:
        if min_price is not None and token.price < min_price:
            continue
        if name_contains is not None and name_contains.lower() not in token.name.lower():
            continue
        if min_volume is not None and token.volume < min_volume:
            continue
        if custom_filter is not None and not custom_filter(token):
            continue
        result.append(token)
    return result

def print_tokens(tokens: List[Token], title: str):
    print(f"\n{title}")
    if not tokens:
        print("هیچ موردی پیدا نشد.")
        return
    headers = ["نام", "قیمت", "حجم", "تغییر ۲۴ساعت (%)", "MA (فرضی)"]
    rows = [[t.name, t.price, t.volume, t.price_change_24h if t.price_change_24h is not None else '-', t.moving_avg if t.moving_avg is not None else '-'] for t in tokens]
    if TABULATE_AVAILABLE:
        print(tabulate(rows, headers, tablefmt="grid", stralign="right", numalign="right", colalign=("right",)*len(headers)))
    else:
        col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]
        print(" | ".join(h.rjust(col_widths[i]) for i, h in enumerate(headers)))
        print("-+-".join("-"*w for w in col_widths))
        for row in rows:
            print(" | ".join(str(row[i]).rjust(col_widths[i]) for i in range(len(headers))))

def analyze_tokens_for_signals(tokens: List[Token]):
    """
    تحلیل پیشرفته برای سیگنال خرید/فروش بر اساس قیمت، تغییر قیمت ۲۴ ساعت، حجم و میانگین متحرک
    """
    print("\nسیگنال‌های خرید/فروش پیشرفته:")
    for t in tokens:
        # منطق نمونه: اگر قیمت فعلی کمتر از میانگین متحرک و تغییر ۲۴ ساعت مثبت باشد و حجم بالا باشد، سیگنال خرید
        buy_cond = (
            t.moving_avg is not None and t.price < t.moving_avg and
            t.price_change_24h is not None and t.price_change_24h > 0 and
            t.volume > 1000000
        )
        # اگر قیمت فعلی بالاتر از میانگین متحرک و تغییر ۲۴ ساعت منفی باشد، سیگنال فروش
        sell_cond = (
            t.moving_avg is not None and t.price > t.moving_avg and
            t.price_change_24h is not None and t.price_change_24h < 0
        )
        if buy_cond:
            print(f"سیگنال خرید: {t.name} (قیمت: {t.price}، تغییر ۲۴ساعت: {t.price_change_24h}%، MA: {t.moving_avg})")
        elif sell_cond:
            print(f"سیگنال فروش: {t.name} (قیمت: {t.price}، تغییر ۲۴ساعت: {t.price_change_24h}%، MA: {t.moving_avg})")
    print("پایان تحلیل.")

def main():
    print("=== شروع تحلیل ===\n")
    import random
    # اگر fetcher موجود بود، داده واقعی بگیر
    if FETCHER_AVAILABLE:
        print("در حال دریافت توکن‌های واقعی بازار از CoinGecko...")
        fetched = fetch_top_tokens(10)
        tokens = []
        for f in fetched:
            price_change = getattr(f, 'price_change_percentage_24h', None)
            moving_avg = round(f.price * (1 + random.uniform(-0.05, 0.05)), 4)
            tokens.append(Token(f.name, f.price, int(f.volume), price_change_24h=price_change, moving_avg=moving_avg))
    else:
        print("داده نمونه استفاده می‌شود.")
        tokens = [
            Token("PepeCoin", 0.0021, 100000, price_change_24h=2.5, moving_avg=0.0025),
            Token("ShibaMoon", 0.00001, 500000, price_change_24h=-1.2, moving_avg=0.000012),
            Token("DogeStar", 0.01, 80000, price_change_24h=0.5, moving_avg=0.009),
            Token("SolanaPump", 0.05, 120000, price_change_24h=3.1, moving_avg=0.048),
            Token("MiniPepe", 0.001, 45000, price_change_24h=-0.7, moving_avg=0.0012),
        ]
    print_tokens(tokens, "توکن‌های اسکن‌شده:")
    print("توکن‌ها نمایش داده شد.")
    filtered_price = filter_tokens(tokens, min_price=0.002)
    print_tokens(filtered_price, "توکن‌های با قیمت بالاتر از 0.002:")
    filtered_volume = filter_tokens(tokens, min_volume=100000)
    print_tokens(filtered_volume, "توکن‌های با حجم بالاتر از 100,000:")
    print("شروع تحلیل سیگنال...")
    analyze_tokens_for_signals(tokens)
    print("تحلیل سیگنال تمام شد.")

    # --- Multi-API Best Coin Signal ---
    print(f"MULTI_API_AVAILABLE: {MULTI_API_AVAILABLE}")
    if MULTI_API_AVAILABLE:
        print("\nدر حال جستجوی بهترین ارز بازار بر اساس داده‌های چند API...")
        scanner = MultiAPIScanner(
            coingecko_key=getattr(config, 'COINGECKO_API_KEY', None),
            cmc_key=getattr(config, 'COINMARKETCAP_API_KEY', None),
            eth_key=getattr(config, 'ETHERSCAN_API_KEY', None),
            bsc_key=getattr(config, 'BSCSCAN_API_KEY', None),
        )
        best_result = scanner.best_coin_signal(limit=5)  # کاهش تعداد ارزها برای جلوگیری از Rate Limit
        best = best_result['best']
        all_coins = best_result['all']
        # نمایش جدول مقایسه‌ای
        print("\nجدول مقایسه‌ای ارزهای برتر:")
        headers = ["نام", "نماد", "قیمت CG", "تغییر CG", "حجم CG", "قیمت CMC", "تغییر CMC", "حجم CMC", "تراکنش ETH", "تراکنش BSC", "امتیاز"]
        rows = [
            [c['name'], c['symbol'], c['price'], c['cg_change_24h'], c['cg_volume'], c['cmc_price'], c['cmc_change_24h'], c['cmc_volume'], c['eth_tx'], c['bsc_tx'], c['score']]
            for c in all_coins
        ]
        if TABULATE_AVAILABLE:
            print(tabulate(rows, headers, tablefmt="grid", stralign="right", numalign="right"))
        else:
            print(" | ".join(headers))
            print("-+-".join("-"*10 for _ in headers))
            for row in rows:
                print(" | ".join(str(x) for x in row))
        if best:
            print(f"\nبهترین ارز بازار:")
            print(f"نام: {best['name']}")
            print(f"نماد: {best['symbol']}")
            print(f"قیمت: {best['price']}")
            print(f"تغییر ۲۴ ساعت: {best['cg_change_24h']}% (CG) / {best['cmc_change_24h']}% (CMC)")
            print(f"حجم: {best['cg_volume']} (CG) / {best['cmc_volume']} (CMC)")
            print(f"تراکنش آنچین: ETH={best['eth_tx']}  BSC={best['bsc_tx']}")
            print(f"امتیاز سیگنال: {best['score']}")
        else:
            print("هیچ ارز مناسبی پیدا نشد.")
        # --- Newly Listed Coins with Growth Potential ---
        print("\nارزهای جدید لیست شده با پتانسیل رشد:")
        new_coins = scanner.detect_newly_listed(days=7, min_volume=1e5, min_change=5)
        if new_coins:
            headers_new = ["نام", "نماد", "قیمت", "حجم", "تغییر ۲۴ساعت", "روز از لیست شدن"]
            rows_new = [[c['name'], c['symbol'], c['price'], c['volume'], c['price_change_24h'], c['listed_days_ago']] for c in new_coins]
            if TABULATE_AVAILABLE:
                print(tabulate(rows_new, headers_new, tablefmt="grid", stralign="right", numalign="right"))
            else:
                print(" | ".join(headers_new))
                print("-+-".join("-"*10 for _ in headers_new))
                for row in rows_new:
                    print(" | ".join(str(x) for x in row))
        else:
            print("هیچ ارز جدید با پتانسیل رشد پیدا نشد.")
        # --- Newly Listed Coins with Sudden Holder Growth ---
        print("\nارزهای جدید با رشد سریع هولدرها (ورود زودهنگام):")
        holder_growth_coins = scanner.detect_holder_growth(days=7, min_growth=50)
        if holder_growth_coins:
            headers_hg = ["نام", "نماد", "قیمت", "تعداد هولدر جدید (۲۴ساعت)", "کل هولدرها", "روز از لیست شدن"]
            rows_hg = [[c['name'], c['symbol'], c['price'], c['holder_growth'], c['holders_now'], c['listed_days_ago']] for c in holder_growth_coins]
            if TABULATE_AVAILABLE:
                print(tabulate(rows_hg, headers_hg, tablefmt="grid", stralign="right", numalign="right"))
            else:
                print(" | ".join(headers_hg))
                print("-+-".join("-"*10 for _ in headers_hg))
                for row in rows_hg:
                    print(" | ".join(str(x) for x in row))
            # ارسال پیام تلگرام برای هر ارز جدید با رشد سریع هولدرها
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            def send_telegram_message(text):
                import requests
                if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                    return
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
                try:
                    requests.post(url, data=data, timeout=10)
                except Exception:
                    pass
            for c in holder_growth_coins:
                # تشخیص منبع داده (اتریوم یا BSC یا کوین‌گکو)
                data_source = ""
                if c.get('holders_now') is not None:
                    if c.get('symbol', '').startswith('0x') or c.get('name', '').lower().endswith('bsc'):
                        data_source = "BSCscan"
                    else:
                        data_source = "Etherscan"
                else:
                    data_source = "CoinGecko"
                msg = (
                    f"🚨 ارز جدید با رشد سریع هولدرها:\n"
                    f"نام: {c['name']}\n"
                    f"نماد: {c['symbol']}\n"
                    f"قیمت: {c['price']}\n"
                    f"تعداد هولدر جدید (۲۴ساعت): {c['holder_growth']}\n"
                    f"کل هولدرها: {c['holders_now']}\n"
                    f"روز از لیست شدن: {c['listed_days_ago']}\n"
                    f"منبع داده: {data_source}"
                )
                send_telegram_message(msg)
                print("سیگنال یافت شد ✅")
        else:
            print("هیچ ارز جدید با رشد سریع هولدرها پیدا نشد.")
    else:
        print("\nبرای سیگنال‌گیری پیشرفته، config.py و کلیدها را وارد کن!")

def send_telegram_test():
    import requests
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("توکن یا chat_id تلگرام تنظیم نشده.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": "✅ پیام تستی از اسکنر ارز دیجیتال (meme_coin_tracker)"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print("پیام تستی با موفقیت به تلگرام ارسال شد.")
        else:
            print(f"ارسال پیام تستی ناموفق بود: {resp.text}")
    except Exception as e:
        print(f"خطا در ارسال پیام تستی: {e}")

if __name__ == "__main__":
    import time
    print("اجرای خودکار هر ۳ دقیقه فعال شد. برای توقف Ctrl+C را بزنید.")
    while True:
        try:
            main()
        except Exception as e:
            print(f"خطا در اجرای تحلیل: {e}")
        time.sleep(300)  # هر ۵ دقیقه برای تست
