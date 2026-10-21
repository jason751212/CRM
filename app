import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. 初始化設定（請更換成你自己的 Supabase 網址與憑證）
SUPABASE_URL = "https://supabase.com/dashboard/project/aeqteslaqeswiahwqgpi"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlcXRlc2xhcWVzd2lhaHdxZ3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MjY1MjQsImV4cCI6MjEwODEwMjUyNH0.Fla34T4FcVXgf_n5ygUICGmXciiWxhnfWuRxLHsY8WU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide", page_title="Amour CRM 後台管理系統")
st.title("💬 Amour CRM 企業管理後台 (DEMO 原型)")

# 2. 撈取資料庫現有的員工，建立側邊欄帳號切換登入器 (DEMO 用)
try:
    users_data = supabase.table("users").select("*").execute().data
    user_options = {u["name"]: u for u in users_data}
except Exception as e:
    st.error(f"資料庫連線失敗: {e}")
    user_options = {}

with st.sidebar:
    st.header("🔑 模擬員工登入驗證")
    if user_options:
        selected_username = st.selectbox("請選擇當前登入者身分：", list(user_options.keys()))
        current_user = user_options[selected_username]
        st.success(f"當前身分：{current_user['name']} \n\n權限級別：{current_user['role'].upper()}")
    else:
        st.warning("請先在 Supabase 寫入使用者資料")
        current_user = None

# 3. 根據登入者的權限，使用不同的 SQL 邏輯撈取客戶資料 (防搶單核心)
if current_user:
    st.subheader(f"📋 客戶追蹤名單 ── 登入視角：{current_user['name']}")
    
    # 💡 核心 SQL 隔離邏輯
    if current_user["role"] == "admin":
        # 主管權限：看全部資料
        query = supabase.table("v_designer_contacts").select("*").execute()
    else:
        # 設計師權限：只看指派給自己的客戶（防搶單物理隔離）
        query = supabase.table("v_designer_contacts").select("*").eq("assigned_designer_id", current_user["id"]).execute()
        
    contacts_df = pd.DataFrame(query.data)
    
    if not contacts_df.empty:
        # 重新排版表格欄位名稱，方便老闆看懂
        contacts_df = contacts_df.rename(columns={
            "contact_name": "客戶名稱",
            "ad_source": "🎯 廣告來源標籤",
            "case_status": "📈 案件狀態",
            "designer_name": "負責設計師",
            "last_message": "💬 最新 LINE 對話"
        })
        # 唯獨不顯示背後的 ID 欄位
        display_cols = ["客戶名稱", "🎯 廣告來源標籤", "📈 案件狀態", "負責設計師", "最新 LINE 對話"]
        st.dataframe(contacts_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("💡 目前您的名下沒有任何客戶名單。")

# 4. DEMO 工具箱：手動模擬新客戶從廣告進件 (不需要 LINE 就能測試！)
st.markdown("---")
st.header("🛠️ DEMO 實戰測試工具箱 (免開 LINE 模擬客戶進件)")
col1, col2, col3 = st.columns(3)

with col1:
    mock_name = st.text_input("輸入模擬屋主姓名", value="竹北小明")
with col2:
    mock_ad = st.selectbox("選擇模擬點擊的 Meta 廣告來源", ["FB_2026現代北歐風專案", "IG_工業風限時送丈量", "自然流量"])
with col3:
    if user_options:
        mock_designer_name = st.selectbox("指定分派給哪位設計師", [k for k, v in user_options.items() if v["role"] == "designer"])
        mock_designer_id = user_options[mock_designer_name]["id"]

if st.button("🚀 模擬客戶點擊廣告並加入 LINE (寫入資料庫)", type="primary"):
    # 產生一組假的 LINE User ID
    import random
    fake_line_id = f"U{random.randint(10000000, 99999999)}"
    
    # 寫入客戶表
    supabase.table("contacts").insert({
        "line_user_id": fake_line_id,
        "name": mock_name,
        "assigned_designer_id": mock_designer_id,
        "utm_source": mock_ad,
        "status": "初次洽談"
    }).execute()
    
    # 寫入第一則訊息
    supabase.table("messages").insert({
        "line_message_id": f"msg_{random.randint(100000, 999999)}",
        "line_user_id": fake_line_id,
        "sender_type": "client",
        "message_text": "你好，我點擊廣告進來，想要諮詢室內設計預算！"
    }).execute()
    
    st.balloons()
    st.success(f"🎉 成功模擬進件！【{mock_name}】已自動指派給【{mock_designer_name}】，標籤為：{mock_ad}。請切換上方登入身分驗證隔離效果！")

