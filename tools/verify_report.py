# usage: verify_report.py store.json report.md   -> every cited post/quote must exist in store with identical numbers
import json, re, sys
S = json.load(open(sys.argv[1])); P, C = S['posts'], S['comments']; R = open(sys.argv[2]).read()
pid = lambda u: (re.search(r'/comments/([a-z0-9]+)', u) or [None, None])[1]
bad = 0
posts = re.findall(r'\[([^\]]+)\]\((https://www\.reddit\.com/r/[^)]*?/comments/[^)]*?)\)\(r/(\S+) · (\d{4}-\d\d-\d\d) · (?:(\d+) 赞|赞数未提供) / (?:(\d+) 评论|评论数未提供)\)', R)
for t, u, s, d, p, c in posts:
    x = P.get(pid(u))
    ok = x and x['url'] == u and x['title'] == t and x['sub'] == s and x['date'] == d and \
        ((x['pts'] is None and not p) or str(x['pts']) == p) and ((x['cmts'] is None and not c) or str(x['cmts']) == c)
    if not ok: bad += 1; print('POST MISMATCH', t, u)
quotes = re.findall(r'「(.*?)」— (\d+) 赞\(\[评论原文\]\((\S+?)\)\)', R)
for q, up, l in quotes:
    if not [c for c in C if c['text'].startswith(q.rstrip('…')) and c['up'] == int(up) and c['post'] == pid(l)]:
        bad += 1; print('QUOTE MISMATCH', q[:60], l)
loose = [u for u in re.findall(r'https://(?:www\.)?reddit\.com/r/[^)\s]*?/comments/[a-z0-9]+', R) if pid(u) not in P]
if loose: bad += len(loose); print('LINKS NOT IN STORE', loose)
print(f'post cites {len(posts)}, quote cites {len(quotes)}, problems {bad}')
sys.exit(1 if bad else 0)
