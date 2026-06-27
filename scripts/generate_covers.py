#!/usr/bin/env python3
import argparse, pathlib, re

POSTS = pathlib.Path('/opt/data/workspace/hugo-blog/content/posts')
OUT = pathlib.Path('/opt/data/workspace/hugo-blog/static/images/covers')
OUT.mkdir(parents=True, exist_ok=True)

PALETTES = {
    'java': ('#111827', '#f97316', '#fb923c', 'JAVA / SPRING', '⌘'),
    'docker': ('#082f49', '#0284c7', '#38bdf8', 'DOCKER / CONTAINERS', '⬡'),
    'linux': ('#0f172a', '#16a34a', '#4ade80', 'LINUX / DEVTOOLS', '>_'),
    'db': ('#2e1065', '#7c3aed', '#c084fc', 'DATABASE / SEARCH', '◫'),
    'cloud': ('#172554', '#4f46e5', '#818cf8', 'CLOUD / PVE / K8S', '☁'),
    'network': ('#083344', '#0891b2', '#67e8f9', 'NETWORK / NGINX', '⇄'),
    'storage': ('#3f1d2e', '#db2777', '#f9a8d4', 'STORAGE / IO', '▣'),
    'default': ('#111827', '#f59e0b', '#fbbf24', 'TECH / NOTES', '⚙'),
}

def classify(title, slug):
    t = (title + ' ' + slug).lower()
    if any(k in t for k in ['java', 'spring']): return 'java'
    if any(k in t for k in ['docker']): return 'docker'
    if any(k in t for k in ['mysql', 'dm8', 'elasticsearch', 'database', '达梦']): return 'db'
    if any(k in t for k in ['proxmox', 'kubernetes', 'k8s', 'k3s', 'cloud-init', 'pve']): return 'cloud'
    if any(k in t for k in ['iptables', 'nftables', 'ipv4', 'ipv6', 'nginx', 'ssl', 'cron', 'file-transfer', 'socat']): return 'network'
    if any(k in t for k in ['bcache', 'swap', 'iops', 'disk', 'gpt', 'gluster', 'mbr', '硬盘', '存储']): return 'storage'
    if any(k in t for k in ['linux', 'debian', 'macos', 'homebrew', 'python', 'svn', 'git', 'frontend', 'jnlp', 'drissionpage', 'caddy']): return 'linux'
    return 'default'

def short_title(title):
    title = re.sub(r'：.*$', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'（.*?）', '', title)
    return title[:28]

def read_title(md):
    m = re.search(r'^title:\s*"(.+?)"', md.read_text(encoding='utf-8'), re.M)
    return m.group(1) if m else md.stem

def write_svg(slug, title):
    cat = classify(title, slug)
    bg, c1, c2, label, glyph = PALETTES[cat]
    st = short_title(title)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-label="{title}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="60%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="shine" cx="82%" cy="18%" r="38%">
      <stop offset="0%" stop-color="rgba(255,255,255,.28)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
    </radialGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#g)"/>
  <rect width="1600" height="900" fill="url(#shine)"/>
  <g opacity=".12">
    <circle cx="1320" cy="170" r="160" fill="#fff"/>
    <circle cx="250" cy="760" r="190" fill="#fff"/>
    <path d="M1080 500h290M1080 570h220M1080 640h330" stroke="#fff" stroke-width="18" stroke-linecap="round"/>
    <rect x="1030" y="450" width="390" height="250" rx="30" stroke="#fff" stroke-width="10" fill="none"/>
  </g>
  <rect x="78" y="74" width="1444" height="752" rx="34" fill="rgba(15,23,42,.18)" stroke="rgba(255,255,255,.22)"/>
  <text x="128" y="186" font-size="34" font-family="Inter,Arial,sans-serif" fill="rgba(255,255,255,.9)">吾爱主机 · 技术博客</text>
  <text x="128" y="254" font-size="32" font-family="JetBrains Mono,Consolas,monospace" fill="rgba(255,255,255,.88)">{glyph} {label}</text>
  <text x="128" y="408" font-size="96" font-weight="800" font-family="Inter,'PingFang SC','Microsoft YaHei',sans-serif" fill="#fff">{st}</text>
  <text x="128" y="742" font-size="30" font-family="JetBrains Mono,Consolas,monospace" fill="rgba(255,255,255,.85)">blog.waihost.com</text>
</svg>'''
    (OUT / f'{slug}.svg').write_text(svg, encoding='utf-8')
    return cat

ap = argparse.ArgumentParser()
ap.add_argument('--slug', help='only generate one slug')
ap.add_argument('--missing-only', action='store_true', help='only generate covers that do not yet exist')
args = ap.parse_args()

files = sorted(POSTS.glob('*.md'))
if args.slug:
    files = [POSTS / f'{args.slug}.md']

count = 0
for md in files:
    if not md.exists():
        continue
    out = OUT / f'{md.stem}.svg'
    if args.missing_only and out.exists():
        continue
    title = read_title(md)
    cat = write_svg(md.stem, title)
    print(f'WROTE {md.stem}.svg [{cat}]')
    count += 1
print(f'Total: {count}')
