# -*- coding: utf-8 -*-
"""
نقطة الدخول للتطبيق: يربط بين محرك الشبكة وواجهة المستخدم
متوافق مع Android و Buildozer - بدون أكواد خاصة بويندوز
كل سطر مشروح باللغة العربية.
"""
import sys
import os

from ui_core import NexusVisionApp
from network_engine import NetworkEngine, precheck_environment


def main():
    # فحص بيئي سريع قبل البدء
    env = precheck_environment()
    missing = [k for k, v in env.items() if v in ('MISSING', 'NO')]
    if missing:
        # عرض تحذير للمستخدم مع ملخص النواقص (يُعرض عند بدء التطبيق)
        details = '\n'.join([f'{k}: {v}' for k, v in env.items()])
        print('تنبيه: بعض المتطلبات قد تكون غير متوفرة. التطبيق سيعمل بوضع المحاكاة إذا لزم.')
        print(details)

    # إنشاء محرك الشبكة
    engine = NetworkEngine()

    # تشغيل تطبيق Kivy
    app = NexusVisionApp(engine=engine)
    app.run()


if __name__ == '__main__':
    main()
