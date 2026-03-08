# -*- coding: utf-8 -*-
"""
Nexus Vision - ممر ذكي Z+
- المحرك يعمل في Thread منفصل (ScannerThread) لضمان عدم تجمد الواجهة
- متوافق 100% مع Xiaomi, Redmi, Poco, Samsung
"""
import sys
import os


def main():
    # لا نطلب الصلاحيات هنا — طلبها قبل فتح الواجهة يسبب خروج التطبيق عند الموافقة.
    # يتم طلبها من الواجهة بعد الظهور (انظر ui_core.on_start).

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
