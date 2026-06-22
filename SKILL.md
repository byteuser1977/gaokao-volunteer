---
name: gaokao-volunteer
description: >-
  高考志愿填报辅助工具。基于北京2026年招生数据（533所院校、3070个专业、985/211/双一流标签、2023-2025分数线位次），
  支持按专业关键词搜索、按院校代号查询、按分数段/标签筛选、物化选科匹配、色弱限制检查。
  适用场景：专业推荐、分数对比、志愿清单生成。
version: 1.1.0
---

# 高考志愿填报 Skill

> 兼容：Hermes / OpenClaw / Claude Code / Trae / Cursor

## 数据文件

JSON数据随skill分发，位于 `data/gaokao-2026-beijing.json`（1.2MB）。

在任何AI工具中使用时，先加载数据：

```python
import json, os

# 自动定位数据文件
def load_data():
    candidates = [
        os.path.join(os.path.dirname(__file__), 'data', 'gaokao-2026-beijing.json'),
        os.path.expanduser('~/.hermes/skills/gaokao-volunteer/data/gaokao-2026-beijing.json'),
        os.path.join(os.getcwd(), 'gaokao-2026-beijing.json'),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    raise FileNotFoundError("gaokao-2026-beijing.json not found")

data = load_data()
# data.keys() → ['meta', 'schools']
# data['schools'] → 533所院校
# data['schools'][0].keys() → ['code','name','location','tags','batches','total_quota','major_groups','score_range']
```

## 数据结构速查

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | string | 院校代号(4位) | `"1047"` |
| `name` | string | 院校全称 | `"北京航空航天大学"` |
| `location` | string | 所在地 | `"北京"` |
| `tags` | string[] | 985/211/双一流 | `["985","211","双一流"]` |
| `batches` | string[] | 招生批次 | `["regular"]` 或 `["early_a"]` |
| `total_quota` | int | 在京招生总人数 | `275` |
| `score_range` | object | 全校分数区间 | `{"2024":{"min":649,"max":667},"2025":{"min":640}}` |
| `major_groups` | array | 专业组列表 | 见下 |

**major_groups 子结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_code` | string | 专业组编号，如`"02"` |
| `subject_requirements` | string | 选考要求，如`"物理+化学(均须选考)"` |
| `admission_scores` | object | `{"2024":{"min":667,"min_rank":1552},"2025":{"min":657}}` |
| `majors` | array | 专业列表 |

**majors 子结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 专业代码(2位) |
| `name` | string | 专业名称（可能含OCR残留）|
| `quota` | int | 招生人数 |
| `tuition` | int | 学费(元/年) |
| `duration` | string | 学制，`"四年"`/`"五年"`/`"八年"` |
| `restrictions` | object/null | 限制条件：`gender`/`vision`/`language`/`physical`/`interview` |
| `notes` | string | 备注 |

## 批次代码

| 值 | 说明 | 包含院校类型 |
|----|------|------------|
| `early_a` | 本科提前批A段 | 军校、公安、消防、外交、综评、飞行 |
| `early_b` | 本科提前批B段 | 双培计划、地方农村专项 |
| `special_sports` | 特殊类型招生 | 高水平运动队 |
| `regular` | 本科普通批 | 所有普通本科 |

## 调用流程（必读）

**每次调用此skill时，第一步必须询问考生基本信息，不得跳过：**

```
请提供以下信息：
1. 性别：男 / 女
2. 选考科目：物理/化学/生物/历史/地理/思想政治（勾选3门）
3. 是否有体检特殊问题？
   - 色弱 / 色盲 / 单色识别能力异常
   - 身高限制（如 <1.65m）
   - 其他体检异常（如肝功能、视力等）
4. 预估分数/位次（如有）
```

询问后才根据回答进行专业筛选。筛选时自动排除：
- 色弱/色盲 → 排除化学类、生物类、医学类、材料类、环境类、食品类、地质类相关专业
- 性别限制 → 排除标注「只招男生/女生」的不符专业
- 身高限制 → 排除有身高要求的专业（军事、公安、体育等）

如果会话上下文中已有这些信息（如memory中保存了用户画像），可直接使用无需重复询问。

## 用户画像（已知信息）

- 2026年北京高考，**585分**，朝阳区**1350名**
- 选科：**物理、化学、生物**
- **色弱**：需避开化学/生物/医学类专业（重点关注 `restrictions.vision` 字段）
- 目标：北航、北理、人大、北邮

## 查询模式

### 按专业关键词搜索

```python
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
                        'major': m['name'], 'quota': m['quota'],
                        'tuition': m['tuition'],
                        'subject': g.get('subject_requirements',''),
                        'restrictions': m.get('restrictions'),
                        'scores': g.get('admission_scores', {}),
                    })
    # 排序：北京优先 > 985 > 211 > 分数降序
    results.sort(key=lambda r: (
        0 if '北京' in r['location'] else 1,
        0 if '985' in r['tags'] else 1,
        0 if '211' in r['tags'] else 1,
        -(max(r['scores'].get('2025',{}).get('min',0),
              r['scores'].get('2024',{}).get('min',0)))
    ))
    return results
```

### 按院校代号查询

```python
def get_school(code, data):
    return next((s for s in data['schools'] if s['code'] == code), None)
```

### 按分数段筛选

```python
def by_score_range(min_score, max_score, data, year='2025'):
    results = []
    for s in data['schools']:
        sr = s.get('score_range', {}).get(year, {})
        score = sr.get('min', 0)
        if min_score <= score <= max_score:
            results.append(s)
    results.sort(key=lambda s: -s['score_range'][year]['min'])
    return results
```

### 按标签筛选

```python
def by_tag(tag, data):  # tag: '985' / '211' / '双一流'
    return [s for s in data['schools'] if tag in s.get('tags',[])]
```

### 色弱限制检查

```python
VISION_KEYWORDS = ['色弱', '色盲', '单色识别', '不招色']

def is_vision_restricted(major):
    """检查专业是否有色觉限制"""
    name = major.get('name', '')
    notes = major.get('notes', '')
    restrictions = major.get('restrictions') or {}
    text = name + notes + str(restrictions.get('vision', ''))
    return any(kw in text for kw in VISION_KEYWORDS)

def check_vision_for_school(school):
    """列出某校所有色觉限制专业"""
    warnings = []
    for g in school.get('major_groups', []):
        for m in g.get('majors', []):
            if is_vision_restricted(m):
                warnings.append(m['name'])
    return warnings
```

### 物化选科匹配

```python
def match_physics_chemistry(data):
    """筛选所有物理+化学专业"""
    results = []
    for s in data['schools']:
        for g in s.get('major_groups', []):
            subj = g.get('subject_requirements', '')
            if '物理' in subj and '化学' in subj:
                for m in g.get('majors', []):
                    results.append({
                        'school': s['name'],
                        'code': s['code'],
                        'tags': s.get('tags',[]),
                        'major': m['name'],
                        'quota': m['quota'],
                        'scores': g.get('admission_scores', {})
                    })
    return results
```

## 输出格式

查询结果用markdown表格呈现：

```
| 代号 | 院校 | 标签 | 专业 | 人数 | 学费 | 选科 | 2024分 | 2025分 | 备注 |
|------|------|------|------|:--:|----:|------|:----:|:----:|------|
```

排序规则：北京优先 → 985 → 211 → 双一流 → 分数降序。分数缺失写`—`。色弱风险写`⚠️`。

## 注意事项

1. JSON专业名可能含OCR残留（学费数字混入等），展示时需要清洗
2. 分数线是**专业组投档最低分**，非具体专业录取分
3. 军事院校A段专业通常无公开分数线
4. 部分院校跨批次招生（如国防科大在A段+普通批），注意区分
5. 2024年含位次数据（`min_rank`），2023/2025仅分数
6. 约842条分数线因选科格式差异未能匹配到专业组
7. **用户色弱**，涉及化学/生物/医学的专业需标注风险
8. B段双培计划有区名额分配，本数据仅含总计划数

## 命令行工具

```bash
# 搜索材料专业
python3 scripts/query.py 材料

# 查看北航详情
python3 scripts/query.py 1047 --school
```

## 相关文件

| 文件 | 路径 | 说明 |
|------|------|------|
| JSON数据 | `data/gaokao-2026-beijing.json` | 主数据文件(1.2MB) |
| 查询脚本 | `scripts/query.py` | 命令行快速查询 |
| 材料清单 | `/mnt/d/temp/gaokao/材料类专业报考清单.md` | 材料专业专项报告 |
| 整理版目录 | `/mnt/d/temp/gaokao/高考志愿填报目录-整理版.md` | 可读版招生目录 |
