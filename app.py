import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns

# --- Password ---
PASSWORD = "123"
password_input = st.text_input("პაროლი:", type="password")

if password_input != PASSWORD:
    st.warning("🔒 გთხოვთ შეიყვანოთ სწორი პაროლი")
    st.stop()

# Streamlit page config
st.set_page_config(page_title="ქროს-სელინგის პროცენტული მაჩვენებელი", layout="wide")

st.title("🛒 ქროს-სელინგის პროცენტული მაჩვენებელი")
st.write("ატვირთეთ ობიექტის რეალიზაცია (Excel ფორმატში)")

uploaded_file = st.file_uploader("ატვირთვა", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df_copy = pd.read_excel(uploaded_file, sheet_name='Sheet')

        unwanted_categories = ['POP', 'COURIER', 'GIFT CARD', 'SERVICE']
        df_filtered = df_copy.copy()
        df_filtered = df_filtered[df_filtered['თანხა'] != 0]
        df_filtered = df_filtered[df_filtered['ფასი'] != 0]
        df_filtered = df_filtered[df_filtered['ფასი 1'] != 0]
        df_filtered = df_filtered[~df_filtered['პროდ. ჯგუფი'].isin(unwanted_categories)]
        df_filtered = df_filtered.dropna(subset=['თანამშრომელი', 'ზედდებული'])

        grouped = (
            df_filtered.groupby(['თანამშრომელი', 'ზედდებული'])
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

        st.success("✅ მონაცემები აიტვირთა წარმატებით!")

        st.subheader("თანამშრომლები ქროს-სელინგის მაჩვენებლით")
        st.dataframe(grouped2.head(10))

        st.markdown("---")
        st.subheader("ქროს-სელინგის გრაფიკი")
        st.markdown("---")

        top = grouped2

        # 🎯 Make small chart (real small)
        sns.set_style("whitegrid")
        fig, ax = plt.subplots(figsize=(3, 1.5))  # ← tiny size now
        bars = ax.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c')

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{width}%', va='center', fontsize=6)

        ax.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=6)
        ax.set_ylabel('თანამშრომელი', fontsize=6)
        ax.tick_params(axis='both', which='major', labelsize=6)
        ax.invert_yaxis()
        ax.grid(True, axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig)

        # 🔍 Expander for full-size version
        with st.expander("🔍 დააწკაპე გასადიდებლად"):
            fig_big, ax_big = plt.subplots(figsize=(10, 5))
            bars_big = ax_big.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c')
            for bar in bars_big:
                width = bar.get_width()
                ax_big.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width}%', va='center', fontsize=10)
            ax_big.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=12)
            ax_big.set_ylabel('თანამშრომელი', fontsize=12)
            ax_big.invert_yaxis()
            ax_big.grid(True, axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig_big)

        st.markdown("---")

        # --- Download Button ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            grouped2.to_excel(writer, index=False, sheet_name='CrossSellingResults')
        excel_data = output.getvalue()

        custom_button = """
        <style>
        div.stDownloadButton > button {
            background-color: white;
            color: black;
            font-size: 18px;
            font-weight: 600;
            border-radius: 10px;
            border: 2px solid #2ca02c;
            padding: 12px 24px;
            transition: all 0.3s ease;
            width: 100%;
        }
        div.stDownloadButton > button:hover {
            background-color: #e6ffe6;
            color: #1a1a1a;
            border-color: #1e8f1e;
        }
        </style>
        """
        st.markdown(custom_button, unsafe_allow_html=True)

        st.download_button(
            label="📥 გადმოწერა Excel ფორმატში",
            data=excel_data,
            file_name="ქროს-სელინგი.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ შეცდომა ფაილის დამუშავებისას: {e}")
else:
    st.info("👆 გთხოვთ ატვირთოთ ფაილი დასათვლელად")
