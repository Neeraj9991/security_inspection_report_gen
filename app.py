import streamlit as st 
from utils.email_processor import EmailProcessor
import pandas as pd
import base64
import io

def main():
    st.set_page_config(
        page_title="Site Inspection Email Generator",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    email_processor = EmailProcessor()

    # Custom CSS
    st.markdown("""
    <style>
        .main .block-container { padding-top: 2rem; }
        .stButton>button, .stDownloadButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📋 Site Inspection Email Generator")
    st.markdown("**Upload an Excel file** with inspection data to generate professional email reports for clients.")

    # Sidebar upload section
    st.sidebar.header("📤 Data Upload")
    with st.sidebar.expander("Download Template", expanded=False):
        st.download_button(
            label="⬇️ Download Excel Template",
            data=open("templates/email_template.xlsx", "rb").read(),
            file_name="email_template.xlsx"
        )

    uploaded_file = st.sidebar.file_uploader("Choose inspection data file", type=['xlsx', 'xls'])

    if uploaded_file:
        try:
            with st.spinner("Processing Excel file..."):
                client_data_list = email_processor.process_excel_file(uploaded_file)

            st.success(f"✅ Processed {len(client_data_list)} client records.")

            # Client selector
            st.subheader("👤 Client Selection")
            client_options = [f"{client['client_name']} ({client['client_email']}) - {len(client['sites'])} sites"
                              for client in client_data_list]
            selected_idx = st.selectbox("Select client to preview email", range(len(client_data_list)),
                                        format_func=lambda x: client_options[x])
            selected_client = client_data_list[selected_idx]

            # Image uploader for each site
            st.subheader("🖼️ Upload Site Images")
            for site in selected_client["sites"]:
                st.markdown(f"**{site['site_name']}** – {site['date']} | {site['shift']}")
                uploaded_images = st.file_uploader(
                    f"Upload up to 3 images for {site['site_name']}",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    key=site["site_name"] + site["date"]
                )
                site["images"] = []
                if uploaded_images:
                    for img in uploaded_images[:6]:
                        img_bytes = img.read()
                        encoded = base64.b64encode(img_bytes).decode("utf-8")
                        ext = img.type.split("/")[-1]
                        site["images"].append({
                            "src": f"data:image/{ext};base64,{encoded}",
                            "alt": f"{site['site_name']} - Uploaded"
                        })

            # Preview section
            st.subheader("✉️ Email Preview")
            email_html = email_processor.generate_email_html(selected_client)
            st.components.v1.html(email_html, height=1000, scrolling=True)

            # Outlook draft creation
            st.sidebar.header("📧 Outlook Draft Actions")
            if st.sidebar.button("📨 Create Outlook Draft"):
                with st.spinner("Creating Outlook draft..."):
                    try:
                        email_processor.create_outlook_draft(selected_client)
                        st.sidebar.success("✅ Outlook draft created!")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error: {str(e)}")

            # Debugging
            if st.checkbox("🔍 Show raw client data"):
                st.json(selected_client)

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
