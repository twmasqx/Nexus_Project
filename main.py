# -*- coding: utf-8 -*-
"""
Nexus Vision - ممر ذكي Z+
نقطة الدخول: ربط المحرك بالواجهة مع استقرار كامل
"""
import sys
import os


def _request_android_permissions():
    """صلاحيات ديناميكية - يمنع الانهيار على الأندرويد"""
    try:
        from android.permissions import request_permissions, Permission
        perms = [
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
            Permission.CHANGE_NETWORK_STATE,
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
