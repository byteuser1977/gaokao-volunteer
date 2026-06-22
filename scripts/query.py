#!/usr/bin/env python3
"""
高考志愿数据快速查询工具
兼容: Hermes / OpenClaw / Claude Code / Trae / Cursor
用法:
  python3 query.py 材料              # 搜索材料专业
  python3 query.py 1047 --school    # 按代号查院校详情
  python3 query.py --score 580 620  # 分数段筛选
  python3 query.py --tag 985        # 985院校列表
"""
import json, os, sys

def find_data():
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'gaokao-2026-beijing.json'),
        os.path.expanduser('~/.hermes/skills/gaokao-volunteer/data/gaokao-2026-beijing.json'),
        os.path.join(os.getcwd(), 'gaokao-2026-beijing.json'),
        '/mnt/d/temp/gaokao/gaokao-2026-beijing.json',
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("gaokao-2026-beijing.json not found")

def load():
    with open(find_data()) as f:
        return json.load(f)

def search_major(keyword, data):
    results = []
    for s in data['schools']:
        for g in s.get('major_groups', []):
            for m in g.get('majors', []):
                if keyword in m.get('name', ''):
                    results.append({
                        'code': s['code'], 'school': s['name'],
                        'location': s.get('location',''),
                        'tags': s.get('tags',[]),
                        'batch': s.get('batches',[])[0] if s.get('batches') else '',
                        'major': m['name'], 'quota': m['quota'],
                        'tuition': m['tuition'], 'subject': g.get('subject_requirements',''),
                        'restrictions': m.get('restrictions'),
                        'scores': g.get('admission_scores', {}),
                    })
    results.sort(key=lambda r: (
        0 if '北京' in r['location'] else 1,
        0 if '985' in r['tags'] else 1,
        0 if '211' in r['tags'] else 1,
        -(max(r['scores'].get('2025',{}).get('min',0),
              r['scores'].get('2024',{}).get('min',0)))
    ))
    return results

def get_school(code, data):
    return next((s for s in data['schools'] if s['code'] == code), None)

def by_score_range(lo, hi, data, year='2025'):
    r = []
    for s in data['schools']:
        sc = s.get('score_range',{}).get(year,{}).get('min',0)
        if lo <= sc <= hi:
            r.append(s)
    r.sort(key=lambda s: -s['score_range'][year]['min'])
    return r

def by_tag(tag, data):
    return sorted(
        [s for s in data['schools'] if tag in s.get('tags',[])],
        key=lambda s: (-s.get('score_range',{}).get('2025',{}).get('min',0)))

def show_school(school):
    print(f"\n## {school['code']} {school['name']} [{school['location']}]")
    print(f"标签: {'/'.join(school['tags']) if school['tags'] else '无'}")
    print(f"总名额: {school['total_quota']}人  批次: {school['batches']}")
    sr = school.get('score_range', {})
    for yr in ['2023','2024','2025']:
        if yr in sr:
            rk = sr[yr].get('min_rank','')
            print(f"  {yr}: {sr[yr]['min']}-{sr[yr]['max']}分" + (f" 位次{rk}" if rk else ""))
    for g in school.get('major_groups', []):
        subj = g.get('subject_requirements','?')
        sc = g.get('admission_scores',{})
        ss = ' | '.join(f"{y}:{sc[y]['min']}" for y in sc)
        print(f"\n  组{{{g['group_code']}}} | {subj}" + (f" | {ss}" if ss else ""))
        for m in g.get('majors', []):
            r = m.get('restrictions') or {}
            n = ', '.join(f"{k}={v}" for k,v in r.items() if v)
            print(f"    {m['code']} {m['name'][:48]:<48} {m['quota']:>3}人 ¥{m['tuition']:>6} {m['duration']}"
                  + (f"  [{n}]" if n else ""))

def table(results, n=50):
    print(f"| 代号 | 院校 | 标签 | 专业 | 人数 | 学费 | 选科 | 2024分 | 2025分 | 批次 |")
    print(f"|------|------|------|------|:--:|----:|------|:----:|:----:|------|")
    bm = {'early_a':'A段','early_b':'B段','regular':'普通','special_sports':'高水'}
    for r in results[:n]:
        t = '/'.join(r['tags'][:2]) or '-'
        s24 = r['scores'].get('2024',{}).get('min','—')
        s25 = r['scores'].get('2025',{}).get('min','—')
        b = bm.get(r['batch'], r['batch'][:2])
        print(f"| {r['code']} | {r['school']} | {t} | {r['major'][:32]} | {r['quota']} | {r['tuition']} | {r['subject'][:14]} | {s24} | {s25} | {b} |")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    data = load()
    a = sys.argv[1]
    if a == '--score' and len(sys.argv) >= 4:
        r = by_score_range(int(sys.argv[2]), int(sys.argv[3]), data)
        print(f"\n## {sys.argv[2]}-{sys.argv[3]}分段 — {len(r)}所")
        for s in r[:30]:
            sc = s.get('score_range',{}).get('2025',{}).get('min','—')
            print(f"  {s['code']} {s['name']:<20} {s['location']:<6} {'/'.join(s['tags'][:2]):<10} {sc}分")
    elif a == '--tag':
        t = sys.argv[2] if len(sys.argv) > 2 else '985'
        r = by_tag(t, data)
        print(f"\n## {t}院校 — {len(r)}所")
        for s in r[:50]:
            sc = s.get('score_range',{}).get('2025',{}).get('min','—')
            print(f"  {s['code']} {s['name']:<24} {s['location']:<8} {sc}分")
    elif a == '--school' and len(sys.argv) > 2:
        s = get_school(sys.argv[2], data)
        if s: show_school(s)
        else: print(f"未找到 {sys.argv[2]}")
    else:
        r = search_major(a, data)
        print(f"\n## '{a}' — {len(r)}条")
        table(r)
