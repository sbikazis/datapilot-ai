"""Domain-aware visual identity system for DataPilot AI.

Presentation-only tokens: themes never alter analytical calculations or evidence.
"""
from __future__ import annotations

from html import escape

THEMES = {
    "Nebula / sci-fi": {
        "label": "Nebula", "mood": "Cosmic research · luminous violet and ion cyan",
        "domains": ("General / mixed data", "Marketing & acquisition"),
        "light": {"canvas":"#f4f2fb","surface":"#ffffff","surface_2":"#eeebf8","text":"#211b38","muted":"#716b88","line":"#ded9ed","accent":"#7656d6","accent_2":"#19a9bd","accent_soft":"#e9e2ff","sidebar":"#17142b","sidebar_text":"#f2efff","hero_1":"#21173f","hero_2":"#3e2b70","glow":"rgba(133,100,255,.20)"},
        "dark": {"canvas":"#0d1020","surface":"#171a31","surface_2":"#202443","text":"#f2efff","muted":"#b3aecb","line":"#343656","accent":"#aa91ff","accent_2":"#56d9e8","accent_soft":"#30274e","sidebar":"#090c19","sidebar_text":"#f2efff","hero_1":"#19132f","hero_2":"#34245d","glow":"rgba(142,112,255,.23)"},
    },
    "Heritage / archive": {
        "label": "Heritage", "mood": "Historical archive · parchment, ink and antique gold",
        "domains": ("People & workforce",),
        "light": {"canvas":"#f6f1e7","surface":"#fffdf7","surface_2":"#eee5d5","text":"#30251d","muted":"#786b5d","line":"#e3d7c4","accent":"#95652f","accent_2":"#8e4e43","accent_soft":"#f2e4cd","sidebar":"#2e241d","sidebar_text":"#fff6e8","hero_1":"#35261d","hero_2":"#76502d","glow":"rgba(177,126,64,.18)"},
        "dark": {"canvas":"#17130f","surface":"#241d17","surface_2":"#30261d","text":"#f7eddd","muted":"#c0ad94","line":"#49392b","accent":"#d5a45f","accent_2":"#c77b68","accent_soft":"#443322","sidebar":"#100d0a","sidebar_text":"#f7eddd","hero_1":"#2c2017","hero_2":"#5b3b23","glow":"rgba(213,164,95,.18)"},
    },
    "Botanical / nature": {
        "label": "Botanical", "mood": "Living systems · forest green, sage and fresh mint",
        "domains": ("Operations & service",),
        "light": {"canvas":"#eff5ef","surface":"#ffffff","surface_2":"#e5eee4","text":"#1c3027","muted":"#63796b","line":"#d5e2d7","accent":"#287b56","accent_2":"#9aab55","accent_soft":"#dff0e4","sidebar":"#153527","sidebar_text":"#effaf1","hero_1":"#153b2b","hero_2":"#39724a","glow":"rgba(72,158,105,.18)"},
        "dark": {"canvas":"#0e1914","surface":"#17271f","surface_2":"#20372b","text":"#eaf6ec","muted":"#a9c2b0","line":"#304b3b","accent":"#76d49b","accent_2":"#c0d879","accent_soft":"#244b36","sidebar":"#09120e","sidebar_text":"#eaf6ec","hero_1":"#10291e","hero_2":"#28583a","glow":"rgba(94,207,137,.18)"},
    },
    "Executive / minimal": {
        "label": "Executive", "mood": "Decision room · precise graphite, cobalt and silver",
        "domains": ("Sales & commerce", "Finance & accounting"),
        "light": {"canvas":"#f2f4f8","surface":"#ffffff","surface_2":"#e9edf4","text":"#1c2638","muted":"#657187","line":"#dce2eb","accent":"#315fbd","accent_2":"#607fae","accent_soft":"#e2eafe","sidebar":"#172338","sidebar_text":"#f2f5fb","hero_1":"#182842","hero_2":"#31548b","glow":"rgba(70,115,205,.16)"},
        "dark": {"canvas":"#101722","surface":"#192435","surface_2":"#233248","text":"#edf3ff","muted":"#b0bfd4","line":"#34445b","accent":"#83aaff","accent_2":"#9bb9d7","accent_soft":"#263b5d","sidebar":"#0b111b","sidebar_text":"#edf3ff","hero_1":"#17243a","hero_2":"#294778","glow":"rgba(92,142,230,.18)"},
    },
    "Oceanic / research": {
        "label": "Oceanic", "mood": "Deep research · midnight blue, turquoise and sea glass",
        "domains": ("Customer & audience",),
        "light": {"canvas":"#eff6f8","surface":"#ffffff","surface_2":"#e4f0f3","text":"#17303b","muted":"#607985","line":"#d5e4e9","accent":"#087f91","accent_2":"#438db2","accent_soft":"#d9f0f1","sidebar":"#102d3b","sidebar_text":"#edfaff","hero_1":"#103444","hero_2":"#146c7b","glow":"rgba(27,169,183,.18)"},
        "dark": {"canvas":"#0c1820","surface":"#142630","surface_2":"#1c3541","text":"#e9f7fa","muted":"#a8c2ca","line":"#2b4854","accent":"#5bd0d1","accent_2":"#77bce5","accent_soft":"#1d454c","sidebar":"#071117","sidebar_text":"#e9f7fa","hero_1":"#102b37","hero_2":"#155665","glow":"rgba(58,196,200,.18)"},
    },
}

THEME_OPTIONS = ["Automatic · domain aware", *THEMES.keys()]


def resolve_theme(choice: str, domain: str) -> dict:
    """Resolve a fixed theme or conservatively map a detected domain to a theme."""
    if choice in THEMES:
        return THEMES[choice]
    for theme in THEMES.values():
        if domain in theme["domains"]:
            return theme
    return THEMES["Nebula / sci-fi"]


def theme_chart_colors(theme: dict, mode: str = "Light") -> list[str]:
    """Return a distinct, appearance-aware palette for categorical chart series."""
    palette = theme["dark" if mode == "Dark" else "light"]
    if mode == "Dark":
        supporting = ["#c7b4ff", "#ffc078", "#83dfb2", "#ff9db2", "#91c8ff"]
    else:
        supporting = ["#7250b5", "#a45b18", "#26734d", "#a33d60", "#315f9b"]
    colors = [palette["accent"], palette["accent_2"], *supporting]
    # A theme may use one of the supporting colors as its accent; preserve unique series colors.
    return list(dict.fromkeys(colors))


def theme_chart_scale(theme: dict, mode: str = "Light") -> list[str]:
    """Return a sequential scale whose low, middle and high values fit the active mode."""
    palette = theme["dark" if mode == "Dark" else "light"]
    return [palette["surface_2"], palette["accent_soft"], palette["accent_2"], palette["accent"]]


def build_theme_css(theme: dict, mode: str = "Light", density: str = "Comfortable") -> str:
    """Build the shared responsive design system from the active theme tokens."""
    palette = theme["dark" if mode == "Dark" else "light"]
    compact = density == "Compact"
    tokens = {
        "__SCHEME__": "dark" if mode == "Dark" else "light",
        "__CANVAS__": palette["canvas"], "__SURFACE__": palette["surface"],
        "__SURFACE2__": palette["surface_2"], "__TEXT__": palette["text"],
        "__MUTED__": palette["muted"], "__LINE__": palette["line"],
        "__ACCENT__": palette["accent"], "__ACCENT2__": palette["accent_2"],
        "__ACCENT_SOFT__": palette["accent_soft"], "__SIDEBAR__": palette["sidebar"],
        "__SIDEBAR_TEXT__": palette["sidebar_text"], "__HERO1__": palette["hero_1"],
        "__HERO2__": palette["hero_2"], "__GLOW__": palette["glow"],
        "__PAD__": "1rem" if compact else "1.55rem",
        "__CARDPAD__": "12px 14px" if compact else "18px 20px",
    }
    css = """
<style>
:root{color-scheme:__SCHEME__;--canvas:__CANVAS__;--surface:__SURFACE__;--surface-2:__SURFACE2__;--text:__TEXT__;--muted:__MUTED__;--line:__LINE__;--accent:__ACCENT__;--accent-2:__ACCENT2__;--accent-soft:__ACCENT_SOFT__;--sidebar:__SIDEBAR__;--sidebar-text:__SIDEBAR_TEXT__;--hero-1:__HERO1__;--hero-2:__HERO2__;--glow:__GLOW__;--radius-card:16px;--radius-control:11px}
.stApp{background:radial-gradient(ellipse at 92% 0%,var(--glow),transparent 34%),var(--canvas)!important;color:var(--text)!important;font-family:Inter,"Segoe UI",system-ui,sans-serif}
.main .block-container{max-width:1540px;padding:__PAD__ clamp(1rem,3vw,2.8rem) 4rem}
.main h1,.main h2,.main h3,.main h4,.main h5{color:var(--text)!important;letter-spacing:-.035em}
.main h1{font-size:clamp(1.65rem,3vw,2.25rem)!important;font-weight:760!important;line-height:1.14!important}
.main h2{font-size:clamp(1.25rem,2.2vw,1.65rem)!important;font-weight:730!important;line-height:1.2!important}
.main h3{font-size:1.08rem!important;font-weight:720!important}
.main p,.main li,.main label{color:var(--text)}
.main [data-testid="stCaptionContainer"],.main .subtle,.main .card-copy,.main .overview-intro{color:var(--muted)!important}
/* Theme transition and text-contrast contract: keep every text layer readable during mode changes. */
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stSidebar"],.main,.main .block-container,
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],[data-testid="column"],
[data-testid="stMetric"],[data-testid="stChatMessage"],[data-testid="stChatInput"],
[data-testid="stExpander"],[data-testid="stDataFrame"],[data-testid="stTable"],
[data-testid="stTabs"] button,.stButton>button,.stDownloadButton>button,
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div,
[data-testid="stDateInput"] input,.main [data-testid="stMarkdownContainer"],
.main [data-testid="stCaptionContainer"],.main p,.main li,.main label,.main small,
.main strong,.main em,.main code,.main blockquote,.main th,.main td,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small,[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{
 transition:color .24s ease,background-color .24s ease,border-color .24s ease,box-shadow .24s ease!important;
}
.main [data-testid="stMarkdownContainer"],.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] li,.main [data-testid="stMarkdownContainer"] span,
.main [data-testid="stMarkdownContainer"] strong,.main [data-testid="stMarkdownContainer"] em,
.main [data-testid="stMarkdownContainer"] code,.main [data-testid="stMarkdownContainer"] blockquote,
.main [data-testid="stMarkdownContainer"] td,.main [data-testid="stMarkdownContainer"] th,
.main [data-testid="stCaptionContainer"],.main [data-testid="stText"],
.main [data-testid="stWidgetLabel"],.main [data-testid="stRadio"] label,
.main [data-testid="stCheckbox"] label,.main [data-testid="stSelectbox"] label,
.main [data-testid="stMultiSelect"] label,.main [data-testid="stSlider"] label,
.main [data-testid="stNumberInput"] label,.main [data-testid="stTextInput"] label,
.main [data-testid="stTextArea"] label,.main [data-testid="stDateInput"] label{
 color:var(--text)!important;
}
.main [data-testid="stCaptionContainer"],.main [data-testid="stCaptionContainer"] *,
.main [data-testid="stMarkdownContainer"] .subtle,.main .subtle,
.main .card-copy,.main .overview-intro,.main .signal-next,
.main .health-foot,.main .workspace-detail,.main .theme-preview-mood,
.main .copilot-side-label,.main .dataset-summary{
 color:var(--muted)!important;
}
.main [data-testid="stMarkdownContainer"] a,.main a{color:var(--accent)!important}
.main [data-testid="stMarkdownContainer"] code{background:var(--surface-2)!important;border:1px solid var(--line);border-radius:5px;padding:.08em .3em}
.main [data-testid="stMarkdownContainer"] pre{background:var(--surface-2)!important;border:1px solid var(--line);border-radius:10px;padding:12px;overflow-x:auto}
.main [data-testid="stMarkdownContainer"] pre code{border:0;padding:0;background:transparent!important}
.main input::placeholder,.main textarea::placeholder,[data-testid="stChatInput"] textarea::placeholder{color:var(--muted)!important;opacity:.82}
.main input:disabled,.main textarea:disabled,.main button:disabled{color:var(--muted)!important;opacity:.62}
[data-testid="stSidebar"]{background:var(--sidebar)!important;border-right:1px solid color-mix(in srgb,var(--sidebar-text) 13%,transparent)}
[data-testid="stSidebar"] *{color:var(--sidebar-text)}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] small{color:color-mix(in srgb,var(--sidebar-text) 72%,transparent)!important}
[data-testid="stSidebar"] hr{border-color:color-mix(in srgb,var(--sidebar-text) 18%,transparent)}
[data-testid="stSidebar"] [role="radiogroup"]{gap:6px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:9px 11px;border:1px solid transparent;border-radius:11px;transition:background .18s,border-color .18s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:color-mix(in srgb,var(--sidebar-text) 9%,transparent)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:color-mix(in srgb,var(--accent) 24%,transparent);border-color:color-mix(in srgb,var(--accent) 55%,transparent)}
[data-testid="stMetric"]{background:linear-gradient(145deg,var(--surface),var(--surface-2))!important;border:1px solid var(--line)!important;border-radius:var(--radius-card)!important;padding:__CARDPAD__!important;box-shadow:0 8px 24px color-mix(in srgb,var(--text) 5%,transparent);min-height:96px}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-weight:650;font-size:.76rem}
[data-testid="stMetricValue"]{color:var(--text)!important;font-weight:780;letter-spacing:-.035em}
.card,.insight,.signal-card,.health-card,.domain-card,.pagehead,.upload-panel,.upload-guidance,.workspace-topbar{transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:var(--radius-card)!important;padding:__CARDPAD__;box-shadow:0 8px 28px color-mix(in srgb,var(--text) 4%,transparent)}
.card:hover,.signal-card:hover,.domain-card:hover{transform:translateY(-2px);box-shadow:0 14px 34px color-mix(in srgb,var(--text) 8%,transparent)}
.card-title,.insight strong,.signal-title,.health-heading strong,.health-row strong,.health-row b,.workspace-filename{color:var(--text)!important}
.card-copy,.insight p,.signal-card p,.signal-next,.health-row span,.health-foot,.workspace-detail{color:var(--muted)!important}
.kicker,.card-label,.replace-label,.brandtag{color:var(--muted)!important;letter-spacing:.13em;font-weight:750}
.brandmark{background:linear-gradient(135deg,var(--accent),var(--accent-2))!important;box-shadow:0 6px 22px var(--glow);border-radius:12px}
.brandname{color:var(--sidebar-text)!important}
.hero,.copilot-hero{position:relative;overflow:hidden;background:radial-gradient(circle at 88% 12%,var(--glow),transparent 32%),linear-gradient(118deg,var(--hero-1),var(--hero-2))!important;border:1px solid color-mix(in srgb,var(--accent) 40%,var(--line));border-radius:22px!important;box-shadow:0 20px 55px color-mix(in srgb,var(--hero-1) 22%,transparent)}
.hero{padding:clamp(22px,3vw,38px)!important;margin-bottom:20px}
.hero:before{content:"";position:absolute;width:240px;height:240px;right:-85px;top:-105px;border:1px solid color-mix(in srgb,var(--sidebar-text) 20%,transparent);border-radius:50%;box-shadow:0 0 0 24px color-mix(in srgb,var(--sidebar-text) 4%),0 0 0 50px color-mix(in srgb,var(--sidebar-text) 3%);pointer-events:none}
.hero .eyebrow{color:var(--accent-2);font-size:.7rem;letter-spacing:.16em;font-weight:800}
.hero h1,.copilot-hero h1{color:#fff!important;font-size:clamp(1.8rem,3.4vw,2.7rem)!important;line-height:1.08!important;letter-spacing:-.05em}
.hero p,.copilot-hero p{color:#e8eaf7!important;max-width:760px}
.hero-meta{color:color-mix(in srgb,#fff 72%,var(--accent-2));font-weight:750;letter-spacing:.13em}
.copilot-hero{padding:clamp(24px,3.4vw,42px);margin:2px 0 24px}
.copilot-hero:after{content:"";position:absolute;width:260px;height:260px;right:-100px;bottom:-190px;border:1px solid rgba(255,255,255,.24);border-radius:50%;box-shadow:0 0 0 25px rgba(255,255,255,.05),0 0 0 52px rgba(255,255,255,.03);pointer-events:none}
.copilot-eyebrow{font-size:.68rem;letter-spacing:.17em;font-weight:850;color:var(--accent-2);margin-bottom:12px}
.copilot-hero h1{margin:0 0 10px!important}
.copilot-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.copilot-meta span{font-size:.72rem;font-weight:700;color:#f4f2ff;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);border-radius:999px;padding:6px 10px}
.copilot-sidepanel{background:var(--surface);border:1px solid var(--line);border-radius:15px;padding:14px;margin:8px 0 18px;box-shadow:0 8px 24px color-mix(in srgb,var(--text) 4%,transparent)}
.copilot-side-label{font-size:.64rem;letter-spacing:.13em;font-weight:850;color:var(--muted);margin-bottom:8px}
.copilot-sidepanel strong{display:block;color:var(--text);font-size:.92rem}
.copilot-sidepanel p{font-size:.76rem;line-height:1.5;color:var(--muted)!important;margin:6px 0 0}
.copilot-welcome{min-height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:34px 22px;border:1px dashed var(--line);border-radius:18px;background:linear-gradient(145deg,var(--surface),var(--surface-2))}
.copilot-welcome-mark{width:54px;height:54px;display:grid;place-items:center;border-radius:17px;background:linear-gradient(135deg,var(--accent),var(--accent-2));color:white;font-size:1.55rem;box-shadow:0 10px 28px var(--glow);margin-bottom:15px}
.copilot-welcome h3{font-size:1.25rem!important;margin:0 0 8px!important}
.copilot-welcome p{max-width:440px;color:var(--muted)!important;line-height:1.6}
.copilot-welcome-note{font-size:.76rem;color:var(--accent);font-weight:700;margin-top:10px}
[data-testid="stChatMessage"]{border:1px solid var(--line);border-radius:16px;padding:12px 14px;margin:10px 0;background:var(--surface);box-shadow:0 6px 20px color-mix(in srgb,var(--text) 3%,transparent)}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p{line-height:1.65}
[data-testid="stChatInput"]{border:1px solid var(--line);border-radius:16px;background:var(--surface);box-shadow:0 8px 28px color-mix(in srgb,var(--text) 6%,transparent)}
[data-testid="stChatInput"] textarea{color:var(--text)!important}
.dataset-summary{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:-5px 0 19px;color:var(--muted);font-size:.76rem}
.dataset-summary>span,.format-list span,.signal-meta span,.signal-index,.signal-kind,.pill,.workspace-session{background:var(--surface-2)!important;color:var(--muted)!important;border:1px solid var(--line)!important;border-radius:8px}
.dataset-summary>span{padding:4px 9px}
.dataset-summary .dataset-kind{background:var(--accent-soft)!important;color:var(--accent)!important;border-color:var(--line)!important;font-weight:750}
.next-step{background:var(--accent-soft)!important;border:1px solid var(--line)!important;border-radius:12px;padding:12px 14px}
.next-step strong{color:var(--accent)!important}
.sectionline{height:1px;background:var(--line)!important;margin:13px 0}
.stButton>button,.stDownloadButton>button{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:var(--radius-control)!important;font-weight:680;min-height:2.65rem;padding:.45rem 1rem;transition:transform .18s,box-shadow .18s,border-color .18s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--accent)!important;box-shadow:0 8px 22px var(--glow);transform:translateY(-1px)}
.stButton>button:active,.stDownloadButton>button:active{transform:translateY(0)}
.stButton>button:disabled,.stDownloadButton>button:disabled{opacity:.48;cursor:not-allowed;box-shadow:none;transform:none}
.stButton>button[kind="primary"],button[kind="primary"]{background:linear-gradient(110deg,var(--accent),var(--accent-2))!important;color:#fff!important;border:0!important}
[data-testid="stTabs"] button{color:var(--muted)!important;font-weight:680}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--accent)!important;border-bottom-color:var(--accent)!important}
[data-testid="stPlotlyChart"],[data-testid="stDataFrame"],[data-testid="stTable"],[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--line)!important;border-radius:14px!important;overflow:hidden}
[data-testid="stPlotlyChart"]{padding:5px}
[data-testid="stExpander"] summary,[data-testid="stExpander"] p{color:var(--text)!important}
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div,[data-testid="stDateInput"] input{background:var(--surface)!important;color:var(--text)!important;border-color:var(--line)!important;border-radius:var(--radius-control)!important}
.stTextInput input:focus,.stTextArea textarea:focus,.stNumberInput input:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:var(--surface)!important;color:var(--text)!important}
[data-baseweb="menu"] *,[role="option"]{color:var(--text)!important}
[data-testid="stFileUploader"]{background:var(--surface-2)!important;border:1px dashed var(--accent)!important;border-radius:14px!important}
[data-testid="stAlert"]{border-radius:13px!important}
[data-testid="stDataFrame"] iframe{color-scheme:__SCHEME__}
a{color:var(--accent)!important;text-decoration-thickness:1px;text-underline-offset:3px}
:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 65%,transparent)!important;outline-offset:3px!important}
.theme-gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:12px 0 18px}
.theme-preview{min-width:0;padding:11px;border:1px solid var(--line);border-radius:13px;background:var(--surface);transition:transform .18s,border-color .18s,box-shadow .18s}
.theme-preview:hover{transform:translateY(-2px);box-shadow:0 10px 24px var(--glow)}
.theme-preview.is-selected{border:2px solid var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.theme-preview-art{height:46px;display:flex;align-items:flex-end;gap:5px;padding:7px;border-radius:8px;background:linear-gradient(120deg,var(--preview-canvas),var(--preview-surface))}
.theme-preview-art span{display:block;height:22px;flex:1;border-radius:4px;background:var(--preview-accent)}
.theme-preview-art span:nth-child(2){height:30px;background:var(--preview-accent2)}
.theme-preview-art span:nth-child(3){height:15px;background:var(--preview-ink)}
.theme-preview-title{margin-top:9px;font-size:.82rem;font-weight:800;color:var(--text)}
.theme-preview-mood{margin-top:3px;font-size:.68rem;line-height:1.4;color:var(--muted)}
.empty{border:1px dashed var(--line);border-radius:12px;padding:24px;text-align:center;color:var(--muted)}
@keyframes dp-rise{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}
.hero,.copilot-hero{animation:dp-rise .45s ease both}
@media(max-width:1100px){.main .block-container{padding-left:1.35rem;padding-right:1.35rem}}
@media(max-width:900px){.main .block-container{padding-left:1rem;padding-right:1rem}.hero,.copilot-hero{border-radius:18px!important}.workspace-topbar{flex-wrap:wrap;align-items:flex-start}.dataset-summary{gap:6px}}
@media(max-width:768px){[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.85rem!important}[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}.main .block-container{padding-top:.9rem;padding-bottom:2rem}.theme-gallery{grid-template-columns:repeat(2,minmax(0,1fr))}[data-testid="stMetric"]{min-height:78px}}
@media(max-width:480px){.main .block-container{padding-left:.75rem;padding-right:.75rem}.main h1{font-size:1.55rem!important}.main h2{font-size:1.2rem!important}.hero,.copilot-hero{padding:20px!important;border-radius:15px!important}.hero-meta{font-size:.58rem}.copilot-meta{gap:5px}.copilot-meta span{font-size:.65rem}[data-testid="stMetric"]{padding:10px!important}.stButton>button,.stDownloadButton>button{width:100%}}
/* Explicit contrast for Streamlit markdown, custom HTML panels and widget internals. */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] h4,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] em,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] blockquote,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] td,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] th,
[data-testid="stMain"] [data-testid="stWidgetLabel"] *,
[data-testid="stMain"] [data-testid="stFileUploader"] label,
[data-testid="stMain"] [data-testid="stFileUploader"] small {color:var(--text)!important}
.upload-panel h2,.pagehead h2,.health-heading,.health-heading strong,.health-row strong,.health-row b,.card-title,.signal-title,.workspace-filename {color:var(--text)!important}
.upload-panel p,.upload-panel .subtle,.pagehead p,.pagehead .subtle,.health-row span,.health-foot,.workspace-detail,.replace-label,.kicker,.card-label,.brandtag,.dataset-summary {color:var(--muted)!important}
[data-testid="stMain"] [data-testid="stTextInput"] input,
[data-testid="stMain"] [data-testid="stTextArea"] textarea,
[data-testid="stMain"] [data-testid="stNumberInput"] input,
[data-testid="stMain"] [data-baseweb="select"] input,
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] *,
[data-testid="stMain"] [data-testid="stRadio"] label *,
[data-testid="stMain"] [data-testid="stCheckbox"] label *,
[data-testid="stMain"] [data-testid="stDateInput"] input {color:var(--text)!important}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] [data-testid="stWidgetLabel"] span,
[data-testid="stMain"] [data-testid="stWidgetLabel"] label {color:var(--text)!important}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] a,[data-testid="stMain"] a {color:var(--accent)!important}
.hero h1,.copilot-hero h1 {color:#fff!important}
.hero p,.copilot-hero p {color:#e8eaf7!important}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
"""
    for key, value in tokens.items():
        css = css.replace(key, value)
    return css


def theme_gallery_html(choice: str, domain: str = "General / mixed data") -> str:
    """Render compact theme previews so visual choices are understandable before selection."""
    active = resolve_theme(choice, domain)["label"]
    cards = []
    for theme in THEMES.values():
        colors = theme["light"]
        selected = " is-selected" if theme["label"] == active else ""
        cards.append(
            f'<div class="theme-preview{selected}" style="--preview-canvas:{colors["canvas"]};'
            f'--preview-surface:{colors["surface"]};--preview-accent:{colors["accent"]};'
            f'--preview-accent2:{colors["accent_2"]};--preview-ink:{colors["text"]}">'
            f'<div class="theme-preview-art"><span></span><span></span><span></span></div>'
            f'<div class="theme-preview-title">{escape(theme["label"])}</div>'
            f'<div class="theme-preview-mood">{escape(theme["mood"])}</div></div>'
        )
    return '<div class="theme-gallery">' + "".join(cards) + "</div>"
