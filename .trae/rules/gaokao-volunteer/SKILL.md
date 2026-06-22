---
name: gaokao-volunteer
description: >-
  高考志愿填报辅助工具。基于北京2026年招生数据（533所院校、968个专业组、21490条专业、985/211/双一流标签、2023-2025分数线位次），
  支持按专业关键词搜索、按院校代号查询、按分数段/标签筛选、物化选科匹配、色弱限制检查。
  适用场景：专业推荐、分数对比、志愿清单生成。
version: 1.1.0
---

# 高考志愿填报 Skill

> 兼容：Hermes / OpenClaw / Claude Code / Trae / Cursor

## 数据文件

JSON数据位于 `data/gaokao-2026-beijing.json`（1.2MB）。

```python
import json, os

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
# data['schools'] → 533所院校列表
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

**major_groups** 子结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_code` | string | 专业组编号，如 `"02"` |
| `subject_requirements` | string | 选考要求，如 `"物理+化学(均须选考)"` |
| `admission_scores` | object | `{"2024":{"min":667,"min_rank":1552},"2025":{"min":657}}` |
| `majors` | array | 专业列表 |

**majors** 子结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 专业代码(2位) |
| `name` | string | 专业名称（可能含OCR残留） |
| `quota` | int | 招生人数 |
| `tuition` | int | 学费(元/年) |
| `duration` | string | 学制：`"四年"` / `"五年"` / `"八年"` |
| `restrictions` | object/null | 限制条件：`gender` / `vision` / `language` / `physical` / `interview` |
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

若会话上下文中已有考生信息（如memory中保存了用户画像），可直接使用，无需重复询问。

## 考生画像（示例，请替换为实际考生信息）

- 2026年北京高考，预估分数段，区排名
- 选科：物理 / 化学 / 生物
- 体检情况：色弱 / 色盲 / 正常 / 其他
- 目标院校：北航、北理、人大、北邮 等

## 查询能力

所有查询函数已实现在 `scripts/query.py` 中，可直接调用或参考其实现逻辑。

### 1. 按专业关键词搜索 `search_major(keyword, data)`

遍历所有院校的所有专业组，匹配专业名称中包含关键词的记录。返回包含院校代号、名称、所在地、标签、专业名、招生人数、学费、选科要求、限制条件、历年分数线的结果列表。

排序规则：北京优先 → 985 → 211 → 2025/2024最高分降序。

### 2. 按院校代号查询 `get_school(code, data)`

通过4位院校代号精确查找院校完整信息，包括所有专业组、专业详情、历年分数线。

### 3. 按分数段筛选 `by_score_range(lo, hi, data, year='2025')`

按指定年份的校投档最低分筛选院校，返回分数降序排列的院校列表。

### 4. 按标签筛选 `by_tag(tag, data)`

按 `985` / `211` / `双一流` 标签筛选院校，按2025年最低分降序排列。

### 5. 色弱/色盲限制检查 `is_vision_restricted(major)`

检查专业名称、备注、`restrictions.vision` 字段中是否包含色觉限制关键词（色弱、色盲、单色识别、不招色）。返回 `True` 表示该专业有色觉限制。

### 6. 物化选科匹配 `match_physics_chemistry(data)`

筛选所有要求同时选考物理和化学的专业组，返回匹配的专业列表。

## 输出格式

查询结果以 Markdown 表格呈现：

```
| 代号 | 院校 | 标签 | 专业 | 人数 | 学费 | 选科 | 2024分 | 2025分 | 批次 |
|------|------|------|------|:--:|----:|------|:----:|:----:|------|
```

排序规则：北京优先 → 985 → 211 → 双一流 → 分数降序。分数缺失写 `—`。色弱风险标注 `⚠️`。

## 注意事项

1. JSON专业名可能含OCR残留（学费数字混入等），展示时需清洗
2. 分数线是**专业组投档最低分**，非具体专业录取分
3. 军事院校A段专业通常无公开分数线
4. 部分院校跨批次招生（如国防科大在A段+普通批），注意区分
5. 2024年含位次数据（`min_rank`），2023/2025仅分数
6. 约842条分数线因选科格式差异未能匹配到专业组
7. B段双培计划有区名额分配，本数据仅含总计划数

## 命令行工具

```bash
python3 scripts/query.py 材料          # 搜索专业
python3 scripts/query.py 1047 --school # 查看院校详情
python3 scripts/query.py --score 580 620  # 分数段筛选
python3 scripts/query.py --tag 985     # 标签筛选
```