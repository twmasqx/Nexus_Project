# -*- coding: utf-8 -*-
"""
Nexus Vision - ممر ذكي Z+
- المحرك يعمل في Thread منفصل (ScannerThread) لضمان عدم تجمد الواجهة
- متوافق 100% مع Xiaomi, Redmi, Poco, Samsung
"""
import sys
import os


def _request_android_permissions():
    """صلاحيات كاملة - يمنع Crash على Xiaomi/Redmi/MIUI"""
    try:
        from android.permissions import request_permissions, Permission
        perms = [
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_WIFI_STATE,
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
            Permission.CHANGE_NETWORK_STATE,
            Permission.CHANGE_WIFI_STATE,
        ]
        request_permissions(perms)
    except Exception:
        pass


def main():
    _request_android_permissions()

    from ui_core import NexusVisionApp
    from network_engine import NetworkEngine, precheck_environment

    try:
        env = precheck_environment()
        missing = [k for k, v in env.items() if v in ('MISSING', 'NO')]
        if missing:
            print('Nexus Vision: وضع الرصد العادي')
    except Exception:
        pass

    try:
        engine = NetworkEngine()
        if hasattr(engine, 'request_root_or_warn'):
            engine.request_root_or_warn()
    except Exception:
        engine = NetworkEngine()

    app = NexusVisionApp(engine=engine)
    app.run()


if __name__ == '__main__':
    main()
