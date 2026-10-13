# reddit-brand-watch

监控 Reddit 上指定品牌、产品线、具体 SKU/型号的讨论,批量检索后生成带原帖证据的洞察/创意周报,封装成 Claude 可调用的 Skill。

## 它做什么

监控清单 -> 批量检索 -> 证据入库 -> 归纳成周报 -> 脚本核验。

核心原则:周报里的链接、赞数、评论数和评论原文一律由脚本从检索结果填入,绝不手写;"契合度""实现难度"这类判断明确标为 Claude 的判断。交付前由 `tools/verify_report.py` 核对每个引用,不一致就不交付。

检索层使用开源技能 [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)(MIT)的免 Key 路径,本仓库不包含它的代码。

## 安装

克隆到本机技能目录即可:

```bash
git clone https://github.com/Atange2023/reddit-brand-watch.git ~/.claude/skills/reddit-brand-watch
```

之后对 Claude 说"盯 Reddit"、"Reddit 竞品声量"、"某型号用户怎么说"、"Reddit 周报"即可触发。

## 已知局限

- 免 Key 路径下 Reddit 搜索页可能异常,召回偏低,部分板块可能零命中;品牌词过短或型号单独搜索时,整条查询可能被相关度门槛过滤为空。
- 只有帖子标题、赞数、评论数和被截断的高赞评论片段(约 200 字符),没有帖子正文。
- 沙箱里无法打开 reddit.com 页面,链接来自检索结果而非人工打开确认。
- 学习练习级别:未做 Reddit 数据商用授权审查,也未对第三方开源工具做安全审查;转正式使用前需要补上。使用前请自行确认符合 Reddit 的用户协议与数据 API 条款,商业用途通常需要 Reddit 官方授权。

## 目录

- `SKILL.md` 技能正文(流程、查询设计要点、报告规则)
- `tools/` 批量检索、入库、出报告、核验脚本和报告骨架
- `LICENSE` MIT 许可证

## 许可

MIT,见 `LICENSE`。检索层 last30days-skill 是独立项目,有它自己的许可(MIT),本仓库不包含其代码。
