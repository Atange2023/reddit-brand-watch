# usage: build_report.py store.json template.md out.md queries.tsv "Sub1,Sub2,..."
# Template placeholders: {{P:postid}}  {{Q:postid:upvotes[:text-prefix]}}  {{S:name}}
import json, re, sys
store, tpl_f, out_f, qtsv, targets = sys.argv[1:6]
S = json.load(open(store)); POSTS, COMMENTS = S['posts'], S['comments']
TARGET = [t.strip() for t in targets.split(',') if t.strip()]
tl = {t.lower() for t in TARGET}

def post(i):
    p = POSTS[i]
    pts = f"{p['pts']} 赞" if p['pts'] is not None else "赞数未提供"
    cm = f"{p['cmts']} 评论" if p['cmts'] is not None else "评论数未提供"
    return f"[{p['title']}]({p['url']})(r/{p['sub']} · {p['date']} · {pts} / {cm})"

def quote(i, up, prefix=''):
    m = [c for c in COMMENTS if c['post'] == i and c['up'] == int(up) and c['text'].startswith(prefix)]
    if len(m) != 1: sys.exit(f"quote lookup failed {i} {up} {prefix!r}: {len(m)} matches")
    c = m[0]
    t = c['text'] + ('…' if len(c['text']) >= 195 else '')
    link = c['link'] if re.search(r'/comment/[a-z0-9]+', c['link']) else POSTS[i]['url']
    return f"「{t}」— {c['up']} 赞([评论原文]({link}))"

qs = [l.rstrip('\n').split('\t') for l in open(qtsv) if l.strip()]
cnt = {q[0]: 0 for q in qs}
for p in POSTS.values():
    for s in p['src']:
        if s in cnt: cnt[s] += 1
empty = [q for q in qs if cnt[q[0]] == 0]
coverage = "| 查询 | 内容 | 返回帖子数 |\n|---|---|---|\n" + "\n".join(f"| {q[0]} | {q[1]} | {cnt[q[0]]} |" for q in qs)
in_t = [p for p in POSTS.values() if p['sub'].lower() in tl]
bd = {}
for p in in_t: bd[p['sub']] = bd.get(p['sub'], 0) + 1
hit = {s.lower() for s in bd}
stats = dict(nq=len(qs), nothing=len(empty), n_posts=len(POSTS), n_comments=len(COMMENTS), n_in=len(in_t),
             pct_out=f"{(1 - len(in_t) / max(len(POSTS), 1)):.0%}", n_hit=len(bd),
             n_targets=len(TARGET), miss='、'.join('r/' + t for t in TARGET if t.lower() not in hit) or '无',
             brk='、'.join(f'r/{k} {v} 帖' for k, v in sorted(bd.items(), key=lambda x: -x[1])),
             empty_list='；'.join(f'{q[0]}「{q[1]}」' for q in empty) or '无', coverage=coverage)
import glob, os
ver = ''
for f in sorted(glob.glob(os.path.dirname(os.path.abspath(qtsv)) + '/q*.md')):
    m = re.search(r'last30days v([\d.]+)', open(f).read())
    if m: ver = m.group(1); break
stats['version'] = ver or '未知'
tpl = open(tpl_f).read()
for k, v in stats.items(): tpl = tpl.replace('{{S:%s}}' % k, str(v))
tpl = re.sub(r'\{\{P:(\w+)\}\}', lambda m: post(m.group(1)), tpl)
tpl = re.sub(r'\{\{Q:(\w+):(\d+)(?::([^}]*))?\}\}', lambda m: quote(m.group(1), m.group(2), m.group(3) or ''), tpl)
open(out_f, 'w').write(tpl)
print('ok', {k: v for k, v in stats.items() if k != 'coverage'})
