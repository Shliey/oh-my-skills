# Oh My Skills

两套独立使用的 Codex 技能：一个把软件需求推进到有证据的交付，另一个把机器学习论文拆到数据和机制层。

| 技能 | 什么时候用 | 能得到什么 |
| --- | --- | --- |
| [Evidence-driven Delivery](skills/evidence-driven-delivery/SKILL.md) | 有目标、issue 或已有变更，需要把工作推进到明确的验收结果 | 项目内的规格、任务、检查记录与可恢复状态；常规步骤由 Codex 推进，重要决定由你确认 |
| [Deep Paper Reading](skills/deep-paper-reading/SKILL.md) | 想看懂论文中的表示、公式、训练、推理或实验 | 带出处的数据流、贯穿示例、证据边界，以及按需提供的论文与源码对照 |

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

安装会复制整个技能目录，包括参考文件和辅助脚本。遇到同名目录时，先对比本机和仓库版本；如需替换，把原目录备份到技能目录之外，再运行安装。安装后打开新的 Codex 会话。

## 在 Codex 中使用

以下是聊天输入，不是终端命令。

**交付一个可验收的改动**

```text
$evidence-driven-delivery 实现订单查询的权限检查，保留现有接口，并验证其他用户无法读取订单。
```

如果你想自己写，可以明确说“我来实现，请只给下一步提示和检查方法”。仅讲解、计划或评审时保持只读；实施请求按授权推进。交付时分别说明测试、实际交互和远端结果验证到了哪一步。

交付辅助脚本需要 Python 3.11+，无第三方 Python 依赖。完整 OpenSpec 交付还需要 OpenSpec CLI；项目自己的构建与测试依赖由项目决定。

**读懂一篇论文**

提供论文文件或可访问的原文，然后按目标调用：

| 模式 | 聊天示例 |
| --- | --- |
| `full`（默认） | `$deep-paper-reading 请用中文完整深读这篇论文。` |
| `overview` | `$deep-paper-reading overview：解释输入输出、整体架构和主要创新。` |
| `module` | `$deep-paper-reading module：拆解量化模块，解释每个维度从哪里来。` |
| `trace` | `$deep-paper-reading trace：用一个例子走完每一步数据转换。` |
| `evidence` | `$deep-paper-reading evidence：核对实验和消融支持了哪些结论。` |

默认只分析论文资料。要对照实现，可以加一句“请对照这个仓库的当前源码，指出公式和实际计算的差异”。源码对照与运行复现是不同任务；没有运行证据时只报告读到的实现。论文未说明的细节会保留为未知，教学值会单独标注。读取 PDF、图表和网页取决于宿主可用的工具。

## 验证与贡献

从仓库根目录运行以下命令。结构检查使用本机随 `skill-creator` 提供的校验器；若你的安装位置不同，请调整脚本路径。

```powershell
$validator = Join-Path $HOME '.codex/skills/.system/skill-creator/scripts/quick_validate.py'
python -X utf8 -B $validator .\skills\evidence-driven-delivery
python -X utf8 -B $validator .\skills\deep-paper-reading
python -X utf8 -B .\skills\evidence-driven-delivery\scripts\test_delivery.py
git diff --check
```

结构检查验证技能包格式。交付测试覆盖控制器行为；完整 Python 和 TypeScript 集成用例还需要 OpenSpec，TypeScript 用例另需 Node.js 和 npm。缺少前提时报告实际跳过项。变更技能指引时，用相关的小场景复查行为，例如“用户明确要自己实现”或“论文没有公开阈值”。

提交反馈时，请提供可公开分享的最小示例、预期行为和观察到的结果。请勿附带私有论文、运行日志、项目数据或凭据。
