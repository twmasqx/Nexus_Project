# -*- coding: utf-8 -*-
"""
واجهة المستخدم الأساسية باستخدام Kivy
متوافقة مع Android و Buildozer
تحتوى على واجهة رادار وتأثيرات مشابهة لـ Glassmorphism
كل سطر مشروح باللغة العربية.
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.core.window import Window
from kivy.metrics import dp
import math
import threading
import time
import os
import json
from typing import List

from network_engine import Device, get_vendor_from_mac


def _angle_diff(a, b):
    """عامل مساعد لتحويل زاوية إلى مدى -180..180"""
    d = (a - b + 180) % 360 - 180
    return abs(d)


class RadarWidget(BoxLayout):
    """عنصر رادار مرئي - Kivy"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0.0
        self.devices: List[Device] = []
        self.size_hint = (1, None)
        self.height = dp(600)
        self.spin_speed = 1.6
        self._device_clicked_callback = None
        Clock.schedule_interval(self._on_tick, 1 / 30.)

    def set_device_clicked_callback(self, callback):
        """ربط دالة عند النقر على جهاز"""
        self._device_clicked_callback = callback

    def _on_tick(self, dt):
        """تحديث الزاوية وإعادة رسم العنصر"""
        self.angle = (self.angle + self.spin_speed) % 360.0
        for d in self.devices:
            d.trail.append((d.x, d.y))
            if len(d.trail) > 8:
                d.trail.pop(0)
            t = time.time() + (hash(d.mac) % 10)
            d.x += math.sin(t * 0.6) * 0.0008
            d.y += math.cos(t * 0.6) * 0.0008
        self._draw()

    def set_devices(self, devices: List[Device]):
        """تحديث قائمة الأجهزة المعروضة"""
        self.devices = list(devices) if devices else []

    def on_touch_down(self, touch):
        """اختبار الضغط على أيقونة جهاز"""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        cx = self.center_x
        cy = self.center_y
        radius = min(self.width, self.height) / 2 - 10
        px, py = touch.pos
        closest = None
        closest_dist = 1e9
        for d in self.devices:
            dx = cx + d.x * radius - px
            dy = cy + d.y * radius - py
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest = d
        if closest and closest_dist <= 28 and self._device_clicked_callback:
            try:
                self._device_clicked_callback(getattr(closest, 'mac', ''))
            except Exception:
                pass
            return True
        return super().on_touch_down(touch)

    def _draw(self):
        """رسم الرادار وكل العناصر"""
        self.canvas.clear()
        with self.canvas:
            Color(0.04, 0.04, 0.055)
            Rectangle(pos=self.pos, size=self.size)
            cx = self.center_x
            cy = self.center_y
            radius = min(self.width, self.height) / 2 - 10

            # دوائر الرادار
            Color(0.31, 0.78, 1.0, 0.31)
            for r in range(1, 5):
                Line(circle=(cx, cy, radius * r / 5), width=1)

            # شعاع المسح (مثلث مملوء)
            angle_rad = math.radians(-self.angle)
            sweep_angle = math.radians(30)
            x1 = cx + radius * math.cos(angle_rad)
            y1 = cy + radius * math.sin(angle_rad)
            x2 = cx + radius * math.cos(angle_rad + sweep_angle)
            y2 = cy + radius * math.sin(angle_rad + sweep_angle)
            Color(0, 1, 0.78, 0.7)
            Triangle(points=[cx, cy, x1, y1, x2, y2])

            # رسم الأجهزة
            for d in self.devices:
                px = cx + d.x * radius
                py = cy + d.y * radius
                dx = px - cx
                dy = py - cy
                dist = math.hypot(dx, dy)
                if dist > radius:
                    nx = dx / dist
                    ny = dy / dist
                    px = cx + nx * radius * 0.98
                    py = cy + ny * radius * 0.98
                    edge_alpha = max(0, 0.86 - (dist - radius) * 0.01)
                else:
                    edge_alpha = 1.0

                # أثر الحركة
                if d.trail:
                    trail_pts = [cx + d.trail[0][0] * radius, cy + d.trail[0][1] * radius]
                    for tx, ty in d.trail[1:]:
                        trail_pts.extend([cx + tx * radius, cy + ty * radius])
                    Color(0, 1, 0.7, 0.5)
                    Line(points=trail_pts, width=2)

                # توهج عند مرور الشعاع
                dev_angle = (math.degrees(math.atan2(d.y, d.x)) + 360) % 360
                if _angle_diff(self.angle, dev_angle) < 6.0:
                    Color(0, 0.86, 1.0, 0.63)
                    Ellipse(pos=(px - 28, py - 28), size=(56, 56))

                # أيقونة الجهاز (دائرة حسب الشركة)
                if d.vendor == 'APPLE':
                    Color(1, 1, 1, edge_alpha)
                else:
                    Color(0.39, 1, 0.47, edge_alpha)
                Ellipse(pos=(px - 10, py - 10), size=(20, 20))

    def on_pos(self, *args):
        self._draw()

    def on_size(self, *args):
        self._draw()


class ScannerThread:
    """خيط ماسح يُنفّذ المسح بشكل دوري ويرسل تحديثات للأجهزة"""
    def __init__(self, engine, interval=3.0, on_devices=None, on_log=None):
        self.engine = engine
        self.interval = interval
        self._running = True
        self._thread = None
        self.on_devices = on_devices
        self.on_log = on_log

    def start(self):
        """بدء الخيط"""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """حلقة المسح المتواصلة"""
        while self._running:
            try:
                devs = self.engine.scan_network(allow_simulation=False)
                for d in devs:
                    name = getattr(d, 'model', '') or d.vendor
                    if self.on_log:
                        self.on_log(f"[{time.strftime('%H:%M:%S')}] Target Locked: {name} ({d.mac})")
                if self.on_devices:
                    self.on_devices(devs)
            except Exception as e:
                if self.on_log:
                    self.on_log(f"[{time.strftime('%H:%M:%S')}] Scan Error: {e}")
            time.sleep(self.interval)

    def stop(self):
        """إيقاف الخيط"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)


class NexusVisionApp(App):
    """التطبيق الرئيسي - Nexus Vision"""
    def __init__(self, engine=None, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine or __import__('network_engine').NetworkEngine()
        self.scanner = None
        self._sniffer_running = False

    def build(self):
        """بناء الواجهة"""
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        root.size_hint = (1, 1)

        # شريط علوي
        top_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self.count_label = Label(
            text='Devices: 0',
            font_size='11sp',
            bold=True,
            size_hint_x=None,
            width=dp(120)
        )
        btn_back = Button(text='◀', size_hint_x=None, width=dp(36), height=dp(28))
        btn_home = Button(text='⌂', size_hint_x=None, width=dp(36), height=dp(28))
        btn_back.bind(on_release=self._back_action)
        btn_home.bind(on_release=self._home_action)
        top_row.add_widget(self.count_label)
        top_row.add_widget(Label(size_hint_x=1))
        top_row.add_widget(btn_back)
        top_row.add_widget(btn_home)
        root.add_widget(top_row)

        # الرادار
        self.radar = RadarWidget()
        self.radar.set_device_clicked_callback(self._on_device_clicked)
        root.add_widget(self.radar)

        # أزرار Intercept / Kick / Scan
        big_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(8))
        for text, action in [
            ('Intercept', self._intercept_action),
            ('Kick', self._kick_action),
            ('Scan', self._on_scan),
        ]:
            btn = Button(
                text=text,
                font_size='18sp',
                background_normal='',
                background_color=(0, 0.17, 0.21, 1),
                size_hint_x=1
            )
            btn.bind(on_release=action)
            big_row.add_widget(btn)
        root.add_widget(big_row)

        # دوائر Navigate, Monitor, Connect, Settings
        circles_row = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(8))
        for name in ['Navigate', 'Monitor', 'Connect', 'Settings']:
            c = Button(
                text=name,
                font_size='9sp',
                background_normal='',
                background_color=(0.2, 0.2, 0.25, 0.5),
                size_hint_x=1
            )
            circles_row.add_widget(c)
        root.add_widget(circles_row)

        root.add_widget(Label(size_hint_y=1))

        # شريط سفلي
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        for text, action in [
            ('Navigate', lambda *a: self._show_msg('Navigate (UI-only)')),
            ('Monitor', self._toggle_sniffer),
            ('Connect', lambda *a: self._show_msg('Connect (UI-only)')),
            ('Settings', lambda *a: self._show_msg('Settings (UI-only)')),
            ('Kill Switch', self._kill_switch),
        ]:
            btn = Button(
                text=text,
                background_normal='',
                background_color=(0.1, 0.2, 0.25, 1) if 'Kill' not in text else (0.7, 0.13, 0.13, 1),
                size_hint_x=1
            )
            btn.bind(on_release=action)
            if text == 'Monitor':
                self.btn_monitor = btn
            btn_row.add_widget(btn)
        root.add_widget(btn_row)

        # مؤقت لجلب البيانات
        Clock.schedule_interval(self._pull_engine, 2.0)

        return root

    def on_start(self):
        """عند بدء التطبيق - تشغيل الماسح"""
        self.scanner = ScannerThread(
            engine=self.engine,
            interval=3.0,
            on_devices=self._on_devices_updated,
            on_log=lambda msg: print(msg)
        )
        self.scanner.start()

    def on_stop(self):
        """عند إيقاف التطبيق"""
        if self.scanner:
            self.scanner.stop()

    def _on_devices_updated(self, devs: List[Device]):
        """عند وصول بيانات جديدة من الماسح"""
        Clock.schedule_once(lambda dt: self._update_devices_ui(devs), 0)

    def _update_devices_ui(self, devs):
        """تحديث الواجهة بالأجهزة (يُنفذ على الخيط الرئيسي)"""
        self.radar.set_devices(devs)
        self.count_label.text = f'Devices: {len(devs)}'
        try:
            entry = {
                'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(devs),
                'devices': [{'ip': d.ip, 'mac': d.mac, 'vendor': d.vendor, 'model': getattr(d, 'model', '')} for d in devs]
            }
            logs = []
            log_path = os.path.join(os.path.dirname(__file__), 'scan_log.json')
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except Exception:
                        logs = []
            logs.append(entry)
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _on_device_clicked(self, mac: str):
        """عند النقر على جهاز"""
        if not mac:
            return
        reqs = []
        try:
            if hasattr(self.engine, 'get_requests_for_device'):
                reqs = self.engine.get_requests_for_device(mac)
        except Exception:
            reqs = []
        txt = f"Device: {mac}\nRecent domains:\n"
        for r in reqs[-8:]:
            txt += f" - {r.get('time')} {r.get('domain')}\n"
        content = Label(text=txt or 'No data', size_hint_y=None)
        popup = Popup(title='Device', content=content, size_hint=(0.9, 0.5))
        content.bind(texture_size=content.setter('size'))
        popup.open()

    def _intercept_action(self, *a):
        """زر Intercept - محاكاة"""
        self._show_msg('Intercept is simulation-only in this build. Opening Monitor.')
        self._open_monitor()

    def _kick_action(self, *a):
        """زر Kick - محاكاة"""
        def confirm(btn):
            if btn.text == 'Yes':
                try:
                    entry = {'ts': time.strftime('%Y-%m-%d %H:%M:%S'), 'event': 'kick_simulated'}
                    log_path = os.path.join(os.path.dirname(__file__), 'actions_log.json')
                    logs = []
                    if os.path.exists(log_path):
                        with open(log_path, 'r', encoding='utf-8') as f:
                            try:
                                logs = json.load(f)
                            except Exception:
                                logs = []
                    logs.append(entry)
                    with open(log_path, 'w', encoding='utf-8') as f:
                        json.dump(logs, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                self._show_msg('Simulated deauthentication packets sent (NO PACKETS ACTUALLY SENT).')
            p.dismiss()

        content = BoxLayout(orientation='vertical', spacing=dp(10))
        content.add_widget(Label(text='Kick will simulate disconnecting a device. Proceed?'))
        btn_box = BoxLayout(spacing=dp(10))
        btn_yes = Button(text='Yes')
        btn_no = Button(text='No')
        p = Popup(title='Kick (Simulation)', content=content, size_hint=(0.8, 0.4))
        btn_yes.bind(on_release=lambda b: confirm(btn_yes))
        btn_no.bind(on_release=lambda b: p.dismiss())
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        content.add_widget(btn_box)
        p.open()

    def _on_scan(self, *a):
        """زر Scan"""
        if self.engine:
            def _scan():
                self.engine.scan_network(allow_simulation=False)
            threading.Thread(target=_scan, daemon=True).start()

    def _toggle_sniffer(self, *a):
        """تبديل الرصد السلبي"""
        if not self.engine:
            return
        if not self._sniffer_running:
            started = self.engine.start_passive_sniffer(self._on_sniff_packet)
            if started:
                self._sniffer_running = True
                self.btn_monitor.text = 'Stop Monitor'
        else:
            try:
                self.engine.stop_passive_sniffer()
            except Exception:
                pass
            self._sniffer_running = False
            self.btn_monitor.text = 'Monitor'

    def _on_sniff_packet(self, info: dict):
        """معالجة حزمة من الرصد السلبي"""
        try:
            src_mac = info.get('src_mac')
            src_ip = info.get('src_ip')
            vendor = get_vendor_from_mac(src_mac) if src_mac else None
            d = Device(ip=src_ip or '0.0.0.0', mac=src_mac or '00:00:00:00:00:00', vendor=vendor or 'Unknown', x=0.0, y=0.0)
            with getattr(self.engine, '_lock', threading.Lock()):
                exists = False
                for ex in getattr(self.engine, 'devices', []):
                    if ex.mac == d.mac:
                        exists = True
                        ex.ip = d.ip or ex.ip
                        ex.vendor = d.vendor or ex.vendor
                        break
                if not exists:
                    self.engine.devices.append(d)
            Clock.schedule_once(lambda dt: self._update_devices_ui(list(getattr(self.engine, 'devices', []))), 0)
        except Exception:
            pass

    def _kill_switch(self, *a):
        """إيقاف الطوارئ"""
        try:
            if self.engine:
                self.engine.stop_passive_sniffer()
        except Exception:
            pass
        self._show_msg('Kill Switch activated.')

    def _back_action(self, *a):
        self._show_msg('Back navigation (UI-only).')

    def _home_action(self, *a):
        self._show_msg('Home (UI-only).')

    def _show_msg(self, text: str):
        """عرض رسالة منبثقة"""
        content = Label(text=text)
        popup = Popup(title='Info', content=content, size_hint=(0.85, 0.35))
        content.bind(texture_size=content.setter('size'))
        popup.open()

    def _pull_engine(self, dt):
        """جلب الأجهزة من المحرك"""
        if self.engine:
            with getattr(self.engine, '_lock', threading.Lock()):
                devices = list(getattr(self.engine, 'devices', []))
            self.radar.set_devices(devices)

    def _open_monitor(self):
        """فتح شاشة المراقب"""
        content = BoxLayout(orientation='vertical', spacing=dp(8))
        toolbar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_refresh = Button(text='Refresh', size_hint_x=None, width=dp(100))
        btn_delete = Button(text='Delete Selected', size_hint_x=None, width=dp(120))
        btn_export = Button(text='Export CSV', size_hint_x=None, width=dp(100))
        toolbar.add_widget(btn_refresh)
        toolbar.add_widget(btn_delete)
        toolbar.add_widget(btn_export)
        content.add_widget(toolbar)

        scroll_content = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))

        def build_tree():
            scroll_content.clear_widgets()
            if self.engine:
                with getattr(self.engine, '_lock', threading.Lock()):
                    for d in getattr(self.engine, 'devices', []):
                        ip = d.ip or ''
                        mac = d.mac or ''
                        vendor = (getattr(d, 'model', '') or d.vendor or '')
                        scroll_content.add_widget(Label(
                            text=f'{ip} | {mac} | {vendor}',
                            size_hint_y=None,
                            height=dp(24)
                        ))
                        try:
                            reqs = self.engine.get_requests_for_device(mac) if hasattr(self.engine, 'get_requests_for_device') else []
                            for r in reqs[-40:]:
                                scroll_content.add_widget(Label(
                                    text=f"  {r.get('time')} - {r.get('domain')}",
                                    size_hint_y=None,
                                    height=dp(20)
                                ))
                        except Exception:
                            pass
            if len(scroll_content.children) == 0:
                scroll_content.add_widget(Label(text='No devices', size_hint_y=None, height=dp(24)))

        build_tree()

        sv = ScrollView(size_hint=(1, 1))
        sv.add_widget(scroll_content)
        content.add_widget(sv)

        popup = Popup(title='Monitor - Devices & Domains', content=content, size_hint=(0.95, 0.85))

        def do_export():
            try:
                export_path = os.path.join(os.path.dirname(__file__), 'requests_export.csv')
                import csv
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(['mac', 'time', 'domain'])
                    for mac, recs in getattr(self.engine, 'requests_log', {}).items():
                        for r in recs:
                            w.writerow([mac, r.get('time'), r.get('domain')])
                self._show_msg(f'Exported to {export_path}')
            except Exception as e:
                self._show_msg(f'Export Error: {e}')

        btn_refresh.bind(on_release=lambda b: build_tree())
        btn_export.bind(on_release=lambda b: do_export())
        btn_delete.bind(on_release=lambda b: build_tree())  # مبسط - إعادة بناء فقط

        popup.open()


if __name__ == '__main__':
    from network_engine import NetworkEngine
    NexusVisionApp(engine=NetworkEngine()).run()
