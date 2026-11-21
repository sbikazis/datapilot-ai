"""Domain-aware visual identity system for DataPilot AI.

The themes are presentation choices only; they never change analysis results.
"""
from __future__ import annotations

THEMES = {
    "Nebula / sci-fi": {
        "label": "Nebula",
        "mood": "Cosmic research · luminous violet and ion cyan",
        "domains": ("General / mixed data", "Marketing & acquisition"),
        "light": {"canvas":"#f4f2fb","surface":"#ffffff","surface_2":"#eeebf8","text":"#211b38","muted":"#716b88","line":"#ded9ed","accent":"#7656d6","accent_2":"#19a9bd","accent_soft":"#e9e2ff","sidebar":"#17142b","sidebar_text":"#f2efff","hero_1":"#21173f","hero_2":"#3e2b70","glow":"rgba(133,100,255,.20)"},
        "dark": {"canvas":"#0d1020","surface":"#171a31","surface_2":"#202443","text":"#f2efff","muted":"#b3aecb","line":"#343656","accent":"#aa91ff","accent_2":"#56d9e8","accent_soft":"#30274e","sidebar":"#090c19","sidebar_text":"#f2efff","hero_1":"#19132f","hero_2":"#34245d","glow":"rgba(142,112,255,.23)"},
    },
    "Heritage / archive": {
        "label": "Heritage",
        "mood": "Historical archive · parchment, ink and antique gold",
        "domains": ("People & workforce",),
        "light": {"canvas":"#f6f1e7","surface":"#fffdf7","surface_2":"#eee5d5","text":"#30251d","muted":"#786b5d","line":"#e3d7c4","accent":"#95652f","accent_2":"#8e4e43","accent_soft":"#f2e4cd","sidebar":"#2e241d","sidebar_text":"#fff6e8","hero_1":"#35261d","hero_2":"#76502d","glow":"rgba(177,126,64,.18)"},
        "dark": {"canvas":"#17130f","surface":"#241d17","surface_2":"#30261d","text":"#f7eddd","muted":"#c0ad94","line":"#49392b","accent":"#d5a45f","accent_2":"#c77b68","accent_soft":"#443322","sidebar":"#100d0a","sidebar_text":"#f7eddd","hero_1":"#2c2017","hero_2":"#5b3b23","glow":"rgba(213,164,95,.18)"},
    },
    "Botanical / nature": {
        "label": "Botanical",
        "mood": "Living systems · forest green, sage and fresh mint",
        "domains": ("Operations & service",),
        "light": {"canvas":"#eff5ef","surface":"#ffffff","surface_2":"#e5eee4","text":"#1c3027","muted":"#63796b","line":"#d5e2d7","accent":"#287b56","accent_2":"#9aab55","accent_soft":"#dff0e4","sidebar":"#153527","sidebar_text":"#effaf1","hero_1":"#153b2b","hero_2":"#39724a","glow":"rgba(72,158,105,.18)"},
        "dark": {"canvas":"#0e1914","surface":"#17271f","surface_2":"#20372b","text":"#eaf6ec","muted":"#a9c2b0","line":"#304b3b","accent":"#76d49b","accent_2":"#c0d879","accent_soft":"#244b36","sidebar":"#09120e","sidebar_text":"#eaf6ec","hero_1":"#10291e","hero_2":"#28583a","glow":"rgba(94,207,137,.18)"},
    },
    "Executive / minimal": {
        "label": "Executive",
        "mood": "Decision room · precise graphite, cobalt and silver",
        "domains": ("Sales & commerce", "Finance & accounting"),
        "light": {"canvas":"#f2f4f8","surface":"#ffffff","surface_2":"#e9edf4","text":"#1c2638","muted":"#657187","line":"#dce2eb","accent":"#315fbd","accent_2":"#607fae","accent_soft":"#e2eafe","sidebar":"#172338","sidebar_text":"#f2f5fb","hero_1":"#182842","hero_2":"#31548b","glow":"rgba(70,115,205,.16)"},
        "dark": {"canvas":"#101722","surface":"#192435","surface_2":"#233248","text":"#edf3ff","muted":"#b0bfd4","line":"#34445b","accent":"#83aaff","accent_2":"#9bb9d7","accent_soft":"#263b5d","sidebar":"#0b111b","sidebar_text":"#edf3ff","hero_1":"#17243a","hero_2":"#294778","glow":"rgba(92,142,230,.18)"},
    },
    "Oceanic / research": {
        "label": "Oceanic",
        "mood": "Deep research · midnight blue, turquoise and sea glass",
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
    for name, theme in THEMES.items():
        if domain in theme["domains"]:
            return theme
    return THEMES["Nebula / sci-fi"]

def theme_chart_colors(theme: dict, mode: str = "Light") -> list[str]:
    """Return a readable categorical palette for the active appearance."""
    palette = theme["dark" if mode == "Dark" else "light"]
    return [palette["accent"], palette["accent_2"], "#a18bd0", "#d99a60", "#6ca98b", "#d17f96", "#7ea4c8"]

def build_theme_css(theme: dict, mode: str = "Light", density: str = "Comfortable") -> str:
    """Build a responsive, contrast-aware stylesheet from a visual theme."""
    palette = theme["dark" if mode == "Dark" else "light"]
    compact = density == "Compact"
    tokens = {
        "__CANVAS__": palette["canvas"], "__SURFACE__": palette["surface"],
        "__SURFACE2__": palette["surface_2"], "__TEXT__": palette["text"],
        "__MUTED__": palette["muted"], "__LINE__": palette["line"],
        "__ACCENT__": palette["accent"], "__ACCENT2__": palette["accent_2"],
        "__ACCENT_SOFT__": palette["accent_soft"], "__SIDEBAR__": palette["sidebar"],
        "__SIDEBAR_TEXT__": palette["sidebar_text"], "__HERO1__": palette["hero_1"],
        "__HERO2__": palette["hero_2"], "__GLOW__": palette["glow"],
        "__PAD__": "1.05rem" if compact else "1.55rem",
        "__CARDPAD__": "12px 14px" if compact else "18px 20px",
    }
    css = """
<style>
:root{color-scheme:__SCHEME__;--canvas:__CANVAS__;--surface:__SURFACE__;--surface-2:__SURFACE2__;--text:__TEXT__;--muted:__MUTED__;--line:__LINE__;--accent:__ACCENT__;--accent-2:__ACCENT2__;--accent-soft:__ACCENT_SOFT__;--sidebar:__SIDEBAR__;--sidebar-text:__SIDEBAR_TEXT__;--hero-1:__HERO1__;--hero-2:__HERO2__;--glow:__GLOW__}
.stApp{background:radial-gradient(ellipse at 92% 0%,var(--glow),transparent 34%),var(--canvas)!important;color:var(--text)!important;font-family:Inter,"Segoe UI",sans-serif}
.main .block-container{max-width:1540px;padding:__PAD__ clamp(1rem,3vw,2.8rem) 4rem}
[data-testid="stSidebar"]{background:var(--sidebar)!important;border-right:1px solid color-mix(in srgb,var(--sidebar-text) 13%,transparent)}
[data-testid="stSidebar"] *{color:var(--sidebar-text)}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] small{color:color-mix(in srgb,var(--sidebar-text) 72%,transparent)!important}
[data-testid="stSidebar"] hr{border-color:color-mix(in srgb,var(--sidebar-text) 18%,transparent)}
[data-testid="stSidebar"] [role="radiogroup"]{gap:6px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:9px 11px;border:1px solid transparent;border-radius:11px;transition:background .18s,border-color .18s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:color-mix(in srgb,var(--sidebar-text) 9%,transparent)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:color-mix(in srgb,var(--accent) 24%,transparent);border-color:color-mix(in srgb,var(--accent) 55%,transparent)}
.main h1,.main h2,.main h3,.main h4,.main h5{color:var(--text)!important;letter-spacing:-.035em}
.main h1{font-size:clamp(1.65rem,3vw,2.25rem)!important;font-weight:760!important}
.main h2{font-size:clamp(1.25rem,2.2vw,1.65rem)!important;font-weight:730!important}
.main h3{font-size:1.08rem!important;font-weight:720!important}
.main p,.main li,.main label,.main [data-testid="stMarkdownContainer"]{color:var(--text)}
.main [data-testid="stCaptionContainer"],.main .subtle,.main .card-copy,.main .overview-intro{color:var(--muted)!important}
[data-testid="stMetric"]{background:linear-gradient(145deg,var(--surface),var(--surface-2))!important;border:1px solid var(--line)!important;border-radius:16px!important;padding:__CARDPAD__!important;box-shadow:0 8px 24px color-mix(in srgb,var(--text) 5%,transparent);min-height:96px}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-weight:650}
[data-testid="stMetricValue"]{color:var(--text)!important;font-weight:780}
.card,.insight,.signal-card,.health-card,.domain-card,.pagehead,.upload-panel,.upload-guidance,.workspace-topbar{transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:16px!important;padding:__CARDPAD__;box-shadow:0 8px 28px color-mix(in srgb,var(--text) 4%,transparent)}
.card:hover,.signal-card:hover,.domain-card:hover{transform:translateY(-2px);box-shadow:0 14px 34px color-mix(in srgb,var(--text) 8%,transparent)}
.card-title,.insight strong,.signal-title,.health-heading strong,.health-row strong,.health-row b,.workspace-filename{color:var(--text)!important}
.card-copy,.insight p,.signal-card p,.signal-next,.health-row span,.health-foot,.workspace-detail{color:var(--muted)!important}
.kicker,.card-label,.replace-label,.brandtag{color:var(--muted)!important;letter-spacing:.13em;font-weight:750}
.brandmark{background:linear-gradient(135deg,var(--accent),var(--accent-2))!important;box-shadow:0 6px 22px var(--glow);border-radius:12px}
.brandname{color:var(--sidebar-text)!important}
.hero{background:radial-gradient(circle at 88% 18%,var(--glow),transparent 32%),linear-gradient(118deg,var(--hero-1),var(--hero-2))!important;border:1px solid color-mix(in srgb,var(--accent) 40%,transparent);border-radius:22px!important;padding:clamp(22px,3vw,38px)!important;box-shadow:0 20px 55px color-mix(in srgb,var(--hero-1) 20%,transparent);animation:dp-rise .55s ease both}
.hero:before{content:"";position:absolute;width:240px;height:240px;right:-85px;top:-105px;border:1px solid color-mix(in srgb,var(--sidebar-text) 20%,transparent);border-radius:50%;box-shadow:0 0 0 24px color-mix(in srgb,var(--sidebar-text) 4%),0 0 0 50px color-mix(in srgb,var(--sidebar-text) 3%)}
.hero .eyebrow{color:color-mix(in srgb,var(--accent-2) 70%,white);font-size:.7rem;letter-spacing:.16em;font-weight:800}
.hero h1{color:#fff!important;font-size:clamp(1.75rem,3.2vw,2.55rem)!important;line-height:1.1!important}
.hero p{color:#e3eaf4!important;max-width:760px}
.hero-meta{color:color-mix(in srgb,#fff 72%,var(--accent-2));font-weight:750;letter-spacing:.13em}
.pagehead h2,.upload-panel h2{color:var(--text)!important}
.upload-panel p,.upload-guidance p,.pagehead .subtle{color:var(--muted)!important}
.dataset-summary>span,.format-list span,.signal-meta span,.signal-index,.signal-kind,.pill,.workspace-session,.insight .kind,.insight .next{background:var(--surface-2)!important;color:var(--muted)!important;border:1px solid var(--line)!important;border-radius:8px}
.dataset-summary .dataset-kind{background:var(--accent-soft)!important;color:var(--accent)!important;border-color:color-mix(in srgb,var(--accent) 25%,var(--line))!important}
.next-step{background:var(--accent-soft)!important;border:1px solid color-mix(in srgb,var(--accent) 22%,var(--line))!important;border-radius:12px}
.next-step strong{color:var(--accent)!important}
.overview-live{background:var(--accent-soft)!important;color:var(--accent)!important;border-color:var(--line)!important}
.health-track{background:var(--surface-2)!important}.health-track>span{background:linear-gradient(90deg,var(--accent),var(--accent-2))!important}
.sectionline{background:var(--line)!important}
.stButton>button,.stDownloadButton>button{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:11px!important;font-weight:680;min-height:2.55rem;transition:transform .18s,box-shadow .18s,border-color .18s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--accent)!important;box-shadow:0 8px 22px var(--glow);transform:translateY(-1px)}
.stButton>button[kind="primary"],button[kind="primary"]{background:linear-gradient(110deg,var(--accent),var(--accent-2))!important;color:#fff!important;border:0!important}
[data-testid="stTabs"] button{color:var(--muted)!important;font-weight:680}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--accent)!important;border-bottom-color:var(--accent)!important}
[data-testid="stPlotlyChart"],[data-testid="stDataFrame"],[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--line)!important;border-radius:14px!important;overflow:hidden}
[data-testid="stExpander"] summary,[data-testid="stExpander"] p{color:var(--text)!important}
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div,[data-testid="stDateInput"] input{background:var(--surface)!important;color:var(--text)!important;border-color:var(--line)!important;border-radius:10px!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:var(--surface)!important;color:var(--text)!important}
[data-baseweb="menu"] *,[role="option"]{color:var(--text)!important}
[data-testid="stFileUploader"]{background:var(--surface-2)!important;border:1px dashed var(--accent)!important;border-radius:14px!important}
[data-testid="stAlert"]{border-radius:13px!important}
[data-testid="stDataFrame"] iframe{color-scheme:__SCHEME__}
:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 65%,transparent)!important;outline-offset:3px!important}
@keyframes dp-rise{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:900px){.main .block-container{padding-left:1rem;padding-right:1rem}.hero{padding:22px!important}.workspace-topbar{flex-wrap:wrap;align-items:flex-start}.dataset-summary{gap:6px}.dataset-summary .dataset-recommendation{flex-basis:100%}}
@media(max-width:640px){.main .block-container{padding-top:.8rem;padding-bottom:2rem}.main h1{font-size:1.55rem!important}.main h2{font-size:1.2rem!important}[data-testid="stMetric"]{min-height:78px;padding:11px!important}[data-testid="stHorizontalBlock"]{gap:.55rem!important}.hero{border-radius:16px!important}.hero-meta{font-size:.58rem}.stButton>button,.stDownloadButton>button{width:100%}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
""".replace("__SCHEME__", "dark" if mode == "Dark" else "light")
    for key, value in tokens.items():
        css = css.replace(key, value)
    return css
