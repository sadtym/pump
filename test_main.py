# تست ساده برای بررسی تابع main
print("شروع تست...")

# وارد کردن تابع main
from main import main

print("تابع main وارد شد.")

try:
    print("اجرای تابع main...")
    main()
    print("تابع main با موفقیت اجرا شد.")
except Exception as e:
    print(f"خطا در اجرای تابع main: {e}")
    import traceback
    traceback.print_exc()

print("پایان تست.")
