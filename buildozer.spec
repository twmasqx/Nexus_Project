[app]
title = NexusVision
package.name = nexusvision
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv
source.main = main.py
version = 0.1
# python3,kivy فقط - requests غير مستخدم، scapy لا يبنى على Android
requirements = python3,kivy
orientation = portrait
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
# تجنب خطأ 100 - قبول ترخيص SDK تلقائياً في CI
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0

[app:android]
android.archs = armeabi-v7a
# إصدار مستقر من python-for-android
p4a.branch = 2024.01.21
