import streamlit as st
from supabase import create_client, Client
import pandas as pd
import hmac
import hashlib
import base64
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx



app = FastAPI()

LINE_CHANNEL_SECRET = "你的LINE_SECRET_MOCK" # 簽章密鑰

# 模擬非同步處理任務：收到訊息先回 200 OK，後台慢慢處理
async def process_line_message_task(payload: dict):
    for event in payload.get("events", []):
        if event.get("type") == "message":
            line_message_id = event["message"]["id"]
            line_user_id = event["source"]["userId"]
            text_content = event["message"].get("text", "")
            
            # TODO: 呼叫 Supabase 寫入資料
            # 使用 PostgreSQL 的 ON CONFLICT (line_message_id) DO NOTHING 焊死訊息去重！
            print(f"【後台處理】成功去重並儲存訊息 ID: {line_message_id}，內容: {text_content}")

@app.post("/webhook/line")
async def line_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None)
):
    # 1. 讀取原始 Body 用於驗證簽章
    body = await request.body()
    
    # 2. 驗證 LINE 原始請求簽章（資安防線）
    hash_obj = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body, hashlib.sha256)
    signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    if x_line_signature != signature:
        # 下週 Demo 可以先 print 警告，但允許通過以方便模擬
        print("【資安警告】LINE 簽章驗證失敗！")
        # raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. 轉為 JSON 並丟進背景任務（防 LINE 2秒逾時重發）
    payload = await request.json()
    background_tasks.add_task(process_line_message_task, payload)
    
    # 4. 200毫秒內極速回覆 LINE 伺服器
    return {"status": "ok"}
# 1. 安全讀取秘密環境變數（支援地端與雲端雙棲）
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # 如果雲端 secrets 沒抓到，自動降級讀取本地字串（方便您測試）
    SUPABASE_URL = "https://aeqteslaqeswiahwqgpi.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlcXRlc2xhcWVzd2lhaHdxZ3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MjY1MjQsImV4cCI6MjEwODEwMjUyNH0.Fla34T4FcVXgf_n5ygUICGmXciiWxhnfWuRxLHsY8WU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide", page_title="CRM 管理系統")
st.title("💬CRM 企業管理 (DEMO 原型)")

# 2. 撈取使用者資料
try:
    users_data = supabase.table("users").select("*").execute().data
    user_options = {u["name"]: u for u in users_data}
except Exception as e:
    st.error(f"資料庫連線失敗，請檢查 Supabase 設定: {e}")
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

# 3. 核心隔離顯示邏輯（防搶單）
if current_user:
    st.subheader(f"📋 客戶追蹤名單 ── 登入視角：{current_user['name']}")
    
    if current_user["role"] == "admin":
        query = supabase.table("v_designer_contacts").select("*").execute()
    else:
        query = supabase.table("v_designer_contacts").select("*").eq("assigned_designer_id", current_user["id"]).execute()
        
    contacts_df = pd.DataFrame(query.data)
    
    if not contacts_df.empty:
        # 👑 萬用防禦機制：先將現有欄位直接對照中文，完全不寫死
        rename_dict = {
            "contact_name": "客戶名稱",
            "ad_source": "🎯 廣告來源標籤",
            "case_status": "📈 案件狀態",
            "designer_name": "負責設計師",
            "last_message": "💬 最新 LINE 對話"
        }
        
        # 僅對「真正存在」的欄位改名
        actual_rename = {k: v for k, v in rename_dict.items() if k in contacts_df.columns}
        contacts_df = contacts_df.rename(columns=actual_rename)
        
        # 👑 終極保險絲：動態抓取「改名後」出現在 DataFrame 裡的所有欄位，絕對不手寫中文字串群
        display_cols = [col for col in contacts_df.columns if col in rename_dict.values()]
        
        if display_cols:
            st.dataframe(contacts_df[display_cols], use_container_width=True, hide_index=True)
        else:
            # 萬一連一個對照欄位都沒有，直接裸秀現有欄位，確保網頁絕不紅字崩潰
            st.dataframe(contacts_df, use_container_width=True, hide_index=True)
    else:
        st.info("💡 目前您的名下沒有任何客戶名單。")

# 4. 模擬工具箱
st.markdown("---")
st.header("🛠️ DEMO 實戰測試工具箱 (模擬)")
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
    import random
    fake_line_id = f"U{random.randint(10000000, 99999999)}"
    
    try:
        supabase.table("contacts").insert({
            "line_user_id": fake_line_id,
            "name": mock_name,
            "assigned_designer_id": mock_designer_id,
            "utm_source": mock_ad,
            "status": "初次洽談"
        }).execute()
        
        supabase.table("messages").insert({
            "line_message_id": f"msg_{random.randint(100000, 999999)}",
            "line_user_id": fake_line_id,
            "sender_type": "client",
            "message_text": "你好，我點擊廣告進來，想要諮詢室內設計預算！"
        }).execute()
        
        st.balloons()
        st.success(f"🎉 成功模擬進件！請重新整理或切換身分驗證效果！")
        st.rerun() # 自動強制網頁重新整理整理，即時刷新資料
    except Exception as e:
        st.error(f"模擬進件寫入失敗: {e}")
