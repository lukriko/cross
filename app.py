import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns

# --- Password ---
PASSWORD = "1234"
password_input = st.text_input("პაროლი:", type="password")

if password_input != PASSWORD:
    st.warning("🔒 გთხოვთ შეიყვანოთ სწორი პაროლი")
    st.stop()

# Streamlit page config
st.set_page_config(page_title="ქროს-სელინგის მაჩვენებელი", layout="wide")

st.title("🛒 ქროს-სელინგის პროცენტული მაჩვენებელი")
st.write("ატვირთეთ ობიექტის რეალიზაცია (Excel ფორმატში)")

uploaded_file = st.file_uploader("ატვირთვა", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df_copy = pd.read_excel(uploaded_file, sheet_name='Sheet')

        # Filter data
        unwanted_categories = ['POP', 'COURIER', 'GIFT CARD', 'SERVICE']
        df_filtered = df_copy.copy()
        df_filtered = df_filtered[
            (df_filtered['თანხა'] != 0)
            & (df_filtered['ფასი'] != 0)
            & (df_filtered['ფასი 1'] != 0)
            & (~df_filtered['პროდ. ჯგუფი'].isin(unwanted_categories))
        ].dropna(subset=['თანამშრომელი', 'ზედდებული'])

        # Group calculations
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
        st.markdown("---")
        st.subheader("თანამშრომლები ქროს-სელინგის მაჩვენებლით")
        st.markdown("---")
        st.dataframe(grouped2.head(10))

        st.markdown("---")
        st.subheader("ქროს-სელინგის გრაფიკი")
        st.markdown("---")

        top = grouped2.head(10)
        sns.set_style("whitegrid")  # light background

        # --- Small Dashboard Chart ---
        fig, ax = plt.subplots(figsize=(3.5, 2.2))
        bars = ax.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c', height=0.5)

        # x-axis scaled above max
        max_val = top['პროცენტულობა'].max()
        ax.set_xlim(0, max_val + 10)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.5, bar.get_y() + bar.get_height()/1.6, f'{width}%', va='center', fontsize=6)

        ax.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=7)
        ax.set_ylabel('თანამშრომელი', fontsize=7)
        ax.tick_params(axis='both', labelsize=6)
        ax.invert_yaxis()
        ax.grid(True, axis='x', linestyle='--', alpha=0.4)
        plt.tight_layout(rect=[0, 0, 0.95, 1])
        st.pyplot(fig, use_container_width=False)

        # --- Expandable Larger Chart ---
        with st.expander("🔍 სრულად ნახვა / დახურვა"):
            fig_big, ax_big = plt.subplots(figsize=(8, 4))
            bars_big = ax_big.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c')

            max_val_big = top['პროცენტულობა'].max()
            ax_big.set_xlim(0, max_val_big + 10)

            for bar in bars_big:
                width = bar.get_width()
                ax_big.text(width + 0.7, bar.get_y() + bar.get_height()/2, f'{width}%', va='center', fontsize=9)

            ax_big.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=10)
            ax_big.set_ylabel('თანამშრომელი', fontsize=10)
            ax_big.invert_yaxis()
            ax_big.grid(True, axis='x', linestyle='--', alpha=0.5)
            plt.tight_layout(rect=[0, 0, 0.95, 1])
            st.pyplot(fig_big, use_container_width=False)

        st.markdown("---")

        # --- Excel Download Button ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            grouped2.to_excel(writer, index=False, sheet_name='CrossSellingResults')
        excel_data = output.getvalue()

        # Custom button styling
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

