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

html body .appview-container .main .block-container,
html body [data-testid="stAppViewContainer"] [data-testid="stMain"] [data-testid="stMainBlockContainer"],
html body [data-testid="stAppViewMain"] > div > div,
html body .stApp > header + .main > .block-container {{
    padding-left: 3rem !important; /* Internal padding */
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    width: 100% !important;
    max-width: calc(100vw - 266px - 3rem) !important; /* Force JS width calculation to stop 3rem before screen edge */
    box-sizing: border-box !important;
}}

/* For Plotly charts escaping the bounds */
html body [data-testid="stVerticalBlock"] > div, 
html body .element-container, 
html body .stPlotlyChart,
html body [data-testid="stDataFrame"],
html body [data-testid="stTable"] {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}}

/* Ensure the custom shell is visible */
#app {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 10;
}}

/* Make Streamlit elements sit on top of the shell but appear as if inside #main */
.stMain, [data-testid="stMain"] {{
    position: fixed;
    left: 266px; /* rail(52) + panel(214) */
    top: 46px;   /* topbar */
    right: 0;
    bottom: 0;
    overflow-y: auto;
    overflow-x: hidden;
    z-index: 20;
    background: transparent !important;
    padding-left: 3rem !important;   /* FOOLPROOF MARGINS */
    padding-right: 3rem !important;  /* FOOLPROOF MARGINS */
    box-sizing: border-box !important;
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

/* Expand Streamlit Tabs spacing to prevent crowded layout */
[data-testid="stTabs"] {{
    margin-top: 2rem !important;
    margin-bottom: 2rem !important;
}}
button[data-baseweb="tab"] {{
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    margin-right: 1rem !important;
}}

</style>
    """)
    return "\n".join([line.strip() for line in style_block.split('\n') if line.strip()])
