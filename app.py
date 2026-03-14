
import os
import streamlit as st
import pandas as pd
from datetime import date, datetime

import db
import auth
import accounting
import exports
import reports

st.set_page_config(page_title="Tomaya Business Cloud", layout="wide")

con = db.connect()
db.init_db(con)
user = auth.login(con)

os.makedirs("exports", exist_ok=True)

def currency():
    return db.get_setting(con, "currency", "N$")

def vat_rate():
    return float(db.get_setting(con, "vat_rate", "0.15"))

def practice_name():
    return db.get_setting(con, "practice_name", "Tomaya Business Cloud")

def companies_df():
    return pd.read_sql_query("SELECT * FROM companies ORDER BY id DESC", con)

def pick_company(key_name="company_select"):
    cdf = companies_df()
    if cdf.empty:
        st.warning("No companies yet. Add a company first.")
        return None
    labels = {f'{r["name"]} (ID {int(r["id"])})': int(r["id"]) for _, r in cdf.iterrows()}
    selected = st.selectbox("Select company", list(labels.keys()), key=key_name)
    return labels[selected]

    cdf = companies_df()
    if cdf.empty:
        st.warning("No companies yet. Add a company first.")
        return None
    labels = {f"{r['name']} (ID {int(r['id'])})": int(r["id"]) for _, r in cdf.iterrows()}
    return labels[st.selectbox("Select company", list(labels.keys()))]

def tx_df(cid: int, start: str, end: str):
    q = ("SELECT tx_date AS date, description, amount, direction, vat_included, category, reference, source "
         "FROM transactions WHERE company_id=? AND tx_date>=? AND tx_date<=? ORDER BY tx_date ASC")
    return pd.read_sql_query(q, con, params=(cid, start, end))

def receipts_df(cid: int, start: str, end: str):
    q = ("SELECT receipt_date, payer, description, amount, vat_included, category, reference, created_at "
         "FROM receipts WHERE company_id=? AND receipt_date>=? AND receipt_date<=? ORDER BY receipt_date ASC")
    return pd.read_sql_query(q, con, params=(cid, start, end))

st.sidebar.title("Tomaya Business Cloud")
st.sidebar.caption(f"User: {user['username']} ({user['role']})")
auth.logout(con)

with st.sidebar.expander("Settings", expanded=False):
    if user["role"] == "ADMIN":
        new_vat = st.number_input("VAT rate", 0.0, 1.0, float(vat_rate()), 0.01)
        new_cur = st.text_input("Currency symbol", value=currency())
        new_name = st.text_input("Practice name", value=practice_name())
        new_pw = st.text_input("Change admin password (min 8 chars)", type="password")
        if st.button("Save settings"):
            db.set_setting(con, "vat_rate", new_vat)
            db.set_setting(con, "currency", new_cur)
            db.set_setting(con, "practice_name", new_name)
            if new_pw and len(new_pw) >= 8:
                cur = con.cursor()
                cur.execute("UPDATE users SET password_hash=? WHERE username='admin'", (db.hash_password(new_pw),))
                con.commit()
            db.log(con, user["username"], "UPDATE_SETTINGS")
            st.success("Saved.")
    else:
        st.info("Settings are Admin-only.")

tabs = st.tabs(["Dashboard","Companies","Receipts","Transactions Import","VAT & Tax Pack","Audit"])

with tabs[0]:
    cdf = companies_df()
    txc = pd.read_sql_query("SELECT COUNT(*) AS n FROM transactions", con).iloc[0]["n"]
    rxc = pd.read_sql_query("SELECT COUNT(*) AS n FROM receipts", con).iloc[0]["n"]
    a,b,c = st.columns(3)
    a.metric("Companies", len(cdf))
    b.metric("Transactions", int(txc))
    c.metric("Receipts", int(rxc))
    st.caption("Start now: Add company → capture receipts → import bank transactions → export VAT pack.")

with tabs[1]:
    st.subheader("Company Register")
    left, right = st.columns([1,2])
    with left:
        mode = st.radio("Action", ["Add new","Edit existing"], horizontal=True)
        cid = pick_copick_company("company_receipts_select")
pick_company("company_import_select")
pick_company("company_taxpack_select")
pick_company("company_edit_select")
mpany() if mode == "Edit existing" else None
row = {}
if cid:
    df = pd.read_sql_query("SELECT * FROM companies WHERE id=?", con, params=(cid,))
            if not df.empty:
                row = df.iloc[0].to_dict()
        with st.form("company_form"):
            name = st.text_input("Company name*", value=row.get("name",""))
            reg_no = st.text_input("Registration no.", value=row.get("reg_no",""))
            tin = st.text_input("TIN", value=row.get("tin",""))
            vat_no = st.text_input("VAT no.", value=row.get("vat_no",""))
            address = st.text_area("Address", value=row.get("address",""), height=70)
            contact_name = st.text_input("Contact name", value=row.get("contact_name",""))
            contact_email = st.text_input("Contact email", value=row.get("contact_email",""))
            contact_phone = st.text_input("Contact phone", value=row.get("contact_phone",""))
            if st.form_submit_button("Save"):
                if not name.strip():
                    st.error("Company name is required.")
                else:
                    cur = con.cursor()
                    if cid:
                        cur.execute("UPDATE companies SET name=?, reg_no=?, tin=?, vat_no=?, address=?, contact_name=?, contact_email=?, contact_phone=? WHERE id=?",
                                    (name.strip(), reg_no.strip(), tin.strip(), vat_no.strip(), address.strip(),
                                     contact_name.strip(), contact_email.strip(), contact_phone.strip(), cid))
                        con.commit()
                        db.log(con, user["username"], "UPDATE_COMPANY", str(cid))
                        st.success("Updated.")
                    else:
                        cur.execute("INSERT INTO companies(name, reg_no, tin, vat_no, address, contact_name, contact_email, contact_phone, created_at) "
                                    "VALUES(?,?,?,?,?,?,?,?,?)",
                                    (name.strip(), reg_no.strip(), tin.strip(), vat_no.strip(), address.strip(),
                                     contact_name.strip(), contact_email.strip(), contact_phone.strip(), datetime.now().isoformat(timespec="seconds")))
                        con.commit()
                        db.log(con, user["username"], "ADD_COMPANY", name.strip())
                        st.success("Added.")
    with right:
        st.dataframe(companies_df(), use_container_width=True)

with tabs[2]:
    st.subheader("Capture Client Receipts")
    cid = pick_company()
    if cid:
        c1,c2,c3 = st.columns(3)
        with c1:
            r_date = st.date_input("Receipt date", value=date.today())
        with c2:
            payer = st.text_input("Payer / Customer")
        with c3:
            amount = st.number_input("Amount", min_value=0.0, value=0.0, step=50.0)
        desc = st.text_input("Description (optional)")
        vat_inc = st.selectbox("VAT included?", ["YES","NO"], index=0)
        category = st.text_input("Category (e.g. Sales, Consulting, Transport)")
        reference = st.text_input("Reference (optional)")
        if st.button("Save receipt"):
            if not payer.strip() or amount <= 0:
                st.error("Payer and amount are required.")
            else:
                cur = con.cursor()
                cur.execute("INSERT INTO receipts(company_id, receipt_date, payer, description, amount, vat_included, category, reference, created_at) "
                            "VALUES(?,?,?,?,?,?,?,?,?)",
                            (cid, r_date.isoformat(), payer.strip(), desc.strip(), float(amount), vat_inc,
                             category.strip(), reference.strip(), datetime.now().isoformat(timespec="seconds")))
                con.commit()
                db.log(con, user["username"], "ADD_RECEIPT", f"{cid}:{payer}:{amount}")
                st.success("Receipt saved.")
        st.divider()
        s1,s2 = st.columns(2)
        with s1: start = st.date_input("View start", value=date.today().replace(day=1), key="rc_s")
        with s2: end = st.date_input("View end", value=date.today(), key="rc_e")
        st.dataframe(receipts_df(cid, str(start), str(end)), use_container_width=True)

with tabs[3]:
    st.subheader("Import Bank Transactions (CSV)")
    cid = pick_company()
    if cid:
        st.caption("Template: templates/transactions_template.csv")
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up:
            df = pd.read_csv(up)
            st.dataframe(df.head(50), use_container_width=True)
            if st.button("Import transactions"):
                df2 = df.copy()
                df2.columns = [c.strip().lower() for c in df2.columns]
                df2["date"] = pd.to_datetime(df2["date"], errors="coerce").dt.date.astype(str)
                df2["direction"] = df2["direction"].astype(str).str.upper().str.strip()
                df2["vat_included"] = df2["vat_included"].astype(str).str.upper().str.strip()
                cur = con.cursor()
                n = 0
                for _, r in df2.iterrows():
                    if r.get("direction") not in ("IN","OUT"):
                        continue
                    cur.execute("INSERT INTO transactions(company_id, tx_date, description, amount, direction, vat_included, category, reference, source, imported_at) "
                                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                                (cid, r["date"], str(r.get("description",""))[:250], float(r.get("amount",0)),
                                 r["direction"], ("YES" if r.get("vat_included","NO")=="YES" else "NO"),
                                 str(r.get("category",""))[:120], str(r.get("reference",""))[:120],
                                 up.name[:120], datetime.now().isoformat(timespec="seconds")))
                    n += 1
                con.commit()
                db.log(con, user["username"], "IMPORT_TRANSACTIONS", f"{cid} rows {n} source={up.name}")
                st.success(f"Imported {n} rows.")
        st.divider()
        s1,s2 = st.columns(2)
        with s1: start = st.date_input("Ledger start", value=date.today().replace(day=1), key="tx_s")
        with s2: end = st.date_input("Ledger end", value=date.today(), key="tx_e")
        st.dataframe(tx_df(cid, str(start), str(end)), use_container_width=True)

with tabs[4]:
    st.subheader("VAT & Tax Working Pack (Draft)")
    cid = pick_company()
    if cid:
        s1,s2 = st.columns(2)
        with s1: start = st.date_input("Period start", value=date.today().replace(day=1), key="p_s")
        with s2: end = st.date_input("Period end", value=date.today(), key="p_e")
        df = tx_df(cid, str(start), str(end))
        if df.empty:
            st.info("No transactions for this period. Import transactions first.")
        else:
            pl = accounting.pl(df)
            vat = accounting.vat_summary(df, vat_rate())
            c1,c2,c3 = st.columns(3)
            c1.metric("Income", f"{currency()}{pl['income']:,.2f}")
            c2.metric("Expenses", f"{currency()}{pl['expense']:,.2f}")
            c3.metric("Profit", f"{currency()}{pl['profit']:,.2f}")
            v1,v2,v3 = st.columns(3)
            v1.metric("Output VAT", f"{currency()}{vat['output_vat']:,.2f}")
            v2.metric("Input VAT", f"{currency()}{vat['input_vat']:,.2f}")
            v3.metric("VAT Payable/(Refund)", f"{currency()}{vat['vat_payable']:,.2f}")

            notes = st.text_area("Notes / adjustments (for your working paper)", height=120)

            if st.button("Export VAT Summary (Excel)"):
                out = pd.DataFrame([vat])
                fname = f"VAT_Summary_{cid}_{start}_{end}.xlsx".replace(":","-")
                path = os.path.join("exports", fname)
                exports.export_excel(path, "VAT", out, title="VAT Summary (Estimate)")
                with open(path, "rb") as f:
                    st.download_button("Download VAT Excel", data=f, file_name=fname,
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            if st.button("Export Tax Working Pack (PDF)"):
                comp = pd.read_sql_query("SELECT name FROM companies WHERE id=?", con, params=(cid,)).iloc[0]["name"]
                fname = f"TaxPack_{cid}_{start}_{end}.pdf".replace(":","-")
                path = os.path.join("exports", fname)
                reports.export_tax_working_pack(path, practice_name(), comp, f"{start} to {end}", currency(), pl, vat, notes)
                with open(path, "rb") as f:
                    st.download_button("Download PDF Pack", data=f, file_name=fname, mime="application/pdf")

with tabs[5]:
    st.subheader("Audit Log")
    adf = pd.read_sql_query("SELECT ts, username, action, details FROM audit_log ORDER BY id DESC LIMIT 500", con)
    st.dataframe(adf, use_container_width=True)
