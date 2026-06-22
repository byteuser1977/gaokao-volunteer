# 高考志愿填报 Skill

基于北京2026年招生数据的AI辅助志愿填报工具，兼容 Hermes / OpenClaw / Claude Code / Trae / Cursor。

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

- **专业搜索** — 按关键词检索所有院校的相关专业
- **分数筛选** — 按分数段/位次匹配合适院校
- **标签过滤** — 按985/211/双一流筛选
- **选科匹配** — 根据物化生等选科组合过滤
- **体检限制** — 自动排除色弱/色盲/身高不符的专业
- **分数线对比** — 展示2023-2025年最低分和位次

## 快速开始

```bash
# 搜索材料专业
python3 scripts/query.py 材料

# 按院校代号查看详情
python3 scripts/query.py 1047 --school

# 分数段筛选（580-620分）
python3 scripts/query.py --score 580 620

# 985院校列表
python3 scripts/query.py --tag 985
```

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
  "schools": [{
    "code": "1047",
    "name": "北京航空航天大学",
    "tags": ["985","211","双一流"],
    "total_quota": 275,
    "score_range": {"2025": {"min": 640, "max": 657}},
    "major_groups": [{
      "group_code": "02",
      "subject_requirements": "物理+化学(均须选考)",
      "admission_scores": {"2025": {"min": 657}},
      "majors": [{
        "code": "20", "name": "工科试验班", "quota": 8,
        "tuition": 5500, "duration": "四年",
        "restrictions": {"gender": null, "vision": null}
      }]
    }]
  }]
}
```

## 注意事项

- 分数线为专业组投档最低分，非具体专业录取分
- 专业名称可能含OCR残留，仅供参考
- 2024年含位次数据，2023/2025仅分数
- 数据来源：北京教育考试院2026年招生专业目录

## 许可

MIT
