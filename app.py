"""EcoCoin — Smart Waste Reward System."""
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from config import APP_NAME, APP_TAGLINE
from database import (
    initialize_database, register_user, authenticate, get_user_balance,
    get_categories, get_active_points, create_request, get_requests,
    get_transactions, get_stats, decide_request, update_category,
    add_collection_point, get_all_users,
)
from auth import current_user

st.set_page_config(page_title="EcoCoin | Smart Waste Rewards", page_icon="♻️", layout="wide")

# Liquid-acrylic visual system: translucent panels, floating orbs, and responsive spacing.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --eco-ink:#173b32; --eco-muted:#60766d; --eco-green:#168765; --eco-line:rgba(255,255,255,.78); }
.stApp {
  background: radial-gradient(ellipse at 12% 5%, rgba(181,239,216,.70), transparent 35%),
              radial-gradient(ellipse at 92% 18%, rgba(202,229,255,.60), transparent 30%),
              radial-gradient(ellipse at 70% 95%, rgba(219,248,229,.85), transparent 36%),
              linear-gradient(135deg,#f7fffb 0%,#edf8f3 48%,#f8fbff 100%);
  color:var(--eco-ink); font-family:'DM Sans',sans-serif;
}
.stApp::before,.stApp::after { content:''; position:fixed; z-index:0; pointer-events:none; border-radius:50%; filter:blur(1px); }
.stApp::before { width:230px;height:230px;left:3%;top:24%;background:radial-gradient(circle at 32% 28%,rgba(255,255,255,.95),rgba(148,225,192,.30) 42%,rgba(255,255,255,.06) 72%);border:1px solid rgba(255,255,255,.75);box-shadow:inset -16px -18px 35px rgba(50,150,110,.08),0 25px 70px rgba(50,130,100,.10);animation:ecoFloat 13s ease-in-out infinite; }
.stApp::after { width:145px;height:145px;right:5%;top:62%;background:radial-gradient(circle at 28% 25%,rgba(255,255,255,.95),rgba(170,210,255,.28) 48%,rgba(255,255,255,.05) 75%);border:1px solid rgba(255,255,255,.85);box-shadow:inset -12px -12px 25px rgba(70,130,190,.08),0 20px 55px rgba(60,110,160,.10);animation:ecoFloat 16s ease-in-out infinite reverse; }
@keyframes ecoFloat { 0%,100%{transform:translate3d(0,0,0) rotate(0deg)} 50%{transform:translate3d(18px,-24px,0) rotate(7deg)} }
[data-testid="stHeader"] { background:rgba(255,255,255,.35); backdrop-filter:blur(22px); }
[data-testid="stAppViewContainer"] > .main { position:relative; z-index:1; }
.block-container { max-width:1440px; padding-top:2.2rem; padding-bottom:3rem; }
h1,h2,h3,h4 { font-family:'Manrope','DM Sans',sans-serif!important; color:var(--eco-ink)!important; letter-spacing:-.035em; }
h1 { font-size:clamp(2rem,4vw,3.25rem)!important; font-weight:800!important; }
h2,h3 { display:table; max-width:100%; padding:.52rem .9rem!important; margin:.85rem 0 .75rem!important; border:1px solid rgba(255,255,255,.92); border-radius:18px; background:linear-gradient(135deg,rgba(255,255,255,.82),rgba(255,255,255,.38)); box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 10px 28px rgba(44,105,79,.07); backdrop-filter:blur(22px); }
p, label, [data-testid="stCaptionContainer"] { color:var(--eco-muted); }
[data-testid="stMetric"] { padding:1.15rem 1.2rem; border:1px solid var(--eco-line); border-radius:23px; background:linear-gradient(140deg,rgba(255,255,255,.84),rgba(255,255,255,.42)); box-shadow:inset 0 1px 0 #fff,0 15px 38px rgba(37,105,77,.08); backdrop-filter:blur(24px); }
[data-testid="stMetricLabel"] { color:#60786e!important; }
[data-testid="stMetricValue"] { color:#147754!important; font-family:'Manrope',sans-serif; font-weight:800; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.45rem; padding:.4rem; border:1px solid rgba(255,255,255,.9); border-radius:20px; background:rgba(255,255,255,.46); backdrop-filter:blur(24px); }
[data-testid="stTabs"] button[data-baseweb="tab"] { border-radius:14px; padding:.65rem 1rem; }
[data-testid="stTabs"] button[aria-selected="true"] { background:rgba(255,255,255,.94); box-shadow:0 5px 18px rgba(40,100,75,.10); color:#147754!important; }
[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid rgba(255,255,255,.92)!important; border-radius:24px!important; background:linear-gradient(145deg,rgba(255,255,255,.78),rgba(255,255,255,.39))!important; box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 16px 40px rgba(43,102,79,.07)!important; backdrop-filter:blur(22px); }
.stButton > button, [data-testid="stFormSubmitButton"] button { border:1px solid rgba(255,255,255,.95)!important; border-radius:15px!important; background:linear-gradient(135deg,#198b66,#42b98c)!important; color:white!important; font-weight:700!important; box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 9px 22px rgba(26,137,98,.20)!important; transition:transform .2s ease,box-shadow .2s ease!important; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover { transform:translateY(-2px); box-shadow:0 13px 28px rgba(26,137,98,.28)!important; }
input,textarea,[data-baseweb="select"] > div { border-radius:13px!important; }
[data-testid="stAlert"] { border-radius:17px; border:1px solid rgba(255,255,255,.75); backdrop-filter:blur(14px); }
[data-testid="stSidebar"] { background:linear-gradient(165deg,rgba(255,255,255,.83),rgba(231,248,239,.74)); border-right:1px solid rgba(255,255,255,.85); backdrop-filter:blur(28px); }
[data-testid="stDataFrame"] { border:1px solid rgba(255,255,255,.9); border-radius:18px; overflow:hidden; }
hr { border-color:rgba(255,255,255,.85)!important; }
@media(max-width:700px) { .block-container{padding:1rem .8rem 2rem} h2,h3{white-space:normal;font-size:1.05rem!important} .stApp::before{width:120px;height:120px;left:-35px}.stApp::after{width:90px;height:90px;right:-20px} }
@media(prefers-reduced-motion:reduce) { .stApp::before,.stApp::after{animation:none} *,*::before,*::after{scroll-behavior:auto!important;transition:none!important} }
</style>
""", unsafe_allow_html=True)
initialize_database()

def heading(title, description=None):
    st.subheader(title)
    if description:
        st.caption(description)

def show_requests(rows):
    if not rows:
        st.info("No requests to show yet.")
        return
    frame = pd.DataFrame(rows)
    cols = [c for c in ["id", "username", "category", "quantity_kg", "estimated_coins",
                        "status", "point_name", "created_at", "decision_reason"] if c in frame.columns]
    frame = frame[cols].rename(columns={
        "id": "Request ID", "username": "User", "category": "Waste type",
        "quantity_kg": "Quantity (kg)", "estimated_coins": "Estimated EcoCoins",
        "status": "Status", "point_name": "Collection point",
        "created_at": "Submitted at", "decision_reason": "Decision / reason"
    })
    st.dataframe(frame, use_container_width=True, hide_index=True)

def login_screen():
    st.title(f"♻️ {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.write("Turn responsible recycling into measurable community impact.")
    login_tab, register_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        st.caption("For a local demo, see the administrator setup notes in README.md. Never publish demo credentials or use them for a real service.")
    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password (8+ characters)", type="password")
            confirm = st.text_input("Confirm password", type="password")
            create = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if create:
            if new_password != confirm:
                st.error("The passwords do not match.")
            else:
                try:
                    register_user(new_username, new_password)
                    st.success("Account created. You can now sign in.")
                except ValueError as exc:
                    st.error(str(exc))

user = current_user()
if not user:
    login_screen()
    st.stop()

with st.sidebar:
    st.markdown(f"## ♻️ {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.write(f"Signed in as **{user['username']}**")
    st.caption("Administrator" if user["role"] == "admin" else "Community member")
    if st.button("Sign out", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()
    st.divider()
    st.caption("EcoCoin prototype • Local SQLite storage")

st.title(f"Welcome, {user['username']} 🌱")
st.caption("Your personal EcoCoin space — every eligible kilogram is a step toward a cleaner community.")

if user["role"] == "admin":
    tabs = st.tabs(["Overview", "Review requests", "Manage rewards", "Collection points", "Users"])
    with tabs[0]:
        heading("Platform overview", "Live totals from saved application records.")
        stats, by_category = get_stats()
        a, b, c, d = st.columns(4)
        a.metric("Requests", int(stats["requests"]))
        b.metric("Approved waste", f'{stats["approved_kg"]:.2f} kg')
        c.metric("Pending reviews", int(stats["pending"]))
        d.metric("EcoCoins awarded", int(stats["approved_coins"]))
        if by_category:
            chart_df = pd.DataFrame(by_category)
            fig, ax = plt.subplots()
            ax.bar(chart_df["category"], chart_df["kg"])
            ax.set_ylabel("Approved waste (kg)")
            ax.set_title("Approved waste by category")
            ax.tick_params(axis="x", rotation=20)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Approve a request to start building the impact chart.")
        heading("All recent requests")
        show_requests(get_requests())
    with tabs[1]:
        heading("Review waste submissions", "Approving a request credits the user's wallet exactly once.")
        pending = [r for r in get_requests(status="Pending")]
        if not pending:
            st.success("There are no pending requests.")
        for item in pending:
            with st.container(border=True):
                st.markdown(f"**Request #{item['id']} · {item['username']} · {item['category']}**")
                st.write(f"Quantity: {item['quantity_kg']:.2f} kg · Estimated reward: {item['estimated_coins']} EcoCoins")
                st.write(f"Collection point: {item['point_name']} · Submitted: {item['created_at']}")
                if item["notes"]:
                    st.write(f"Notes: {item['notes']}")
                reason = st.text_input("Decision note (required for rejection)", key=f"decision_{item['id']}")
                left, right = st.columns(2)
                if left.button("Approve and credit", key=f"approve_{item['id']}", type="primary"):
                    try:
                        decide_request(item["id"], user["id"], True, reason)
                        st.success(f"Request #{item['id']} approved; {item['estimated_coins']} EcoCoins credited.")
                        st.rerun()
                    except (ValueError, sqlite3.Error) as exc:
                        st.error(str(exc))
                if right.button("Reject request", key=f"reject_{item['id']}"):
                    try:
                        decide_request(item["id"], user["id"], False, reason)
                        st.warning(f"Request #{item['id']} rejected.")
                        st.rerun()
                    except (ValueError, sqlite3.Error) as exc:
                        st.error(str(exc))
        heading("Request history")
        show_requests(get_requests(status="Approved") + get_requests(status="Rejected"))
    with tabs[2]:
        heading("Waste categories and reward rates")
        st.caption("Rates are illustrative and can be changed for your demonstration.")
        for cat in get_categories():
            with st.form(f"category_{cat['name']}"):
                st.write(f"**{cat['name']}**")
                accepted = st.checkbox("Eligible for rewards", value=bool(cat["accepted"]), key=f"eligible_{cat['name']}")
                rate = st.number_input("EcoCoins per kg", min_value=0, max_value=100000,
                                       value=int(cat["reward_rate"]), step=1, key=f"rate_{cat['name']}")
                save = st.form_submit_button("Save category")
            if save:
                try:
                    update_category(cat["name"], accepted, rate)
                    st.success(f"Saved {cat['name']} settings.")
                    st.rerun()
                except (ValueError, sqlite3.Error) as exc:
                    st.error(str(exc))
    with tabs[3]:
        heading("Collection point directory")
        points = get_active_points()
        if points:
            st.dataframe(pd.DataFrame(points).rename(columns={
                "name":"Name", "address":"Address", "accepted_waste":"Accepted waste",
                "hours":"Hours", "contact":"Contact", "active":"Active", "id":"ID"
            }), use_container_width=True, hide_index=True)
        with st.form("add_point"):
            st.write("**Add a collection point**")
            name = st.text_input("Point name")
            address = st.text_input("Address / area")
            accepted_waste = st.text_input("Accepted waste, comma-separated", value="Plastic, Polythene")
            hours = st.text_input("Operating hours", value="Mon–Sat, 9:00 AM–5:00 PM")
            contact = st.text_input("Contact (optional)")
            add = st.form_submit_button("Add collection point", type="primary")
        if add:
            try:
                add_collection_point(name, address, accepted_waste, hours, contact)
                st.success("Collection point added.")
                st.rerun()
            except (ValueError, sqlite3.Error) as exc:
                st.error("Could not add collection point: " + str(exc))
        st.warning("Starter collection points are demo records, not verified real locations.")
    with tabs[4]:
        heading("Registered accounts")
        st.dataframe(pd.DataFrame(get_all_users()), use_container_width=True, hide_index=True)
else:
    tabs = st.tabs(["Dashboard", "Submit waste", "My requests", "EcoCoin wallet", "Collection points", "Impact"])
    with tabs[0]:
        stats, by_category = get_stats(user["id"])
        balance = get_user_balance(user["id"])
        a, b, c, d = st.columns(4)
        a.metric("EcoCoin balance", balance, help="Calculated from saved wallet transactions.")
        b.metric("Approved waste", f'{stats["approved_kg"]:.2f} kg')
        c.metric("Requests", int(stats["requests"]))
        d.metric("Pending", int(stats["pending"]))
        st.info("Submit eligible waste, then wait for administrator approval before rewards are added to your wallet.")
        heading("Recent activity")
        show_requests(get_requests(user["id"])[:5])
    with tabs[1]:
        heading("Submit recyclable waste", "Your reward is estimated now and credited only after approval.")
        categories = get_categories()
        category_names = [c["name"] for c in categories]
        category_map = {c["name"]: c for c in categories}
        points = get_active_points()
        point_map = {p["id"]: p for p in points}
        if not points:
            st.error("No active collection points are available. Contact an administrator.")
        else:
            with st.form("waste_submission"):
                category = st.selectbox("Waste category", category_names)
                quantity = st.number_input("Quantity (kg)", min_value=0.0, max_value=100000.0,
                                           value=1.0, step=0.5, format="%.2f")
                point_id = st.selectbox("Collection point", list(point_map.keys()),
                                        format_func=lambda value: point_map[value]["name"])
                notes = st.text_area("Notes (optional)", max_chars=500)
                selected = category_map[category]
                selected_point = point_map[point_id]
                accepted_here = {x.strip().casefold() for x in selected_point["accepted_waste"].split(",")}
                eligible = bool(selected["accepted"]) and category.casefold() in accepted_here and quantity > 0
                estimate = int(quantity * selected["reward_rate"]) if eligible else 0
                st.info(f"Estimated reward: **{estimate} EcoCoins** · Rate: {selected['reward_rate']} EcoCoins/kg")
                if not selected["accepted"]:
                    st.warning("This waste category is not eligible for rewards.")
                elif category.casefold() not in accepted_here:
                    st.warning("The selected collection point does not accept this waste category.")
                submit = st.form_submit_button("Submit waste request", type="primary", use_container_width=True)
            if submit:
                try:
                    request_id, coins = create_request(user["id"], category, quantity, notes, point_id)
                    st.success(f"Request #{request_id} submitted. Estimated reward: {coins} EcoCoins. Rewards are pending approval.")
                except (ValueError, sqlite3.Error) as exc:
                    st.error(str(exc))
    with tabs[2]:
        heading("My waste requests")
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Approved", "Rejected"])
        category_filter = st.selectbox("Filter by category", ["All"] + [c["name"] for c in get_categories()])
        rows = get_requests(user["id"], status_filter)
        if category_filter != "All":
            rows = [r for r in rows if r["category"] == category_filter]
        show_requests(rows)
    with tabs[3]:
        heading("My EcoCoin wallet")
        st.metric("Available balance", f"{get_user_balance(user['id'])} EcoCoins")
        transactions = get_transactions(user["id"])
        if transactions:
            frame = pd.DataFrame(transactions).rename(columns={
                "id":"Transaction ID", "request_id":"Request ID", "amount":"Amount",
                "transaction_type":"Type", "reason":"Description", "created_at":"Date"
            })
            st.dataframe(frame[["Transaction ID", "Request ID", "Type", "Amount", "Description", "Date"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No wallet transactions yet. Approved requests will appear here.")
    with tabs[4]:
        heading("Collection point directory")
        points = get_active_points()
        if points:
            for point in points:
                with st.container(border=True):
                    st.markdown(f"**📍 {point['name']}**")
                    st.write(point["address"])
                    st.write(f"**Accepts:** {point['accepted_waste']}")
                    st.write(f"**Hours:** {point['hours']}")
                    if point["contact"]:
                        st.write(f"**Contact:** {point['contact']}")
            st.caption("Demo locations are illustrative and have not been verified as real collection centers.")
        else:
            st.info("No active collection points.")
    with tabs[5]:
        heading("Your environmental impact", "Only approved requests count toward these totals.")
        stats, by_category = get_stats(user["id"])
        a, b, c = st.columns(3)
        a.metric("Recyclable waste approved", f'{stats["approved_kg"]:.2f} kg')
        b.metric("Approved requests", len([r for r in get_requests(user["id"]) if r["status"] == "Approved"]))
        c.metric("EcoCoins earned", int(stats["approved_coins"]))
        if by_category:
            frame = pd.DataFrame(by_category)
            fig, ax = plt.subplots()
            ax.bar(frame["category"], frame["kg"])
            ax.set_ylabel("Approved waste (kg)")
            ax.set_title("Your approved recycling by category")
            ax.tick_params(axis="x", rotation=20)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Your impact chart will appear after a request is approved.")
        st.caption("EcoCoin reports measured approved waste. It does not claim verified carbon savings.")

st.divider()
st.caption("EcoCoin is a hackathon prototype. Starter collection points and reward rates are demonstration data.")
