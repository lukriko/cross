import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns

# ============================================================
# 🔐 PASSWORD PROTECTION
# ============================================================
PASSWORD = "1234"
password_input = st.text_input("პაროლი:", type="password")
if password_input != PASSWORD:
    st.warning("🔒 გთხოვთ შეიყვანოთ სწორი პაროლი")
    st.stop()

# ============================================================
# ⚙️ PAGE CONFIG
# ============================================================
st.set_page_config(page_title="ქროს-სელინგის მაჩვენებელი", layout="wide")
st.title("🛒 ქროს-სელინგისა და სქინქეარის პროცენტული მაჩვენებელი")
st.write("ატვირთეთ ობიექტის რეალიზაცია (Excel ფორმატში)")

uploaded_file = st.file_uploader("ატვირთვა", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # --- Detect Excel engine ---
        file_extension = uploaded_file.name.split('.')[-1]
        if file_extension == 'xls':
            df_copy = pd.read_excel(uploaded_file, sheet_name='Sheet', engine='xlrd')
        else:
            df_copy = pd.read_excel(uploaded_file, sheet_name='Sheet', engine='openpyxl')

        # ============================================================
        # 🧮 CROSS-SELLING CALCULATIONS (EMPLOYEE LEVEL)
        # ============================================================
        unwanted_categories_cross = ['POP', 'COURIER', 'GIFT CARD', 'SERVICE', 'VISAGE', 'UNIFORM', 'FURNITURE', '-']
        df = df_copy.copy()
        df = df[
            (df['თანხა'] != 0)
            & (df['ფასი'] != 0)
            & (df['ფასი 1'] != 0)
            & (~df['პროდ. ჯგუფი'].isin(unwanted_categories_cross))
        ].dropna(subset=['თანამშრომელი', 'ზედდებული'])

        grouped = (
            df.groupby(['თანამშრომელი', 'ზედდებული'])
            .size()
            .reset_index(name='კალათაში_არსებული_პროდუქტები')
        )
        grouped['2_ზე_მეტი_მოცემულ_კალათაში'] = (grouped['კალათაში_არსებული_პროდუქტები'] > 2).astype(int)

        grouped2 = (
            grouped.groupby(['თანამშრომელი'])
            .agg({'2_ზე_მეტი_მოცემულ_კალათაში': 'sum'})
            .reset_index()
        )

        basket_counts = (
            grouped.groupby('თანამშრომელი')['ზედდებული']
            .count()
            .reset_index(name='სულ_კალათები')
        )

        grouped2 = grouped2.merge(basket_counts, on='თანამშრომელი', how='left')
        grouped2['პროცენტულობა'] = round(
            (grouped2['2_ზე_მეტი_მოცემულ_კალათაში'] / grouped2['სულ_კალათები']) * 100, 2
        )
        grouped2 = grouped2.sort_values(by='პროცენტულობა', ascending=False)

        # ============================================================
        # 🌍 TOTAL COMBINED CROSS-SELLING (ALL EMPLOYEES TOGETHER)
        # ============================================================
        overall = (
            df.groupby(['ზედდებული'])
            .size()
            .reset_index(name='კალათაში_არსებული_პროდუქტები')
        )
        overall['2_ზე_მეტი_მოცემულ_კალათაში'] = (
            overall['კალათაში_არსებული_პროდუქტები'] > 2
        ).astype(int)

        total_baskets = overall.shape[0]
        total_big_baskets = overall['2_ზე_მეტი_მოცემულ_კალათაში'].sum()
        cross_total_pct = round((total_big_baskets / total_baskets) * 100, 2)

        # ============================================================
        # 💆‍♀️ SKINCARE SHARE (EMPLOYEE LEVEL + TOTAL) — FIXED
        # ============================================================
        df_skin = df_copy.copy()
        df_skin = df_skin[
            (df_skin['თანხა'] != 0)
            & (~df_skin['პროდ. ჯგუფი'].isin(['SERVICE', 'GIFT CARD']))
        ]

        df_skincare = df_skin[df_skin['პროდ. ჯგუფი'] == 'SKIN CARE']
        df_full = df_skin

        grouped_full = (
            df_full.groupby('თანამშრომელი', as_index=False)['თანხა']
            .sum()
            .rename(columns={'თანხა': 'სრული გაყიდვები'})
        )
        grouped_skincare = (
            df_skincare.groupby('თანამშრომელი', as_index=False)['თანხა']
            .sum()
            .rename(columns={'თანხა': 'სქინქეარის გაყიდვები'})
        )

        combined = grouped_full.merge(grouped_skincare, on='თანამშრომელი', how='left')
        combined['სქინქეარის გაყიდვები'] = combined['სქინქეარის გაყიდვები'].fillna(0)
        combined['პროცენტული მაჩვენებელი'] = (
            combined['სქინქეარის გაყიდვები'] / combined['სრული გაყიდვები'] * 100
        ).round(2)
        combined = combined.sort_values(by='პროცენტული მაჩვენებელი', ascending=False)

        total_sales_all_emps = combined['სრული გაყიდვები'].sum()
        total_skin_all_emps = combined['სქინქეარის გაყიდვები'].sum()
        skincare_total_pct = round((total_skin_all_emps / total_sales_all_emps) * 100, 2)

        # ============================================================
        # ✅ DISPLAY SECTION
        # ============================================================
        st.success("✅ მონაცემები აიტვირთა წარმატებით!")
        st.markdown("---")
        st.subheader("🌍 საერთო მაჩვენებლები (ყველა თანამშრომელი ერთად)")
        col1, col2 = st.columns(2)
        col1.metric("🛍️ საერთო ქროს-სელინგის მაჩვენებელი", f"{cross_total_pct} %")
        col2.metric("💆‍♀️ საერთო სქინქეარის წილი", f"{skincare_total_pct} %")

        st.markdown("---")
        st.subheader("👩‍💼 თანამშრომლები ქროს-სელინგის მაჩვენებლით")
        st.dataframe(grouped2.head(10))

        sns.set_style("whitegrid")
        fig, ax = plt.subplots(figsize=(3.5, 2.2))
        top = grouped2.head(10)
        bars = ax.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c', height=0.5)
        max_val = top['პროცენტულობა'].max()
        ax.set_xlim(0, max_val + 10)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 0.5, bar.get_y() + bar.get_height()/1.6, f'{w}%', va='center', fontsize=6)
        ax.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=7)
        ax.set_ylabel('თანამშრომელი', fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        ax.invert_yaxis()
        ax.grid(True, axis='x', linestyle='--', alpha=0.4)
        plt.tight_layout(rect=[0, 0, 0.95, 1])
        st.pyplot(fig, use_container_width=False)

        # --- SINGLE, CORRECT SKINCARE DISPLAY ---
        st.markdown("---")
        st.subheader("💆‍♀️ თანამშრომლების სქინქეარის გაყიდვების წილი")
        st.dataframe(combined.head(10))

        fig2, ax2 = plt.subplots(figsize=(3.5, 2.2))
        top_skin = combined.head(10)
        bars2 = ax2.barh(top_skin['თანამშრომელი'], top_skin['პროცენტული მაჩვენებელი'], color='#1f77b4', height=0.5)
        max_val2 = top_skin['პროცენტული მაჩვენებელი'].max()
        ax2.set_xlim(0, max_val2 + 10)
        for bar in bars2:
            w = bar.get_width()
            ax2.text(w + 0.5, bar.get_y() + bar.get_height()/1.6, f'{w}%', va='center', fontsize=6)
        ax2.set_xlabel('% სქინქეარის გაყიდვები', fontsize=7)
        ax2.set_ylabel('თანამშრომელი', fontsize=7)
        ax2.tick_params(axis='both', labelsize=6)
        ax2.invert_yaxis()
        ax2.grid(True, axis='x', linestyle='--', alpha=0.4)
        plt.tight_layout(rect=[0, 0, 0.95, 1])
        st.pyplot(fig2, use_container_width=False)

        # ============================================================
        # 📥 DOWNLOAD EXCEL
        # ============================================================
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            grouped2.to_excel(writer, index=False, sheet_name='ქროს-სელინგი')
            combined.to_excel(writer, index=False, sheet_name='სქინქეარი')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 გადმოწერა Excel ფორმატში",
            data=excel_data,
            file_name="ქროს-სელინგი_და_სქინქეარი.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ შეცდომა ფაილის დამუშავებისას: {e}")

else:
    st.info("👆 გთხოვთ ატვირთოთ ფაილი დასათვლელად")
