import os

def get_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            custom_css = f.read()
    except Exception as e:
        custom_css = f"/* Error loading css: {e} */"

    import textwrap
    style_block = textwrap.dedent(f"""
<style>
{custom_css}

/* --- STREAMLIT OVERRIDES TO HIDE UI --- */
[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
[data-testid="stSidebar"] {{ 
    width: 0 !important; 
    min-width: 0 !important; 
    max-width: 0 !important; 
    padding: 0 !important;
    visibility: hidden !important; 
}}
footer {{ visibility: hidden; height: 0; }}

.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
}}

#MainMenu {{ visibility: hidden; }}
header {{ visibility: hidden; }}

/* Position Streamlit's main content area into the shell's #main */
[data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}

/* Ensure the custom shell is visible */
#app {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 10;
}}

/* Make Streamlit elements sit on top of the shell but appear as if inside #main */
.stMain {{
    position: fixed;
    left: 266px; /* rail(52) + panel(214) */
    top: 46px;   /* topbar */
    right: 0;
    bottom: 0;
    overflow-y: auto;
    z-index: 20;
    background: transparent !important;
}}

/* Hide default Streamlit padding/margin on main area */
[data-testid="stAppViewMain"] {{
    padding-top: 0 !important;
}}

/* CRITICAL: Ensure actual metrics/charts are above the fixed #app shell */
[data-testid="stVerticalBlock"], .block-container {{
    position: relative;
    z-index: 100 !important;
    color: #e6edf3 !important; /* Force white text */
}}

/* Force text color on common elements to avoid black-on-black */
h1, h2, h3, h4, h5, h6, p, li, span, div {{
    color: #e6edf3 !important;
}}

</style>
    """)
    return "\n".join([line.strip() for line in style_block.split('\n') if line.strip()])
