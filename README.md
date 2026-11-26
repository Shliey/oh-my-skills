# Oh My Skills

为 Agent 提供两套可独立使用的工作指令。一套帮助你完成任务并查验结果，另一套带你沿原文读懂机器学习论文。每项技能都可以安装到 Codex，也可以直接把完整的 `SKILL.md` 交给聊天 Agent。

[快速上手](#快速上手) · [安装到 Codex](#安装到-codex) · [使用场景](#使用场景) · [验证与反馈](#验证与反馈)

| 技能 | 适合什么时候用 | 可得到的结果 |
| --- | --- | --- |
| [Evidence-driven Delivery](skills/evidence-driven-delivery/SKILL.md) | 实现改动、修订文档或核对已有成果 | 可用产物、实际核验结果和待确认事项 |
| [Deep Paper Reading](skills/deep-paper-reading/SKILL.md) | 深读论文、追踪张量形状或核对实验结论 | 带来源的解释、数据流、双栏批注或汇报讲稿 |

技能各由一份 Markdown 构成，无额外运行时依赖。读取文件、运行测试和生成成品取决于当前 Agent 可用的工具。

## 快速上手

**直接在聊天中试用。** 打开上表中任意一份 `SKILL.md`，复制全文到同一个会话，再附上材料和任务。在其他 Agent 中可以直接使用下面示例的任务描述。

**已经装到 Codex。** 在对话里输入技能名和任务，按需附上仓库、文档或论文。

```text
$evidence-driven-delivery 根据我提供的会议笔记写一份可直接复制的通知，核对时间和负责人，把待补信息单独列出。
```

```text
$deep-paper-reading trace 根据我附上的论文，沿一条输入解释图 2 的每个数据箭头、各阶段的张量形状和证据缺口。
```

## 安装到 Codex

以下命令适用于 Windows PowerShell。先在想保存仓库的父目录运行：

```powershell
git clone https://github.com/Shliey/oh-my-skills.git
cd oh-my-skills
```

在仓库根目录运行下面的命令。默认安装两项技能。只需要一项时，把 `$selectedSkills` 改成对应的单项数组，例如 `@('deep-paper-reading')`。

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

New-Item -ItemType Directory -Path $skillsRoot -Force -ErrorAction Stop | Out-Null
foreach ($name in $selectedSkills) {
    Copy-Item -LiteralPath (Join-Path '.\skills' $name) `
        -Destination (Join-Path $skillsRoot $name) -Recurse -ErrorAction Stop
}
```

安装后打开一个新的 Codex 会话。更新已安装的同名技能时，先把旧目录备份到技能搜索目录之外，再运行安装。支持技能目录的其他 Agent 可以按其安装方式复制对应技能目录。

## 使用场景

### Evidence-driven Delivery

给出目标、可用材料和希望确认的结果。要完成改动时，可以说「修复这个函数，保持现有接口，并用已有用例验证」。只想让 Agent 找问题时，可以说「只评审这份改动，指出最重要的问题和依据」。想自己做时，可以要求「只给下一步提示和检查方法」。

交付时会说明产物、实际做过的检查和剩余缺口。纯聊天可以完成文本交付和依据核对。涉及测试、运行或远端发布时，实际结论取决于当前工具和权限。

### Deep Paper Reading

提供论文原文、可访问的论文链接或节选。默认中文，按问题选择阅读范围。在 Codex 中可以把下列模式加到 `$deep-paper-reading` 后。

| 模式 | 用来回答 |
| --- | --- |
| `full`（默认） | 论文解决什么，从输入到结论的证据链是什么？ |
| `overview` | 输入输出、总体架构和主要发现是什么？ |
| `module` | 这条图中箭头、这个公式或模块具体做什么？ |
| `trace` | 一条输入怎样变成输出，每一步的数据形状是什么？ |
| `evidence` | 指标、基线和消融支持了哪些结论？ |
| `presentation` | 如何把原文内容编排成图解汇报和逐页讲稿？ |

有文件输出能力时，完整深读默认交付一个离线双栏 HTML，左栏为可收录的原文与中文译文，右栏为对应批注。纯聊天默认 Markdown，也可明确指定 `full format=markdown` 或 `module format=html`。需要对照源码时，附上允许读取的仓库或文件，并说明要核对的机制。

## 验证与反馈

提交修改前运行 `git diff --check`。如果本机已有 `skill-creator` 的校验器，可以从仓库根目录检查两份技能的元数据。按本机实际安装路径调整校验器位置。

```powershell
$validator = Join-Path $HOME '.codex/skills/.system/skill-creator/scripts/quick_validate.py'
python -X utf8 -B $validator .\skills\evidence-driven-delivery
python -X utf8 -B $validator .\skills\deep-paper-reading
```

修改技能指令时，用一个代表性任务检查实际输出。反馈时附上所用技能、最小可共享示例、预期和实际结果。
