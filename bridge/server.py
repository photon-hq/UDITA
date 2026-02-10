#!/usr/bin/env python3
"""Mac bridge: multi-iPhone remote control via WebDriverAgent (WDA)."""

import argparse,base64,json,logging,os,re,socket,subprocess,threading,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime
from pathlib import Path
import requests
from flask import Flask,Response,jsonify,request,send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO,format="[%(asctime)s] %(message)s",datefmt="%H:%M:%S")
log=logging.getLogger("bridge")
app=Flask(__name__)
CORS(app)

# Config from env so any Mac/network works. No hardcoded IP.
IPHONE_IP=None  # set at startup from env IP or --ip; or pick device in dashboard
WDA_PORT=int(os.environ.get("WDA_PORT","8100"))
DW=int(os.environ.get("SCREEN_WIDTH","393"))
DH=int(os.environ.get("SCREEN_HEIGHT","852"))
SID=None
events=[]
ev_lock=threading.Lock()
# Multi-device: list of IPs. Load from DEVICES env; add when user selects/sets IP.
_devices_lock=threading.Lock()
DEVICES=[]  # manual / env
# Continuous scan: background thread updates this list.
SCANNED_DEVICES=[]  # [{"ip":str,"status":"reachable"}, ...]
_scan_lock=threading.Lock()
SCAN_INTERVAL=15  # seconds
SCAN_TIMEOUT=0.8  # per-IP timeout

def ev(t,d=None):
    with ev_lock:
        events.append({"type":t,"ts":datetime.now().isoformat(),**(d or {})})
        if len(events)>2000:events.pop(0)

def wu(ip=None):
    addr=ip or IPHONE_IP
    return f"http://{addr}:{WDA_PORT}" if addr else None

# ── WDA proxy ─────────────────────────────────────────────────────────────────

def w(method,path,body=None,timeout=15,ip=None):
    url=wu(ip)
    if not url:return {"error":"no device selected"}
    try:
        r=requests.request(method,f"{url}{path}",json=body,timeout=timeout)
        return r.json()
    except Exception as e:return {"error":str(e)}

def sid():
    global SID
    if not IPHONE_IP:return None
    if SID:
        r=w("GET",f"/session/{SID}/window/size",timeout=3)
        if (r.get("value") or {}).get("error")=="invalid session id":
            log.info("Session expired"); SID=None
    if not SID:
        r=w("POST","/session",{"capabilities":{}})
        SID=r.get("sessionId") or (r.get("value") or {}).get("sessionId")
        if SID:log.info(f"Session: {SID}")
    return SID

def wda_ready():
    if not IPHONE_IP:return False
    try:return (w("GET","/status",timeout=3).get("value") or {}).get("ready",False)
    except:return False

def wda_size():
    s=sid()
    if not s:return DW,DH
    v=(w("GET",f"/session/{s}/window/size") or {}).get("value",{})
    return v.get("width",DW),v.get("height",DH)

# ── Generic WDA passthrough ──────────────────────────────────────────────────
# Any WDA endpoint can be called via /wda/* passthrough

@app.route("/wda/<path:path>",methods=["GET","POST","PUT","DELETE"])
def wda_passthrough(path):
    """Pass any request directly to WDA. Session ID auto-injected."""
    s=sid()
    body=request.get_json(force=True,silent=True)
    # If path contains {sessionId}, replace it
    full_path=f"/{path}"
    if s and "{sessionId}" in full_path:
        full_path=full_path.replace("{sessionId}",s)
    r=w(request.method,full_path,body)
    return jsonify(r)

# ── Convenience endpoints (wrap WDA with session management) ─────────────────

@app.route("/api/ping")
def r_ping():return jsonify({"status":"ok"})

@app.route("/api/status")
def r_status():
    wo=wda_ready()
    ww,hh=DW,DH
    if wo:
        try:ww,hh=wda_size()
        except:pass
    info={}
    if wo:
        r=w("GET","/status",timeout=3)
        info=r.get("value",{})
    return jsonify({"wda":"connected" if wo else "not reachable","wda_url":wu() or "",
        "iphone_ip":IPHONE_IP or "","screen":{"width":ww,"height":hh},"session":SID,
        "device_info":info})

def _ensure_device(ip):
    with _devices_lock:
        if ip and ip not in DEVICES:
            DEVICES.append(ip)

def _get_local_subnet():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip=s.getsockname()[0]
        s.close()
        return ".".join(ip.split(".")[:-1])
    except Exception:
        return "192.168.0"

def _check_wda(ip,timeout=SCAN_TIMEOUT):
    try:
        r=requests.get(f"http://{ip}:{WDA_PORT}/status",timeout=timeout)
        return (r.json().get("value") or {}).get("ready",False)
    except Exception:
        return False

def _scan_subnet():
    subnet=_get_local_subnet()
    ips=[f"{subnet}.{i}" for i in range(1,255)]
    found=[]
    with ThreadPoolExecutor(max_workers=50) as ex:
        def check(ip):
            return (ip,_check_wda(ip))
        for ip,ok in ex.map(check,ips):
            if ok:found.append(ip)
    with _scan_lock:
        global SCANNED_DEVICES
        SCANNED_DEVICES=[{"ip":ip,"status":"reachable"} for ip in found]
    if found:log.info(f"Scan found: {found}")

def _scanner_loop():
    while True:
        try:_scan_subnet()
        except Exception as e:log.warning(f"Scan error: {e}")
        time.sleep(SCAN_INTERVAL)

@app.route("/api/scan-now",methods=["POST"])
def r_scan_now():
    """Run one subnet scan in background; devices list updates in a few seconds."""
    def _run():
        try:_scan_subnet()
        except Exception as e:log.warning(f"Scan-now error: {e}")
    threading.Thread(target=_run,daemon=True).start()
    return jsonify({"status":"ok","message":"Scan started; refresh devices in a few seconds"})

@app.route("/api/devices")
def r_devices():
    """List devices: scanned (continuous) + manual IPs. Click one to select."""
    with _scan_lock:
        scanned=list(SCANNED_DEVICES)
    scanned_ips={d["ip"] for d in scanned}
    with _devices_lock:
        manual=[ip for ip in DEVICES if ip not in scanned_ips]
    out=list(scanned)
    for ip in manual:
        out.append({"ip":ip,"status":"reachable" if _check_wda(ip,timeout=2) else "not reachable"})
    if not out and IPHONE_IP:
        out=[{"ip":IPHONE_IP,"status":"reachable" if _check_wda(IPHONE_IP,timeout=2) else "not reachable"}]
    return jsonify({"devices":out,"current":IPHONE_IP})

@app.route("/api/device/select",methods=["POST"])
def r_device_select():
    global IPHONE_IP,SID
    d=request.get_json(force=True,silent=True) or {}
    ip=(d.get("ip") or "").strip()
    if not ip:return jsonify({"error":"Missing ip"}),400
    IPHONE_IP=ip;SID=None
    _ensure_device(ip)
    log.info(f"Selected device: {ip}")
    return jsonify({"status":"ok","ip":IPHONE_IP})

@app.route("/api/set-ip",methods=["POST"])
def r_setip():
    global IPHONE_IP,SID
    d=request.get_json(force=True,silent=True) or {}
    raw=d.get("ip",IPHONE_IP or "")
    IPHONE_IP=(raw.strip() if raw else None);SID=None
    if IPHONE_IP:_ensure_device(IPHONE_IP)
    return jsonify({"status":"ok","ip":IPHONE_IP})

# Touch
@app.route("/api/tap",methods=["POST"])
def r_tap():
    d=request.get_json(force=True,silent=True) or {}
    x,y=d.get("x"),d.get("y")
    if x is None or y is None:return jsonify({"error":"Missing x,y"}),400
    s=sid()
    r=w("POST",f"/session/{s}/wda/tap",{"x":x,"y":y}) if s else {"error":"no session"}
    ev("tap",{"x":x,"y":y});return jsonify({"status":"ok","wda":r})

@app.route("/api/double-tap",methods=["POST"])
def r_dtap():
    d=request.get_json(force=True,silent=True) or {}
    x,y=d.get("x"),d.get("y")
    if x is None or y is None:return jsonify({"error":"Missing x,y"}),400
    s=sid()
    r=w("POST",f"/session/{s}/wda/doubleTap",{"x":x,"y":y}) if s else {"error":"no session"}
    ev("double_tap",{"x":x,"y":y});return jsonify({"status":"ok","wda":r})

@app.route("/api/long-press",methods=["POST"])
def r_lp():
    d=request.get_json(force=True,silent=True) or {}
    x,y,dur=d.get("x"),d.get("y"),d.get("duration",1.5)
    if x is None or y is None:return jsonify({"error":"Missing x,y"}),400
    s=sid()
    r=w("POST",f"/session/{s}/wda/touchAndHold",{"x":x,"y":y,"duration":dur}) if s else {"error":"no session"}
    ev("long_press",{"x":x,"y":y});return jsonify({"status":"ok","wda":r})

@app.route("/api/swipe",methods=["POST"])
def r_swipe():
    d=request.get_json(force=True,silent=True) or {}
    f,t=d.get("from",{}),d.get("to",{})
    x1,y1,x2,y2=f.get("x"),f.get("y"),t.get("x"),t.get("y")
    if None in (x1,y1,x2,y2):return jsonify({"error":"Missing from/to"}),400
    s=sid()
    # Use W3C actions for swipe (most reliable)
    dur=d.get("duration",0.5)
    dur_ms=int(dur*1000) if isinstance(dur,float) and dur<10 else int(dur) if isinstance(dur,(int,float)) else 500
    r=w("POST",f"/session/{s}/actions",{"actions":[{"type":"pointer","id":"f1","parameters":{"pointerType":"touch"},"actions":[
        {"type":"pointerMove","duration":0,"x":int(x1),"y":int(y1)},
        {"type":"pointerDown","button":0},
        {"type":"pointerMove","duration":dur_ms,"x":int(x2),"y":int(y2)},
        {"type":"pointerUp","button":0}
    ]}]}) if s else {"error":"no session"}
    ev("swipe",{"from":f,"to":t});return jsonify({"status":"ok","wda":r})

@app.route("/api/drag",methods=["POST"])
def r_drag():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/dragfromtoforduration",{
        "fromX":d.get("fromX",d.get("from",{}).get("x",0)),
        "fromY":d.get("fromY",d.get("from",{}).get("y",0)),
        "toX":d.get("toX",d.get("to",{}).get("x",0)),
        "toY":d.get("toY",d.get("to",{}).get("y",0)),
        "duration":d.get("duration",1)
    }) if s else {"error":"no session"}
    ev("drag",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/pinch",methods=["POST"])
def r_pinch():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/pinch",{"scale":d.get("scale",0.5),"velocity":d.get("velocity",-2),"x":d.get("x",DW//2),"y":d.get("y",DH//2)}) if s else {"error":"no session"}
    ev("pinch",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/rotate",methods=["POST"])
def r_rotate():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/rotate",d) if s else {"error":"no session"}
    ev("rotate",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/scroll",methods=["POST"])
def r_scroll():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/scroll",d) if s else {"error":"no session"}
    ev("scroll",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/two-finger-tap",methods=["POST"])
def r_2ft():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/twoFingerTap",{"x":d.get("x",DW//2),"y":d.get("y",DH//2)}) if s else {"error":"no session"}
    ev("two_finger_tap",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/multi-tap",methods=["POST"])
def r_mt():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/tapWithNumberOfTaps",{"x":d.get("x",DW//2),"y":d.get("y",DH//2),"numberOfTaps":d.get("taps",2),"numberOfTouches":d.get("touches",1)}) if s else {"error":"no session"}
    ev("multi_tap",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/force-touch",methods=["POST"])
def r_ft():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/wda/forceTouch",{"x":d.get("x"),"y":d.get("y"),"pressure":d.get("pressure",1),"duration":d.get("duration",1)}) if s else {"error":"no session"}
    ev("force_touch",d);return jsonify({"status":"ok","wda":r})

# W3C Actions (raw)
@app.route("/api/actions",methods=["POST"])
def r_actions():
    d=request.get_json(force=True,silent=True) or {}
    s=sid()
    r=w("POST",f"/session/{s}/actions",d) if s else {"error":"no session"}
    ev("actions");return jsonify({"status":"ok","wda":r})

# Device
@app.route("/api/home",methods=["POST"])
def r_home():
    s=sid();r=w("POST",f"/session/{s}/wda/pressButton",{"name":"home"}) if s else w("POST","/wda/homescreen")
    ev("home");return jsonify({"status":"ok","wda":r})

@app.route("/api/homescreen",methods=["POST"])
def r_hs():
    r=w("POST","/wda/homescreen");ev("homescreen");return jsonify({"status":"ok","wda":r})

@app.route("/api/press-button",methods=["POST"])
def r_btn():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/pressButton",{"name":d.get("name","home")}) if s else {"error":"no session"}
    ev("press_button",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/lock",methods=["POST"])
def r_lock():
    s=sid();r=w("POST",f"/session/{s}/wda/lock") if s else w("POST","/wda/lock")
    ev("lock");return jsonify({"status":"ok","wda":r})

@app.route("/api/unlock",methods=["POST"])
def r_unlock():
    s=sid();r=w("POST",f"/session/{s}/wda/unlock") if s else w("POST","/wda/unlock")
    ev("unlock");return jsonify({"status":"ok","wda":r})

@app.route("/api/locked")
def r_locked():
    s=sid();r=w("GET",f"/session/{s}/wda/locked") if s else w("GET","/wda/locked")
    return jsonify(r)

@app.route("/api/orientation",methods=["GET"])
def r_orient():
    s=sid();return jsonify(w("GET",f"/session/{s}/orientation") if s else {})

@app.route("/api/orientation",methods=["POST"])
def r_set_orient():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/orientation",d) if s else {})

@app.route("/api/rotation",methods=["GET"])
def r_rot():
    s=sid();return jsonify(w("GET",f"/session/{s}/rotation") if s else {})

@app.route("/api/rotation",methods=["POST"])
def r_set_rot():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/rotation",d) if s else {})

@app.route("/api/battery")
def r_batt():
    """Battery info from WDA. level is 0.0–1.0 (UIDevice.batteryLevel); we add percentage 0–100."""
    s=sid()
    if not s:
        return jsonify({"error":"no session"})
    raw=w("GET",f"/session/{s}/wda/batteryInfo")
    if not isinstance(raw,dict):
        return jsonify(raw if raw else {})
    if raw.get("error"):
        return jsonify(raw)
    # WDA returns {"sessionId":"...", "value": {"level": 0.0–1.0, "state": 1|2|3|4}}
    inner=raw.get("value")
    if inner is None:
        inner=raw
    level=inner.get("level") if isinstance(inner,dict) else None
    try:
        level_f=float(level)
    except (TypeError,ValueError):
        level_f=None
    if level_f is not None:
        pct=int(round(level_f*100 if level_f<=1 else level_f))
        pct=min(100,max(0,pct))
    else:
        pct=None
    # Build new response so percentage is always present when we have level
    out={"sessionId":raw.get("sessionId")}
    if isinstance(inner,dict):
        out["value"]=dict(inner)
        if pct is not None:
            out["value"]["percentage"]=pct
            out["percentage"]=pct
    else:
        out["value"]=inner
        if pct is not None:
            out["percentage"]=pct
    return jsonify(out)

@app.route("/api/device-info")
def r_devinfo():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/device/info") if s else w("GET","/wda/device/info"))

@app.route("/api/active-app")
def r_activeapp():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/activeAppInfo") if s else w("GET","/wda/activeAppInfo"))

@app.route("/api/screen-info")
def r_screeninfo():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/screen") if s else w("GET","/wda/screen"))

# Keyboard
@app.route("/api/type",methods=["POST"])
def r_type():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/keys",{"value":list(d.get("text",""))}) if s else {"error":"no session"}
    ev("type",{"text":d.get("text","")});return jsonify({"status":"ok","wda":r})

@app.route("/api/dismiss-keyboard",methods=["POST"])
def r_dismisskb():
    s=sid();r=w("POST",f"/session/{s}/wda/keyboard/dismiss") if s else {"error":"no session"}
    ev("dismiss_keyboard");return jsonify({"status":"ok","wda":r})

# Clipboard
@app.route("/api/clipboard/get",methods=["POST"])
def r_getclip():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/getPasteboard",d) if s else {})

@app.route("/api/clipboard/set",methods=["POST"])
def r_setclip():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/setPasteboard",d) if s else {})

# Alert
@app.route("/api/alert")
def r_alert():
    s=sid();return jsonify(w("GET",f"/session/{s}/alert/text") if s else {})

@app.route("/api/alert/accept",methods=["POST"])
def r_alert_ok():
    s=sid();r=w("POST",f"/session/{s}/alert/accept") if s else {"error":"no session"}
    ev("alert_accept");return jsonify({"status":"ok","wda":r})

@app.route("/api/alert/dismiss",methods=["POST"])
def r_alert_no():
    s=sid();r=w("POST",f"/session/{s}/alert/dismiss") if s else {"error":"no session"}
    ev("alert_dismiss");return jsonify({"status":"ok","wda":r})

@app.route("/api/alert/buttons")
def r_alert_btns():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/alert/buttons") if s else {})

# Apps
@app.route("/api/launch",methods=["POST"])
def r_launch():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/apps/launch",{"bundleId":d.get("bundle_id"),"arguments":d.get("args",[]),"environment":d.get("env",{})}) if s else {"error":"no session"}
    ev("launch",{"bundle_id":d.get("bundle_id")});return jsonify({"status":"ok","wda":r})

@app.route("/api/activate",methods=["POST"])
def r_activate():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/apps/activate",{"bundleId":d.get("bundle_id")}) if s else {"error":"no session"}
    ev("activate",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/terminate",methods=["POST"])
def r_terminate():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/apps/terminate",{"bundleId":d.get("bundle_id")}) if s else {"error":"no session"}
    ev("terminate",d);return jsonify({"status":"ok","wda":r})

@app.route("/api/app-state",methods=["POST"])
def r_appstate():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/apps/state",{"bundleId":d.get("bundle_id")}) if s else {})

@app.route("/api/app-list")
def r_applist():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/apps/list") if s else {})

@app.route("/api/deactivate-app",methods=["POST"])
def r_deactivate():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/deactivateApp",d) if s else {})

@app.route("/api/open-url",methods=["POST"])
def r_openurl():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/url",{"url":d.get("url","")}) if s else {})

# Elements
@app.route("/api/click",methods=["POST"])
def r_click():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    if not s:return jsonify({"error":"no session"})
    r=w("POST",f"/session/{s}/element",{"using":"name","value":d.get("name","")})
    eid=(r.get("value") or {}).get("ELEMENT")
    if not eid:return jsonify({"error":f"'{d.get('name')}' not found"})
    cr=w("POST",f"/session/{s}/element/{eid}/click")
    ev("click",{"name":d.get("name")});return jsonify({"status":"ok","element":d.get("name"),"wda":cr})

@app.route("/api/find",methods=["POST"])
def r_find():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/elements",{"using":d.get("using","name"),"value":d.get("value","")}) if s else {})

@app.route("/api/active-element")
def r_active_el():
    s=sid();return jsonify(w("GET",f"/session/{s}/element/active") if s else {})

# Call control
@app.route("/api/answer-call",methods=["POST"])
def r_answer():
    s=sid()
    if not s:return jsonify({"error":"no session"})
    for n in ["Accept","Answer","Answer video call","Answer audio call"]:
        r=w("POST",f"/session/{s}/element",{"using":"name","value":n})
        eid=(r.get("value") or {}).get("ELEMENT")
        if eid:
            w("POST",f"/session/{s}/element/{eid}/click")
            ev("answer_call",{"element":n});return jsonify({"status":"ok","element":n})
    return jsonify({"status":"no_call_button"})

@app.route("/api/decline-call",methods=["POST"])
def r_decline():
    s=sid()
    if not s:return jsonify({"error":"no session"})
    for n in ["Decline","Reject","End"]:
        r=w("POST",f"/session/{s}/element",{"using":"name","value":n})
        eid=(r.get("value") or {}).get("ELEMENT")
        if eid:
            w("POST",f"/session/{s}/element/{eid}/click")
            ev("decline_call",{"element":n});return jsonify({"status":"ok","element":n})
    return jsonify({"status":"no_decline_button"})

# Screenshot
@app.route("/api/screenshot")
def r_ss():
    s=sid()
    r=w("GET",f"/session/{s}/screenshot") if s else w("GET","/screenshot")
    b64=r.get("value","")
    if b64:return jsonify({"status":"ok","base64":b64})
    return jsonify({"error":"failed"}),500

@app.route("/api/screenshot.png")
def r_ss_png():
    s=sid()
    r=w("GET",f"/session/{s}/screenshot") if s else w("GET","/screenshot")
    b64=r.get("value","")
    if b64:return Response(base64.b64decode(b64),mimetype="image/png")
    return "Failed",500

# Source/elements
@app.route("/api/source")
def r_src():
    s=sid();return jsonify(w("GET",f"/session/{s}/source") if s else w("GET","/source"))

@app.route("/api/accessible-source")
def r_asrc():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/accessibleSource") if s else {})

@app.route("/api/elements")
def r_els():
    s=sid()
    if not s:return jsonify({"elements":[],"count":0})
    xml=(w("GET",f"/session/{s}/source") or {}).get("value","")
    vis=[]
    for m in re.finditer(r'<(\w+)\s+([^>]+?)/?>', xml):
        a=dict(re.findall(r'(\w+)="([^"]*)"',m.group(2)))
        n=a.get("name") or a.get("label") or ""
        x,y,ww,h=int(a.get("x","0")),int(a.get("y","0")),int(a.get("width","0")),int(a.get("height","0"))
        if ww>0 and h>0 and n:
            vis.append({"type":(a.get("type","")).replace("XCUIElementType",""),"name":n,"x":x,"y":y,"w":ww,"h":h,"cx":x+ww//2,"cy":y+h//2})
    return jsonify({"elements":vis[:100],"count":len(vis)})

# Siri
@app.route("/api/siri",methods=["POST"])
def r_siri():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/siri/activate",{"text":d.get("text","")}) if s else {"error":"no session"}
    ev("siri",d);return jsonify({"status":"ok","wda":r})

# Appearance
@app.route("/api/appearance",methods=["POST"])
def r_appearance():
    d=request.get_json(force=True,silent=True) or {}
    return jsonify(w("POST","/wda/device/appearance",d))

# Location
@app.route("/api/location")
def r_loc():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/device/location") if s else {})

@app.route("/api/simulated-location",methods=["GET"])
def r_simloc():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/simulatedLocation") if s else {})

@app.route("/api/simulated-location",methods=["POST"])
def r_set_simloc():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/simulatedLocation",d) if s else {})

@app.route("/api/simulated-location",methods=["DELETE"])
def r_del_simloc():
    s=sid();return jsonify(w("DELETE",f"/session/{s}/wda/simulatedLocation") if s else {})

# Video
@app.route("/api/video/start",methods=["POST"])
def r_vid_start():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/video/start",d) if s else w("POST","/wda/video/start",d))

@app.route("/api/video/stop",methods=["POST"])
def r_vid_stop():
    s=sid();return jsonify(w("POST",f"/session/{s}/wda/video/stop") if s else w("POST","/wda/video/stop"))

@app.route("/api/video")
def r_vid_get():
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/video") if s else w("GET","/wda/video"))

# Picker wheel
@app.route("/api/picker-select",methods=["POST"])
def r_picker():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    eid=d.get("element_id","")
    return jsonify(w("POST",f"/session/{s}/wda/pickerwheel/{eid}/select",d) if s else {})

# Settings
@app.route("/api/settings",methods=["GET"])
def r_settings():
    s=sid();return jsonify(w("GET",f"/session/{s}/appium/settings") if s else {})

@app.route("/api/settings",methods=["POST"])
def r_set_settings():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/appium/settings",d) if s else {})

# Accessibility audit
@app.route("/api/accessibility-audit",methods=["POST"])
def r_axaudit():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/performAccessibilityAudit",d) if s else {})

# Health check
@app.route("/api/healthcheck")
def r_health():
    return jsonify(w("GET","/wda/healthcheck"))

# Notifications
@app.route("/api/expect-notification",methods=["POST"])
def r_notif():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/expectNotification",d) if s else {})

# ── Missing endpoints (complete WDA coverage) ────────────────────────────────

# Alert text set
@app.route("/api/alert/text",methods=["POST"])
def r_alert_text():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/alert/text",d) if s else {})

# Touch ID
@app.route("/api/touch-id",methods=["POST"])
def r_touchid():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    r=w("POST",f"/session/{s}/wda/touch_id",d) if s else {"error":"no session"}
    ev("touch_id",d);return jsonify({"status":"ok","wda":r})

# Launch unattached
@app.route("/api/launch-unattached",methods=["POST"])
def r_launch_un():
    d=request.get_json(force=True,silent=True) or {}
    return jsonify(w("POST","/wda/apps/launchUnattached",d))

# Reset app auth
@app.route("/api/reset-app-auth",methods=["POST"])
def r_resetauth():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/resetAppAuth",d) if s else {})

# Timeouts
@app.route("/api/timeouts",methods=["POST"])
def r_timeouts():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/timeouts",d) if s else {})

# Press and drag with velocity
@app.route("/api/press-drag-velocity",methods=["POST"])
def r_pdv():
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/pressAndDragWithVelocity",d) if s else {})

# Window rect
@app.route("/api/window-rect")
def r_winrect():
    s=sid();return jsonify(w("GET",f"/session/{s}/window/rect") if s else {})

# ── Element operations (by UUID) ─────────────────────────────────────────────

@app.route("/api/element/<eid>/enabled")
def r_el_enabled(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/enabled") if s else {})

@app.route("/api/element/<eid>/rect")
def r_el_rect(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/rect") if s else {})

@app.route("/api/element/<eid>/attribute/<name>")
def r_el_attr(eid,name):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/attribute/{name}") if s else {})

@app.route("/api/element/<eid>/text")
def r_el_text(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/text") if s else {})

@app.route("/api/element/<eid>/displayed")
def r_el_disp(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/displayed") if s else {})

@app.route("/api/element/<eid>/selected")
def r_el_sel(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/selected") if s else {})

@app.route("/api/element/<eid>/name")
def r_el_name(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/element/{eid}/name") if s else {})

@app.route("/api/element/<eid>/value",methods=["POST"])
def r_el_setval(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/element/{eid}/value",d) if s else {})

@app.route("/api/element/<eid>/click",methods=["POST"])
def r_el_click(eid):
    s=sid()
    r=w("POST",f"/session/{s}/element/{eid}/click") if s else {"error":"no session"}
    ev("element_click",{"eid":eid});return jsonify({"status":"ok","wda":r})

@app.route("/api/element/<eid>/clear",methods=["POST"])
def r_el_clear(eid):
    s=sid();return jsonify(w("POST",f"/session/{s}/element/{eid}/clear") if s else {})

@app.route("/api/element/<eid>/screenshot")
def r_el_ss(eid):
    s=sid()
    r=w("GET",f"/session/{s}/element/{eid}/screenshot") if s else {}
    b64=r.get("value","")
    if b64:return Response(base64.b64decode(b64),mimetype="image/png")
    return jsonify(r)

@app.route("/api/element/<eid>/accessible")
def r_el_ax(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/element/{eid}/accessible") if s else {})

@app.route("/api/element/<eid>/accessibility-container")
def r_el_axc(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/element/{eid}/accessibilityContainer") if s else {})

@app.route("/api/element/<eid>/visible-cells")
def r_el_cells(eid):
    s=sid();return jsonify(w("GET",f"/session/{s}/wda/element/{eid}/getVisibleCells") if s else {})

@app.route("/api/element/<eid>/scroll-to",methods=["POST"])
def r_el_scrollto(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/scrollTo",d) if s else {})

@app.route("/api/element/<eid>/swipe",methods=["POST"])
def r_el_swipe(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/swipe",d) if s else {})

@app.route("/api/element/<eid>/pinch",methods=["POST"])
def r_el_pinch(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/pinch",d) if s else {})

@app.route("/api/element/<eid>/tap",methods=["POST"])
def r_el_tap(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/tap",d) if s else {})

@app.route("/api/element/<eid>/double-tap",methods=["POST"])
def r_el_dtap(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/doubleTap",d) if s else {})

@app.route("/api/element/<eid>/two-finger-tap",methods=["POST"])
def r_el_2ft(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/twoFingerTap",d) if s else {})

@app.route("/api/element/<eid>/touch-and-hold",methods=["POST"])
def r_el_tah(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/touchAndHold",d) if s else {})

@app.route("/api/element/<eid>/force-touch",methods=["POST"])
def r_el_ft(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/forceTouch",d) if s else {})

@app.route("/api/element/<eid>/rotate",methods=["POST"])
def r_el_rot(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/rotate",d) if s else {})

@app.route("/api/element/<eid>/scroll",methods=["POST"])
def r_el_scroll(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/scroll",d) if s else {})

@app.route("/api/element/<eid>/drag",methods=["POST"])
def r_el_drag(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/dragfromtoforduration",d) if s else {})

@app.route("/api/element/<eid>/press-drag-velocity",methods=["POST"])
def r_el_pdv(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/pressAndDragWithVelocity",d) if s else {})

@app.route("/api/element/<eid>/keyboard-input",methods=["POST"])
def r_el_kbinput(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/keyboardInput",d) if s else {})

@app.route("/api/element/<eid>/multi-tap",methods=["POST"])
def r_el_multitap(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/wda/element/{eid}/tapWithNumberOfTaps",d) if s else {})

# Sub-element finding
@app.route("/api/element/<eid>/element",methods=["POST"])
def r_el_find(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/element/{eid}/element",d) if s else {})

@app.route("/api/element/<eid>/elements",methods=["POST"])
def r_el_finds(eid):
    d=request.get_json(force=True,silent=True) or {};s=sid()
    return jsonify(w("POST",f"/session/{s}/element/{eid}/elements",d) if s else {})

# Events
@app.route("/api/events")
def r_ev_list():
    with ev_lock:return jsonify({"events":list(events[-200:]),"count":len(events)})

@app.route("/api/events/clear",methods=["POST"])
def r_evc():
    with ev_lock:events.clear()
    return jsonify({"status":"ok"})

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return Response(DASHBOARD,mimetype="text/html")

DASHBOARD=open(os.path.join(os.path.dirname(__file__),"dashboard.html")).read() if os.path.exists(os.path.join(os.path.dirname(__file__),"dashboard.html")) else "<h1>Dashboard not found</h1>"

if __name__=="__main__":
    pa=argparse.ArgumentParser()
    pa.add_argument("--ip",default=None,help="Default device IP (or set env IP)")
    pa.add_argument("--port",type=int,default=int(os.environ.get("PORT","5050")),help="Bridge port (default 5050, or env PORT)")
    a=pa.parse_args()
    IPHONE_IP=(os.environ.get("IP","").strip() or None)
    if a.ip:IPHONE_IP=a.ip
    env_devices=[x.strip() for x in os.environ.get("DEVICES","").split(",") if x.strip()]
    if env_devices:
        DEVICES=env_devices
        if IPHONE_IP and IPHONE_IP not in DEVICES:
            DEVICES.insert(0,IPHONE_IP)
    else:
        DEVICES=[IPHONE_IP] if IPHONE_IP else []

    log.info("="*50)
    log.info("UDITA")
    log.info("="*50)
    log.info(f"Devices (manual): {DEVICES}")
    # Start continuous subnet scan (WDA on :8100)
    t=threading.Thread(target=_scanner_loop,daemon=True)
    t.start()
    log.info("Network scan running (every %ss)"%SCAN_INTERVAL)
    if wda_ready():
        log.info("WDA: CONNECTED")
        try:
            r=w("GET","/status",timeout=3)
            ip=(r.get("value") or {}).get("ios",{}).get("ip")
            if ip:IPHONE_IP=ip
        except:pass
        DW,DH=wda_size();log.info(f"Screen: {DW}x{DH}");sid()
    else:
        log.warning("WDA not reachable")
    log.info(f"\nDashboard: http://localhost:{a.port}\n")

    # Reload dashboard on each request (for dev)
    @app.before_request
    def reload_dash():
        global DASHBOARD
        dp=os.path.join(os.path.dirname(__file__),"dashboard.html")
        if os.path.exists(dp):DASHBOARD=open(dp).read()

    app.run(host="0.0.0.0",port=a.port,debug=False)
