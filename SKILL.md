---
name: reddit-brand-watch
description: 监控 Reddit 上指定品牌、产品线、具体 SKU/型号(以及关注的板块)的讨论,定期批量检索并生成带原帖证据的洞察/创意周报。用户说"盯 Reddit"、"Reddit 竞品/品牌声量"、"某型号用户怎么说"、"每周产品创新点子库"、"Reddit 周报"时使用。
---

# Reddit 品牌/产品/SKU 监控与周报

把"监控清单 → 批量检索 → 证据入库 → 归纳成周报 → 脚本核验"固化为可重复的流程。核心原则:**数字、链接、评论原文一律由脚本从检索结果填入,绝不手写;判断类内容(契合度、难度、机会点)明确标为 Claude 的判断。**

检索层使用开源技能 mvanhorn/last30days-skill(MIT)的免 Key 路径。它只是检索层:返回帖子标题、赞数、评论数和高赞评论片段(评论约 200 字符截断,无帖子正文)。主题聚类、机会点、打分由你来做。

## 0. 监控清单(个性化配置)

在用户的连接文件夹里维护 `reddit-watch/watchlist.md`(没有就先创建,并用 AskUserQuestion 向用户确认内容)。字段:

- **关注对象**:品牌、产品线、具体 SKU/型号(型号写成用户会在帖子里打的写法,如 `DCD791`、`M18 Fuel`)。分"自家"和"竞品"。
- **板块**:要监控的 subreddit 列表。
- **主题词**:痛点/需求/玩法类关键词(如 battery runtime complaints、storage wish list)。
- **时间窗口**:默认 7 天;首次或样本太少时用 30 天。
- **报告语言与读者**:例如中文、产品经理。

示例(STANLEY 百得苏州学习项目的默认值,可改):自家 STANLEY、DEWALT、Craftsman、BLACK+DECKER;竞品 Milwaukee、Makita、Ryobi、Bosch;板块 Tools、HomeImprovement、DIY、woodworking、MilwaukeeTool、Dewalt、Craftsman、ToolBox;读者为产品创新团队,报告用中文。

## 1. 准备环境(每个新会话做一次)

```bash
mkdir -p /tmp/rw && cd /tmp/rw && git clone --depth 1 https://github.com/mvanhorn/last30days-skill.git src
mkdir -p /tmp/rw/tools && cp "<本技能目录>/tools/"* /tmp/rw/tools/
```

需要 `uv`(用 `uv run --python 3.12` 自动准备 Python 3.12,沙箱自带的 3.10 不够)。若克隆失败,如实告诉用户并停止,不要改用别的抓取方式。`<本技能目录>` 指本 SKILL.md 所在目录;脚本都在它的 `tools/` 子目录里。

`tools/` 里的文件:

- **run_batch.sh** `<last30days目录> <批次目录> <起始行> <结束行>`:并行前台运行 queries.tsv 中指定行(每行 `q01<TAB>查询词<TAB>板块1,板块2`),`xargs -P4`,总超时 170 秒,结果追加到 done.txt。环境变量 `DAYS` 改时间窗口(默认 30)。
- **build_store.py** `<批次目录> <store.json>`:解析所有 q*.md,抽取帖子(id、标题、日期、板块、赞数、评论数、来源查询)和 "Top Community Comments" 里的评论,存为 JSON。
- **dump_store.py** `<store.json>`:按评论数降序打印帖子及其高赞评论,供通读。
- **build_report.py** `<store.json> <template.md> <out.md> <queries.tsv> "<监控板块,逗号分隔>"`:展开模板占位符 `{{P:帖子ID}}`(标题+链接+板块+日期+赞数+评论数)、`{{Q:帖子ID:赞数[:原文前缀]}}`(评论原文+赞数+评论链接,找不到或有歧义直接报错)、`{{S:名称}}`(统计:version、nq、nothing、n_posts、n_comments、n_in、pct_out、n_hit、n_targets、miss、brk、empty_list、coverage)。
- **verify_report.py** `<store.json> <report.md>`:逐一核对报告里每个帖子引用和每条评论原文是否与 store 完全一致,并检查报告里没有 store 之外的 Reddit 链接;有问题则退出码 1。
- **report_skeleton.md**:报告骨架,复制为 `template.md` 后按本次内容改写。

## 2. 设计查询

在批次目录 `/tmp/rw/<日期>/` 下写 `queries.tsv`,每行三列、制表符分隔:`q01<TAB>查询词<TAB>板块1,板块2`。查询 ID 必须是 `q` 加两位数字。

设计要点(都是实测踩出来的):

- **查询要带限定词,不要只写品牌名。** 单搜 "Milwaukee" 返回的全是密尔沃基城市帖,单搜 "Craftsman" 混进工匠风老房子。写成 "Milwaukee M18 battery problems"、"Craftsman wrench set quality"。
- **SKU/型号要带品类词**,如 "DeWalt DCD791 drill"。型号单独搜容易被相关度门槛过滤。
- **每个关注对象至少 2 到 3 种写法**(品牌+品类、品牌+问题、品牌 vs 竞品),因为内置相关度门槛会把整条查询过滤为空。实测中 STANLEY 相关的 6 条查询(卷尺、FATMAX、Stanley 对比 DeWalt 等)全部为空,这是最大的坑;出现空返回就换写法重跑,并在局限说明里如实记录。
- 每条查询配最相关的 3 到 4 个板块,不要把所有板块塞给每条查询。
- 一次约 20 条:覆盖"自家品牌"、"竞品"、"SKU"、"主题词"四类。

## 3. 批量检索(严格遵守沙箱限制)

- 单次 bash 调用约 175 秒会被强制终止,**后台进程在调用结束后会被杀**。所以必须前台运行,每次调用最多跑 4 条(`run_batch.sh` 内置 `xargs -P4` 和 170 秒总超时)。
- 一次调用示例:`bash /tmp/rw/tools/run_batch.sh /tmp/rw/src /tmp/rw/<日期> 1 4`,下一次 `5 8`,依此类推。设置环境变量 `DAYS=7` 可改时间窗口(默认 30)。
- 输出里 `rc=124` 表示超时,把那几行单独重跑一次;仍失败就记入局限说明。
- 不加 `--deep`(更慢,且会超时)。

跑完后检查:`ls <批次目录>/q*.md | wc -l`,并看 `done.txt`。

## 4. 入库与阅读证据

```bash
python3 -I /tmp/rw/tools/build_store.py /tmp/rw/<日期> /tmp/rw/<日期>/store.json
python3 -I /tmp/rw/tools/dump_store.py /tmp/rw/<日期>/store.json
```

完整读一遍 dump,再归纳。注意:

- 某条查询的 md 里出现 "Nothing solid this window" 表示被相关度门槛过滤为空,不要从中推断任何结论。
- 看 `r/` 板块分布:板块外的帖子是噪声,不要拿来当证据。
- 只拿到标题和互动数、没有评论原文的帖子,只能写进品牌速览并标注"仅标题,倾向不可靠"。

## 5. 归纳并写报告

1. 把 report_skeleton.md 复制为 `template.md`,按本次内容改写。
2. 主题 = 至少有 2 个独立帖子或 1 个帖子加高赞评论支撑的反复出现的痛点/需求/玩法。Top 5 左右,证据弱的放进"观察项"。
3. **引用只用占位符**:`{{P:帖子ID}}` 展开成"标题+链接+板块+日期+赞数+评论数";`{{Q:帖子ID:赞数}}` 或 `{{Q:帖子ID:赞数:文本前缀}}` 展开成评论原文+赞数+评论链接(同帖同赞数有多条时用前缀区分)。占位符找不到或有歧义会直接报错。
4. 英文原话后面跟"(意思:…)"中文转述。讽刺、有歧义或被截断的地方要明说,读不懂就写"无法确认,请人工阅读原帖",不要猜。
5. 证据强度按骨架里的规则打分;契合度、实现难度是你的判断,必须标"(判断)"。
6. 机会点要具体、能追溯到上面的证据,每个主题 1 到 3 条。
7. 局限说明必须如实写:未命中的板块、空返回的查询、评论截断、赞数缺失、样本量、地域偏差。

生成并核验:

```bash
python3 -I /tmp/rw/tools/build_report.py /tmp/rw/<日期>/store.json /tmp/rw/<日期>/template.md /tmp/rw/<日期>/report.md /tmp/rw/<日期>/queries.tsv "Tools,HomeImprovement,DIY"   # 最后一个参数是监控板块列表
python3 -I /tmp/rw/tools/verify_report.py /tmp/rw/<日期>/store.json /tmp/rw/<日期>/report.md
```

`verify_report.py` 必须输出 `problems 0` 才能交付;它会检查每个帖子引用和评论原文是否与检索结果完全一致。再通读一遍报告里的"意思:…"转述是否忠于原话。

## 6. 交付

- 报告、store.json、各 q*.md、queries.tsv 一并保存到用户文件夹 `reddit-watch/<日期>/`,在回复里只给报告的链接和一段简短结论。
- 对照用户的验收标准(若有)汇报:覆盖板块数、主题数、证据数、噪声占比,以及 STANLEY 等自家品牌是否拿到了评论内容。诚实说明不达标之处。
- 如果用户想定期运行,可用定时任务创建每周任务,提示词里写明"使用 reddit-brand-watch 技能,按 reddit-watch/watchlist.md 运行并把报告存入 reddit-watch/<日期>/"。告诉用户定时任务只在应用打开时运行。

## 已知局限(向用户如实说明)

- 免 Key 路径下 Reddit 搜索页可能返回异常("Unrecognized response"),导致召回偏低、部分板块完全没有命中。申请 Reddit 官方 API 凭证后再接入 last30days 通常能改善,但未验证。
- 无帖子正文,评论约 200 字符截断。
- 无法打开 reddit.com 页面核验链接(沙箱抓取会遇到验证页)。链接和数字来自检索结果本身,而非人工打开确认。
- Reddit 用户偏北美发烧友,对其他地区和一般家装用户的代表性有限。
- 这是学习练习级别的流程,未做 Reddit 数据商用授权审查和第三方开源工具的安全审查;转正式使用前需要补上。
