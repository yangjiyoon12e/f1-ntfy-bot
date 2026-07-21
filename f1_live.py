import requests
import os

def get_live_session():
    try:
        res = requests.get("https://api.openf1.org/v1/sessions?is_active=true")
        sessions = res.json()
        if not sessions:
            res = requests.get("https://api.openf1.org/v1/sessions")
            sessions = res.json()
            return sessions[-1] if sessions else None
        return sessions[0]
    except: return None

def get_latest_flag_status(session_key):
    try:
        res = requests.get(f"https://api.openf1.org/v1/race_control?session_key={session_key}")
        data = res.json()
        if not data: return "🟢 GREEN (정상)"
        latest = data[-1]
        msg = latest.get("message", "").upper()
        flag = latest.get("flag", "")
        if "VIRTUAL SAFETY CAR" in msg: return "🟨 🚨 VSC 발령"
        if "SAFETY CAR" in msg: return "🏎️ 🚨 SAFETY CAR 투입"
        flag_map = {"RED": "🔴 RED FLAG (중단)", "YELLOW": "🟡 YELLOW (주의)", "CHEQUERED": "🏁 FINISH"}
        return flag_map.get(flag, "🟢 GREEN (정상)")
    except: return "데이터 확인 불가"

def main():
    topic = os.getenv("NTFY_TOPIC")
    session = get_live_session()
    if not session: return

    s_key = session['session_key']
    flag = get_latest_flag_status(s_key)
    
    # 순위 가져오기
    pos_res = requests.get(f"https://api.openf1.org/v1/position?session_key={s_key}").json()
    drv_res = requests.get(f"https://api.openf1.org/v1/drivers?session_key={s_key}").json()
    drv_map = {d['driver_number']: d['last_name'] for d in drv_res}
    
    latest_pos = {}
    for p in pos_res: latest_pos[p['driver_number']] = p
    sorted_pos = sorted(latest_pos.values(), key=lambda x: x['position'])[:10]

    msg = f"🚩 상태: {flag}\n\n🏆 Top 10 순위:\n"
    for p in sorted_pos:
        name = drv_map.get(p['driver_number'], f"No.{p['driver_number']}")
        msg += f"{p['position']}위: {name}\n"

    requests.post(f"https://ntfy.sh/{topic}", data=msg.encode('utf-8'),
                  headers={"Title": f"🏎️ F1 {session['location']} Live", "Priority": "default"})

if __name__ == "__main__":
    main()
