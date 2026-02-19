

def get_css():
    try:
        with open("styles.css", "r") as f:
            custom_css = f.read()
    except:
        custom_css = ""

    return f"""
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

    </style>
    """
