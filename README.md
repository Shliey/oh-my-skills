# Oh My Skills

两套独立使用的技能，分别用于有证据的任务交付与机器学习论文深读。

| 技能 | 什么时候用 | 能得到什么 |
| --- | --- | --- |
| [Evidence-driven Delivery](skills/evidence-driven-delivery/SKILL.md) | 需要交付、修订或验收软件、文档或研究材料 | 产物、实际检查结果与待核事项 |
| [Deep Paper Reading](skills/deep-paper-reading/SKILL.md) | 想看懂论文的论证和方法，或只想问清一个公式 | 原文证据、图解、形状追踪和实验核对；支持 Markdown、双栏 HTML 和论文汇报 |

## 安装

以下是 Windows PowerShell 命令。在你想存放仓库的父目录运行：

```powershell
git clone https://github.com/Shliey/oh-my-skills.git
cd oh-my-skills
```

从仓库根目录运行下面的安装命令。默认同时安装两个技能；若只要一个，把 `$selectedSkills` 设为只含对应技能名的数组，例如 `@('deep-paper-reading')`。

```powershell
$selectedSkills = @('evidence-driven-delivery', 'deep-paper-reading')
$skillsRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $HOME '.codex/skills'
}

foreach ($name in $selectedSkills) {
    $source = Join-Path '.\skills' $name
    $target = Join-Path $skillsRoot $name
    if (!(Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "找不到技能，请从 oh-my-skills 仓库根目录运行：$name"
    }
    if (Test-Path -LiteralPath $target) {
        throw "已安装同名技能，请先检查并备份：$target"
    }
}

New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
foreach ($name in $selectedSkills) {
    Copy-Item -LiteralPath (Join-Path '.\skills' $name) `
        -Destination (Join-Path $skillsRoot $name) -Recurse
}
```

两项技能分别由一份 Markdown 组成。安装会复制对应目录。遇到同名目录时，先对比本机和仓库版本；如需替换，把原目录备份到技能目录之外，再运行安装。安装后打开新的 Codex 会话。

## 使用方式

Codex 支持用下列技能名调用。其他 Agent 可以直接加载或粘贴对应的完整 `SKILL.md`，再附上任务。技能本身无需运行时依赖，文件生成、浏览和执行取决于 Agent 提供的能力。

以下是聊天输入，不是终端命令。

**交付一个可验收的改动**

```text
$evidence-driven-delivery 实现订单查询的权限检查，保留现有接口，并验证其他用户无法读取订单。
```

如果你想自己做，可以明确说“请只给下一步提示和检查方法”。技能会按你的意图区分交付、评审、计划和指导。

在其他 Agent 中，加载 [Evidence-driven Delivery](skills/evidence-driven-delivery/SKILL.md) 后可使用以下任务文本。

```text
根据下面的会议记录写一封可直接发送的通知草稿。核对日期、行动项和负责人，缺失的信息单独列出。
```

Agent 按任务使用手头的资料和工具，并说明实际核验了什么。

**读懂一篇论文**

提供论文文件或可访问的原文，然后按目标调用：

| 模式 | 聊天示例 |
| --- | --- |
| `full`（默认） | `$deep-paper-reading full：完整深读这篇论文，课程：机器学习。` |
| `overview` | `$deep-paper-reading overview：解释输入输出、整体架构和主要创新。` |
| `module` | `$deep-paper-reading module：拆解量化模块，解释每个维度从哪里来。` |
| `trace` | `$deep-paper-reading trace：用一个例子走完每一步数据转换。` |
| `evidence` | `$deep-paper-reading evidence：核对实验和消融支持了哪些结论。` |
| `presentation` | `$deep-paper-reading presentation：按原文制作论文汇报页纲和逐页讲稿。` |

默认只分析论文资料。要对照实现，可以加一句“请对照这个仓库的当前源码，指出公式和实际计算的差异”。源码对照与运行复现是不同任务；没有运行证据时只报告读到的实现。论文未说明的细节会保留为未知，教学值会单独标注。读取 PDF、图表和网页取决于宿主可用的工具。

有文件输出能力时，完整深读默认使用单文件离线双栏 HTML。左栏排原文和中文译文，右栏逐段批注。纯聊天默认以 Markdown 完成同样的阅读任务。用 `full format=markdown` 指定 Markdown，或用 `module format=html` 交付指定模块的双栏内容。只提供摘要或节选时，报告会标明实际覆盖范围。

在其他 Agent 中，加载 [Deep Paper Reading](skills/deep-paper-reading/SKILL.md) 后可使用以下任务文本。

```text
根据我附上的论文节选，用中文沿一条输入追到输出，写清图中各箭头、张量形状和证据缺口。
```

## 验证与贡献

从仓库根目录运行以下命令。结构检查使用本机随 `skill-creator` 提供的校验器；若你的安装位置不同，请调整脚本路径。

```powershell
$validator = Join-Path $HOME '.codex/skills/.system/skill-creator/scripts/quick_validate.py'
python -X utf8 -B $validator .\skills\evidence-driven-delivery
python -X utf8 -B $validator .\skills\deep-paper-reading
git diff --check
```

结构检查验证技能包格式。修改技能指令时，用真实任务复查实际输出。例如，确认 Evidence-driven Delivery 能在纯聊天中交付文档，并按用户要求保持评审只读。验证 Deep Paper Reading 时，分别检查纸面推导、源码依据、实际数据和未知项。

提交反馈时，请提供可公开分享的最小示例、预期行为和观察到的结果。请勿附带私有论文、运行日志、项目数据或凭据。
