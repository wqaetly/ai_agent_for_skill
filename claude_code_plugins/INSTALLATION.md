# 安装指南

快速安装和测试所有 Claude Code 插件的指南。

## 🚀 快速开始 (本地测试)

由于您在开发目录中，可以直接安装：

### 步骤 1: 添加插件市场

在 Claude Code 中运行：
```
/plugin marketplace add E:\Study\wqaetly\ai_agent_for_skill\claude_code_plugins
```

或使用项目根目录的相对路径：
```
/plugin marketplace add ./claude_code_plugins
```

### 步骤 2: 安装插件

#### 安装 Claude 开发规范插件 (推荐首先安装)
```
/plugin install claude-standards@nkg-game-development-marketplace
```

#### 安装游戏技能配置插件
```
/plugin install game-skill-config@nkg-game-development-marketplace
```

#### 安装 Unity 编译插件
```
/plugin install nkg-unity@nkg-game-development-marketplace
```

### 步骤 3: 重启 Claude Code

退出并重启 Claude Code 以加载插件。

### 步骤 4: 验证安装

检查插件是否已加载：
```
/help
```

您应该看到以下新增命令：

#### Claude 开发规范插件命令：
- `/standards-load` - 加载开发规范
- `/standards-config` - 配置规范参数
- `/standards-status` - 查看规范状态

#### 游戏技能配置插件命令：
- `/skill-generate` - 生成新的技能配置
- `/skill-analyze` - 分析现有技能
- `/skill-debug` - 调试技能问题
- `/skill-list` - 列出所有技能
- `/skill-compare` - 对比技能

#### Unity 编译插件命令：
- `/compile` - 智能编译 Unity 项目
- `/find-assembly` - 查找程序集

## 🧪 插件测试

### 测试 Claude 开发规范插件

#### 测试 1: 加载开发规范
```
/standards-load
```

Claude 应该：
1. 显示成功加载的规范模块
2. 列出当前配置详情
3. 提供使用提示

#### 测试 2: 配置规范参数
```
/standards-config language --primary zh-CN
/standards-config socratic --auto-activate true
```

#### 测试 3: 查看规范状态
```
/standards-status --detailed
```

#### 测试 4: 触发苏格拉底式对话
尝试使用关键词：
```
为什么选择这个架构方案？
```

Claude 应该自动进入深度质疑模式。

### 测试游戏技能配置插件

#### 测试 1: 生成简单技能
```
/skill-generate

创建一个简单的火球术技能，造成 100 点魔法伤害
```

Claude 应该：
1. 如有需要询问澄清问题
2. 生成完整的 JSON 配置
3. 保存到 `Assets/Skills/` 目录
4. 解释技能机制

#### 测试 2: 分析现有技能
```
/skill-analyze

分析 Assets/Skills/TryndamereBloodlust.json
```

Claude 应该：
1. 读取文件
2. 提供详细的机制分析
3. 显示时间轴可视化
4. 计算不同等级的数值
5. 给出改进建议

#### 测试 3: 列出所有技能
```
/skill-list
```

Claude 应该显示项目中所有技能的格式化列表。

#### 测试 4: 对比技能
```
/skill-compare

对比 TryndamereBloodlust.json 和 SionSoulFurnaceV2.json
```

Claude 应该显示并排对比和平衡性分析。

#### 测试 5: 自然语言激活 (代理/技能激活)
尝试自然语言而不是命令：
```
我需要一个消耗法力值来恢复生命值的治愈技能。
治疗效果应该随法术强度缩放。
```

技能配置专家代理或游戏技能系统专家应该自动激活。

#### 测试 6: 验证钩子
创建或编辑技能文件，验证钩子应该自动运行：
```
创建新文件：Assets/Skills/TestSkill.json

然后修改并保存
```

保存后您应该看到验证消息。

### 测试 Unity 编译插件

#### 测试 1: 智能编译
```
/compile
```

Claude 应该智能识别项目类型并执行编译。

#### 测试 2: 查找程序集
```
/find-assembly UnityEngine
```

## 🔧 故障排除

### 命令未显示

如果命令没有在 `/help` 中出现：

1. 检查插件是否已安装：
   ```
   /plugin
   ```

2. 验证市场是否已添加：
   ```
   /plugin marketplace list
   ```

3. 检查插件是否已启用：
   ```
   /plugin list
   ```

4. 尝试重新安装：
   ```
   /plugin uninstall claude-standards@nkg-game-development-marketplace
   /plugin install claude-standards@nkg-game-development-marketplace
   ```

5. 重启 Claude Code

### 钩子不工作

如果验证钩子没有触发：

1. 检查脚本是否可执行：
   ```bash
   cd claude_code_plugins/game-skill-config-plugin/scripts
   ls -la
   ```

   如果不可执行：
   ```bash
   chmod +x *.sh
   ```

2. 手动测试脚本：
   ```bash
   ./validate-skill.sh "../../../ai_agent_for_skill/Assets/Skills/TryndamereBloodlust.json"
   ```

3. 检查 Python 是否可用：
   ```bash
   python3 --version
   ```

### 代理未激活

代理应该在您提到技能配置时自动激活。如果没有：

1. 先尝试使用命令：`/skill-generate`
2. 明确指定："使用技能配置专家帮我..."
3. 直接引用技能文件："分析 TryndamereBloodlust.json"

### Windows 路径问题

如果在 Windows 上遇到路径问题：

使用正斜杠或转义反斜杠：
```
/plugin marketplace add E:/Study/wqaetly/ai_agent_for_skill/claude_code_plugins
```

或在您的项目内：
```
cd E:\Study\wqaetly\ai_agent_for_skill
claude
/plugin marketplace add ./claude_code_plugins
```

### 中文规范未生效

如果中文开发规范没有生效：

1. 检查规范是否已加载：
   ```
   /standards-status --module language-standards
   ```

2. 重新加载语言规范：
   ```
   /standards-load --language
   ```

3. 检查配置冲突：
   ```
   /standards-config check-conflicts
   ```

## 📁 插件结构

您已安装的插件具有以下结构：

```
claude_code_plugins/
├── .claude-plugin/
│   └── marketplace.json         # 市场定义
├── claude-standards/            # 开发规范插件
│   ├── .claude-plugin/
│   │   └── plugin.json          # 插件清单
│   ├── prompts/                 # 提示词模块
│   ├── commands/                # 管理命令
│   ├── hooks/                   # 钩子配置
│   ├── config/                  # 配置文件
│   ├── scripts/                 # 管理脚本
│   └── README.md                # 文档
└── game-skill-config-plugin/
    ├── .claude-plugin/
    │   └── plugin.json          # 插件清单
    ├── commands/
    │   ├── skill-generate.md    # 生成新技能
    │   ├── skill-analyze.md     # 分析现有技能
    │   ├── skill-debug.md       # 调试技能问题
    │   ├── skill-list.md        # 列出所有技能
    │   └── skill-compare.md     # 对比技能
    ├── agents/
    │   └── skill-config-specialist.md  # 专门代理
    ├── skills/
    │   └── skill-system-expert/
    │       └── SKILL.md         # 代理技能
    ├── hooks/
    │   └── hooks.json           # 钩子配置
    ├── scripts/
    │   ├── validate-skill.sh    # 验证脚本
    │   └── detect-skill-intent.sh  # 意图检测
    ├── README.md                # 文档
    ├── LICENSE                  # MIT 许可证
    └── CHANGELOG.md             # 版本历史
```

## 🎯 后续步骤

成功安装后：

1. **建立开发规范** - 首先运行 `/standards-load` 建立中文开发基础
2. **生成您的第一个技能** - 尝试 `/skill-generate` 配合简单概念
3. **分析现有技能** - 使用 `/skill-analyze` 了解当前技能
4. **对比平衡性** - 使用 `/skill-compare` 检查技能间平衡
5. **使用自然语言** - 直接描述需求，让代理帮助

## 📞 支持

如果遇到问题：

1. 检查此安装指南
2. 查看主要的 [README.md](claude-standards/README.md) 和 [README.md](game-skill-config-plugin/README.md)
3. 运行调试模式的 Claude Code：`claude --debug`
4. 检查 [CHANGELOG.md](game-skill-config-plugin/CHANGELOG.md)

## 🛠️ 开发模式

如果您想修改插件：

1. 修改相关插件目录中的文件
2. 卸载：`/plugin uninstall [plugin-name]@nkg-game-development-marketplace`
3. 重新安装：`/plugin install [plugin-name]@nkg-game-development-marketplace`
4. 重启 Claude Code
5. 测试您的更改

## 🎮 推荐使用流程

1. **安装顺序**：claude-standards → game-skill-config → nkg-unity
2. **首次使用**：先运行 `/standards-load` 建立开发规范
3. **日常开发**：利用自然语言激活相应代理
4. **质量控制**：依赖自动化钩子和验证机制

祝您开发愉快！🎮✨

**让 Claude 更懂中文开发规范！** 🇨🇳
