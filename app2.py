import streamlit as st
from jinja2 import Template
import base64
from pathlib import Path

st.set_page_config(page_title="SGV Guideline Generator", layout="centered")
st.title("🖨️ SGV Security Guidelines Print")

title = st.text_input("Enter Title", value="")
content = st.text_area("Enter Content Below:", height=400)

if st.button("💡 Preview & Print HTML"):
    template_path = Path("templates/guidelines_template.html")
    template_str = template_path.read_text(encoding="utf-8")
    template = Template(template_str)
    html_content = template.render(title=title, content=content)

    b64_html = base64.b64encode(html_content.encode("utf-8")).decode()
    src = f"data:text/html;base64,{b64_html}"

    st.components.v1.iframe(src, height=800, scrolling=True)
    # st.markdown(f'<a href="{src}" target="_blank">🖨️ Open in New Tab to Print</a>', unsafe_allow_html=True)
