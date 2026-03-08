[app]
title = NexusVision
package.name = nexusvision
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,jpeg
source.main = main.py
version = 0.2
# متوافق مع Xiaomi, Poco, Redmi, Samsung - جميع الإصدارات
requirements = python3,kivy,kivymd,pillow,plyer
orientation = portrait

# صلاحيات الممر الذكي
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CHANGE_WIFI_STATE,CHANGE_NETWORK_STATE,VIBRATE,FOREGROUND_SERVICE

# التوافق الشامل: Android 5.0 (21) حتى 15 (34)
android.minapi = 21
android.api = 34

# دعم المعالجات القديمة والحديثة
android.archs = armeabi-v7a,arm64-v8a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0

[app:android]
# إصدار مستقر من python-for-android
p4a.branch = 2024.01.21
