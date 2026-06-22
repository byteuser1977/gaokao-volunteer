# 高考志愿填报 Skill

基于北京2026年招生数据的AI辅助志愿填报工具，兼容 Hermes / OpenClaw / Claude Code / Trae / Cursor。

## 项目结构

```
gaokao-volunteer/
├── data/
│   └── gaokao-2026-beijing.json   # 主数据文件 (1.2MB)
├── scripts/
│   └── query.py                    # 命令行查询工具
├── SKILL.md                        # AI Skill 定义文件
└── README.md
```

## 数据规模

| 维度 | 数量 |
|------|:----:|
| 院校 | 533所 |
| 专业组 | 968个 |
| 专业条目 | 21,490条 |
| 985院校 | 43所 |
| 211院校 | 104所 |
| 双一流 | 131所 |
| 分数线 | 2023-2025年 |

## 功能

- **专业搜索** — 按关键词检索所有院校的相关专业，结果按北京优先 → 985 → 211 → 分数降序排列
- **院校详情** — 按4位院校代号查看完整信息（专业组、各专业招生人数、学费、历年分数线）
- **分数筛选** — 按分数段/位次匹配合适院校，支持指定年份
- **标签过滤** — 按985/211/双一流标签筛选院校列表
- **选科匹配** — 根据物理+化学等选科组合过滤专业组
- **体检限制** — 自动识别色弱/色盲/身高/性别限制的专业，辅助排除不适宜报考的志愿
- **分数线对比** — 展示2023-2025年专业组投档最低分和位次

## 命令行快速开始

```bash
# 按专业关键词搜索
python3 scripts/query.py 材料
python3 scripts/query.py 计算机
python3 scripts/query.py 临床医学

# 按院校代号查看详情
python3 scripts/query.py 1047 --school    # 北京航空航天大学
python3 scripts/query.py 1001 --school    # 北京大学

# 按分数段筛选（580-620分）
python3 scripts/query.py --score 580 620

# 按标签筛选
python3 scripts/query.py --tag 985       # 985院校
python3 scripts/query.py --tag 211       # 211院校
python3 scripts/query.py --tag 双一流    # 双一流院校
```

### 输出格式

搜索结果以 Markdown 表格呈现：

```
| 代号 | 院校 | 标签 | 专业 | 人数 | 学费 | 选科 | 2024分 | 2025分 | 批次 |
```

院校详情输出包含全校分数区间、各专业组选科要求与投档分、每个专业的招生人数/学费/学制/限制条件。

## 招生批次

| 批次代码 | 说明 | 包含院校类型 |
|----------|------|-------------|
| `early_a` | 本科提前批A段 | 军校、公安、消防、外交、综评、飞行 |
| `early_b` | 本科提前批B段 | 双培计划、地方农村专项 |
| `special_sports` | 特殊类型招生 | 高水平运动队 |
| `regular` | 本科普通批 | 所有普通本科 |

## 在AI工具中使用

加载 `SKILL.md` 作为系统提示或规则文件：

- **Hermes**: `skill_view(name='gaokao-volunteer')`
- **OpenClaw**: 放入 `~/.openclaw/skills/`
- **Claude Code**: 放入 `.claude/skills/` 或引用为规则
- **Cursor/Trae**: 放入 `.cursor/rules/` 或 `.trae/rules/`

然后直接提问：「推荐北京985计算机专业」「物化生580-600分有什么选择」「北航所有专业详情」。

## 数据结构

```json
{
  "meta": { "region": "北京", "year": 2026 },
  "schools": [{
    "code": "1047",
    "name": "北京航空航天大学",
    "location": "北京",
    "tags": ["985", "211", "双一流"],
    "batches": ["regular"],
    "total_quota": 275,
    "score_range": {
      "2023": { "min": 650, "max": 660 },
      "2024": { "min": 649, "max": 667, "min_rank": null },
      "2025": { "min": 640, "max": 657 }
    },
    "major_groups": [{
      "group_code": "02",
      "subject_requirements": "物理+化学(均须选考)",
      "admission_scores": {
        "2024": { "min": 667, "min_rank": 1552 },
        "2025": { "min": 657 }
      },
      "majors": [{
        "code": "20",
        "name": "工科试验班(未来空天领军计划)",
        "quota": 8,
        "tuition": 5500,
        "duration": "四年",
        "restrictions": { "gender": null, "vision": null },
        "notes": ""
      }]
    }]
  }]
}
```

### 字段速查

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | string | 院校代号(4位) | `"1047"` |
| `name` | string | 院校全称 | `"北京航空航天大学"` |
| `location` | string | 所在地 | `"北京"` |
| `tags` | string[] | 985/211/双一流 | `["985","211","双一流"]` |
| `batches` | string[] | 招生批次 | `["regular"]` |
| `total_quota` | int | 在京招生总人数 | `275` |
| `score_range` | object | 全校分数区间(按年) | `{"2025":{"min":640,"max":657}}` |
| `major_groups` | array | 专业组列表 | — |
| `group_code` | string | 专业组编号 | `"02"` |
| `subject_requirements` | string | 选考要求 | `"物理+化学(均须选考)"` |
| `admission_scores` | object | 专业组投档分(按年) | `{"2024":{"min":667,"min_rank":1552}}` |
| `majors[].code` | string | 专业代码(2位) | `"20"` |
| `majors[].name` | string | 专业名称 | `"工科试验班"` |
| `majors[].quota` | int | 招生人数 | `8` |
| `majors[].tuition` | int | 学费(元/年) | `5500` |
| `majors[].duration` | string | 学制 | `"四年"/"五年"/"八年"` |
| `majors[].restrictions` | object | 限制条件 | `{"gender":"男","vision":"色弱"}` |
| `majors[].notes` | string | 备注 | — |

## 注意事项

- 分数线为专业组投档最低分，非具体专业录取分，仅供参考
- 2024年含位次数据（`min_rank`），2023/2025仅分数
- 军事院校提前批A段通常无公开分数线
- 约842条分数线因选科格式差异未能匹配到专业组
- 数据来源基于互联网，专业推荐仅供参考，请以官方招生目录为准

## 许可

MIT