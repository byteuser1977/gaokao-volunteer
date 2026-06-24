---
name: gaokao-volunteer
description: >-
  高考志愿填报辅助工具。基于北京2026年招生数据（533所院校、968个专业组、21490条专业、985/211/双一流标签、2023-2025分数线位次），
  支持按专业关键词搜索、按院校代号查询、按分数段/标签筛选、物化选科匹配、色弱限制检查。
  适用场景：专业推荐、分数对比、志愿清单生成。
version: 1.2.0
---

# 高考志愿填报 Skill

> 兼容：Hermes / OpenClaw / Claude Code / Trae / Cursor

## 数据文件层级

| 层级 | 路径 | 格式 | 用途 |
|------|------|------|------|
| **原始数据** | `data/gaokao-2026-beijing.json` | JSON | 程序化查询（1.7MB, 533校完整数据） |
| **OCR 原文** | `data/content.txt` | TXT | PDF 原始 OCR 文本（273KB） |
| **清洗文本** | `data/clean/*.md` | Markdown | 去杂合并后的纯文本（7文件，~570KB） |
| **格式化文本** | `data/formatted/*.md` | Markdown | 层级标题 + 专业列表 + 注释引用（7文件，~620KB） |

### 格式化文本结构

```
## 本科普通批招生院校专业及人数             ← 批次标题
### 1047 北京航空航天大学 275人 [985/211/双一流]  ← 院校
#### {02} 物理+化学(均须选考)               ← 专业组 + 选科要求
- 20 工科试验班 8人 ¥5500 四年              ← 专业条目 (代码 名称 人数 学费)
- 21 人工智能 5人 ¥5500 四年
> 以上专业办学地点：学院路校区                ← 注释/限制条件
```

**格式化文本是 AI Agent 直接可读的最优数据源**——层级清晰、专业已拆分、括号完整、间距规范。

### JSON 数据加载

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

### 院校 (school)

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | string | 院校代号(4位) | `"1047"` |
| `name` | string | 院校全称 | `"北京航空航天大学"` |
| `location` | string | 所在地 | `"北京"` |
| `tags` | string[] | 985/211/双一流 | `["985","211","双一流"]` |
| `batches` | string[] | 招生批次 | `["regular"]` 或 `["early_a"]` |
| `total_quota` | int | 在京招生总人数 | `275` |
| `score_range` | object | 全校分数区间(按年) | `{"2024":{"min":649,"max":667},"2025":{"min":640}}` |
| `major_groups` | array | 专业组列表 | 见下 |

### 专业组 (major_group)

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_code` | string | 专业组编号，如 `"02"` |
| `subject_requirements` | string | 选考要求，如 `"物理+化学(均须选考)"` |
| `admission_scores` | object | `{"2024":{"min":667,"min_rank":1552},"2025":{"min":657}}` |
| `majors` | array | 专业列表 |

### 专业 (major)

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 专业代码(2位)，含数字+字母扩展码（如 `1A`, `AD`） |
| `name` | string | 专业名称（可能含 OCR 残留，展示时需清洗） |
| `quota` | int | 招生人数 |
| `tuition` | int | 学费(元/年) |
| `duration` | string | 学制：`"四年"` / `"五年"` / `"八年"` |
| `restrictions` | object/null | `gender` / `vision` / `language` / `physical` / `interview` |
| `notes` | string | 备注 |

## 招生批次

| 批次代码 | 说明 | 包含院校类型 |
|----------|------|-------------|
| `early_a` | 本科提前批A段 | 军校、公安、消防、外交、综评(▲)、飞行 |
| `early_b` | 本科提前批B段 | 双培计划、地方农村专项 |
| `special_sports` | 特殊类型招生 | 高水平运动队 |
| `regular` | 本科普通批 | 所有普通本科 |

## 调用流程（必读）

**每次调用此 skill 时，第一步必须询问考生基本信息，不得跳过：**

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

收集信息后自动执行以下排除规则：
- **色弱/色盲** → 排除含化学类、生物类、医学类、材料类、环境类、食品类、地质类、药学类的专业
- **单色识别能力异常** → 排除标注「不招单色识别能力异常」的专业
- **性别限制** → 排除标注「只招男生/女生」的不符性别专业
- **身高限制** → 排除标注身高要求的专业（军事、公安、体育类为主）
- **语种限制** → 标注「只招英语考生」的专业，非英语考生应排除

若会话上下文中已有考生画像（memory / 前序对话），可直接复用，无需重复询问。

## 数据查询方式

### 方式一：JSON 程序化查询（适合精确筛选）

```python
# 所有函数已实现在 scripts/query.py 中
from scripts.query import search_major, get_school, by_score_range, by_tag

results = search_major("计算机", data)     # 关键词搜索
school  = get_school("1047", data)         # 院校代号查询
schools = by_score_range(580, 620, data)   # 分数段筛选
schools = by_tag("985", data)              # 标签筛选
```

### 方式二：Markdown 直接阅读（适合人工浏览）

直接读取 `data/formatted/` 下的文件：

| 文件 | 内容 |
|------|------|
| `02-本科提前批A段.md` | 军校/公安/外交/飞行/综评 |
| `03-本科提前批B段.md` | 双培计划/地方农村专项 |
| `04-特殊类型招生.md` | 高水平运动队 |
| `05-本科普通批.md` | **全部 533 所普通本科院校** |
| `01-说明.md` | 填报规则说明 |
| `06-院校代号一览表.md` | 省市代号对照表 |

### 查询函数参考

#### 1. 专业关键词搜索 `search_major(keyword, data)`

遍历所有院校专业组，匹配专业名含关键词的记录。返回含院校代号、名称、所在地、标签、专业名、人数、学费、选科要求、限制条件、历年分数线的列表。

**排序规则**：北京优先 → 985 → 211 → 双一流 → 2025/2024 最高分降序。

#### 2. 院校详情 `get_school(code, data)`

通过 4 位代号精确查找院校完整信息：所有专业组、专业详情、历年分数/位次。

#### 3. 分数段筛选 `by_score_range(lo, hi, data, year='2025')`

按指定年份全校投档最低分筛选，分数降序排列。

#### 4. 标签筛选 `by_tag(tag, data)`

按 `985` / `211` / `双一流` 筛选，按 2025 年最低分降序排列。

#### 5. 色觉限制检查 `is_vision_restricted(major)`

检查专业名、备注、`restrictions.vision` 中是否含色觉限制关键词（色弱、色盲、单色识别、不招色）。

#### 6. 物化选科匹配 `match_physics_chemistry(data)`

筛选要求同时选考物理+化学的所有专业组。

## 输出格式

查询结果优先以 Markdown 表格呈现：

```
| 代号 | 院校 | 标签 | 专业 | 人数 | 学费 | 选科 | 2024分 | 2025分 | 批次 |
|------|------|------|------|:--:|----:|------|:----:|:----:|------|
```

排序：北京优先 → 985 → 211 → 双一流 → 分数降序。缺失分数写 `—`。色觉限制标 `⚠️`。

单院校详情输出包含：全校分数区间、各专业组选科与投档分、每个专业的人/费/学制/限制。

## 关键符号速查

| 符号 | 含义 |
|:----:|------|
| ▲ | 综合评价录取模式 |
| ■ | 须面试或加试 |
| ● | 特殊培养方向标记 |
| ⚠️ | 色觉/体检限制风险 |
| `(男)` `(女)` | 性别限制 |
| 3+1 / 1+2+1 | 双培计划联合培养模式 |

## 工具脚本

```bash
# 命令行查询
python scripts/query.py 计算机              # 搜索专业
python scripts/query.py 1047 --school       # 查院校详情
python scripts/query.py --score 580 620     # 分数段筛选
python scripts/query.py --tag 985           # 985院校

# 数据清洗流水线
python scripts/clean_to_markdown.py         # content.txt → data/clean/
python scripts/format_markdown.py           # data/clean/ → data/formatted/

# 数据校验
python scripts/verify_against_formatted.py  # 校验 JSON ↔ 格式化文本
```

## 注意事项

1. **专业名清洗**：JSON 中 `majors[].name` 可能含 OCR 残留（学费数字混入、括号未闭合），展示前需清洗
2. **分数线说明**：分数线为**专业组投档最低分**，非具体专业录取分；2024 年含位次（`min_rank`），2023/2025 仅分数
3. **军事院校**：A 段军事院校通常无公开分数线（`score_range` 为空）
4. **跨批次院校**：部分院校跨批次招生（如国防科大同时在 A 段和普通批），注意区分
5. **B 段双培计划**：有区级名额分配，本数据仅含总计划数，分区名额详见各专业备注
6. **分数线缺口**：约 842 条专业组分数线因选科格式差异未能匹配
7. **数据时效**：基于 2026 年 6 月发布的招生目录，实际录取以考试院最终公布为准
