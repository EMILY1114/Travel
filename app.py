import streamlit as st
import folium
from streamlit_folium import st_folium
import math
from datetime import datetime
import urllib.parse

# ==========================================
# 1. 網頁初始配置與手機版 UI 視覺優化
# ==========================================
st.set_page_config(
    page_title="2026 墨爾本 9 日旅程地圖",
    layout="centered",  # 使用 centered 更適合手機直式螢幕閱讀
    initial_sidebar_state="collapsed",
    page_icon="🐨"
)

# 注入 CSS 樣式：移除 Streamlit 預設過寬的邊距，並美化元件外觀
st.markdown("""
    <style>
    /* 調整主要區塊的邊距，讓手機版畫面極大化 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }
    /* 讓地圖的 iframe 圓角化並填滿寬度 */
    iframe {
        width: 100% !important;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(21, 43, 51, 0.12);
    }
    /* 美化單選下拉選單 */
    .stSelectbox label {
        font-weight: 700;
        color: #1f4e56;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🐨 2026 墨爾本 9 日旅程互動地圖")
st.caption("✨ 專屬手機導航面板｜整合大洋路自駕、蒸汽火車與市區深度遊")

# ==========================================
# 2. 行程核心資料庫 (完整修正冒號與引號問題)
# ==========================================
days_data = [
    {
        "name": "Day 1｜9/19(六) 抵達墨爾本",
        "color": "#0f766e",
        "routeFactor": 1.25,
        "avgSpeed": 35,
        "category": "city",
        "transport": "機場巴士進市區",
        "stay": "住墨爾本市區",
        "note": "抵達後搭 SkyBus 到 Southern Cross，再進市區飯店辦理入住。",
        "depart": "依航班抵達時間",
        "duration": "半日移動＋入住",
        "points": [
            { "name": "墨爾本機場 Melbourne Airport", "lat": -37.6690, "lng": 144.8410 },
            { "name": "SkyBus 南十字星車站 Southern Cross", "lat": -37.8183, "lng": 144.9525 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 2｜9/20(日) City Walk",
        "color": "#2563eb",
        "routeFactor": 1.18,
        "avgSpeed": 22,
        "category": "city",
        "transport": "步行＋免費電車",
        "stay": "住墨爾本市區",
        "note": "以市中心散步為主，串連市場、教堂、圖書館與市集。",
        "depart": "09:00",
        "duration": "約 8-10 小時",
        "points": [
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 },
            { "name": "維多利亞女王市場 Queen Victoria Market", "lat": -37.8076, "lng": 144.9568 },
            { "name": "聖派翠克教堂 St Patrick's Cathedral", "lat": -37.8098, "lng": 144.9763 },
            { "name": "維多利亞州立圖書館 State Library Victoria", "lat": -37.8097, "lng": 144.9653 },
            { "name": "南墨爾本市場 South Melbourne Market", "lat": -37.8318, "lng": 144.9580 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 3｜9/21(一) 大洋路",
        "color": "#ea580c",
        "routeFactor": 1.42,
        "avgSpeed": 68,
        "category": "drive",
        "transport": "租車自駕",
        "stay": "住 Port Campbell",
        "note": "沿大洋路一路往西，晚上直接住坎貝爾港，避免當天折返墨爾本。",
        "depart": "07:30",
        "duration": "約 11-12 小時",
        "points": [
            { "name": "墨爾本租車出發", "lat": -37.8136, "lng": 144.9631 },
            { "name": "吉朗 Geelong", "lat": -38.1499, "lng": 144.3617 },
            { "name": "小紅帽燈塔 Split Point Lighthouse", "lat": -38.4707, "lng": 144.1062 },
            { "name": "洛恩小鎮 Lorne", "lat": -38.5426, "lng": 143.9730 },
            { "name": "阿波羅灣 Apollo Bay", "lat": -38.7548, "lng": 143.6686 },
            { "name": "十二門徒 Twelve Apostles", "lat": -38.6656, "lng": 143.1050 },
            { "name": "坎貝爾港 Port Campbell", "lat": -38.6192, "lng": 142.9958 }
        ]
    },
    {
        "name": "Day 4｜9/22(二) Port Campbell → Werribee → City Walk",
        "color": "#7c3aed",
        "routeFactor": 1.35,
        "avgSpeed": 76,
        "category": "drive",
        "transport": "租車回程＋市區步行",
        "stay": "住墨爾本市區",
        "note": "從坎貝爾港開回墨爾本，先到 Werribee，再回市區還車與簡單 city walk。",
        "depart": "08:00",
        "duration": "約 9-10 小時",
        "points": [
            { "name": "坎貝爾港 Port Campbell", "lat": -38.6192, "lng": 142.9958 },
            { "name": "威勒比野生動物園 Werribee Open Range Zoo", "lat": -37.9158, "lng": 144.6688 },
            { "name": "墨爾本還車", "lat": -37.8136, "lng": 144.9631 },
            { "name": "弗林德斯街車站 Flinders Street Station", "lat": -37.8183, "lng": 144.9671 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 5｜9/23(三) 蒸汽火車＋動物＋企鵝島",
        "color": "#0ea5e9",
        "routeFactor": 1.32,
        "avgSpeed": 50,
        "category": "drive",
        "transport": "建議租車或一日團",
        "stay": "住墨爾本市區",
        "note": "順路版動線改為蒸汽火車 → Maru → 企鵝島，回程視時間停彩虹小屋再回市區。",
        "depart": "07:00",
        "duration": "約 12-13 小時",
        "points": [
            { "name": "墨爾本市區出發", "lat": -37.8136, "lng": 144.9631 },
            { "name": "貝爾格雷夫蒸汽火車 Belgrave Puffing Billy", "lat": -37.9100, "lng": 145.3530 },
            { "name": "Maru 無尾熊動物園 Maru Koala and Animal Park", "lat": -38.4384, "lng": 145.4025 },
            { "name": "菲利浦島企鵝歸巢 Phillip Island Penguin Parade", "lat": -38.5122, "lng": 145.1456 },
            { "name": "布萊頓彩虹小屋 Brighton Bathing Boxes", "lat": -37.9187, "lng": 144.9861 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 6｜9/24(四) Bendigo",
        "color": "#16a34a",
        "routeFactor": 1.25,
        "avgSpeed": 78,
        "category": "city",
        "transport": "火車／大眾運輸",
        "stay": "住墨爾本市區",
        "note": "Bendigo 改成搭大眾運輸單日往返，建議從 Southern Cross 搭 V/Line 前往。",
        "depart": "08:30",
        "duration": "約 9 小時",
        "points": [
            { "name": "墨爾本市區出發", "lat": -37.8136, "lng": 144.9631 },
            { "name": "南十字星車站 Southern Cross", "lat": -37.8183, "lng": 144.9525 },
            { "name": "本迪戈 Bendigo", "lat": -36.7570, "lng": 144.2794 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 7｜9/25(五) 皇家秀",
        "color": "#dc2626",
        "routeFactor": 1.16,
        "avgSpeed": 30,
        "category": "city",
        "transport": "電車／火車",
        "stay": "住墨爾本市區",
        "note": "以 Melbourne Royal Show 為主，建議預留整天並避開下班人潮離場。",
        "depart": "10:00",
        "duration": "約 8-9 小時",
        "points": [
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 },
            { "name": "墨爾本皇家秀場 Melbourne Showgrounds", "lat": -37.7849, "lng": 144.9199 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 8｜9/26(六) City Walk",
        "color": "#9333ea",
        "routeFactor": 1.15,
        "avgSpeed": 24,
        "category": "city",
        "transport": "步行＋免費電車",
        "stay": "住墨爾本市區",
        "note": "補成完整市區日，適合安排巷弄、河岸與百貨採買，作為前一天皇家秀後的彈性調整。",
        "depart": "09:30",
        "duration": "約 8 小時",
        "points": [
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 },
            { "name": "德格雷夫街 Degraves Street", "lat": -37.8171, "lng": 144.9668 },
            { "name": "聯邦廣場 Federation Square", "lat": -37.8183, "lng": 144.9691 },
            { "name": "塗鴉巷 Hosier Lane", "lat": -37.8168, "lng": 144.9690 },
            { "name": "皇家拱廊 Royal Arcade", "lat": -37.8144, "lng": 144.9632 },
            { "name": "布洛克拱廊 Block Arcade", "lat": -37.8155, "lng": 144.9630 },
            { "name": "南岸河濱步道 Southbank Promenade", "lat": -37.8203, "lng": 144.9645 },
            { "name": "Emporium／CBD 補買 Emporium Melbourne", "lat": -37.8110, "lng": 144.9638 },
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 }
        ]
    },
    {
        "name": "Day 9｜9/27(日) Shopping + 回程",
        "color": "#14b8a6",
        "routeFactor": 1.2,
        "avgSpeed": 34,
        "category": "shopping",
        "transport": "市區購物＋機場巴士",
        "stay": "返程航班",
        "note": "最後半天集中 DFO 與伴手禮採買，再回 Southern Cross 搭 SkyBus 去機場。",
        "depart": "依航班時間倒推",
        "duration": "約 4-6 小時",
        "points": [
            { "name": "墨爾本市區住宿", "lat": -37.8136, "lng": 144.9631 },
            { "name": "南碼頭 DFO DFO South Wharf", "lat": -37.8243, "lng": 144.9505 },
            { "name": "伴手禮採買", "lat": -37.8130, "lng": 144.9625 },
            { "name": "SkyBus 南十字星車站 Southern Cross", "lat": -37.8183, "lng": 144.9525 },
            { "name": "墨爾本機場 Melbourne Airport", "lat": -37.6690, "lng": 144.8410 }
        ]
    }
]

# 分類標籤樣式對照表
DAY_CATEGORY_STYLES = {
    "city": {"label": "市區", "color": "#0f766e"},
    "drive": {"label": "自駕", "color": "#ea580c"},
    "shopping": {"label": "購物", "color": "#7c3aed"}
}

# ==========================================
# 3. 功能函式：計算兩點之間的球面距離 (Haversine 公式)與 URL 產生器
# ==========================================
def to_rad(value):
    return value * math.pi / 180

def haversine_km(p1, p2):
    R = 6371  # 地球半徑 (公里)
    d_lat = to_rad(p2["lat"] - p1["lat"])
    d_lng = to_rad(p2["lng"] - p1["lng"])
    lat1 = to_rad(p1["lat"])
    lat2 = to_rad(p2["lat"])
    
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def build_google_maps_stop_url(p):
    return f"https://www.google.com/maps/search/?api=1&query={p['lat']},{p['lng']}"

def build_google_maps_route_url(day):
    if not day["points"]:
        return "https://www.google.com/maps"
    if len(day["points"]) == 1:
        return build_google_maps_stop_url(day["points"][0])
        
    origin = f"{day['points'][0]['lat']},{day['points'][0]['lng']}"
    destination = f"{day['points'][-1]['lat']},{day['points'][-1]['lng']}"
    waypoints = "|".join([f"{p['lat']},{p['lng']}" for p in day["points"][1:-1]])
    
    travel_mode = "walking"
    if "routeMode" in day and day["routeMode"] == "transit":
        travel_mode = "transit"
    elif day["category"] == "drive":
        travel_mode = "driving"
        
    params = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": travel_mode
    }
    if waypoints:
        params["waypoints"] = waypoints
        
    return f"https://www.google.com/maps/dir/?{urllib.parse.urlencode(params)}"

def get_featured_day_index():
    start_date = datetime(2026, 9, 19)
    end_date = datetime(2026, 9, 27)
    today = datetime.now()
    
    if today < start_date:
        return 0
    if today > end_date:
        return len(days_data) - 1
    return (today - start_date).days

def get_stay_points():
    seen = set()
    stay_points = []
    for day in days_data:
        last_point = day["points"][-1]
        if last_point["name"] not in seen:
            seen.add(last_point["name"])
            stay_points.append(last_point)
    return stay_points

# ==========================================
# 4. 頂部手機快捷入口面板 (Mobile Hero)
# ==========================================
st.markdown("### 🗺️ 手機快捷入口")
featured_idx = get_featured_day_index()
featured_day = days_data[featured_idx]
featured_route_url = build_google_maps_route_url(featured_day)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    st.link_button(
        f"🚗 今日導航軌跡\n({featured_day['name'].split('｜')[0]})",
        featured_route_url,
        use_container_width=True,
        type="primary"
    )
    stay_points = get_stay_points()
    st.link_button(
        "🏨 快速開住宿點位置",
        build_google_maps_stop_url(stay_points[0] if stay_points else days_data[0]["points"][-1]),
        use_container_width=True
    )
with col_btn2:
    st.link_button(
        "🛫 墨爾本機場起點",
        build_google_maps_stop_url(days_data[0]["points"][0]),
        use_container_width=True
    )
    st.link_button(
        "🛍️ 南碼頭 DFO 購物",
        build_google_maps_stop_url(days_data[-1]["points"][1]),
        use_container_width=True
    )

# ==========================================
# 5. 地圖渲染區塊 (Leaflet/Folium 核心)
# ==========================================
st.markdown("### 📍 旅程互動地圖軸")

m = folium.Map(
    location=[-38.05, 144.45],
    zoom_start=8,
    tiles="OpenStreetMap",
    control_scale=True
)

for day in days_data:
    day_style = DAY_CATEGORY_STYLES.get(day["category"], {"label": "一般", "color": day["color"]})
    lat_lngs = [[p["lat"], p["lng"]] for p in day["points"]]
    
    folium.PolyLine(
        locations=lat_lngs,
        color=day["color"],
        weight=4,
        opacity=0.85,
        tooltip=f"{day['name']} ({day_style['label']})"
    ).add_to(m)
    
    for index, point in enumerate(day["points"]):
        if index > 0:
            prev_point = day["points"][index - 1]
            leg_km = haversine_km(prev_point, point) * day["routeFactor"]
            leg_hours = leg_km / max(18, day["avgSpeed"])
            leg_info = f"上一段估算: {leg_km:.1f} km, {leg_hours:.2f} hr"
            
            mid_lat = (prev_point["lat"] + point["lat"]) / 2
            mid_lng = (prev_point["lng"] + point["lng"]) / 2
            folium.Marker(
                location=[mid_lat, mid_lng],
                icon=folium.DivIcon(
                    html=f'<div style="color: #0c3b3d; font-size: 10px; font-weight: 700; text-shadow: 0 1px 1px #fff; white-space: nowrap;">{leg_hours:.2f} hr</div>'
                )
            ).add_to(m)
        else:
            leg_info = "出發起點"
            
        stop_url = build_google_maps_stop_url(point)
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 13px; width: 200px; line-height: 1.4;">
            <strong style="color: {day['color']};">{day['name']}</strong><br>
            <span style="color: #5f6b75;">{day_style['label']} ｜ 節點 {index + 1}</span><br>
            <b>📍 {point['name']}</b><br>
            <small style="color: #415a68;">{leg_info}</small><br><br>
            <a href="{stop_url}" target="_blank" 
               style="display: block; text-align: center; background-color: {day['color']}; color: white; padding: 6px 10px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 11px;">
               🌐 開啟 Google 地圖導航
            </a>
        </div>
        """
        
        folium.CircleMarker(
            location=[point["lat"], point["lng"]],
            radius=6,
            color=day["color"],
            weight=2,
            fill_color="#ffffff",
            fill_opacity=1,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)



st_folium(m, width="100%", height=420)

# ==========================================
# 6. 每日行程詳細展開與卡片總覽區塊 (Day List)
# ==========================================
st.markdown("### 📅 每日詳細行程細節")

day_options = ["顯示全部天數"] + [d["name"] for d in days_data]
selected_day = st.selectbox("🔍 快速跳轉天數卡片：", day_options)

for day in days_data:
    if selected_day != "顯示全部天數" and selected_day != day["name"]:
        continue
        
    day_style = DAY_CATEGORY_STYLES.get(day["category"], {"label": "一般", "color": day["color"]})
    
    total_direct_km = 0
    for i in range(1, len(day["points"])):
        total_direct_km += haversine_km(day["points"][i-1], day["points"][i])
    total_est_km = total_direct_km * day["routeFactor"]
    
    with st.expander(f"📍 {day['name']} ({day_style['label']} ｜ 預估 {total_est_km:.0f} km)", expanded=(selected_day != "顯示全部天數")):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.link_button("🗺️ 開啟當日 Google 地圖主路線", build_google_maps_route_url(day), use_container_width=True)
        with col_m2:
            st.link_button("🏁 開啟今日出發起點", build_google_maps_stop_url(day["points"][0]), use_container_width=True)
            
        st.markdown(f"""
        - **⏱️ 建議出發**：{day['depart']}
        - **⌛ 預計安排**：{day['duration']}
        - **🚌 交通工具**：{day['transport']}
        - **🏨 住宿安排**：{day['stay']}
        - **💡 隨行備註**：{day['note']}
        """)
        
        st.markdown("**📌 依序停靠站點 (點擊名稱可直接開地圖)：**")
        for idx, pt in enumerate(day["points"]):
            st.markdown(f"{idx+1}. [{pt['name']}]({build_google_maps_stop_url(pt)})")
            
        st.markdown("**🚗 每一小段行車時間預估：**")
        for i in range(1, len(day["points"])):
            p_from = day["points"][i-1]
            p_to = day["points"][i]
            segment_km = haversine_km(p_from, p_to) * day["routeFactor"]
            segment_hours = segment_km / max(18, day["avgSpeed"])
            st.markdown(f"- *{p_from['name']}* → *{p_to['name']}*：\n  `{segment_hours:.2f} 乘車小時` ({segment_km:.1f} 公里)")