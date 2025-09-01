# Claude Code PM

[![Automaze](https://img.shields.io/badge/By-automaze.io-4b3baf)](https://automaze.io)
&nbsp;
[![Claude Code](https://img.shields.io/badge/+-Claude%20Code-d97757)](https://github.com/automazeio/ccpm/blob/main/README.md)
[![GitHub Issues](https://img.shields.io/badge/+-GitHub%20Issues-1f2328)](https://github.com/automazeio/ccpm)
&nbsp;
[![MIT License](https://img.shields.io/badge/License-MIT-28a745)](https://github.com/automazeio/ccpm/blob/main/LICENSE)
&nbsp;
[![Follow on 𝕏](https://img.shields.io/badge/𝕏-@aroussi-1c9bf0)](http://x.com/intent/follow?screen_name=aroussi)
&nbsp;
[![Star this repo](https://img.shields.io/badge/★-Star%20this%20repo-e7b10b)](https://github.com/automazeio/ccpm)

### Claude Code workflow to ship ~~faster~~ _better_ using spec-driven development, GitHub issues, Git worktrees, and mutiple AI agents running in parallel.

Stop losing context. Stop blocking on tasks. Stop shipping bugs. This battle-tested system turns PRDs into epics, epics into GitHub issues, and issues into production code – with full traceability at every step.

![Claude Code PM](screenshot.webp)

## Table of Contents

- [Background](#background)
- [The Workflow](#the-workflow)
- [What Makes This Different?](#what-makes-this-different)
- [Why GitHub Issues?](#why-github-issues)
- [Core Principle: No Vibe Coding](#core-principle-no-vibe-coding)
- [System Architecture](#system-architecture)
- [Workflow Phases](#workflow-phases)
- [Command Reference](#command-reference)
- [The Parallel Execution System](#the-parallel-execution-system)
- [Key Features & Benefits](#key-features--benefits)
- [Proven Results](#proven-results)
- [Example Flow](#example-flow)
- [Get Started Now](#get-started-now)
- [Local vs Remote](#local-vs-remote)
- [Technical Notes](#technical-notes)
- [Support This Project](#support-this-project)

## Background

Every team struggles with the same problems:
- **Context evaporates** between sessions, forcing constant re-discovery
- **Parallel work creates conflicts** when multiple developers touch the same code
- **Requirements drift** as verbal decisions override written specs
- **Progress becomes invisible** until the very end

This system solves all of that.

## The Workflow

```mermaid
graph LR
    A[PRD Creation] --> B[Epic Planning]
    B --> C[Task Decomposition]
    C --> D[GitHub Sync]
    D --> E[Parallel Execution]
```

### See It In Action (60 seconds)

```bash
# Create a comprehensive PRD through guided brainstorming
/pm:prd-new memory-system

# Transform PRD into a technical epic with task breakdown
/pm:prd-parse memory-system

# Push to GitHub and start parallel execution
/pm:epic-oneshot memory-system
/pm:issue-start 1235
```

## What Makes This Different?

| Traditional Development | Claude Code PM System |
|------------------------|----------------------|
| Context lost between sessions | **Persistent context** across all work |
| Serial task execution | **Parallel agents** on independent tasks |
| "Vibe coding" from memory | **Spec-driven** with full traceability |
| Progress hidden in branches | **Transparent audit trail** in GitHub |
| Manual task coordination | **Intelligent prioritization** with `/pm:next` |

## Why GitHub Issues?

Most Claude Code workflows operate in isolation – a single developer working with AI in their local environment. This creates a fundamental problem: **AI-assisted development becomes a silo**.

By using GitHub Issues as our database, we unlock something powerful:

### 🤝 **True Team Collaboration**
- Multiple Claude instances can work on the same project simultaneously
- Human developers see AI progress in real-time through issue comments
- Team members can jump in anywhere – the context is always visible
- Managers get transparency without interrupting flow

### 🔄 **Seamless Human-AI Handoffs**
- AI can start a task, human can finish it (or vice versa)
- Progress updates are visible to everyone, not trapped in chat logs
- Code reviews happen naturally through PR comments
- No "what did the AI do?" meetings

### 📈 **Scalable Beyond Solo Work**
- Add team members without onboarding friction
- Multiple AI agents working in parallel on different issues
- Distributed teams stay synchronized automatically
- Works with existing GitHub workflows and tools

### 🎯 **Single Source of Truth**
- No separate databases or project management tools
- Issue state is the project state
- Comments are the audit trail
- Labels provide organization

This isn't just a project management system – it's a **collaboration protocol** that lets humans and AI agents work together at scale, using infrastructure your team already trusts.

## Core Principle: No Vibe Coding

> **Every line of code must trace back to a specification.**

We follow a strict 5-phase discipline:

1. **🧠 Brainstorm** - Think deeper than comfortable
2. **📝 Document** - Write specs that leave nothing to interpretation
3. **📐 Plan** - Architect with explicit technical decisions
4. **⚡ Execute** - Build exactly what was specified
5. **📊 Track** - Maintain transparent progress at every step

No shortcuts. No assumptions. No regrets.

## System Architecture

```
.claude/
├── CLAUDE.md          # Always-on instructions (copy content to your project's CLAUDE.md file)
├── agents/            # Task-oriented agents (for context preservation)
├── commands/          # Command definitions
│   ├── context/       # Create, update, and prime context
│   ├── pm/            # ← Project management commands (this system)
│   └── testing/       # Prime and execute tests (edit this)
├── context/           # Project-wide context files
├── epics/             # ← PM's local workspace (place in .gitignore)
│   └── [epic-name]/   # Epic and related tasks
│       ├── epic.md    # Implementation plan
│       ├── [#].md     # Individual task files
│       └── updates/   # Work-in-progress updates
├── prds/              # ← PM's PRD files
├── rules/             # Place any rule files you'd like to reference here
└── scripts/           # Place any script files you'd like to use here
```

## Workflow Phases

### 1. Product Planning Phase

```bash
/pm:prd-new feature-name
```
Launches comprehensive brainstorming to create a Product Requirements Document capturing vision, user stories, success criteria, and constraints.

**Output:** `.claude/prds/feature-name.md`

### 2. Implementation Planning Phase

```bash
/pm:prd-parse feature-name
```
Transforms PRD into a technical implementation plan with architectural decisions, technical approach, and dependency mapping.

**Output:** `.claude/epics/feature-name/epic.md`

### 3. Task Decomposition Phase

```bash
/pm:epic-decompose feature-name
```
Breaks epic into concrete, actionable tasks with acceptance criteria, effort estimates, and parallelization flags.

**Output:** `.claude/epics/feature-name/[task].md`

### 4. GitHub Synchronization

```bash
/pm:epic-sync feature-name
# Or for confident workflows:
/pm:epic-oneshot feature-name
```
Pushes epic and tasks to GitHub as issues with appropriate labels and relationships.

### 5. Execution Phase

```bash
/pm:issue-start 1234  # Launch specialized agent
/pm:issue-sync 1234   # Push progress updates
/pm:next             # Get next priority task
```
Specialized agents implement tasks while maintaining progress updates and an audit trail.

## Command Reference

> [!TIP]
> Type `/pm:help` for a concise command summary

### Initial Setup
- `/pm:init` - Install dependencies and configure GitHub

### PRD Commands
- `/pm:prd-new` - Launch brainstorming for new product requirement
- `/pm:prd-parse` - Convert PRD to implementation epic
- `/pm:prd-list` - List all PRDs
- `/pm:prd-edit` - Edit existing PRD
- `/pm:prd-status` - Show PRD implementation status

### Epic Commands
- `/pm:epic-decompose` - Break epic into task files
- `/pm:epic-sync` - Push epic and tasks to GitHub
- `/pm:epic-oneshot` - Decompose and sync in one command
- `/pm:epic-list` - List all epics
- `/pm:epic-show` - Display epic and its tasks
- `/pm:epic-close` - Mark epic as complete
- `/pm:epic-edit` - Edit epic details
- `/pm:epic-refresh` - Update epic progress from tasks

### Issue Commands
- `/pm:issue-show` - Display issue and sub-issues
- `/pm:issue-status` - Check issue status
- `/pm:issue-start` - Begin work with specialized agent
- `/pm:issue-sync` - Push updates to GitHub
- `/pm:issue-close` - Mark issue as complete
- `/pm:issue-reopen` - Reopen closed issue
- `/pm:issue-edit` - Edit issue details

### Workflow Commands
- `/pm:next` - Show next priority issue with epic context
- `/pm:status` - Overall project dashboard
- `/pm:standup` - Daily standup report
- `/pm:blocked` - Show blocked tasks
- `/pm:in-progress` - List work in progress

### Sync Commands
- `/pm:sync` - Full bidirectional sync with GitHub
- `/pm:import` - Import existing GitHub issues

### Maintenance Commands
- `/pm:validate` - Check system integrity
- `/pm:clean` - Archive completed work
- `/pm:search` - Search across all content

## The Parallel Execution System

### Issues Aren't Atomic

Traditional thinking: One issue = One developer = One task

**Reality: One issue = Multiple parallel work streams**

A single "Implement user authentication" issue isn't one task. It's...

- **Agent 1**: Database tables and migrations
- **Agent 2**: Service layer and business logic
- **Agent 3**: API endpoints and middleware
- **Agent 4**: UI components and forms
- **Agent 5**: Test suites and documentation

All running **simultaneously** in the same worktree.

### The Math of Velocity

**Traditional Approach:**
- Epic with 3 issues
- Sequential execution

**This System:**
- Same epic with 3 issues
- Each issue splits into ~4 parallel streams
- **12 agents working simultaneously**

We're not assigning agents to issues. We're **leveraging multiple agents** to ship faster.

### Context Optimization

**Traditional single-thread approach:**
- Main conversation carries ALL the implementation details
- Context window fills with database schemas, API code, UI components
- Eventually hits context limits and loses coherence

**Parallel agent approach:**
- Main thread stays clean and strategic
- Each agent handles its own context in isolation
- Implementation details never pollute the main conversation
- Main thread maintains oversight without drowning in code

Your main conversation becomes the conductor, not the orchestra.

### GitHub vs Local: Perfect Separation

**What GitHub Sees:**
- Clean, simple issues
- Progress updates
- Completion status

**What Actually Happens Locally:**
- Issue #1234 explodes into 5 parallel agents
- Agents coordinate through Git commits
- Complex orchestration hidden from view

GitHub doesn't need to know HOW the work got done – just that it IS done.

### The Command Flow

```bash
# Analyze what can be parallelized
/pm:issue-analyze 1234

# Launch the swarm
/pm:epic-start memory-system

# Watch the magic
# 12 agents working across 3 issues
# All in: ../epic-memory-system/

# One clean merge when done
/pm:epic-merge memory-system
```

## Key Features & Benefits

### 🧠 **Context Preservation**
Never lose project state again. Each epic maintains its own context, agents read from `.claude/context/`, and updates locally before syncing.

### ⚡ **Parallel Execution**
Ship faster with multiple agents working simultaneously. Tasks marked `parallel: true` enable conflict-free concurrent development.

### 🔗 **GitHub Native**
Works with tools your team already uses. Issues are the source of truth, comments provide history, and there is no dependency on the Projects API.

### 🤖 **Agent Specialization**
Right tool for every job. Different agents for UI, API, and database work. Each reads requirements and posts updates automatically.

### 📊 **Full Traceability**
Every decision is documented. PRD → Epic → Task → Issue → Code → Commit. Complete audit trail from idea to production.

### 🚀 **Developer Productivity**
Focus on building, not managing. Intelligent prioritization, automatic context loading, and incremental sync when ready.

## Proven Results

Teams using this system report:
- **89% less time** lost to context switching – you'll use `/compact` and `/clear` a LOT less
- **5-8 parallel tasks** vs 1 previously – editing/testing multiple files at the same time
- **75% reduction** in bug rates – due to the breaking down features into detailed tasks
- **Up to 3x faster** feature delivery – based on feature size and complexity

## Example Flow

```bash
# Start a new feature
/pm:prd-new memory-system

# Review and refine the PRD...

# Create implementation plan
/pm:prd-parse memory-system

# Review the epic...

# Break into tasks and push to GitHub
/pm:epic-oneshot memory-system
# Creates issues: #1234 (epic), #1235, #1236 (tasks)

# Start development on a task
/pm:issue-start 1235
# Agent begins work, maintains local progress

# Sync progress to GitHub
/pm:issue-sync 1235
# Updates posted as issue comments

# Check overall status
/pm:epic-show memory-system
```

## Get Started Now

### Quick Setup (2 minutes)

1. **Install this repository into your project**:

   #### Unix/Linux/macOS

   ```bash
   cd path/to/your/project/
   curl -sSL https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.sh | bash
   # or: wget -qO- https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.sh | bash
   ```

   #### Windows (PowerShell)
   ```bash
   cd path/to/your/project/
   iwr -useb https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.bat | iex
   ```
   > ⚠️ **IMPORTANT**: If you already have a `.claude` directory, clone this repository to a different directory and copy the contents of the cloned `.claude` directory to your project's `.claude` directory.

   See full/other installation options in the [installation guide ›](https://github.com/automazeio/ccpm/tree/main/install)


2. **Initialize the PM system**:
   ```bash
   /pm:init
   ```
   This command will:
   - Install GitHub CLI (if needed)
   - Authenticate with GitHub
   - Install [gh-sub-issue extension](https://github.com/yahsan2/gh-sub-issue) for proper parent-child relationships
   - Create required directories
   - Update .gitignore

3. **Create `CLAUDE.md`** with your repository information
   ```bash
   /init include rules from .claude/CLAUDE.md
   ```
   > If you already have a `CLAUDE.md` file, run: `/re-init` to update it with important rules from `.claude/CLAUDE.md`.

4. **Prime the system**:
   ```bash
   /context:create
   ```



### Start Your First Feature

```bash
/pm:prd-new your-feature-name
```

Watch as structured planning transforms into shipped code.

## Local vs Remote

| Operation | Local | GitHub |
|-----------|-------|--------|
| PRD Creation | ✅ | — |
| Implementation Planning | ✅ | — |
| Task Breakdown | ✅ | ✅ (sync) |
| Execution | ✅ | — |
| Status Updates | ✅ | ✅ (sync) |
| Final Deliverables | — | ✅ |

## Technical Notes

### GitHub Integration
- Uses **gh-sub-issue extension** for proper parent-child relationships
- Falls back to task lists if extension not installed
- Epic issues track sub-task completion automatically
- Labels provide additional organization (`epic:feature`, `task:feature`)

### File Naming Convention
- Tasks start as `001.md`, `002.md` during decomposition
- After GitHub sync, renamed to `{issue-id}.md` (e.g., `1234.md`)
- Makes it easy to navigate: issue #1234 = file `1234.md`

### Design Decisions
- Intentionally avoids GitHub Projects API complexity
- All commands operate on local files first for speed
- Synchronization with GitHub is explicit and controlled
- Worktrees provide clean git isolation for parallel work
- GitHub Projects can be added separately for visualization

---

## Support This Project

Claude Code PM was developed at [Automaze](https://automaze.io) **for developers who ship, by developers who ship**.

If Claude Code PM helps your team ship better software:

- ⭐ **[Star this repository](https://github.com/automazeio/ccpm)** to show your support
- 🐦 **[Follow @aroussi on X](https://x.com/aroussi)** for updates and tips


---

> [!TIP]
> **Ship faster with Automaze.** We partner with founders to bring their vision to life, scale their business, and optimize for success.
> **[Visit Automaze to book a call with me ›](https://automaze.io)**

---

## 🌍 English Operation Guide / 英文操作指南

### Quick Start for English Users / 英文用户快速开始

#### 1. System Installation / 系统安装
```bash
# Navigate to your project directory / 进入你的项目目录
cd your-project-directory/

# Install CCPM system (Unix/Linux/macOS) / 安装CCPM系统(Unix/Linux/macOS)
curl -sSL https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.sh | bash

# For Windows (PowerShell) / Windows系统(PowerShell)
iwr -useb https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.bat | iex
```

#### 2. Initial Setup / 初始设置
```bash
# Initialize the project management system / 初始化项目管理系统
/pm:init

# This will: / 这将:
# - Install GitHub CLI (if needed) / 安装GitHub CLI(如果需要)
# - Authenticate with your GitHub account / 验证你的GitHub账户
# - Install required extensions / 安装必需的扩展
# - Create necessary directory structure / 创建必要的目录结构
```

#### 3. Project Configuration / 项目配置
```bash
# Create or update your CLAUDE.md file / 创建或更新CLAUDE.md文件
/init include rules from .claude/CLAUDE.md

# Generate project context documentation / 生成项目上下文文档
/context:create
```

### Core Workflow Commands / 核心工作流命令

#### Product Planning / 产品规划
```bash
# Create a new Product Requirements Document / 创建新的产品需求文档
/pm:prd-new feature-name

# Convert PRD to technical implementation plan / 将PRD转换为技术实现计划
/pm:prd-parse feature-name
```

#### Task Management / 任务管理
```bash
# Break epic into actionable tasks / 将史诗任务分解为可执行任务
/pm:epic-decompose feature-name

# Push tasks to GitHub as issues / 将任务推送到GitHub作为issue
/pm:epic-sync feature-name

# Or do both in one step / 或者一步完成两者
/pm:epic-oneshot feature-name
```

#### Execution & Monitoring / 执行与监控
```bash
# Start working on a specific issue / 开始处理特定issue
/pm:issue-start 1234

# Check current status / 检查当前状态
/pm:status

# Get next priority task / 获取下一个优先任务
/pm:next

# Sync progress to GitHub / 同步进度到GitHub
/pm:issue-sync 1234
```

### Key Directory Structure / 关键目录结构
```
.claude/
├── CLAUDE.md          # Project instructions for Claude / Claude项目指令
├── agents/            # Specialized task agents / 专业化任务代理
├── commands/          # Command definitions / 命令定义
├── context/           # Project context documentation / 项目上下文文档
├── epics/            # Implementation plans and tasks / 实施计划和任务
├── prds/             # Product requirements documents / 产品需求文档
├── rules/            # Development rules and patterns / 开发规则和模式
└── scripts/          # Utility scripts / 实用脚本
```

### Common Operations / 常用操作

#### Starting a New Feature / 开始新功能
```bash
# 1. Create requirements / 创建需求
/pm:prd-new user-authentication

# 2. Review and refine the PRD / 审查和完善PRD
# 3. Create implementation plan / 创建实施计划
/pm:prd-parse user-authentication

# 4. Break into tasks and push to GitHub / 分解任务并推送到GitHub
/pm:epic-oneshot user-authentication

# 5. Start development / 开始开发
/pm:issue-start 1235
```

#### Daily Workflow / 日常工作流
```bash
# Check what to work on next / 检查下一步该做什么
/pm:next

# Start working on the recommended task / 开始处理推荐的任务
/pm:issue-start [issue-number]

# Periodically sync progress / 定期同步进度
/pm:issue-sync [issue-number]

# End of day status check / 结束时的状态检查
/pm:status
```

#### Team Collaboration / 团队协作
```bash
# Import existing GitHub issues / 导入现有的GitHub issue
/pm:import

# Full sync with GitHub / 与GitHub完全同步
/pm:sync

# Check blocked tasks / 检查被阻塞的任务
/pm:blocked

# View work in progress / 查看进行中的工作
/pm:in-progress
```

### Troubleshooting / 故障排除

#### Common Issues / 常见问题
- **GitHub authentication fails**: Run `gh auth login` manually / GitHub认证失败: 手动运行 `gh auth login`
- **Missing gh-sub-issue extension**: Install via `gh extension install yahsan2/gh-sub-issue` / 缺少gh-sub-issue扩展: 通过 `gh extension install yahsan2/gh-sub-issue` 安装
- **Permission errors**: Check write permissions in `.claude/` directory / 权限错误: 检查 `.claude/` 目录的写入权限

#### System Maintenance / 系统维护
```bash
# Validate system integrity / 验证系统完整性
/pm:validate

# Clean up completed work / 清理已完成的工作
/pm:clean

# Search across all content / 搜索所有内容
/pm:search
```

### Best Practices / 最佳实践

1. **Always start with PRDs**: Use `/pm:prd-new` before coding / 始终从PRD开始: 编码前使用 `/pm:prd-new`
2. **Sync regularly**: Use `/pm:issue-sync` to maintain GitHub visibility / 定期同步: 使用 `/pm:issue-sync` 保持GitHub可见性
3. **Use parallel execution**: Tasks marked `parallel: true` enable concurrent development / 使用并行执行: 标记为 `parallel: true` 的任务支持并发开发
4. **Maintain context**: Regular `/context:update` keeps documentation current / 维护上下文: 定期 `/context:update` 保持文档最新
5. **Leverage specialized agents**: Different agents for UI, API, database work / 利用专业化代理: 不同的代理处理UI、API、数据库工作

### Support Resources / 支持资源
- **GitHub Repository**: https://github.com/automazeio/ccpm / GitHub仓库
- **Documentation**: Check the `docs/` directory for detailed guides / 文档: 查看 `docs/` 目录获取详细指南
- **Issues**: Report problems via GitHub Issues / 问题: 通过GitHub Issues报告问题
- **Community**: Follow [@aroussi on X](https://x.com/aroussi) for updates / 社区: 关注 [@aroussi on X](https://x.com/aroussi) 获取更新

---

## Star History

![Star History Chart](https://api.star-history.com/svg?repos=automazeio/ccpm)
