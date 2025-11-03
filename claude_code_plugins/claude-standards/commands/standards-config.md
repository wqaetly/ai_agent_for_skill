# 配置 Claude 开发规范

配置和管理 Claude 开发规范的具体参数和设置，支持项目级别的个性化配置。

## 使用方法

```bash
/standards-config [选项] [参数]
```

## 配置选项

### 语言设置
```bash
/standards-config language --primary zh-CN
/standards-config language --style direct
/standards-config language --comments chinese_with_space
```

### 工作原则设置
```bash
/standards-config principles --quality-gate strict
/standards-config principles --architecture-aware true
/standards-config principles --incremental-improvement true
```

### 苏格拉底对话设置
```bash
/standards-config socratic --auto-activate true
/standards-config socratic --intensity deep
/standards-config socratic --triggers "为什么,架构,最佳实践"
```

### 质量底线设置
```bash
/standards-config quality --architecture-decay true
/standards-config quality --technical-debt threshold:high
/standards-config quality --performance-alert true
```

## 详细配置选项

### 语言配置 (language)
- `--primary <lang>`: 主要语言 (zh-CN, en-US)
- `--style <style>`: 表达风格 (direct, formal, friendly)
- `--terms <format>`: 技术术语处理 (keep_english, translate, mixed)
- `--comments <format>`: 注释格式 (chinese, english, mixed)

### 工作原则配置 (principles)
- `--context-priority <bool>`: 项目上下文优先
- `--architecture-aware <bool>`: 架构感知模式
- `--quality-oriented <level>`: 质量导向级别 (strict, moderate, relaxed)
- `--incremental-only <bool>`: 仅允许增量改进

### 苏格拉底对话配置 (socratic)
- `--auto-activate <bool>`: 自动激活深度对话
- `--intensity <level>`: 质疑强度 (gentle, deep, intense)
- `--triggers <keywords>`: 激活关键词列表
- `--timeout <seconds>`: 对话超时时间

### 质量底线配置 (quality)
- `--architecture-decay <bool>`: 架构腐化检测
- `--debt-threshold <level>`: 技术债务阈值 (low, medium, high)
- `--performance-alert <bool>`: 性能劣化警报
- `--maintainability-check <bool>`: 可维护性检查

## 配置文件管理

### 保存配置
```bash
/standards-config save --name my-project-config
/standards-config save --global
/standards-config save --project
```

### 加载配置
```bash
/standards-config load --name my-project-config
/standards-config load --default
/standards-config load --file /path/to/config.json
```

### 列出配置
```bash
/standards-config list
/standards-config list --global
/standards-config list --local
```

### 删除配置
```bash
/standards-config delete --name my-project-config
/standards-config reset --to-default
```

## 配置示例

### 适合初创项目的配置
```bash
/standards-config language --primary zh-CN --style direct
/standards-config principles --quality-oriented moderate --incremental-only true
/standards-config socratic --auto-activate false
/standards-config quality --debt-threshold medium
/standards-config save --name startup-config
```

### 适合企业级项目的配置
```bash
/standards-config language --primary zh-CN --style formal
/standards-config principles --quality-oriented strict --architecture-aware true
/standards-config socratic --auto-activate true --intensity deep
/standards-config quality --architecture-decay true --performance-alert true
/standards-config save --name enterprise-config
```

### 适合个人项目的配置
```bash
/standards-config language --primary zh-CN --style direct
/standards-config principles --context-priority true
/standards-config socratic --auto-activate true --triggers "为什么,为什么这样"
/standards-config quality --maintainability-check true
/standards-config save --name personal-config
```

## 配置验证

### 验证当前配置
```bash
/standards-config validate
/standards-config validate --strict
/standards-config validate --show-conflicts
```

### 检查配置冲突
```bash
/standards-config check-conflicts
/standards-config check-conflicts --with-plugin game-skill-config
```

## 高级功能

### 配置模板
```bash
/standards-config template --list
/standards-config template --apply startup
/standards-config template --create --name custom-template
```

### 配置导入导出
```bash
/standards-config export --format json --file standards.json
/standards-config import --file standards.json
/standards-config import --url https://example.com/standards.json
```

### 团队同步
```bash
/standards-config sync --team
/standards-config sync --remote https://github.com/team/standards
/standards-config sync --push
```

## 输出格式

### 配置成功
```
✅ Claude 开发规范配置已更新

📋 当前配置概览:
语言设置: 中文 (直接风格)
工作原则: 质量导向 (严格模式)
苏格拉底对话: 智能激活 (深度质疑)
质量底线: 全部启用

💾 配置已保存到: .claude/standards/config.json
🔄 重启会话以应用新配置
```

### 配置验证结果
```
🔍 配置验证结果

✅ 通过的检查:
- 语言设置一致性
- 工作原则兼容性
- 质量底线完整性

⚠️ 警告:
- 苏格拉底对话可能与其他插件冲突
- 建议降低质疑强度以避免过度质疑

❌ 错误:
- 无

📊 配置健康度: 85/100
```