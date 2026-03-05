
import pandas as pd

def vat_portion(amount_inclusive: float, vat_rate: float) -> float:
    return float(amount_inclusive) * float(vat_rate) / (1.0 + float(vat_rate))

def vat_summary(df: pd.DataFrame, vat_rate: float) -> dict:
    if df.empty:
        return {"sales_vat_inclusive":0.0,"purchases_vat_inclusive":0.0,"output_vat":0.0,"input_vat":0.0,"vat_payable":0.0}
    df = df.copy()
    df["vat_included"] = df["vat_included"].astype(str).str.upper().str.strip()
    df["direction"] = df["direction"].astype(str).str.upper().str.strip()
    sales_inc = df[(df["direction"]=="IN") & (df["vat_included"]=="YES")]["amount"].sum()
    purch_inc = df[(df["direction"]=="OUT") & (df["vat_included"]=="YES")]["amount"].sum()
    output_vat = vat_portion(sales_inc, vat_rate)
    input_vat = vat_portion(purch_inc, vat_rate)
    return {
        "sales_vat_inclusive": float(sales_inc),
        "purchases_vat_inclusive": float(purch_inc),
        "output_vat": float(output_vat),
        "input_vat": float(input_vat),
        "vat_payable": float(output_vat - input_vat),
    }

def pl(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"income":0.0,"expense":0.0,"profit":0.0}
    income = float(df[df["direction"]=="IN"]["amount"].sum())
    expense = float(df[df["direction"]=="OUT"]["amount"].sum())
    return {"income": income, "expense": expense, "profit": income-expense}
