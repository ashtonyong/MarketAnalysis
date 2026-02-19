
def get_css():
    return """
    <style>
        /* --- GLOBAL VARIABLES --- */
        :root {
            /* Surfaces */
            --bg:     #070b12;
            --s1:     #0c1220;
            --s2:     #101928;
            --s3:     #141f30;

            /* Borders */
            --border:  rgba(255, 255, 255, 0.055);
            --border2: rgba(255, 255, 255, 0.10);

            /* Accents */
            --blue:   #3b82f6;
            --blue-d: rgba(59, 130, 246, 0.12);
            --blue-m: rgba(59, 130, 246, 0.25);
            --green:   #10b981;
            --green-d: rgba(16, 185, 129, 0.12);
            --green-b: rgba(16, 185, 129, 0.25);
            --red:     #ef4444;
            --red-d:   rgba(239, 68, 68, 0.12);
            --red-b:   rgba(239, 68, 68, 0.25);
            --amber:   #f59e0b;
            --amber-d: rgba(245, 158, 11, 0.12);
            --amber-b: rgba(245, 158, 11, 0.25);
            --violet:  #8b5cf6;
            --violet-d: rgba(139, 92, 246, 0.12);
            --violet-b: rgba(139, 92, 246, 0.25);

            /* Text */
            --tp: #e2e8f0;   /* Primary   */
            --ts: #64748b;   /* Secondary */
            --tm: #2d3f52;   /* Muted     */

            /* Layout */
            --rail:  52px;
            --panel: 214px;
            --top:   46px;

            /* Typography */
            --sans: 'Bricolage Grotesque', sans-serif;
            --mono: 'JetBrains Mono', monospace;

            /* Radii */
            --r-sm: 4px;
            --r-md: 6px;
            --r-lg: 8px;
        }

        /* --- FONTS --- */
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300;12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

        /* --- GLOBAL OVERRIDES --- */
        html, body, [class*="css"] {
            font-family: var(--sans) !important;
            background-color: var(--bg) !important;
            color: var(--tp) !important;
        }
        
        /* Hide Default Header/Footer */
        header[data-testid="stHeader"] { visibility: hidden; height: 0; }
        footer { visibility: hidden; height: 0; }
        
        /* Main Container */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            overflow: hidden;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--tm); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--ts); }
        
        /* --- COMPONENTS --- */
        
        /* Buttons */
        .stButton button {
            background-color: var(--blue);
            color: white;
            border: 1px solid var(--blue);
            font-family: var(--mono);
            font-size: 11px;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #2563eb;
            border-color: #2563eb;
        }
        
        /* Ghost Button Variant (Secondary) */
        button.ghost {
            background: transparent !important;
            border: 1px solid var(--border) !important;
            color: var(--ts) !important;
        }
        button.ghost:hover {
            background: var(--s3) !important;
            color: var(--tp) !important;
            border-color: var(--border2) !important;
        }

        /* Inputs & Selects */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: var(--s2) !important;
            border: 1px solid var(--border) !important;
            color: var(--tp) !important;
            font-family: var(--mono) !important;
            border-radius: 4px !important;
        }
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: var(--blue) !important;
            box-shadow: none !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: var(--s1) !important;
            color: var(--tp) !important;
            font-family: var(--sans) !important;
            font-size: 12px !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
        }
        .streamlit-expanderContent {
            background-color: var(--s1) !important;
            border: 1px solid var(--border);
            border-top: none;
            border-radius: 0 0 4px 4px;
        }
        
        /* Metrics */
        div[data-testid="stMetric"] {
            background-color: var(--s1);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px;
        }
        div[data-testid="stMetricLabel"] { font-size: 10px !important; color: var(--ts) !important; letter-spacing: 1px; text-transform: uppercase; }
        div[data-testid="stMetricValue"] { font-family: var(--sans) !important; font-weight: 600 !important; font-size: 24px !important; color: var(--tp) !important; }
        div[data-testid="stMetricDelta"] { font-family: var(--mono) !important; font-size: 10px !important; }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--border);
            gap: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: var(--sans);
            font-size: 11px;
            color: var(--ts);
            border: none;
            background: transparent;
            padding-bottom: 8px;
        }
        .stTabs [aria-selected="true"] {
            color: var(--blue) !important;
            border-bottom: 2px solid var(--blue) !important;
            font-weight: 600;
        }
        
        /* Divider */
        hr { border-color: var(--border) !important; }

        /* --- CUSTOM LAYOUT CLASSES --- */
        .rail-container {
            width: 52px;
            height: 100vh;
            background: var(--s1);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 10px;
            position: fixed;
            top: 46px; /* Below topbar */
            left: 0;
            z-index: 90;
        }
        
        .nav-panel {
            width: 210px;
            height: 100vh;
            background: var(--s1);
            border-right: 1px solid var(--border);
            position: fixed;
            top: 46px;
            left: 52px;
            z-index: 80;
            padding: 14px 0;
            overflow-y: auto;
        }
        
        .main-content {
            margin-left: 262px; /* 52 + 210 */
            padding: 20px;
            margin-top: 46px;
            height: calc(100vh - 46px);
            overflow-y: auto;
        }
        
        .topbar {
            height: 46px;
            background: var(--s1);
            border-bottom: 1px solid var(--border);
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            padding: 0;
        }
        
        /* Rail Items - Targeted as best as possible */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button {
            width: 42px !important; 
            height: 36px !important;
            border-radius: 6px !important;
            display: flex; align-items: center; justify-content: center;
            color: var(--ts) !important;
            cursor: pointer;
            margin-bottom: 8px;
            font-size: 10px !important;
            font-weight: 700 !important;
            padding: 0 !important;
        }
        
        /* Panel Items - Ensure they are NOT affected */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] button {
             width: 100% !important;
             justify-content: flex-start !important;
             height: auto !important;
             padding: 8px 14px !important;
             font-size: 12px !important;
             font-weight: 400 !important;
        }

        /* Nav Item Active State Override */
        [data-testid="stSidebar"] button[kind="primary"] {
            background: var(--blue-d) !important;
            border-left: 2px solid var(--blue) !important;
            border: none;
            color: var(--blue) !important;
            font-weight: 500 !important;
        }
        
        /* Animations */
        @keyframes fadeSlide { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .animate-enter { animation: fadeSlide 0.3s ease forwards; }

    </style>
    """
