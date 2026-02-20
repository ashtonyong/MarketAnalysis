/* ============================================================
   VP TERMINAL — app.js
   Handles all UI interactions, navigation state, clock, and
   view switching. This file is UI-only — it does NOT touch
   any data fetching, analysis logic, or Python-side code.
   ============================================================ */

'use strict';

/* ══════════════════════════════════════════════════════════
   NAV DATA — mirrors your existing 9 categories exactly.
   Add/remove views here to keep nav in sync with features.
══════════════════════════════════════════════════════════ */
const NAV = {
    core: {
        name: 'Core',
        desc: 'Dashboard, alerts & live market overview',
        icon: 'home',
        accentClass: 'blue',
        sections: {
            'View': [
                { label: 'Home', viewId: 'home', badge: null },
                { label: 'Chart', viewId: 'chart', badge: null },
                { label: 'News', viewId: 'news', badge: 'LIVE' },
                { label: 'Events', viewId: 'events', badge: null },
            ]
        }
    },
    technical: {
        name: 'Technical',
        desc: 'Price structure, patterns & multi-timeframe',
        icon: 'activity',
        accentClass: 'violet',
        sections: {
            'View': [
                { label: 'Market Structure', viewId: 'market_structure', badge: null },
                { label: 'FVG Scanner', viewId: 'fvg_scanner', badge: 'NEW' },
                { label: 'MTF Confluence', viewId: 'mtf_confluence', badge: null },
                { label: 'Session Ranges', viewId: 'session_range', badge: null },
                { label: 'Pre/Post Tracker', viewId: 'prepost_tracker', badge: null },
                { label: 'Targets', viewId: 'price_targets', badge: null },
                { label: 'Range Analysis', viewId: 'range_dashboard', badge: null },
            ]
        }
    },
    volume: {
        name: 'Volume & Order Flow',
        desc: 'Depth, liquidity & volume profile analysis',
        icon: 'bar-chart-2',
        accentClass: 'blue',
        sections: {
            'Analysis': [
                { label: 'Volume Profile', viewId: 'volume_profile', badge: null },
                { label: 'Order Flow', viewId: 'order_flow', badge: null },
                { label: 'Liquidity Heatmap', viewId: 'liquidity_heatmap', badge: null },
                { label: 'Session Analysis', viewId: 'session_analysis', badge: null },
            ]
        }
    },
    volatility: {
        name: 'Volatility & Risk',
        desc: 'Options, GARCH, vol surface & portfolio risk',
        icon: 'zap',
        accentClass: 'amber',
        sections: {
            'Tools': [
                { label: 'Portfolio Risk', viewId: 'portfolio_risk', badge: null },
                { label: 'Earnings Volatility', viewId: 'earnings_volatility', badge: null },
                { label: 'GARCH Forecast', viewId: 'garch_forecaster', badge: null },
                { label: 'Vol Surface', viewId: 'vol_surface', badge: null },
                { label: 'Options Flow', viewId: 'options_flow', badge: 'LIVE' },
                { label: 'Options Chain', viewId: 'options_analytics', badge: null },
            ]
        }
    },
    fundamental: {
        name: 'Fundamental',
        desc: 'Valuation, earnings, peers & dividends',
        icon: 'file-text',
        accentClass: 'green',
        sections: {
            'Metrics': [
                { label: 'Valuation (DCF)', viewId: 'dcf_engine', badge: null },
                { label: 'Valuation History', viewId: 'valuation_history', badge: null },
                { label: 'Analyst Ratings', viewId: 'analyst_ratings', badge: null },
                { label: 'Peers', viewId: 'peer_comparison', badge: null },
                { label: 'Dividends', viewId: 'dividend_tracker', badge: null },
            ]
        }
    },
    institutional: {
        name: 'Institutional',
        desc: 'Smart money tracking & ownership data',
        icon: 'building',
        accentClass: 'blue',
        sections: {
            'Tracking': [
                { label: 'Institutional Ownership', viewId: 'institutional_tracker', badge: null },
                { label: 'Insider Trading', viewId: 'insider_tracker', badge: null },
                { label: 'Short Interest', viewId: 'short_interest', badge: null },
                { label: 'Sentiment Timeline', viewId: 'sentiment_timeline', badge: null },
            ]
        }
    },
    quant: {
        name: 'Quant & Strategy',
        desc: 'Backtests, factor models & correlations',
        icon: 'cpu',
        accentClass: 'violet',
        sections: {
            'Models': [
                { label: 'Regime Backtest', viewId: 'regime_backtest', badge: null },
                { label: 'Pairs Trading', viewId: 'pairs_trading', badge: null },
                { label: 'Rolling Beta', viewId: 'rolling_beta', badge: null },
                { label: 'Factor Model', viewId: 'factor_model', badge: null },
                { label: 'Correlation', viewId: 'correlation', badge: null },
            ]
        }
    },
    screeners: {
        name: 'Screeners',
        desc: 'Setup scanner, fundamentals & RS rating',
        icon: 'search',
        accentClass: 'blue',
        sections: {
            'Scanner': [
                { label: 'Setup Scanner', viewId: 'setup_scanner', badge: null },
                { label: 'Fundamental Screener', viewId: 'fundamental_screener', badge: null },
                { label: 'RS Rating', viewId: 'rs_rating', badge: null },
            ]
        }
    },
    research: {
        name: 'Research & AI',
        desc: 'Backtester, AI insights & custom tools',
        icon: 'brain',
        accentClass: 'amber',
        sections: {
            'Lab': [
                { label: 'Backtester', viewId: 'backtester', badge: null },
                { label: 'AI Insights', viewId: 'ai_report', badge: 'AI' },
                { label: 'Tools', viewId: 'tools', badge: null },
            ]
        }
    }
};

/* ══════════════════════════════════════════════════════════
   SVG ICONS — inline, no CDN dependency
══════════════════════════════════════════════════════════ */
const ICONS = {
    home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    activity: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    'bar-chart-2': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
    zap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
    'file-text': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    building: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="1"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
    cpu: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>`,
    search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
    brain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.04Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.04Z"/></svg>`,
    // UI icons
    bell: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
    check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"/></svg>`,
    monitor: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
    refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`,
    settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
    share: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>`,
    'trending-up': `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`,
};

function icon(name, size = 16) {
    const s = ICONS[name] || ICONS['home'];
    return s.replace('<svg', `<svg width="${size}" height="${size}"`);
}

/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
const state = {
    category: 'core',
    navLabel: 'Home',
    viewId: 'home',
    ticker: 'SPY',
    period: '1mo',
    interval: '1d',
};

/* ══════════════════════════════════════════════════════════
   RENDER RAIL
══════════════════════════════════════════════════════════ */
function renderRail() {
    const rail = document.getElementById('rail');
    rail.innerHTML = '';

    Object.entries(NAV).forEach(([key, cat]) => {
        const el = document.createElement('div');
        el.className = 'rail-item' + (key === state.category ? ' active' : '');
        el.dataset.cat = key;
        el.innerHTML = icon(cat.icon) + `<div class="rail-tip">${cat.name}</div>`;
        el.addEventListener('click', () => selectCategory(key));
        rail.appendChild(el);
    });

    // Spacer
    const sp = document.createElement('div');
    sp.className = 'rail-spacer';
    rail.appendChild(sp);
}

/* ══════════════════════════════════════════════════════════
   RENDER NAV PANEL
══════════════════════════════════════════════════════════ */
function renderNav() {
    const panel = document.getElementById('nav-panel');
    const cat = NAV[state.category];
    let html = `
    <div class="nav-cat-hd">
      <div class="nav-cat-name">${cat.name}</div>
      <div class="nav-cat-desc">${cat.desc}</div>
    </div>
    <div class="nav-scroll">`;

    Object.entries(cat.sections).forEach(([sectionName, items]) => {
        html += `<div class="nav-section"><span class="nav-sec-lbl">${sectionName}</span>`;
        items.forEach(item => {
            const isActive = item.label === state.navLabel && state.category === state.category;
            const active = (item.viewId === state.viewId) ? ' active' : '';
            let badgeHtml = '';
            if (item.badge) {
                const cls = item.badge === 'NEW' ? 'new' : item.badge === 'AI' ? 'ai' : item.badge === 'LIVE' ? 'alert' : '';
                badgeHtml = `<span class="nav-badge ${cls}">${item.badge}</span>`;
            }
            html += `
        <div class="nav-item${active}" data-view="${item.viewId}" data-label="${item.label}">
          <span class="nav-item-lbl">${item.label}</span>
          ${badgeHtml}
        </div>`;
        });
        html += `</div>`;
    });

    html += `</div>
    <div class="nav-footer"><span class="nav-ver">VP Terminal v2.3</span></div>`;

    panel.innerHTML = html;

    // Bind nav item clicks
    panel.querySelectorAll('.nav-item').forEach(el => {
        el.addEventListener('click', () => {
            state.viewId = el.dataset.view;
            state.navLabel = el.dataset.label;
            renderNav();
            showView(state.viewId, el.dataset.label);
            if (typeof syncToStreamlit === 'function') syncToStreamlit();
        });
    });
}

/* ══════════════════════════════════════════════════════════
   CATEGORY SELECTION
══════════════════════════════════════════════════════════ */
function selectCategory(key) {
    state.category = key;

    // Auto-select first item
    const cat = NAV[key];
    const firstSec = Object.values(cat.sections)[0];
    const firstItem = firstSec[0];
    state.viewId = firstItem.viewId;
    state.navLabel = firstItem.label;

    renderRail();
    renderNav();
    showView(firstItem.viewId, firstItem.label);
    if (typeof syncToStreamlit === 'function') syncToStreamlit();
}

/* ══════════════════════════════════════════════════════════
   VIEW SWITCHING
══════════════════════════════════════════════════════════ */
function showView(viewId, label) {
    // Hide all
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Try named view first
    const target = document.getElementById('view-' + viewId);
    if (target) {
        target.classList.add('active');
        return;
    }

    // Fall back to generic scaffold
    const generic = document.getElementById('view-generic');
    if (generic) {
        document.getElementById('generic-title')?.setAttribute('data-label', label);
        const titleEl = generic.querySelector('.ph-title');
        const subEl = generic.querySelector('.ph-subtitle');
        const sLabel = generic.querySelector('.scaffold-title');
        if (titleEl) titleEl.textContent = label;
        if (subEl) subEl.textContent = `${state.ticker} · Loading analysis…`;
        if (sLabel) sLabel.textContent = label + ' — Content loads here';
        generic.classList.add('active');
    }
}

/* ══════════════════════════════════════════════════════════
   TOPBAR WIRING
══════════════════════════════════════════════════════════ */
function wireTopbar() {
    // Ticker
    const tickerInput = document.getElementById('tickerInput');
    if (tickerInput) {
        tickerInput.addEventListener('change', e => {
            state.ticker = e.target.value.toUpperCase().trim() || 'SPY';
            tickerInput.value = state.ticker;
            onTickerChange();
        });
        tickerInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') tickerInput.blur();
        });
    }

    // Period
    const periodSel = document.getElementById('periodSel');
    if (periodSel) {
        periodSel.addEventListener('change', e => { state.period = e.target.value; onSettingChange(); });
    }

    // Interval
    const intervalSel = document.getElementById('intervalSel');
    if (intervalSel) {
        intervalSel.addEventListener('change', e => { state.interval = e.target.value; onSettingChange(); });
    }

    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('loading');
            onRefresh();
            setTimeout(() => refreshBtn.classList.remove('loading'), 1200);
        });
    }
}

/* ══════════════════════════════════════════════════════════
   HOOKS — connect these to your existing Python/Streamlit logic
══════════════════════════════════════════════════════════ */

// Bridge to Streamlit via Query Parameters
function syncToStreamlit() {
    console.log('[VP] Syncing to Streamlit:', state.ticker, state.viewId);
    const url = new URL(window.location.href);
    url.searchParams.set('ticker', state.ticker);
    url.searchParams.set('view', state.viewId);
    url.searchParams.set('cat', state.category);
    window.history.pushState({}, '', url);

    // Attempt to trigger Streamlit rerun by clicking a hidden refresh button if it exists
    // or just let the query param change be detected on next interaction.
    // In many Streamlit environments, window.parent.location update triggers it.
    window.parent.postMessage({
        type: 'streamlit:set_query_params',
        query_params: {
            ticker: state.ticker,
            view: state.viewId,
            cat: state.category
        }
    }, '*');
}

// Called when ticker changes — wire to your existing ticker handler
function onTickerChange() {
    console.log('[VP] Ticker changed to:', state.ticker);
    syncToStreamlit();
    updateSubtitles();
}

// Called when period/interval changes
function onSettingChange() {
    console.log('[VP] Settings changed:', state.period, state.interval);
    syncToStreamlit();
    updateSubtitles();
}

// Called when refresh button clicked
function onRefresh() {
    console.log('[VP] Refresh triggered');
    syncToStreamlit();
}

function updateSubtitles() {
    document.querySelectorAll('.ph-subtitle[data-dynamic]').forEach(el => {
        el.textContent = `${state.ticker} · ${state.period} · ${state.interval}`;
    });
}

/* ══════════════════════════════════════════════════════════
   TAB GROUPS — generic handler for any .tab-group
══════════════════════════════════════════════════════════ */
function wireTabGroups() {
    // Page header tabs
    document.querySelectorAll('.ph-tabs').forEach(group => {
        group.querySelectorAll('.ph-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                group.querySelectorAll('.ph-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.dataset.tab;
                if (target) {
                    const parent = tab.closest('.view');
                    parent?.querySelectorAll('.tab-pane').forEach(p => {
                        p.classList.toggle('hidden', p.dataset.pane !== target);
                    });
                }
            });
        });
    });

    // Heatmap tabs
    document.querySelectorAll('.hm-tabs').forEach(group => {
        group.querySelectorAll('.hm-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                group.querySelectorAll('.hm-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
            });
        });
    });

    // Chart toolbar timeframe buttons (mutually exclusive)
    const tfGroup = ['1m', '5m', '15m', '30m', '1D', '1W', '1M'];
    document.querySelectorAll('.chart-toolbar').forEach(toolbar => {
        toolbar.querySelectorAll('.ct-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (tfGroup.includes(btn.textContent.trim())) {
                    toolbar.querySelectorAll('.ct-btn').forEach(b => {
                        if (tfGroup.includes(b.textContent.trim())) b.classList.remove('active');
                    });
                    btn.classList.add('active');
                } else {
                    // Overlay toggles are independent
                    btn.classList.toggle('active');
                }
            });
        });
    });
}

/* ══════════════════════════════════════════════════════════
   LIVE CLOCK
══════════════════════════════════════════════════════════ */
const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

function updateClock() {
    const now = new Date();
    const timeStr = [now.getHours(), now.getMinutes(), now.getSeconds()]
        .map(n => String(n).padStart(2, '0')).join(':');
    const dateStr = `EST · ${DAYS[now.getDay()]} ${MONTHS[now.getMonth()]} ${now.getDate()}`;

    const timeEl = document.getElementById('clockTime');
    const dateEl = document.getElementById('clockDate');
    if (timeEl) timeEl.textContent = timeStr;
    if (dateEl) dateEl.textContent = dateStr;
}

/* ══════════════════════════════════════════════════════════
   MARKET STATUS — basic time-based detection
   Override with real market status from your backend
══════════════════════════════════════════════════════════ */
function updateMarketStatus() {
    const now = new Date();
    const day = now.getDay(); // 0=Sun, 6=Sat
    const hour = now.getHours();
    const minute = now.getMinutes();
    const mins = hour * 60 + minute;

    // EST: 9:30–16:00 on weekdays = market open
    const isOpen = day >= 1 && day <= 5 && mins >= 570 && mins < 960;

    const badge = document.getElementById('marketBadge');
    if (!badge) return;

    if (isOpen) {
        badge.className = 'market-badge open';
        badge.innerHTML = `<div class="status-dot"></div> MARKET OPEN`;
    } else {
        badge.className = 'market-badge closed';
        badge.innerHTML = `<div class="status-dot"></div> MARKET CLOSED`;
    }
}

/* ══════════════════════════════════════════════════════════
   PRICE SIMULATION — dev-only mock, replace with real feed
══════════════════════════════════════════════════════════ */
let _mockPrice = 686.29;

function startPriceSim() {
    setInterval(() => {
        _mockPrice += (Math.random() - 0.49) * 0.18;
        _mockPrice = Math.max(678, Math.min(696, _mockPrice));
        document.querySelectorAll('[data-live-price]').forEach(el => {
            el.textContent = '$' + _mockPrice.toFixed(2);
        });
    }, 800);
}

/* ══════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════ */
const initApp = () => {
    // Build navigation
    if (typeof renderRail === 'function') renderRail();
    if (typeof renderNav === 'function') renderNav();
    if (typeof showView === 'function' && state.viewId) showView(state.viewId, state.navLabel);

    // Wire controls
    wireTopbar();
    wireTabGroups();

    // Live clock
    updateClock();
    updateMarketStatus();
    setInterval(updateClock, 1000);
    setInterval(updateMarketStatus, 30_000);

    // Connected to Real Data via Streamlit Bridge
    console.log('[VP Terminal] UI initialised (Live Mode) ✓');
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
