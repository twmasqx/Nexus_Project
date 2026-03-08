[app]
title = NexusVision
package.name = nexusvision
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,jpeg,json
source.main = main.py
version = 0.2
# متوافق 100% مع Xiaomi, Redmi, Poco, Samsung
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,plyer,requests,scapy
orientation = portrait

# صلاحيات كاملة - يمنع Crash على Xiaomi/Redmi
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CHANGE_WIFI_STATE,CHANGE_NETWORK_STATE,VIBRATE,FOREGROUND_SERVICE,WAKE_LOCK

# التوافق: Android 5.0 (21) حتى 15 (34)
android.minapi = 21
android.api = 34
android.archs = armeabi-v7a,arm64-v8a

# Xiaomi Fix - ضروري لـ MIUI
android.enable_androidx = True

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0

[app:android]
p4a.branch = 2024.01.21
