import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns

# --- Password ---
PASSWORD = "123"  # change this to your password
password_input = st.text_input("პაროლი:", type="password")

if password_input != PASSWORD:
    st.warning("🔒 გთხოვთ შეიყვანოთ სწორი პაროლი")
    st.stop()  # stops execution if password is wrong

# Streamlit page config
st.set_page_config(page_title="ქროს-სელინგის პროცენტული მაჩვენებელი", layout="wide")

st.title("🛒ქროს-სელინგის პროცენტული მაჩვენებელი")
st.write("ატვირთეთ ობიექტის რეალიზაცია(ექსელის ფორმატში)")

# --- Upload Section ---
uploaded_file = st.file_uploader("ატვირთვა", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df_copy = pd.read_excel(uploaded_file, sheet_name='Sheet')
        
        # Filter unwanted data
        unwanted_categories = ['POP', 'COURIER', 'GIFT CARD', 'SERVICE']
        df_filtered = df_copy.copy()
        df_filtered = df_filtered[df_filtered['თანხა'] != 0]
        df_filtered = df_filtered[df_filtered['ფასი'] != 0]
        df_filtered = df_filtered[df_filtered['ფასი 1'] != 0]
        df_filtered = df_filtered[~df_filtered['პროდ. ჯგუფი'].isin(unwanted_categories)]
        df_filtered = df_filtered.dropna(subset=['თანამშრომელი', 'ზედდებული'])

        # Group and calculate
        grouped = (
            df_filtered
            .groupby(['თანამშრომელი', 'ზედდებული'])
            .size()
            .reset_index(name='კალათაში_არსებული_პროდუქტები')
        )
        grouped['2_ზე_მეტი_მოცემულ_კალათაში'] = (grouped['კალათაში_არსებული_პროდუქტები'] > 2).astype(int)

        grouped2 = (
            grouped
            .groupby(['თანამშრომელი'])
            .agg({'2_ზე_მეტი_მოცემულ_კალათაში': 'sum'})
            .reset_index()
        )

        basket_counts = (
            grouped
            .groupby('თანამშრომელი')['ზედდებული']
            .count()
            .reset_index(name='სულ_კალათები')
        )

        grouped2 = grouped2.merge(basket_counts, on='თანამშრომელი', how='left')

        grouped2['პროცენტულობა'] = round(
            (grouped2['2_ზე_მეტი_მოცემულ_კალათაში'] / grouped2['სულ_კალათები']) * 100, 2
        )
        grouped2 = grouped2.sort_values(by='პროცენტულობა', ascending=False)

        st.success("✅ მონაცემები აიტვირთა წარმატებით!")

        # Show top 10 table
        st.subheader("თანამშრობლები ქროს-სელინგის მაჩვენებლით")
        st.dataframe(grouped2.head(10))

        # --- Small, Prettier Bar Chart ---
        top = grouped2
        st.markdown("---")  # ← 
        st.subheader("თანამშრომელი ქროს-სელინგის მიხედვით")
        st.markdown("---")  # ← 
    
        col1, col2 = st.columns([1, 2])  # smaller column for chart
        with col1:
            sns.set_style("whitegrid")
            fig, ax = plt.subplots(figsize=(7, 5))  # small compact figure
            bars = ax.barh(top['თანამშრომელი'], top['პროცენტულობა'], color='#2ca02c')
            
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/1.56, f'{width}%', va='center', fontsize=10)
            
            ax.set_xlabel('% კალათები 3+ პროდუქტით', fontsize=12)
            ax.set_ylabel('თანამშრომელი', fontsize=12)
            # ax.set_title('თანამშრომ', fontsize=14)
            ax.invert_yaxis()
            ax.grid(True, axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig)
        st.markdown("---")  # ← 

        # --- Download Button ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            grouped2.to_excel(writer, index=False, sheet_name='CrossSellingResults')
        excel_data = output.getvalue()

# --- Elegant Download Button Styling ---
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
            background-color: #e6ffe6; /* soft green background */
            color: #1a1a1a; /* darker text */
            border-color: #1e8f1e; /* slightly darker green border */
            transform: scale(1.02);
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
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("👆 გთხოვთ ატვირტოთ ფაილი დასათვლელად")

















