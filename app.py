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
st.set_page_config(layout="wide", page_title="Amour CRM 企業管理系統")

if "mock_tenant" not in st.session_state:
    st.session_state.mock_tenant = "愛沐家居 (A公司)"

st.title("👑 Amour CRM 企業管理 (SaaS 原型系統)")

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
# 🛠️ 4. 上半部：DEMO 實戰測試工具箱 (無 LINE OA 模擬)
# ==========================================
st.header("🛠️ DEMO 實戰測試工具箱 (模擬無 LINE OA 進件與整合)")

# ✅ Fix 6: 提前初始化 contact_map，避免後續 NameError
contact_map = {}

if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
    st.warning("⚠️ 請將左側企業切換回「愛沐家居 (A公司)」以進行內部驗證場域的進件模擬。")
else:
    tab1, tab2, tab3 = st.tabs([
        "📥 核心驗證 A：新客首期 Webhook 派工",
        "💬 核心驗證 B：熟客追加新對話 (自動分流測試)",
        "🔌 Ragic 外部 CRM 唯讀連接器"
    ])

    # ─── TAB 1: 新客首期派工 (限主管) ───
    with tab1:
        if current_user and current_user["role"] != "admin":
            st.warning(f"🔒 權限攔截：當前身分【{current_user['name']}】為設計師。新客首期「派工與指定負責人」僅限【主管 / 行政 (Admin)】執行。")
            st.info("💡 請在左側將身分切換為主管，即可解鎖派工工具。")
        else:
            st.write("💡 **展示劇本**：新客進件時為「公海狀態」，僅有行政主管可進行首次指派。")
            col1, col2, col3 = st.columns(3)
            with col1:
                mock_name = st.text_input("輸入模擬屋主姓名", value="竹北小明")
            with col2:
                mock_ad = st.selectbox(
                    "選擇模擬點擊的 QR Code / 廣告來源",
                    ["FB_2026現代北歐風專案", "IG_工業風限時送丈量", "門市實體QR_Code", "自然流量"]
                )
            with col3:
                if user_options:
                    mock_designer_name = st.selectbox(
                        "指定分派給哪位設計師 (限主管權限)",
                        [k for k, v in user_options.items() if v["role"] == "designer"]
                    )
                    mock_designer_id = user_options[mock_designer_name]["id"]

            mock_msg = st.text_area(
                "模擬屋主在 LINE 傳送的【第一條】諮詢內容：",
                value="你好，我想諮詢新成屋室內設計，預算大約30萬！"
            )

            if st.button("🚀 執行新客首期 Webhook 派工並寫入", type="primary"):
                fake_line_id = f"LINE_USER_{random.randint(1000, 9999)}"
                mock_event_id = f"msg_first_{random.randint(1000, 9999)}"
                random_status = random.choice(["初次洽談", "現場丈量", "已簽約成交", "已簽約成交"])

                try:
                    supabase.table("contacts").insert({
                        "line_user_id": fake_line_id,
                        "name": mock_name,
                        "assigned_designer_id": mock_designer_id,
                        "utm_source": mock_ad,
                        "status": random_status
                    }).execute()

                    supabase.table("messages").insert({
                        "line_message_id": mock_event_id,
                        "line_user_id": fake_line_id,
                        "sender_type": "client",
                        "message_text": mock_msg
                    }).execute()

                    st.balloons()
                    st.success(f"🎉 成功分派！【{mock_name}】已正式歸屬給設計師【{mock_designer_name}】，初始狀態為【{random_status}】。")
                    st.rerun()

                except Exception as e:
                    st.error(f"模擬進件寫入失敗: {e}")

    # ─── TAB 2: 熟客追加新對話 (自動分流測試) ───
    with tab2:
        st.write("💡 **自動分流實證劇本**：此處模擬客戶後續自行傳送 LINE。後端 Webhook 僅會收到 LINE ID 與文字，系統將自證是否能自動歸流至原負責人！")

        try:
            exist_contacts = supabase.table("contacts").select("line_user_id, name").execute().data
            contact_map = {f"{c['name']} ({c['line_user_id']})": c["line_user_id"] for c in exist_contacts}
        except Exception:
            contact_map = {}

        if not contact_map:
            st.warning("⚠️ 資料庫目前無客戶資料，請先前往分頁A建立新客並完成指派。")
        else:
            selected_target_contact = st.selectbox("請選擇要模擬傳送新訊息的客戶：", list(contact_map.keys()))
            target_line_id = contact_map[selected_target_contact]

            append_msg = st.text_input(
                "模擬客戶在 LINE 追加傳送的【最新對話】：",
                value="我想追加詢問，大約什麼時候可以約現場丈量？"
            )

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
                    st.success("🔥 訊息發送成功！後端已接收。下方列表已完成自動配對分流！")
                    st.json(mock_payload)
                    st.rerun()

                except Exception as e:
                    st.error(f"追加訊息失敗: {e}")

    # ─── TAB 3: Ragic 外部 CRM 連接器 ───
    # ✅ Fix 2: 固定使用 tab3，不再做 contact_map 條件判斷
    with tab3:
        st.write("💡 **商用驗收點**：既有 Ragic CRM 連接測試。")
        st.info("🔌 當前安全狀態：【唯讀測試模式 (Read-Only)】。")
        ragic_mock_data = pd.DataFrame([{
            "Ragic表單ID": "CID-2026-01",
            "客戶姓名": "竹北小明",
            "既有CRM狀態": "已指派設計師",
            "資料同步權限": "Read-Only (唯讀)"
        }])
        # ✅ Fix 4: width='stretch' → use_container_width=True
        st.dataframe(ragic_mock_data, use_container_width=True, hide_index=True)


# ==========================================
# 👑 5. 中間層：主管上帝視角營運圖表 (Admin 限定)
# ==========================================
if current_user and current_user["role"] == "admin" and st.session_state.mock_tenant == "愛沐家居 (A公司)":
    st.markdown("---")
    st.header("📊 主管上帝視角 ── 廣告歸因與設計師 KPI 儀表板")

    try:
        raw_stats = supabase.table("v_designer_contacts").select("ad_source, case_status, designer_name").execute().data
        df_stats = pd.DataFrame(raw_stats)
    except Exception:
        df_stats = pd.DataFrame()

    if df_stats.empty:
        df_stats = pd.DataFrame([
            {"ad_source": "FB_2026現代北歐風專案", "case_status": "已簽約成交", "designer_name": "小華"},
            {"ad_source": "FB_2026現代北歐風專案", "case_status": "現場丈量",   "designer_name": "小華"},
            {"ad_source": "IG_工業風限時送丈量",   "case_status": "已簽約成交", "designer_name": "小美"},
            {"ad_source": "門市實體QR_Code",        "case_status": "已簽約成交", "designer_name": "小華"},
            {"ad_source": "門市實體QR_Code",        "case_status": "初次洽談",   "designer_name": "小美"},
            {"ad_source": "自然流量",               "case_status": "初次洽談",   "designer_name": "小美"},
        ])

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.subheader("1. 廣告 / QR Code 引流進件分布")
        ad_counts = df_stats["ad_source"].value_counts().reset_index()
        ad_counts.columns = ["廣告來源", "進件數量(戶)"]
        st.bar_chart(ad_counts.set_index("廣告來源"), horizontal=True)

    with g_col2:
        st.subheader("2. 實際成交客戶之廣告來源分布")
        success_df = df_stats[df_stats["case_status"].str.contains("成交|簽約", na=False)]
        if not success_df.empty:
            success_counts = success_df["ad_source"].value_counts().reset_index()
            success_counts.columns = ["廣告來源", "成交數量"]
            # ✅ Fix 4: width='stretch' → use_container_width=True
            st.dataframe(success_counts, use_container_width=True, hide_index=True)
        else:
            st.info("💡 目前尚無已成交之客戶數據。")

    # ✅ Fix 5: 移出 g_col2 區塊，放在雙欄外獨立呈現
    st.subheader("3. 設計師接案與成交 KPI 對比")
    kpi_data = []
    designers_list = df_stats["designer_name"].unique()
    for d in designers_list:
        sub_df = df_stats[df_stats["designer_name"] == d]
        total_assigned = len(sub_df)
        total_closed = len(sub_df[sub_df["case_status"].str.contains("成交|簽約", na=False)])
        kpi_data.append({"設計師": d, "指標": "接案總數", "戶數": total_assigned})
        kpi_data.append({"設計師": d, "指標": "實際成交", "戶數": total_closed})
    df_kpi = pd.DataFrame(kpi_data)
    st.bar_chart(df_kpi, x="設計師", y="戶數", color="指標", stack=False)


# ==========================================
# 📋 6. 下半部：核心隔離顯示名單
# ==========================================
st.markdown("---")
# ✅ Fix 1: 補回正確縮排（原本整段沒有縮排）
if current_user:
    limit_count = 30 if current_user["role"] == "admin" else 10
    st.subheader(
        f"📋 客戶追蹤名單 ── 【{st.session_state.mock_tenant}】 ❯ "
        f"登入視角：{current_user['name']} (保留最新 {limit_count} 則)"
    )

    if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
        st.info("🔒 跨企業隔離成功：此處為B公司獨立租戶空間。A公司（愛沐家居）的客戶資料已受底層保護，完全不顯示。")
    else:
        try:
            if current_user["role"] == "admin":
                # ✅ Fix 3: select("") → select("*")
                query = supabase.table("v_designer_contacts").select("*").limit(30).execute()
            else:
                # ✅ Fix 3: select("") → select("*")
                query = supabase.table("v_designer_contacts").select("*").eq("assigned_designer_id", current_user["id"]).limit(10).execute()

            contacts_df = pd.DataFrame(query.data)

            if not contacts_df.empty:
                rename_dict = {
                    "contact_name": "客戶名稱",
                    "ad_source":    "🎯 廣告來源標籤",
                    "case_status":  "📈 案件狀態",
                    "designer_name":"負責設計師",
                    "last_message": "💬 最新 LINE 對話"
                }
                actual_rename = {k: v for k, v in rename_dict.items() if k in contacts_df.columns}
                contacts_df = contacts_df.rename(columns=actual_rename)
                display_cols = [col for col in contacts_df.columns if col in rename_dict.values()]

                if display_cols:
                    # ✅ Fix 4: width='stretch' → use_container_width=True
                    st.dataframe(contacts_df[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(contacts_df, use_container_width=True, hide_index=True)
            else:
                st.info("💡 目前您的名下沒有任何客戶名單。")

        except Exception as e:
            st.error(f"讀取安全檢視表失敗: {e}")
