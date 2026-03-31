#!/usr/bin/env python3
"""
Yerbateca Static Site Generator
Reads data JSONs → generates complete HTML site.
Zero dependencies beyond Python stdlib.

All CSS + JS inlined — no path resolution issues.
"""
import json, os, re, shutil, sys
from html import escape
from datetime import date

# ── Config ──
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SITE_DIR, "data")
ASSETS_DIR = os.path.join(SITE_DIR, "assets")
IMG_DIR = os.path.join(ASSETS_DIR, "img", "plantas")

SITE_URL = "https://yerbateca.com"
SITE_NAME = "Yerbateca"
SITE_SUBTITLE = "Enciclopedia de Plantas Medicinales de América Latina"
TODAY = date.today().isoformat()

# ── Region mapping ──
REGION_MAP = {
    "PE": "andes", "BO": "andes", "EC": "andes", "CO": "andes",
    "BR": "amazonia", "VE": "amazonia",
    "CU": "caribe", "DO": "caribe", "PR": "caribe", "JM": "caribe",
    "MX": "mexico", "GT": "mesoamerica", "HN": "mesoamerica",
    "CR": "mesoamerica", "PA": "mesoamerica", "NI": "mesoamerica",
}

REGION_NAMES = {
    "andes": "Andes", "amazonia": "Amazonia", "caribe": "Caribe",
    "mesoamerica": "Mesoamérica", "mexico": "México", "pantropical": "Pantropical",
}

REGION_COLORS = {
    "andes": "#4A6741", "amazonia": "#8B6914", "caribe": "#3A6A7A",
    "mesoamerica": "#8B4A2A", "mexico": "#6A4A6A", "pantropical": "#6A7A4A",
}

REGION_DESCRIPTIONS = {
    "andes": "Los Andes abarcan desde Venezuela hasta Chile, una región con extraordinaria diversidad botánica a lo largo de pisos altitudinales que van desde los valles tropicales hasta la puna. Las comunidades andinas han desarrollado una farmacopea tradicional sofisticada durante milenios.",
    "amazonia": "La Amazonia alberga la mayor biodiversidad del planeta. Sus pueblos indígenas poseen conocimientos ancestrales sobre miles de plantas medicinales, muchas aún no estudiadas por la ciencia occidental.",
    "caribe": "Las islas del Caribe combinan tradiciones medicinales africanas, indígenas taínas y europeas, creando una herbolaria única rica en plantas tropicales.",
    "mesoamerica": "Mesoamérica, cuna de las civilizaciones maya y azteca, tiene una tradición herbolaria documentada desde los códices prehispánicos.",
    "mexico": "México posee una de las herbolarias más ricas del mundo, con más de 4,000 especies de plantas medicinales documentadas y una tradición que combina conocimientos prehispánicos y coloniales.",
    "pantropical": "Plantas de distribución pantropical, cultivadas y utilizadas medicinalmente en múltiples regiones de América Latina.",
}

# ════════════════════════════════════════════
# EMBEDDED CSS — all styles in one string
# ════════════════════════════════════════════

EMBEDDED_CSS = """
/* ── Design Tokens ── */
:root {
  --bg-page: #F0E8D8;
  --bg-card: #F5EFE2;
  --bg-sidebar: #EBE3D3;
  --bg-highlight: #E8E0CE;
  --bg-footer: #2C1810;
  --bg-nav: #2C1810;
  --ink: #2C1810;
  --ink-secondary: #5C4A3A;
  --ink-muted: #8A7A6A;
  --ink-faint: #A89A8A;
  --ink-inverse: #F0E8D8;
  --accent: #4A6741;
  --accent-hover: #5D8251;
  --accent-warm: #8B6914;
  --accent-warm-h: #A07D28;
  --accent-sepia: #5C4A3A;
  --border: #D4C4A8;
  --border-light: #E2D6C0;
  --border-strong: #BCA882;
  --safe: #4A6741;
  --caution: #A67B25;
  --danger: #8B3A2A;
  --region-andes: #4A6741;
  --region-amazonia: #8B6914;
  --region-caribe: #3A6A7A;
  --region-mesoamerica: #8B4A2A;
  --region-mexico: #6A4A6A;
  --region-pantropical: #6A7A4A;
  --font-heading: 'Cormorant Garamond', 'Georgia', serif;
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-latin: 'Cormorant Garamond', 'Georgia', serif;
  --text-xs: 0.72rem;
  --text-sm: 0.85rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.35rem;
  --text-2xl: 1.7rem;
  --text-3xl: 2.1rem;
  --text-4xl: 2.75rem;
  --text-5xl: 3.8rem;
  --sp-xs: 0.25rem;
  --sp-sm: 0.5rem;
  --sp-md: 1rem;
  --sp-lg: 1.5rem;
  --sp-xl: 2.5rem;
  --sp-2xl: 4rem;
  --sp-3xl: 6rem;
  --max-width: 1120px;
  --max-content: 720px;
  --sidebar-w: 320px;
  --radius: 3px;
  --radius-lg: 6px;
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --duration: 200ms;
}

/* ── Reset ── */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
img, svg { display: block; max-width: 100%; height: auto; }
a { color: inherit; text-decoration: none; }
button { font: inherit; cursor: pointer; border: none; background: none; }
ul, ol { list-style: none; }
table { border-collapse: collapse; width: 100%; }

/* ── Document ── */
html {
  background: var(--bg-page);
  min-height: 100vh;
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.75;
  color: var(--ink);
  background: var(--bg-page);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: 600;
  line-height: 1.25;
  color: var(--ink);
  letter-spacing: -0.01em;
}

h1 { font-size: var(--text-4xl); margin-bottom: var(--sp-lg); }
h2 { font-size: var(--text-2xl); margin-top: var(--sp-2xl); margin-bottom: var(--sp-md); }
h3 { font-size: var(--text-xl); margin-top: var(--sp-xl); margin-bottom: var(--sp-sm); }
p { max-width: 40em; margin-bottom: var(--sp-md); }
p + p { margin-top: var(--sp-sm); }

.content a, .prose a {
  color: var(--accent);
  text-decoration: underline;
  text-decoration-color: var(--border);
  text-underline-offset: 3px;
  transition: text-decoration-color var(--duration) var(--ease);
}
.content a:hover, .prose a:hover { text-decoration-color: var(--accent); }

.latin, .scientific-name, em.latin {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--accent-sepia);
}

/* ── Section Icons ── */
.section-icon {
  display: inline-block;
  width: 1.2em;
  height: 1.2em;
  vertical-align: -0.15em;
  margin-right: 0.4em;
  opacity: 0.5;
}

/* ── Navigation ── */
.site-nav {
  background: var(--bg-nav);
  border-bottom: 2px solid var(--accent-warm);
  padding: 0 var(--sp-xl);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 0;
  height: 56px;
}

.site-nav .nav-logo {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--ink-inverse);
  letter-spacing: 0.06em;
  margin-right: auto;
  display: flex;
  align-items: center;
  gap: 0.6em;
}

.site-nav .nav-logo .logo-icon {
  width: 24px;
  height: 24px;
  opacity: 0.7;
}

.site-nav .nav-links {
  display: flex;
  align-items: center;
  gap: 0;
  height: 100%;
}

.site-nav .nav-links a {
  color: var(--ink-inverse);
  opacity: 0.65;
  font-size: var(--text-sm);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  transition: opacity var(--duration) var(--ease);
  padding: 0 var(--sp-lg);
  height: 100%;
  display: flex;
  align-items: center;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.site-nav .nav-links a:hover {
  opacity: 1;
  border-bottom-color: var(--accent-warm);
}

/* ── Layout ── */
.site-wrapper {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--sp-xl);
}

.page-content {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--sp-2xl) 0;
}

/* ── Breadcrumb ── */
.breadcrumb {
  font-size: var(--text-sm);
  color: var(--ink-muted);
  margin: var(--sp-lg) 0 var(--sp-xl);
  font-family: var(--font-body);
}
.breadcrumb a {
  color: var(--ink-muted);
  text-decoration: underline;
  text-decoration-color: var(--border);
  text-underline-offset: 2px;
}
.breadcrumb a:hover { color: var(--ink-secondary); }
.breadcrumb .sep { margin: 0 0.4em; opacity: 0.4; }

/* ── Hero ── */
.hero {
  text-align: center;
  padding: var(--sp-3xl) 0 var(--sp-2xl);
}

.hero-title {
  font-family: var(--font-heading);
  font-size: var(--text-5xl);
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink);
  margin-bottom: var(--sp-sm);
}

.hero-subtitle {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--ink-muted);
  font-size: var(--text-xl);
  margin-bottom: var(--sp-xl);
  letter-spacing: 0.02em;
}

.hero-intro {
  max-width: 36em;
  margin: 0 auto;
  color: var(--ink-secondary);
  line-height: 1.8;
  font-size: var(--text-base);
}

/* ── Botanical Divider ── */
.botanical-rule {
  border: none;
  text-align: center;
  margin: var(--sp-xl) 0;
  color: var(--border-strong);
  font-size: var(--text-xs);
  letter-spacing: 0.4em;
  line-height: 1;
}
.botanical-rule::before {
  content: '\\2500\\2500\\2500  \\2726  \\2500\\2500\\2500';
}

/* ── Section Heading ── */
.section-heading {
  text-align: center;
  margin-bottom: var(--sp-xl);
}
.section-heading h2 {
  font-size: var(--text-2xl);
  margin-top: 0;
  margin-bottom: var(--sp-xs);
}
.section-heading p {
  color: var(--ink-muted);
  font-size: var(--text-sm);
  margin: 0 auto;
}

/* ── Plant Card ── */
.plant-card {
  display: block;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform var(--duration) var(--ease),
              box-shadow var(--duration) var(--ease);
  border: 1px solid var(--border-light);
}

.plant-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(44, 24, 16, 0.1);
  border-color: var(--border);
}

.plant-card .card-image {
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: var(--bg-page);
  display: flex;
  align-items: center;
  justify-content: center;
}

.plant-card .card-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  mix-blend-mode: darken;
  padding: var(--sp-sm);
}

.plant-card .card-placeholder {
  color: var(--border);
  font-size: 3rem;
  opacity: 0.4;
}

.plant-card .card-body {
  padding: var(--sp-md) var(--sp-md) var(--sp-lg);
}

.plant-card .card-title {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: var(--sp-xs);
}

.plant-card .card-latin {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--accent-sepia);
  font-size: var(--text-sm);
  margin-bottom: var(--sp-sm);
}

.plant-card .card-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  flex-wrap: wrap;
}

/* ── Plant Grid ── */
.plant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--sp-lg);
  margin: var(--sp-lg) 0;
}

/* ── Monograph Layout ── */
.monograph { max-width: var(--max-width); margin: 0 auto; }

.mono-header {
  margin-bottom: var(--sp-lg);
  border-bottom: 1px solid var(--border-light);
  padding-bottom: var(--sp-md);
}
.mono-header .mono-latin {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--accent-sepia);
  font-size: var(--text-lg);
  margin-bottom: 0;
}
.mono-header .mono-name {
  font-size: var(--text-3xl);
  margin-bottom: var(--sp-xs);
  line-height: 1.15;
}
.mono-header .mono-regions { margin: 0; }

.mono-body {
  display: grid;
  grid-template-columns: 1fr minmax(300px, 48%);
  gap: var(--sp-xl);
  align-items: start;
}

.mono-text {}
.mono-section h2 {
  margin-top: var(--sp-lg);
  margin-bottom: var(--sp-sm);
  font-size: var(--text-xl);
}
.mono-section:first-child h2 { margin-top: 0; }
.mono-section p { margin-bottom: var(--sp-sm); }

.mono-plate {
  position: sticky;
  top: 72px;
}
.mono-plate .ill-frame {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--sp-lg);
  cursor: pointer;
  transition: box-shadow var(--duration) var(--ease);
}
.mono-plate .ill-frame:hover {
  box-shadow: 0 8px 24px rgba(44, 24, 16, 0.08);
}
.mono-plate .ill-frame img {
  width: 100%;
  mix-blend-mode: darken;
  border-radius: var(--radius);
}
.mono-plate .ill-caption {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--accent-sepia);
  font-size: var(--text-sm);
  text-align: center;
  margin-top: var(--sp-sm);
  line-height: 1.4;
}
.mono-plate .ill-source {
  font-size: var(--text-xs);
  color: var(--ink-faint);
  text-align: center;
  margin-top: 2px;
}

.mono-footer {
  margin-top: var(--sp-xl);
  border-top: 1px solid var(--border-light);
  padding-top: var(--sp-xl);
}

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 99px;
  font-size: var(--text-xs);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.badge-family {
  background: rgba(74, 103, 65, 0.1);
  color: var(--accent);
  border: 1px solid rgba(74, 103, 65, 0.2);
}

/* ── Region Tags ── */
.region-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 99px;
  font-size: var(--text-xs);
  font-weight: 500;
  border: 1px solid;
}
.region-tag::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.region-andes       { color: var(--region-andes);       border-color: var(--region-andes); }
.region-amazonia    { color: var(--region-amazonia);    border-color: var(--region-amazonia); }
.region-caribe      { color: var(--region-caribe);      border-color: var(--region-caribe); }
.region-mesoamerica { color: var(--region-mesoamerica); border-color: var(--region-mesoamerica); }
.region-mexico      { color: var(--region-mexico);      border-color: var(--region-mexico); }
.region-pantropical { color: var(--region-pantropical); border-color: var(--region-pantropical); }

/* ── Region Card ── */
.region-card {
  display: block;
  padding: var(--sp-lg) var(--sp-xl);
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--border);
  transition: all var(--duration) var(--ease);
}
.region-card:hover {
  background: var(--bg-highlight);
  transform: translateX(4px);
}
.region-card .rc-name {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: 2px;
}
.region-card .rc-count {
  font-size: var(--text-sm);
  color: var(--ink-muted);
}

/* ── Region Map ── */
.region-map { max-width: 320px; }
.region-map path {
  fill: var(--border-light);
  stroke: var(--bg-page);
  stroke-width: 1.5;
  transition: fill-opacity 0.2s;
}
.region-map .map-mexico path { fill: var(--region-mexico); fill-opacity: 0.7; }
.region-map .map-mesoamerica path { fill: var(--region-mesoamerica); fill-opacity: 0.7; }
.region-map .map-caribe path { fill: var(--region-caribe); fill-opacity: 0.7; }
.region-map .map-andes path { fill: var(--region-andes); fill-opacity: 0.7; }
.region-map .map-amazonia path { fill: var(--region-amazonia); fill-opacity: 0.7; }
.region-map .map-neutral path { fill: var(--border); fill-opacity: 0.3; }
.region-map .map-highlighted path { fill-opacity: 1; }
.region-map .map-dimmed path { fill-opacity: 0.15; }
.region-map a:hover path { fill-opacity: 1; }

.map-with-cards {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--sp-xl);
  align-items: start;
  max-width: 700px;
  margin: var(--sp-md) auto;
}

@media (max-width: 600px) {
  .map-with-cards { grid-template-columns: 1fr; }
  .region-map { max-width: 240px; margin: 0 auto var(--sp-md); }
}

/* ── Use Tags ── */
.use-tag {
  display: inline-block;
  padding: 4px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 99px;
  font-size: var(--text-sm);
  color: var(--ink-secondary);
  margin: 3px 4px 3px 0;
  transition: all var(--duration) var(--ease);
}
.use-tag:hover {
  background: var(--bg-highlight);
  border-color: var(--border);
  color: var(--ink);
}

/* ── Data Table ── */
.data-table {
  font-size: var(--text-sm);
  margin: var(--sp-md) 0 var(--sp-lg);
}
.data-table th, .data-table td {
  padding: var(--sp-sm) var(--sp-md);
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}
.data-table th {
  font-weight: 500;
  color: var(--ink-secondary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom-color: var(--border);
}
.data-table tr:last-child td { border-bottom: none; }

.kv-table th {
  width: 28%;
  color: var(--ink-muted);
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
  font-size: var(--text-base);
  white-space: nowrap;
}
.kv-table td { font-weight: 500; }

/* ── Compound Pill ── */
.compound {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px 4px 8px;
  background: rgba(74, 103, 65, 0.06);
  border: 1px solid rgba(74, 103, 65, 0.12);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  margin: 3px 6px 3px 0;
}
.compound .compound-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
}

/* ── Info Box ── */
.info-box {
  padding: var(--sp-md) var(--sp-lg);
  border-left: 3px solid var(--border);
  background: var(--bg-card);
  border-radius: 0 var(--radius) var(--radius) 0;
  margin: var(--sp-lg) 0;
  font-size: var(--text-sm);
}
.info-box.warning {
  border-left-color: var(--caution);
  background: rgba(166, 123, 37, 0.04);
}

/* ── Related Grid ── */
.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--sp-md);
  margin: var(--sp-md) 0;
}

.related-card {
  display: block;
  padding: var(--sp-md) var(--sp-lg);
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  transition: all var(--duration) var(--ease);
}
.related-card:hover {
  background: var(--bg-highlight);
  border-color: var(--border);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(44, 24, 16, 0.06);
}

.related-card .related-name {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 600;
}
.related-card .related-latin {
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--accent-sepia);
  font-size: var(--text-sm);
}

/* ── Index Card Grid ── */
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--sp-md);
  margin: var(--sp-lg) 0;
}

.index-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-md) var(--sp-lg);
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  transition: all var(--duration) var(--ease);
}
.index-card:hover {
  background: var(--bg-highlight);
  border-color: var(--border);
}
.index-card .ic-name {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 600;
}
.index-card .ic-count {
  font-size: var(--text-sm);
  color: var(--ink-muted);
  white-space: nowrap;
}

/* ── Lightbox ── */
.lightbox {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(44, 24, 16, 0.90);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.lightbox.active { display: flex; }
.lightbox img {
  max-width: 90vw;
  max-height: 88vh;
  object-fit: contain;
  border-radius: var(--radius);
}
.lightbox .lightbox-caption {
  position: absolute;
  bottom: var(--sp-xl);
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-latin);
  font-style: italic;
  color: var(--ink-inverse);
  font-size: var(--text-lg);
  background: rgba(44, 24, 16, 0.6);
  padding: var(--sp-xs) var(--sp-lg);
  border-radius: var(--radius);
  white-space: nowrap;
}
.lightbox .lightbox-close {
  position: absolute;
  top: var(--sp-lg);
  right: var(--sp-lg);
  color: var(--ink-inverse);
  font-size: var(--text-3xl);
  opacity: 0.7;
  cursor: pointer;
  background: none;
  border: none;
  line-height: 1;
  transition: opacity var(--duration) var(--ease);
}
.lightbox .lightbox-close:hover { opacity: 1; }

/* ── Footer ── */
.site-footer {
  background: var(--bg-footer);
  color: var(--ink-inverse);
  padding: var(--sp-2xl) var(--sp-xl);
  margin-top: var(--sp-3xl);
  text-align: center;
  font-size: var(--text-sm);
}
.site-footer p { max-width: none; margin: var(--sp-xs) auto; opacity: 0.6; }
.site-footer .footer-brand {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  letter-spacing: 0.06em;
  opacity: 0.8;
  margin-bottom: var(--sp-md);
}

/* ── About / Prose ── */
.prose {
  max-width: var(--max-content);
  margin: 0 auto;
}
.prose p {
  max-width: none;
  line-height: 1.85;
  color: var(--ink-secondary);
}
.prose h2 { margin-top: var(--sp-xl); }
.prose ul {
  list-style: disc;
  padding-left: var(--sp-xl);
  margin: var(--sp-md) 0;
}
.prose li {
  margin-bottom: var(--sp-sm);
  color: var(--ink-secondary);
}

/* ── Stats Row ── */
.stats-row {
  display: flex;
  justify-content: center;
  gap: var(--sp-2xl);
  margin: var(--sp-xl) 0;
  padding: var(--sp-lg) 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
}
.stat { text-align: center; }
.stat .stat-num {
  font-family: var(--font-heading);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--accent);
}
.stat .stat-label {
  font-size: var(--text-sm);
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Print ── */
@media print {
  .site-nav, .site-footer, .lightbox { display: none; }
  body { background: white; color: #000; font-size: 11pt; line-height: 1.6; }
  .mono-plate img { mix-blend-mode: normal; }
  .mono-body { grid-template-columns: 1fr 45%; }
  .mono-plate { position: static; }
  .plant-card { break-inside: avoid; }
  h2 { page-break-after: avoid; }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  :root { --text-5xl: 2.5rem; --text-4xl: 2rem; }
  .site-wrapper { padding: 0 var(--sp-md); }
  .mono-body {
    grid-template-columns: 1fr;
  }
  .mono-plate {
    order: -1;
    position: static;
  }
  .mono-plate .ill-frame {
    max-width: 400px;
    margin: 0 auto;
  }
  .plant-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--sp-md); }
  .site-nav { padding: 0 var(--sp-md); height: auto; flex-wrap: wrap; padding-top: var(--sp-sm); padding-bottom: var(--sp-sm); }
  .site-nav .nav-links { gap: 0; flex-wrap: wrap; }
  .site-nav .nav-links a { padding: var(--sp-xs) var(--sp-sm); height: auto; font-size: var(--text-xs); }
  .hero { padding: var(--sp-2xl) 0 var(--sp-xl); }
  .stats-row { gap: var(--sp-lg); flex-wrap: wrap; }
  .index-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .plant-grid { grid-template-columns: 1fr 1fr; }
  .stats-row { flex-direction: column; gap: var(--sp-md); }
}

::selection { background: var(--accent); color: var(--ink-inverse); }
"""

# ════════════════════════════════════════════
# EMBEDDED JS — lightbox
# ════════════════════════════════════════════

EMBEDDED_JS = """
(function() {
  'use strict';
  var overlay = null;
  function create() {
    overlay = document.createElement('div');
    overlay.className = 'lightbox';
    overlay.innerHTML = '<button class="lightbox-close" aria-label="Cerrar">&times;</button>'
      + '<img alt="">'
      + '<div class="lightbox-caption"></div>';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay || e.target.classList.contains('lightbox-close')) close();
    });
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') close(); });
  }
  function open(src, caption) {
    if (!overlay) create();
    overlay.querySelector('img').src = src;
    overlay.querySelector('.lightbox-caption').textContent = caption || '';
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    if (!overlay) return;
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
  document.addEventListener('click', function(e) {
    var el = e.target.closest('.ill-frame');
    if (!el) return;
    e.preventDefault();
    var img = el.querySelector('img');
    if (!img) return;
    var full = img.dataset.full || img.src;
    open(full, img.alt || '');
  });
})();
"""

# ════════════════════════════════════════════
# LATIN AMERICA MAP — simplified inline SVG
# ════════════════════════════════════════════

LATAM_MAP_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" class="region-map">
  <g class="map-region map-mexico"><path d="M30,50 L120,30 L170,60 L180,100 L160,120 L140,110 L120,130 L100,120 L80,140 L60,130 L50,100 L30,80Z"/></g>
  <g class="map-region map-mesoamerica"><path d="M80,140 L100,135 L110,145 L95,155 L80,150Z"/><path d="M100,135 L125,130 L130,145 L110,150 L110,145Z"/><path d="M110,150 L130,145 L135,165 L115,170Z"/><path d="M115,170 L135,165 L138,185 L120,188Z"/><path d="M120,188 L138,185 L160,190 L155,200 L130,195Z"/></g>
  <g class="map-region map-caribe"><path d="M130,95 L190,80 L200,90 L185,100 L140,105Z"/><path d="M160,115 L175,112 L178,118 L163,120Z"/><path d="M220,100 L245,95 L248,108 L225,112Z"/><path d="M255,100 L270,98 L272,106 L257,108Z"/></g>
  <g class="map-region map-andes"><path d="M130,195 L155,200 L175,210 L190,250 L170,270 L145,260 L120,230 L110,210Z"/><path d="M110,260 L145,260 L140,290 L115,300 L105,280Z"/><path d="M105,280 L115,300 L140,290 L155,340 L145,400 L110,420 L90,380 L85,320Z"/><path d="M155,340 L200,350 L210,400 L190,430 L145,420 L145,400Z"/></g>
  <g class="map-region map-amazonia"><path d="M175,210 L200,195 L260,190 L280,210 L250,230 L220,250 L190,250Z"/><path d="M190,250 L220,250 L250,230 L280,210 L340,220 L380,260 L390,320 L370,380 L340,430 L300,480 L260,500 L230,480 L200,450 L190,430 L210,400 L200,350 L155,340 L140,290 L145,260 L170,270Z"/></g>
  <g class="map-neutral"><path d="M110,420 L145,420 L145,440 L135,500 L120,560 L105,600 L95,580 L90,520 L95,460Z"/><path d="M145,420 L190,430 L200,450 L230,480 L220,520 L190,560 L160,580 L135,560 L120,560 L135,500 L145,440Z"/></g>
</svg>'''


def render_region_map(highlight: str | None = None, link_regions: bool = True) -> str:
    """Render the Latin America map with optional region highlight."""
    svg = LATAM_MAP_SVG
    if highlight:
        # Add highlighted/dimmed classes
        for region in ["mexico", "mesoamerica", "caribe", "andes", "amazonia"]:
            old_class = f'map-region map-{region}'
            if region == highlight:
                new_class = f'map-region map-{region} map-highlighted'
            else:
                new_class = f'map-region map-{region} map-dimmed'
            svg = svg.replace(old_class, new_class)
    return svg


# ── Helpers ──
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[áà]', 'a', text)
    text = re.sub(r'[éè]', 'e', text)
    text = re.sub(r'[íì]', 'i', text)
    text = re.sub(r'[óò]', 'o', text)
    text = re.sub(r'[úùü]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text.strip('-')


def load_data():
    """Load and prepare all data."""
    with open(os.path.join(DATA_DIR, "herbs_raw.json")) as f:
        raw = json.load(f)

    plants = []
    for p in raw["plants"]:
        slug = slugify(p.get("id", p["common_name"]))
        regions = set()
        for cc in p.get("regions", []):
            r = REGION_MAP.get(cc)
            if r:
                regions.add(r)
        if not regions and p.get("origin") == "Naturalized":
            regions.add("pantropical")

        plants.append({
            "slug": slug,
            "common_name": p["common_name"],
            "common_names_alt": p.get("common_names_alt", []),
            "scientific_name": p["scientific_name"],
            "family": p["family"],
            "family_slug": slugify(p["family"]),
            "origin": p.get("origin", ""),
            "parts_used": p.get("parts_used", []),
            "traditional_uses": p.get("traditional_uses", []),
            "modern_evidence": p.get("modern_evidence", ""),
            "active_compounds": p.get("active_compounds", []),
            "articles": p.get("articles", []),
            "keywords": p.get("keywords", []),
            "regions": sorted(regions),
            "country_codes": p.get("regions", []),
            "products_linked": p.get("products_linked", []),
            "has_illustration": os.path.isdir(os.path.join(IMG_DIR, slug)),
        })

    conditions = {}
    for p in plants:
        for use in p["traditional_uses"]:
            slug_c = slugify(use)
            if slug_c not in conditions:
                conditions[slug_c] = {"slug": slug_c, "name": use.capitalize(), "plants": [], "count": 0}
            conditions[slug_c]["plants"].append(p["slug"])
            conditions[slug_c]["count"] += 1

    families = {}
    for p in plants:
        fs = p["family_slug"]
        if fs not in families:
            families[fs] = {"slug": fs, "name": p["family"], "plants": [], "count": 0}
        families[fs]["plants"].append(p["slug"])
        families[fs]["count"] += 1

    regions = {}
    for p in plants:
        for r in p["regions"]:
            if r not in regions:
                regions[r] = {"slug": r, "name": REGION_NAMES.get(r, r), "plants": [], "count": 0}
            regions[r]["plants"].append(p["slug"])
            regions[r]["count"] += 1

    plant_map = {p["slug"]: p for p in plants}
    for p in plants:
        related = set()
        for other in plants:
            if other["slug"] != p["slug"] and other["family"] == p["family"]:
                related.add(other["slug"])
        for use in p["traditional_uses"][:2]:
            for other in plants:
                if other["slug"] != p["slug"] and use in other["traditional_uses"]:
                    related.add(other["slug"])
        p["related_plants"] = sorted(related)[:6]

    return plants, dict(sorted(conditions.items())), dict(sorted(families.items())), dict(sorted(regions.items())), plant_map


# ════════════════════════════════════════════
# HTML FRAGMENTS
# ════════════════════════════════════════════

def html_head(title: str, description: str, path: str = "", canonical: str | None = None) -> str:
    canon = canonical or (SITE_URL + "/" + path)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} — {SITE_NAME}</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:type" content="article">
<meta property="og:locale" content="es_LA">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>{EMBEDDED_CSS}</style>
</head>
<body>
"""


LEAF_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="logo-icon"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>'


def html_nav(css_root: str = "") -> str:
    return f"""<nav class="site-nav">
  <a href="{css_root}" class="nav-logo">{LEAF_SVG} Yerbateca</a>
  <div class="nav-links">
    <a href="{css_root}plantas/">Plantas</a>
    <a href="{css_root}familias/">Familias</a>
    <a href="{css_root}regiones/">Regiones</a>
    <a href="{css_root}condiciones/">Condiciones</a>
    <a href="{css_root}sobre/">Sobre</a>
  </div>
</nav>
"""


def html_breadcrumb(items: list, css_root: str = "") -> str:
    parts = []
    for i, (label, href) in enumerate(items):
        if i < len(items) - 1:
            parts.append(f'<a href="{css_root}{href}">{escape(label)}</a>')
        else:
            parts.append(f'<span>{escape(label)}</span>')
    return '<div class="breadcrumb">' + '<span class="sep">&#8250;</span>'.join(parts) + '</div>'


def html_footer() -> str:
    return f"""<footer class="site-footer">
  <div class="footer-brand">{SITE_NAME}</div>
  <p>{SITE_SUBTITLE}</p>
  <p>Fuentes: PubMed, Scopus, Biodiversity Heritage Library</p>
  <p>La informaci&oacute;n es educativa y no sustituye consejo m&eacute;dico profesional.</p>
</footer>
<script>{EMBEDDED_JS}</script>
</body>
</html>
"""


def html_section_icon(icon_id: str) -> str:
    """Lucide icons (ISC license) — inline SVG, 24x24, 2px stroke."""
    _A = 'class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    icons = {
        "icon-sprout": f'<svg {_A}><path d="M14 9.536V7a4 4 0 0 1 4-4h1.5a.5.5 0 0 1 .5.5V5a4 4 0 0 1-4 4 4 4 0 0 0-4 4c0 2 1 3 1 5a5 5 0 0 1-1 3"/><path d="M4 9a5 5 0 0 1 8 4 5 5 0 0 1-8-4"/><path d="M5 21h14"/></svg>',
        "icon-leaf": f'<svg {_A}><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>',
        "icon-flask": f'<svg {_A}><path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/><path d="M8.5 2h7"/></svg>',
        "icon-book": f'<svg {_A}><path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/></svg>',
        "icon-shield": f'<svg {_A}><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>',
        "icon-globe": f'<svg {_A}><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
        "icon-map-pin": f'<svg {_A}><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>',
    }
    return icons.get(icon_id, '')


def html_plant_card(plant: dict, css_root: str = "") -> str:
    if plant["has_illustration"]:
        img_html = f'''<div class="card-image">
        <img src="{css_root}assets/img/plants/{plant["slug"]}/thumb.png"
             alt="Ilustraci&oacute;n bot&aacute;nica de {escape(plant["common_name"])}"
             loading="lazy" decoding="async">
      </div>'''
    else:
        img_html = '<div class="card-image"><div class="card-placeholder">&#9752;</div></div>'

    region_badges = ""
    for r in plant["regions"][:2]:
        name = REGION_NAMES.get(r, r)
        region_badges += f'<span class="region-tag region-{r}">{name}</span>'

    return f"""<a href="{css_root}plantas/{plant["slug"]}/" class="plant-card">
  {img_html}
  <div class="card-body">
    <div class="card-title">{escape(plant["common_name"])}</div>
    <div class="card-latin"><em>{escape(plant["scientific_name"])}</em></div>
    <div class="card-meta">
      <span class="badge badge-family">{escape(plant["family"])}</span>
      {region_badges}
    </div>
  </div>
</a>"""


# ════════════════════════════════════════════
# PAGE GENERATORS
# ════════════════════════════════════════════

def generate_homepage(plants: list, conditions: dict, families: dict, regions: dict) -> str:
    # Featured: prioritize plants with illustrations
    illustrated = [p for p in plants if p["has_illustration"]]
    non_illustrated = [p for p in plants if not p["has_illustration"]]
    featured = (illustrated + non_illustrated)[:12]
    cards = "\n".join(html_plant_card(p) for p in featured)

    # Stats
    n_plants = len(plants)
    n_illustrated = len(illustrated)
    n_families = len(families)
    n_regions = len(regions)

    # Region cards
    region_cards = ""
    for slug, info in sorted(regions.items(), key=lambda x: -x[1]["count"]):
        color = REGION_COLORS.get(slug, "#888")
        desc_text = REGION_DESCRIPTIONS.get(slug, "")
        short_desc = (desc_text[:100] + "...") if len(desc_text) > 100 else desc_text
        region_cards += f'''<a href="regiones/{slug}/" class="region-card" style="border-left-color:{color}">
      <div class="rc-name" style="color:{color}">{info["name"]}</div>
      <div class="rc-count">{info["count"]} plantas</div>
    </a>\n'''

    # Top conditions
    top_conditions = sorted(conditions.values(), key=lambda x: -x["count"])[:16]
    use_tags = ""
    for c in top_conditions:
        use_tags += f'<a href="condiciones/{c["slug"]}/" class="use-tag">{c["name"]} ({c["count"]})</a>\n'

    html = html_head(SITE_NAME, SITE_SUBTITLE)
    html += html_nav()
    html += f"""
<div class="site-wrapper">
  <header class="hero">
    <h1 class="hero-title">Yerbateca</h1>
    <p class="hero-subtitle">Enciclopedia de Plantas Medicinales de Am&eacute;rica Latina</p>
    <div class="botanical-rule"></div>
    <p class="hero-intro">
      Yerbateca re&uacute;ne monograf&iacute;as ilustradas de plantas medicinales tradicionales
      de Am&eacute;rica Latina. Cada entrada incluye l&aacute;minas bot&aacute;nicas hist&oacute;ricas,
      clasificaci&oacute;n cient&iacute;fica, compuestos activos y evidencia contempor&aacute;nea.
    </p>
  </header>

  <div class="stats-row">
    <div class="stat">
      <div class="stat-num">{n_plants}</div>
      <div class="stat-label">Plantas</div>
    </div>
    <div class="stat">
      <div class="stat-num">{n_families}</div>
      <div class="stat-label">Familias</div>
    </div>
    <div class="stat">
      <div class="stat-num">{n_regions}</div>
      <div class="stat-label">Regiones</div>
    </div>
    <div class="stat">
      <div class="stat-num">{n_illustrated}</div>
      <div class="stat-label">Ilustradas</div>
    </div>
  </div>

  <div class="page-content" style="max-width:var(--max-width);">
    <div class="section-heading">
      <h2>Plantas Destacadas</h2>
      <p>Monograf&iacute;as con ilustraciones bot&aacute;nicas restauradas</p>
    </div>
    <div class="plant-grid">
      {cards}
    </div>

    <div style="text-align:center;margin:var(--sp-xl) 0;">
      <a href="plantas/" class="use-tag" style="font-size:var(--text-base);padding:8px 24px;">
        Ver las {n_plants} plantas &rarr;
      </a>
    </div>

    <div class="botanical-rule"></div>

    <div class="section-heading">
      <h2>Por Regi&oacute;n</h2>
      <p>Plantas organizadas por su regi&oacute;n de origen</p>
    </div>
    <div class="map-with-cards">
      {render_region_map()}
      <div class="index-grid" style="grid-template-columns:1fr;">
        {region_cards}
      </div>
    </div>

    <div class="botanical-rule"></div>

    <div class="section-heading">
      <h2>Por Condici&oacute;n</h2>
      <p>Usos terap&eacute;uticos tradicionales</p>
    </div>
    <div style="text-align:center;max-width:650px;margin:var(--sp-md) auto;">
      {use_tags}
    </div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_plant_page(plant: dict, plant_map: dict, conditions: dict, css_root: str = "../../") -> str:
    # Illustration plate (right column)
    plate_html = ""
    if plant["has_illustration"]:
        plate_html = f"""<aside class="mono-plate">
      <div class="ill-frame">
        <img src="{css_root}assets/img/plants/{plant["slug"]}/medium.png"
             data-full="{css_root}assets/img/plants/{plant["slug"]}/full.png"
             alt="Ilustraci&oacute;n bot&aacute;nica de {escape(plant["scientific_name"])}"
             loading="lazy" decoding="async">
      </div>
      <div class="ill-caption"><em>{escape(plant["scientific_name"])}</em></div>
      <div class="ill-source">L&aacute;mina restaurada digitalmente</div>
    </aside>"""

    parts_html = ", ".join(p.capitalize() for p in plant["parts_used"]) if plant["parts_used"] else "&mdash;"
    origin_text = escape(plant.get("origin", "")) or "&mdash;"

    taxonomy = f"""<table class="data-table kv-table">
      <tr><th>Familia</th><td><a href="{css_root}familias/{plant["family_slug"]}/" style="color:var(--accent);text-decoration:underline;text-decoration-color:var(--border);text-underline-offset:2px;">{escape(plant["family"])}</a></td></tr>
      <tr><th>Nombre cient&iacute;fico</th><td><em class="latin">{escape(plant["scientific_name"])}</em></td></tr>
      <tr><th>Nombres comunes</th><td>{escape(", ".join([plant["common_name"]] + plant["common_names_alt"]))}</td></tr>
      <tr><th>Partes utilizadas</th><td>{parts_html}</td></tr>
      <tr><th>Origen</th><td>{origin_text}</td></tr>
    </table>"""

    region_tags = ""
    for r in plant["regions"]:
        name = REGION_NAMES.get(r, r)
        region_tags += f'<a href="{css_root}regiones/{r}/" class="region-tag region-{r}">{name}</a> '

    compounds_html = ""
    if plant["active_compounds"]:
        pills = "".join(f'<span class="compound"><span class="compound-dot"></span>{escape(c)}</span>' for c in plant["active_compounds"])
        compounds_html = f"""<section class="mono-section">
      <h2>{html_section_icon("icon-flask")} Compuestos Activos</h2>
      <div style="margin:var(--sp-sm) 0;">{pills}</div>
    </section>"""

    evidence_html = ""
    if plant["modern_evidence"]:
        articles_inline = ""
        if plant["articles"]:
            links = "".join(
                f'<div style="margin-top:var(--sp-sm);"><a href="https://botanicaandina.com/noticias/{art}/" style="color:var(--accent);text-decoration:underline;text-decoration-color:var(--border);text-underline-offset:2px;" target="_blank" rel="noopener">{escape(art.replace("-", " ").capitalize())}</a></div>'
                for art in plant["articles"][:5]
            )
            articles_inline = f'<div style="margin-top:var(--sp-md);">{links}</div>'
        evidence_html = f"""<section class="mono-section">
      <h2>{html_section_icon("icon-book")} Evidencia Cient&iacute;fica</h2>
      <p>{escape(plant["modern_evidence"])}</p>
      {articles_inline}
    </section>"""
    elif plant["articles"]:
        links = "".join(
            f'<div style="margin-bottom:var(--sp-sm);"><a href="https://botanicaandina.com/noticias/{art}/" style="color:var(--accent);text-decoration:underline;text-decoration-color:var(--border);text-underline-offset:2px;" target="_blank" rel="noopener">{escape(art.replace("-", " ").capitalize())}</a></div>'
            for art in plant["articles"][:5]
        )
        evidence_html = f"""<section class="mono-section">
      <h2>Investigaciones Relacionadas</h2>
      <div>{links}</div>
    </section>"""

    uses_html = ""
    if plant["traditional_uses"]:
        items = "".join(
            f'<a href="{css_root}condiciones/{slugify(use)}/" class="use-tag">{use.capitalize()}</a>\n'
            for use in plant["traditional_uses"]
        )
        uses_html = f"""<section class="mono-section">
      <h2>{html_section_icon("icon-leaf")} Usos Tradicionales</h2>
      <div style="display:flex;flex-wrap:wrap;gap:var(--sp-sm);">{items}</div>
    </section>"""

    precautions_html = f"""<section class="mono-section">
      <h2>{html_section_icon("icon-shield")} Precauciones</h2>
      <div class="info-box warning">
        <p>Esta informaci&oacute;n es educativa y no sustituye el consejo m&eacute;dico profesional.
        Consulte a un profesional de la salud antes de usar plantas medicinales,
        especialmente si est&aacute; embarazada, amamantando o toma medicamentos.</p>
      </div>
    </section>"""

    related_html = ""
    if plant["related_plants"]:
        cards = ""
        for slug in plant["related_plants"][:4]:
            rp = plant_map.get(slug)
            if rp:
                cards += f"""<a href="{css_root}plantas/{slug}/" class="related-card">
          <div class="related-name">{escape(rp["common_name"])}</div>
          <div class="related-latin"><em>{escape(rp["scientific_name"])}</em></div>
        </a>\n"""
        if cards:
            related_html = f"""<footer class="mono-footer">
      <h2>Plantas Relacionadas</h2>
      <div class="related-grid">{cards}</div>
    </footer>"""

    title = plant["common_name"]
    desc = f"{plant['common_name']} ({plant['scientific_name']}) \u2014 propiedades, usos tradicionales, evidencia cient\u00edfica y compuestos activos."

    # For plants without illustration, use single-column layout
    body_class = "mono-body" if plant["has_illustration"] else "mono-body"
    grid_style = "" if plant["has_illustration"] else ' style="grid-template-columns:1fr;"'

    html = html_head(title, desc, f"plantas/{plant['slug']}/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Plantas", "plantas/"), (title, "")], css_root)}

  <article class="monograph content">
    <header class="mono-header">
      <p class="mono-latin"><em>{escape(plant["scientific_name"])}</em></p>
      <h1 class="mono-name">{escape(title)}</h1>
      <div class="mono-regions">{region_tags}</div>
    </header>

    <div class="{body_class}"{grid_style}>
      <div class="mono-text">
        <section class="mono-section">
          <h2>{html_section_icon("icon-sprout")} Clasificaci&oacute;n Bot&aacute;nica</h2>
          {taxonomy}
        </section>

        {uses_html}
        {compounds_html}
        {evidence_html}
        {precautions_html}
      </div>

      {plate_html}
    </div>

    {related_html}
  </article>
</div>
"""
    html += html_footer()
    return html


def generate_plants_index(plants: list, css_root: str = "../") -> str:
    cards = "\n".join(html_plant_card(p, css_root) for p in sorted(plants, key=lambda x: x["common_name"]))
    html = html_head("Plantas Medicinales", f"{len(plants)} plantas medicinales de América Latina", "plantas/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Plantas", "")], css_root)}
  <div class="page-content" style="max-width:var(--max-width);">
    <h1>Plantas Medicinales</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      {len(plants)} monograf&iacute;as de plantas medicinales tradicionales de Am&eacute;rica Latina.
    </p>
    <div class="plant-grid">{cards}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_condition_page(condition: dict, plant_map: dict, css_root: str = "../../") -> str:
    cards = ""
    for slug in condition["plants"]:
        p = plant_map.get(slug)
        if p:
            cards += html_plant_card(p, css_root)

    desc = f"Plantas medicinales con propiedades para {condition['name'].lower()}."
    html = html_head(condition["name"], desc, f"condiciones/{condition['slug']}/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Condiciones", "condiciones/"), (condition["name"], "")], css_root)}
  <div class="page-content content" style="max-width:var(--max-width);">
    <h1>{escape(condition["name"])}</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      {condition["count"]} plantas medicinales con propiedades para {escape(condition["name"].lower())}.
    </p>
    <div class="plant-grid">{cards}</div>
    <div class="info-box">
      <p>La informaci&oacute;n presentada es educativa. Consulte a un profesional de la salud.</p>
    </div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_conditions_index(conditions: dict, css_root: str = "../") -> str:
    items = ""
    for c in sorted(conditions.values(), key=lambda x: -x["count"]):
        items += f'<a href="{c["slug"]}/" class="index-card"><span class="ic-name">{c["name"]}</span><span class="ic-count">{c["count"]} plantas</span></a>\n'

    html = html_head("Condiciones", "Plantas medicinales organizadas por condición o uso terapéutico", "condiciones/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Condiciones", "")], css_root)}
  <div class="page-content" style="max-width:var(--max-width);">
    <h1>Condiciones</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      Plantas medicinales organizadas por condici&oacute;n o uso terap&eacute;utico.
    </p>
    <div class="index-grid">{items}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_region_page(region: dict, plant_map: dict, css_root: str = "../../") -> str:
    cards = ""
    for slug in region["plants"]:
        p = plant_map.get(slug)
        if p:
            cards += html_plant_card(p, css_root)

    desc_text = REGION_DESCRIPTIONS.get(region["slug"], "")
    desc_html = f'<p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);max-width:40em;">{escape(desc_text)}</p>' if desc_text else ''

    desc = f"Plantas medicinales de la región {region['name']}."
    color = REGION_COLORS.get(region["slug"], "#888")
    html = html_head(region["name"], desc, f"regiones/{region['slug']}/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Regiones", "regiones/"), (region["name"], "")], css_root)}
  <div class="page-content content" style="max-width:var(--max-width);">
    <div style="display:flex;gap:var(--sp-xl);align-items:start;margin-bottom:var(--sp-xl);">
      <div>
        <h1 style="color:{color}">Plantas de {escape(region["name"])}</h1>
        <p style="color:var(--ink-muted);margin-bottom:var(--sp-sm);">
          {region["count"]} plantas medicinales
        </p>
        {desc_html}
      </div>
      <div style="flex-shrink:0;">
        {render_region_map(highlight=region["slug"])}
      </div>
    </div>
    <div class="plant-grid">{cards}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_regions_index(regions: dict, css_root: str = "../") -> str:
    items = ""
    for r in sorted(regions.values(), key=lambda x: -x["count"]):
        color = REGION_COLORS.get(r["slug"], "#888")
        items += f'<a href="{r["slug"]}/" class="region-card" style="border-left-color:{color}"><span class="rc-name" style="color:{color}">{r["name"]}</span><span class="rc-count">{r["count"]} plantas</span></a>\n'

    html = html_head("Regiones", "Plantas medicinales por región geográfica", "regiones/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Regiones", "")], css_root)}
  <div class="page-content" style="max-width:var(--max-width);">
    <h1>Regiones</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      Plantas medicinales por regi&oacute;n geogr&aacute;fica de Am&eacute;rica Latina.
    </p>
    <div class="index-grid">{items}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_family_page(family: dict, plant_map: dict, css_root: str = "../../") -> str:
    cards = ""
    for slug in family["plants"]:
        p = plant_map.get(slug)
        if p:
            cards += html_plant_card(p, css_root)

    desc = f"Familia {family['name']} — plantas medicinales."
    html = html_head(family["name"], desc, f"familias/{family['slug']}/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Familias", "familias/"), (family["name"], "")], css_root)}
  <div class="page-content content" style="max-width:var(--max-width);">
    <h1>{escape(family["name"])}</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      {family["count"]} plantas medicinales de la familia {escape(family["name"])}.
    </p>
    <div class="plant-grid">{cards}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_families_index(families: dict, css_root: str = "../") -> str:
    items = ""
    for f in sorted(families.values(), key=lambda x: -x["count"]):
        items += f'<a href="{f["slug"]}/" class="index-card"><span class="ic-name">{f["name"]}</span><span class="ic-count">{f["count"]} plantas</span></a>\n'

    html = html_head("Familias Botánicas", "Plantas medicinales por familia botánica", "familias/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Familias", "")], css_root)}
  <div class="page-content" style="max-width:var(--max-width);">
    <h1>Familias Bot&aacute;nicas</h1>
    <p style="color:var(--ink-secondary);margin-bottom:var(--sp-xl);">
      Plantas medicinales organizadas por familia bot&aacute;nica.
    </p>
    <div class="index-grid">{items}</div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_about(css_root: str = "../") -> str:
    html = html_head("Sobre Yerbateca", "Enciclopedia de plantas medicinales de América Latina", "sobre/")
    html += html_nav(css_root)
    html += f"""
<div class="site-wrapper">
  {html_breadcrumb([("Inicio", ""), ("Sobre", "")], css_root)}
  <div class="page-content">
    <h1 style="text-align:center;">Sobre Yerbateca</h1>
    <div class="botanical-rule"></div>
    <div class="prose">
      <p>
        Yerbateca es un proyecto de documentaci&oacute;n bot&aacute;nica que re&uacute;ne informaci&oacute;n
        sobre plantas medicinales utilizadas tradicionalmente en Am&eacute;rica Latina.
        Nuestro objetivo es preservar y difundir el conocimiento etnobotánico de la regi&oacute;n,
        conectando la sabidur&iacute;a ancestral con la investigaci&oacute;n cient&iacute;fica moderna.
      </p>
      <p>
        Las ilustraciones provienen de atlas bot&aacute;nicos del siglo XIX restaurados
        digitalmente mediante inteligencia artificial, preservando la precisi&oacute;n
        morfol&oacute;gica original mientras se mejora la calidad visual. Cada l&aacute;mina
        ha sido procesada para integrarse arm&oacute;nicamente con el dise&ntilde;o general
        del sitio.
      </p>
      <p>
        La informaci&oacute;n cient&iacute;fica se basa en fuentes revisadas por pares
        (PubMed, Scopus) y monograf&iacute;as de la EMA/ESCOP. Cada entrada incluye
        clasificaci&oacute;n taxon&oacute;mica, compuestos activos documentados,
        usos tradicionales y evidencia cl&iacute;nica disponible.
      </p>

      <h2>Fuentes Principales</h2>
      <ul>
        <li><strong>K&ouml;hler&rsquo;s Medizinal-Pflanzen</strong> (1887) — Atlas bot&aacute;nico alemán</li>
        <li><strong>American Medicinal Plants</strong> (Millspaugh, 1887)</li>
        <li><strong>Album de la Flora Argentina</strong> (1862)</li>
        <li><strong>Biodiversity Heritage Library</strong> — Archivo digital de historia natural</li>
        <li><strong>PubMed / MEDLINE</strong> — Base de datos de literatura biom&eacute;dica</li>
        <li><strong>Scopus</strong> — &Iacute;ndice de literatura cient&iacute;fica</li>
      </ul>

      <h2>Aviso Legal</h2>
      <p>
        La informaci&oacute;n presentada en Yerbateca tiene fines exclusivamente educativos
        e informativos. No constituye consejo m&eacute;dico, diagn&oacute;stico ni tratamiento.
        Consulte siempre a un profesional de la salud calificado antes de utilizar
        plantas medicinales, especialmente si est&aacute; embarazada, amamantando,
        toma medicamentos o padece alguna condici&oacute;n m&eacute;dica.
      </p>
    </div>
  </div>
</div>
"""
    html += html_footer()
    return html


def generate_sitemap(plants: list, conditions: dict, families: dict, regions: dict) -> str:
    urls = [SITE_URL + "/"]
    urls.append(SITE_URL + "/plantas/")
    for p in plants:
        urls.append(f"{SITE_URL}/plantas/{p['slug']}/")
    urls.append(SITE_URL + "/condiciones/")
    for c in conditions.values():
        urls.append(f"{SITE_URL}/condiciones/{c['slug']}/")
    urls.append(SITE_URL + "/regiones/")
    for r in regions.values():
        urls.append(f"{SITE_URL}/regiones/{r['slug']}/")
    urls.append(SITE_URL + "/familias/")
    for f in families.values():
        urls.append(f"{SITE_URL}/familias/{f['slug']}/")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod></url>\n'
    xml += '</urlset>'
    return xml


# ════════════════════════════════════════════
# MAIN BUILD
# ════════════════════════════════════════════

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build() -> None:
    print("Loading data...")
    plants, conditions, families, regions, plant_map = load_data()
    print(f"  {len(plants)} plants, {len(conditions)} conditions, {len(families)} families, {len(regions)} regions")
    ill_count = sum(1 for p in plants if p["has_illustration"])
    print(f"  {ill_count} with illustrations")

    print("Generating homepage...")
    write_file(os.path.join(SITE_DIR, "index.html"), generate_homepage(plants, conditions, families, regions))

    print("Generating plant pages...")
    for p in plants:
        path = os.path.join(SITE_DIR, "plantas", p["slug"], "index.html")
        write_file(path, generate_plant_page(p, plant_map, conditions))

    write_file(os.path.join(SITE_DIR, "plantas", "index.html"), generate_plants_index(plants))

    print("Generating condition pages...")
    for c in conditions.values():
        path = os.path.join(SITE_DIR, "condiciones", c["slug"], "index.html")
        write_file(path, generate_condition_page(c, plant_map))
    write_file(os.path.join(SITE_DIR, "condiciones", "index.html"), generate_conditions_index(conditions))

    print("Generating region pages...")
    for r in regions.values():
        path = os.path.join(SITE_DIR, "regiones", r["slug"], "index.html")
        write_file(path, generate_region_page(r, plant_map))
    write_file(os.path.join(SITE_DIR, "regiones", "index.html"), generate_regions_index(regions))

    print("Generating family pages...")
    for f in families.values():
        path = os.path.join(SITE_DIR, "familias", f["slug"], "index.html")
        write_file(path, generate_family_page(f, plant_map))
    write_file(os.path.join(SITE_DIR, "familias", "index.html"), generate_families_index(families))

    print("Generating about page...")
    write_file(os.path.join(SITE_DIR, "sobre", "index.html"), generate_about())

    write_file(os.path.join(SITE_DIR, "sitemap.xml"), generate_sitemap(plants, conditions, families, regions))
    write_file(os.path.join(SITE_DIR, "robots.txt"), "User-agent: *\nDisallow: /\n")

    total = len(plants) + len(conditions) + len(families) + len(regions) + 6
    print(f"\nDone: {total} pages generated")
    print(f"  {len(plants)} plant monographs ({ill_count} illustrated)")
    print(f"  {len(conditions)} condition pages")
    print(f"  {len(families)} family pages")
    print(f"  {len(regions)} region pages")
    print(f"  + homepage, indexes, about, sitemap")


if __name__ == "__main__":
    build()
