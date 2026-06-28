import streamlit as st
import requests
import json
import markdown
from fpdf import FPDF
import re

st.set_page_config(page_title="AI Construction Quotation", layout="centered")
st.title("🏗️ AI Construction Quotation Generator")

st.sidebar.header("🔑 Settings")
api_key = st.secrets.get("DEEPSEEK_API_KEY")
if not api_key:
    st.sidebar.warning("API Key missing in Secrets. Please add it.")
else:
    st.sidebar.success("✅ API Key Loaded!")

st.sidebar.markdown("---")
st.sidebar.markdown("*📦 Package Data Format (Example):*")
st.sidebar.code("""
Foundation: 550
Structure: 1200
Finishing: 750
Electrical: 250
Plumbing: 180
Labour: 350
""")

st.header("📋 Client Requirements")
col1, col2 = st.columns(2)
with col1:
    client_name = st.text_input("Client Name")
    site_location = st.text_input("Site Location")
with col2:
    plot_size = st.number_input("Plot Size (sq ft)", min_value=0.0, step=100.0)
    floors = st.number_input("Floors", min_value=1, step=1)

specific_req = st.text_area("Specific Requirements (e.g., Premium Tiles)")
package_data = st.text_area("📦 Paste Your Construction Package Rates here", height=150)

if 'quotation' not in st.session_state:
    st.session_state.quotation = None

if st.button("🚀 Generate New Quotation", type="primary"):
    if not api_key:
        st.error("❌ API Key missing in Streamlit Secrets!")
    elif not package_data:
        st.error("❌ Kripya Package Rates paste karein.")
    else:
        with st.spinner("DeepSeek AI calculate kar raha hai..."):
            try:
                total_area = plot_size * floors
                prompt = f"""
                You are a professional construction cost estimator.
                RATE CARD:
                {package_data}
                CLIENT DETAILS:
                - Name: {client_name if client_name else 'N/A'}
                - Location: {site_location if site_location else 'N/A'}
                - Total Built-up Area: {total_area} sq ft
                - Special Requirements: {specific_req if specific_req else 'None'}
                TASK:
                1. Calculate total cost. Show breakdown per category in a table.
                2. If special requirements exist, add a 10-20% premium.
                3. Output in professional Markdown format with Grand Total, Validity, and T&C.
                """
                
                # --- DeepSeek API को सीधे Call करना (बिना openai लाइब्रेरी के) ---
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
                
                st.session_state.quotation = raw
                st.success("✅ Quotation Generate Ho Gaya!")
                
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

if st.session_state.quotation:
    st.markdown("---")
    st.markdown(st.session_state.quotation)
    
    def generate_pdf(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        clean_text = re.sub(r'\\(.?)\\*', r'\1', text)
        clean_text = re.sub(r'\(.?)\*', r'\1', clean_text)
        clean_text = re.sub(r'#{1,6} ', '', clean_text)
        clean_text = re.sub(r'\|', ' ', clean_text)
        clean_text = re.sub(r'-+', '', clean_text)
        lines = clean_text.split('\n')
        for line in lines:
            if line.strip() == "":
                pdf.ln(5)
            else:
                pdf.multi_cell(0, 6, line.strip())
        return pdf.output(dest='S').encode('latin-1')

    pdf_data = generate_pdf(st.session_state.quotation)
    st.download_button(
        label="📥 Download Quotation as PDF",
        data=pdf_data,
        file_name=f"Quotation_{client_name if client_name else 'Client'}.pdf",
        mime="application/pdf"
    )
