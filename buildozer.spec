[app]
title = NexusVision
package.name = nexusvision
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv
source.main = main.py
version = 0.1
# scapy removed - لا يبنى جيداً على Android، التطبيق يعمل بوضع المحاكاة
requirements = python3,kivy,requests
orientation = portrait
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
# تجنب خطأ 100 - قبول ترخيص SDK تلقائياً في CI
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
