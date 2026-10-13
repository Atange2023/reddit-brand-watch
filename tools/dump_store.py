# usage: dump_store.py store.json   -> readable evidence dump (posts sorted by comment count, with their top comments)
import json, sys
S = json.load(open(sys.argv[1])); P, C = S['posts'], S['comments']
by = {}
for c in C: by.setdefault(c['post'], []).append(c)
for i, p in sorted(P.items(), key=lambda x: -(x[1]['cmts'] or 0)):
    print(f"\n## [{i}] r/{p['sub']} {p['date']} {p['pts']}pts/{p['cmts']}cmt | {p['title']}  <{','.join(p['src'])}>")
    for c in sorted(by.get(i, []), key=lambda c: -c['up']):
        print(f"   - ({c['up']}↑) {c['text'][:230]}")
