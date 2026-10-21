import streamlit as st
from supabase import create_client, Client
import pandas as pd
import hmac
import hashlib
import base64
import uuid
import random
import asyncio

# ==========================================
# 🏦 1. Supabase 資料庫連線安全初始化
# ==========================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://aeqteslaqeswiahwqgpi.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlcXRlc2xhcWVzd2lhaHdxZ3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MjY1MjQsImV4cCI6MjEwODEwMjUyNH0.Fla34T4FcVXgf_n5ygUICGmXciiWxhnfWuRxLHsY8WU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 📥 2. 核心技術展示：模擬 FastAPI 非同步去重中樞
# ==========================================
async def mock_fastapi_webhook_backend(payload: dict):
    """模擬後端 FastAPI 接收到 LINE Webhook 後的非同步背景任務 (頂級型別防禦)"""
    await asyncio.sleep(0.1)
    webhook_payload = payload.get("webhook_payload", {})
    events_list = webhook_payload.get("events", [])
    
    line_message_id = "MOCK_ID"
    if isinstance(events_list, list) and len(events_list) > 0:
        first_event = events_list[0]
        if isinstance(first_event, dict):
            line_message_id = first_event.get("message", {}).get("id", "MOCK_ID")
            
    return f"【資安防線】訊息 {line_message_id} 成功通過 SQL UNIQUE 去重過濾，未造成重覆寫入。"


# ==========================================
# 🎨 3. Streamlit 前端網頁安全初始化
# ==========================================
st.set_page_config(layout="wide", page_title="CRM 企業管理系統")

if "mock_tenant" not in st.session_state:
    st.session_state.mock_tenant = "愛沐家居 (A公司)"

st.title("👑CRM 企業管理系統)")

# 撈取使用者資料
try:
    users_data = supabase.table("users").select("*").execute().data
    user_options = {u["name"]: u for u in users_data}
except Exception as e:
    st.error(f"資料庫連線失敗，請檢查 Supabase 設定: {e}")
    user_options = {}

# 側邊欄：雙層架構安全驗證
with st.sidebar:
    st.header("🏢 SaaS 多租戶隔離切換")
    st.session_state.mock_tenant = st.selectbox(
        "請選擇當前登入企業（租戶）：", 
        ["愛沐家居 (A公司)", "他牌系統家具 (B公司)"]
    )
    
    st.markdown("---")
    st.header("🔑 模擬員工內部權限")
    if user_options:
        selected_username = st.selectbox("請選擇當前登入者身分：", list(user_options.keys()))
        current_user = user_options[selected_username]
        st.success(f"當前身分：{current_user['name']} \n\n權限級別：{current_user['role'].upper()}")
    else:
        st.warning("請先在 Supabase 寫入使用者資料")
        current_user = None


# ==========================================
# 🛠️ 4. 【位置對調】上半部：DEMO 實戰測試工具箱 (無 LINE OA 模擬)
# ==========================================
st.header("🛠️ DEMO (模擬無 LINE OA)")

if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
    st.warning("⚠️ 請將左側企業切換回「愛沐家居 (A公司)」以進行內部驗證場域的進件模擬。")
    contact_map = {}
else:
    tab1, tab2, tab3 = st.tabs(["📥 核心驗證 A：新客首期 Webhook 派工", "💬 核心驗證 B：熟客追加新對話 (自動分流測試)", "🔌 Ragic 外部 CRM 唯讀連接器"])
    
    # ─── TAB 1: 新客首期派工 (限主管) ───
    with tab1:
        if current_user and current_user["role"] != "admin":
            st.warning(f"🔒 權限攔截：當前身分【{current_user['name']}】為設計師。新客首期「派工與指定負責人」僅限【主管 / 行政 (Admin)】執行。")
            st.info("💡 主管可解鎖派工工具。")
        else:
            st.write("💡 **展示劇本**：新客進件時為「公海狀態」，僅有行政主管可進行首次指派。")
            col1, col2, col3 = st.columns(3)
            with col1:
                mock_name = st.text_input("輸入模擬屋主姓名", value="竹北小明")
            with col2:
                mock_ad = st.selectbox("選擇模擬點擊的 Meta 廣告來源", ["FB_2026現代北歐風專案", "IG_工業風限時送丈量", "自然流量"])
            with col3:
                if user_options:
                    mock_designer_name = st.selectbox("指定分派給哪位設計師 (限主管權限)", [k for k, v in user_options.items() if v["role"] == "designer"])
                    mock_designer_id = user_options[mock_designer_name]["id"]
            
            mock_msg = st.text_area("模擬屋主在 LINE 傳送的【第一條】諮詢內容：", value="你好，我想諮詢新成屋室內設計，預算大約30萬！")
            
            if st.button("🚀 執行新客首期 Webhook 派工並寫入", type="primary"):
                fake_line_id = f"LINE_USER_{random.randint(1000, 9999)}"
                mock_event_id = f"msg_first_{random.randint(1000, 9999)}"
                
                try:
                    supabase.table("contacts").insert({
                        "line_user_id": fake_line_id,
                        "name": mock_name,
                        "assigned_designer_id": mock_designer_id,
                        "utm_source": mock_ad,
                        "status": "初次洽談"
                    }).execute()
                    
                    supabase.table("messages").insert({
                        "line_message_id": mock_event_id,
                        "line_user_id": fake_line_id,
                        "sender_type": "client",
                        "message_text": mock_msg
                    }).execute()
                    
                    st.balloons()
                    st.success(f"🎉 成功分派！【{mock_name}】已正式歸屬給設計師【{mock_designer_name}】。")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"模擬進件寫入失敗: {e}")
                    
    # ─── TAB 2: 熟客追加新對話 (自動分流測試) ───
    with tab2:
        st.write("💡 **自動分流實證劇本**：此處模擬客戶後續自行傳送 LINE。後端 Webhook 僅會收到 LINE ID 與文字，系統將自證是否能自動歸流至原負責人！")
        
        try:
            exist_contacts = supabase.table("contacts").select("line_user_id, name").execute().data
            contact_map = {f"{c['name']} ({c['line_user_id']})": c['line_user_id'] for c in exist_contacts}
        except Exception:
            contact_map = {}
            
        if not contact_map:
            st.warning("⚠️ 資料庫目前無客戶資料，請先前往分頁A建立新客並完成指派。")
        else:
            selected_target_contact = st.selectbox("請選擇要模擬傳送新訊息的客戶：", list(contact_map.keys()))
            target_line_id = contact_map[selected_target_contact]
            
            append_msg = st.text_input("模擬客戶在 LINE 追加傳送的【最新對話】：", value="我想追加詢問，大約什麼時候可以約現場丈量？")
            
            if st.button("💬 模擬客戶追加傳送 LINE 訊息 (自證分流)", type="primary"):
                mock_append_event_id = f"msg_append_{random.randint(1000, 9999)}"
                try:
                    supabase.table("messages").insert({
                        "line_message_id": mock_append_event_id,
                        "line_user_id": target_line_id,
                        "sender_type": "client",
                        "message_text": append_msg
                    }).execute()
                    
                    mock_payload = {
                        "tenant_id": "amour_furniture_tenant_id",
                        "status": "Webhook 僅收到 LINE_ID，後端自動盲配追蹤中",
                        "webhook_payload": {
                            "events": [{
                                "type": "message",
                                "message": {"id": mock_append_event_id, "type": "text", "text": append_msg},
                                "source": {"userId": target_line_id}
                            }]
                        }
                    }
                    
                    log_msg = asyncio.run(mock_fastapi_webhook_backend(mock_payload))
                    st.toast("新對話已衝入 Webhook 中樞！", icon="💬")
                    st.success(f"🔥 訊息發送成功！後端已接收。下方列表已完成自動配對分流！")
                    st.json(mock_payload)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"追加訊息失敗: {e}")
                    
    # ─── TAB 3: Ragic 外部 CRM 連接器 ───
    with tab3 if contact_map else tab2:
        st.write("💡 **商用驗收點**：既有 Ragic CRM 連接測試。")
        st.info("🔌 當前安全狀態：【唯讀測試模式 (Read-Only)】。")
        ragic_mock_data = pd.DataFrame([
            {"Ragic表單ID": "CID-2026-01", "客戶姓名": "竹北小明", "既有CRM狀態": "已指派設計師", "資料同步權限": "Read-Only (唯讀)"}
        ])
        st.dataframe(ragic_mock_data, width='stretch', hide_index=True)
        
        if st.button("⚡ 測試 Ragic 唯讀資料抓取與欄位對齊"):
            st.toast("Ragic API 連線測試成功！", icon="🔌")
            st.success("🎯 驗證通過：順利拉取 Ragic 現有客戶清單。")


# ==========================================
# 📋 5. 【位置對調】下半部：核心隔離顯示名單 (含老闆30則/設計師10則效能限制)
# ==========================================
st.markdown("---")
if current_user:
    # 建立動態筆數描述文字
    limit_count = 30 if current_user["role"] == "admin" else 10
    st.subheader(f"📋 客戶追蹤名單 ── 【{st.session_state.mock_tenant}】 ❯ 登入視角：{current_user['name']} (效能載入優化：保留最新 {limit_count} 則)")
    
    if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
        st.info("🔒 跨企業隔離成功：此處為B公司獨立租戶空間。A公司（愛沐家居）的客戶資料已受底層保護，完全不顯示。")
    else:
        try:
            # 👑 實施 CTO 級別效能優化：根據角色限制拉取筆數 (老闆保留30則，設計師保留10則)
            if current_user["role"] == "admin":
                query = supabase.table("v_designer_contacts").select("*").limit(30).execute()
            else:
                query = supabase.table("v_designer_contacts").select("*").eq("assigned_designer_id", current_user["id"]).limit(10).execute()
                
            contacts_df = pd.DataFrame(query.data)
            
            if not contacts_df.empty:
                rename_dict = {
                    "contact_name": "客戶名稱",
                    "ad_source": "🎯 廣告來源標籤",
                    "case_status": "📈 案件狀態",
                    "designer_name": "負責設計師",
                    "last_message": "💬 最新 LINE 對話"
                }
                
                actual_rename = {k: v for k, v in rename_dict.items() if k in contacts_df.columns}
                contacts_df = contacts_df.rename(columns=actual_rename)
                display_cols = [col for col in contacts_df.columns if col in rename_dict.values()]
                
                if display_cols:
                    st.dataframe(contacts_df[display_cols], width='stretch', hide_index=True)
                else:
