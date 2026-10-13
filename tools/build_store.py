import re, glob, json, sys
batch, out = sys.argv[1], sys.argv[2]
pid = lambda u: (re.search(r'/comments/([a-z0-9]+)', u) or [None, None])[1]
posts, comments = {}, {}
for f in sorted(glob.glob(batch + '/q*.md')):
    tag = f.split('/')[-1][:-3]
    t = open(f).read()
    for m in re.finditer(r'\d+\. \[reddit\] (.*?)\n\s+- (\d{4}-\d\d-\d\d) \| r/(\S+) \| \[([^\]]*)\].*?\n\s+- URL: \[(\S+?)\]', t):
        title, date, sub, stat, url = m.groups()
        i = pid(url)
        if not i: continue
        pm, cm = re.search(r'(\d+)pts', stat), re.search(r'(\d+)cmt', stat)
        p = posts.setdefault(i, dict(id=i, url=url.rstrip('/'), title=title, date=date, sub=sub,
                                     pts=int(pm.group(1)) if pm else None, cmts=int(cm.group(1)) if cm else None, src=[]))
        if tag not in p['src']: p['src'].append(tag)
        if p['pts'] is None and pm: p['pts'] = int(pm.group(1))
        if p['cmts'] is None and cm: p['cmts'] = int(cm.group(1))
    for m in re.finditer(r'^- "(.*?)" — u/(\S+) \((\d+) upvotes\) — (https://reddit\.com/\S+)$', t, re.M):
        txt, u, up, link = m.groups()
        cid = re.search(r'/comment/([a-z0-9]*)', link)
        comments[(pid(link), cid.group(1) if cid else '', txt[:40])] = dict(post=pid(link), cid=cid.group(1) if cid else '', user=u, up=int(up), text=txt, link=link)
json.dump(dict(posts=posts, comments=list(comments.values())), open(out, 'w'), ensure_ascii=False, indent=1)
print(len(posts), 'posts', len(comments), 'comments')
