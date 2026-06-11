import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from llm_agent import analyze_spike
from env_config import get_supabase_config, has_supabase_admin_key

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Thiếu cấu hình SUPABASE_URL và SUPABASE key trong .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

SPIKE_THRESHOLD = 5  # Ngưỡng bùng nổ: >= 5 phản hồi P2-P5 cùng một khu vực
TRIGGER_SEVERITIES = ["P2", "P3", "P4", "P5"]
SEVERITY_RANK = {severity: rank for rank, severity in enumerate(["P1", "P2", "P3", "P4", "P5"], start=1)}

def detect_spikes(hours: int = 1, max_feedback: int = 1000, max_spikes: int = 3, texts_per_area: int = 20):
    print("[Spike Detector] Đang quét hệ thống để tìm kiếm sự cố bùng nổ...")
    if not has_supabase_admin_key():
        return {
            "spikes_detected": 0,
            "warning": "Missing SUPABASE_SERVICE_ROLE_KEY in root .env. Spike detection may only see public/RLS-visible rows.",
        }

    db = get_supabase()
    
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    # P1 is informational/positive. P2-P5 can create a ticket when an area spikes.
    response = db.table("feedback") \
        .select("id, text, area, severity, topic") \
        .gte("created_at", since) \
        .in_("severity", TRIGGER_SEVERITIES) \
        .order("created_at", desc=True) \
        .limit(max_feedback) \
        .execute()
        
    data = response.data
    if not data:
        print("[Spike Detector] Không có feedback tiêu cực nào gần đây.")
        return {"spikes_detected": 0, "records_scanned": 0}
        
    # Gom nhóm theo khu vực (area)
    area_counts = {}
    area_texts = {}
    area_severities = {}
    
    for row in data:
        area = row.get("area", "Unknown")
        text = row.get("text", "")
        
        if area not in area_counts:
            area_counts[area] = 0
            area_texts[area] = []
            area_severities[area] = []
            
        area_counts[area] += 1
        area_severities[area].append(row.get("severity", "P2"))
        if len(area_texts[area]) < texts_per_area:
            area_texts[area].append(text)
        
    spike_candidates = [
        (area, count)
        for area, count in area_counts.items()
        if count >= SPIKE_THRESHOLD
    ]
    spike_candidates.sort(key=lambda item: item[1], reverse=True)
    selected_spikes = spike_candidates[:max_spikes]

    profiles_res = db.table("profiles").select("id").limit(1).execute()
    mock_user_id = profiles_res.data[0]["id"] if profiles_res.data else None

    alerts_created = 0
    alerts_by_severity = {severity: 0 for severity in TRIGGER_SEVERITIES}

    for area, count in selected_spikes:
        alert_severity = max(
            area_severities[area],
            key=lambda severity: SEVERITY_RANK.get(severity, 0),
        )
        print(f"🚨 PHÁT HIỆN SPIKE: Khu vực {area} có {count} phàn nàn nghiêm trọng!")
            
        print(f"[{area}] Đang gửi dữ liệu cho AI phân tích...")
        alert_data = analyze_spike(area, area_texts[area])

        if mock_user_id:
            alert_payload = {
                "user_id": mock_user_id,
                "title": alert_data.get("title", f"Spike tại {area}"),
                "description": alert_data.get("description", "Không có mô tả chi tiết") + f"\n\n**Action Plan:** {alert_data.get('action', '')}\n**Assigned Team:** {alert_data.get('assigned_team', '')}",
                "severity": alert_severity,
                "area": area,
                "status": "open"
            }

            try:
                db.table("alerts").insert(alert_payload).execute()
                alerts_created += 1
                alerts_by_severity[alert_severity] += 1
                print(f"✅ Đã tạo Alert khẩn cấp cho {area} thành công!")
            except Exception as e:
                print(f"❌ Lỗi khi lưu Alert vào DB: {e}")
        else:
            print("❌ Không có user_id hợp lệ để lưu Alert!")
                
    return {
        "spikes_detected": len(selected_spikes),
        "candidate_spikes": len(spike_candidates),
        "alerts_created": alerts_created,
        "alerts_by_severity": alerts_by_severity,
        "trigger_severities": TRIGGER_SEVERITIES,
        "records_scanned": len(data),
        "max_feedback": max_feedback,
        "max_spikes": max_spikes,
    }

if __name__ == "__main__":
    detect_spikes()
