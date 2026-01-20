using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace RAG
{
    /// <summary>
    /// RAG Configuration Editor Window
    /// Based on UIElements for modern editing experience
    /// </summary>
    public class RAGConfigEditorWindow : EditorWindow
    {
        private RAGConfig config;
        private SerializedObject serializedConfig;
        
        // Tab system
        private VisualElement tabContent;
        private int currentTab = 0;
        private Button[] tabButtons;
        
        // Prompt preview
        private TextField promptPreviewField;
        
        // Styles
        private const string WINDOW_TITLE = "RAG 配置中心";
        private const float MIN_WIDTH = 600f;
        private const float MIN_HEIGHT = 500f;
        
        // Color scheme
        private static readonly Color TabActiveColor = new Color(0.3f, 0.5f, 0.8f);
        private static readonly Color TabInactiveColor = new Color(0.25f, 0.25f, 0.25f);
        private static readonly Color HeaderColor = new Color(0.2f, 0.2f, 0.2f);
        private static readonly Color SectionColor = new Color(0.18f, 0.18f, 0.18f);

        [MenuItem("Tools/RAG System/配置中心 (Config Center)", priority = 99)]
        public static void ShowWindow()
        {
            var window = GetWindow<RAGConfigEditorWindow>();
            window.titleContent = new GUIContent(WINDOW_TITLE, EditorGUIUtility.IconContent("Settings").image);
            window.minSize = new Vector2(MIN_WIDTH, MIN_HEIGHT);
        }

        private void OnEnable()
        {
            config = RAGConfig.Instance;
            if (config != null)
            {
                serializedConfig = new SerializedObject(config);
            }
        }

        private void CreateGUI()
        {
            var root = rootVisualElement;
            root.style.backgroundColor = new Color(0.15f, 0.15f, 0.15f);
            
            // Main container
            var mainContainer = new VisualElement();
            mainContainer.style.flexGrow = 1;
            mainContainer.style.paddingTop = 10;
            mainContainer.style.paddingBottom = 10;
            mainContainer.style.paddingLeft = 10;
            mainContainer.style.paddingRight = 10;
            root.Add(mainContainer);
            
            // Header
            CreateHeader(mainContainer);
            
            // Tab bar
            CreateTabBar(mainContainer);
            
            // Tab content area
            tabContent = new VisualElement();
            tabContent.style.flexGrow = 1;
            tabContent.style.marginTop = 10;
            mainContainer.Add(tabContent);
            
            // Footer with buttons
            CreateFooter(mainContainer);
            
            // Show first tab
            SwitchTab(0);
        }

        private void CreateHeader(VisualElement parent)
        {
            var header = new VisualElement();
            header.style.flexDirection = FlexDirection.Row;
            header.style.alignItems = Align.Center;
            header.style.backgroundColor = HeaderColor;
            header.style.paddingTop = 15;
            header.style.paddingBottom = 15;
            header.style.paddingLeft = 15;
            header.style.paddingRight = 15;
            header.style.borderBottomLeftRadius = 8;
            header.style.borderBottomRightRadius = 8;
            header.style.borderTopLeftRadius = 8;
            header.style.borderTopRightRadius = 8;
            header.style.marginBottom = 10;
            
            // Icon - using Unity built-in icon
            var icon = new VisualElement();
            icon.style.width = 28;
            icon.style.height = 28;
            icon.style.marginRight = 10;
            icon.style.backgroundImage = Background.FromTexture2D(EditorGUIUtility.IconContent("Settings").image as Texture2D);
            header.Add(icon);
            
            // Title section
            var titleSection = new VisualElement();
            titleSection.style.flexGrow = 1;
            
            var title = new Label("RAG 系统配置中心");
            title.style.fontSize = 18;
            title.style.unityFontStyleAndWeight = FontStyle.Bold;
            title.style.color = Color.white;
            titleSection.Add(title);
            
            var subtitle = new Label("集中管理 DeepSeek API、服务器、路径和 Prompt 模板配置");
            subtitle.style.fontSize = 11;
            subtitle.style.color = new Color(0.7f, 0.7f, 0.7f);
            subtitle.style.marginTop = 3;
            titleSection.Add(subtitle);
            
            header.Add(titleSection);
            
            // Status indicator
            var statusContainer = new VisualElement();
            statusContainer.style.flexDirection = FlexDirection.Row;
            statusContainer.style.alignItems = Align.Center;
            
            var statusDot = new VisualElement();
            statusDot.style.width = 10;
            statusDot.style.height = 10;
            statusDot.style.borderTopLeftRadius = 5;
            statusDot.style.borderTopRightRadius = 5;
            statusDot.style.borderBottomLeftRadius = 5;
            statusDot.style.borderBottomRightRadius = 5;
            statusDot.style.backgroundColor = config != null ? Color.green : Color.red;
            statusDot.style.marginRight = 5;
            statusContainer.Add(statusDot);
            
            var statusLabel = new Label(config != null ? "配置已加载" : "配置未找到");
            statusLabel.style.fontSize = 11;
            statusLabel.style.color = new Color(0.7f, 0.7f, 0.7f);
            statusContainer.Add(statusLabel);
            
            header.Add(statusContainer);
            parent.Add(header);
        }

        private void CreateTabBar(VisualElement parent)
        {
            var tabBar = new VisualElement();
            tabBar.style.flexDirection = FlexDirection.Row;
            tabBar.style.marginBottom = 5;

            string[] tabNames = { "[Skill] 技能系统", "[Buff] Buff系统", "[AI] DeepSeek API", "[Server] 服务器", "[Path] 路径", "[Prompt] 模板", "[Test] 测试" };
            tabButtons = new Button[tabNames.Length];

            for (int i = 0; i < tabNames.Length; i++)
            {
                int tabIndex = i;
                var btn = new Button(() => SwitchTab(tabIndex));
                btn.text = tabNames[i];
                btn.style.flexGrow = 1;
                btn.style.height = 35;
                btn.style.marginRight = i < tabNames.Length - 1 ? 3 : 0;
                btn.style.borderTopLeftRadius = 6;
                btn.style.borderTopRightRadius = 6;
                btn.style.borderBottomLeftRadius = 0;
                btn.style.borderBottomRightRadius = 0;
                btn.style.borderBottomWidth = 0;
                btn.style.fontSize = 11;
                tabButtons[i] = btn;
                tabBar.Add(btn);
            }

            parent.Add(tabBar);
        }

        private void SwitchTab(int index)
        {
            currentTab = index;
            
            // Update tab button styles
            for (int i = 0; i < tabButtons.Length; i++)
            {
                tabButtons[i].style.backgroundColor = i == index ? TabActiveColor : TabInactiveColor;
                tabButtons[i].style.color = i == index ? Color.white : new Color(0.7f, 0.7f, 0.7f);
            }
            
            // Clear and rebuild content
            tabContent.Clear();
            
            var scrollView = new ScrollView(ScrollViewMode.Vertical);
            scrollView.style.flexGrow = 1;
            
            switch (index)
            {
                case 0:
                    CreateSkillSystemTab(scrollView);
                    break;
                case 1:
                    CreateBuffSystemTab(scrollView);
                    break;
                case 2:
                    CreateDeepSeekTab(scrollView);
                    break;
                case 3:
                    CreateServerTab(scrollView);
                    break;
                case 4:
                    CreatePathsTab(scrollView);
                    break;
                case 5:
                    CreatePromptTab(scrollView);
                    break;
                case 6:
                    CreatePreviewTab(scrollView);
                    break;
            }
            
            tabContent.Add(scrollView);
        }

        #region Tab Contents

        private void CreateSkillSystemTab(VisualElement parent)
        {
            var container = CreateSectionContainer("技能系统类型配置", "配置用于适配不同项目技能架构的类型信息（支持适配到其他 Unity 项目）");

            // 基类配置区域
            var baseTypeSection = CreateSubSection("基类与程序集配置");

            AddNestedConfigField(baseTypeSection, "Action 基类类型名", "skillSystemConfig.baseActionTypeName",
                "Action 基类的完整类型名（如：SkillSystem.Actions.ISkillAction）");
            AddNestedConfigField(baseTypeSection, "技能数据类型名", "skillSystemConfig.skillDataTypeName",
                "技能数据类的完整类型名（如：SkillSystem.Data.SkillData）");
            AddNestedConfigField(baseTypeSection, "技能轨道类型名", "skillSystemConfig.skillTrackTypeName",
                "技能轨道类的完整类型名（如：SkillSystem.Data.SkillTrack）");
            AddNestedConfigField(baseTypeSection, "程序集名称", "skillSystemConfig.assemblyName",
                "目标程序集名称（如：Assembly-CSharp）");

            container.Add(baseTypeSection);

            // 特性配置区域
            var attrSection = CreateSubSection("Odin/Unity 特性名称配置");

            AddNestedConfigField(attrSection, "显示名称特性", "skillSystemConfig.displayNameAttributeName",
                "用于获取 Action 显示名称的特性类名");
            AddNestedConfigField(attrSection, "分类特性", "skillSystemConfig.categoryAttributeName",
                "用于获取 Action 分类的特性类名");
            AddNestedConfigField(attrSection, "LabelText 特性", "skillSystemConfig.labelTextAttributeName",
                "Odin LabelText 特性类名");
            AddNestedConfigField(attrSection, "BoxGroup 特性", "skillSystemConfig.boxGroupAttributeName",
                "Odin BoxGroup 特性类名");
            AddNestedConfigField(attrSection, "InfoBox 特性", "skillSystemConfig.infoBoxAttributeName",
                "Odin InfoBox 特性类名");
            AddNestedConfigField(attrSection, "MinValue 特性", "skillSystemConfig.minValueAttributeName",
                "Odin MinValue 特性类名");

            container.Add(attrSection);

            // Schema 字段映射区域
            var mappingSection = CreateSubSection("Schema 字段映射（Python 端使用）");

            var mappingHint = new Label("配置 Unity 字段名到 Python Schema 字段名的映射关系");
            mappingHint.style.fontSize = 11;
            mappingHint.style.color = new Color(0.6f, 0.6f, 0.6f);
            mappingHint.style.marginBottom = 10;
            mappingSection.Add(mappingHint);

            // 显示当前映射列表
            if (serializedConfig != null)
            {
                var mappingsProp = serializedConfig.FindProperty("schemaFieldMappings");
                if (mappingsProp != null)
                {
                    for (int i = 0; i < mappingsProp.arraySize; i++)
                    {
                        var element = mappingsProp.GetArrayElementAtIndex(i);
                        var unityField = element.FindPropertyRelative("unityFieldName");
                        var pythonField = element.FindPropertyRelative("pythonFieldName");
                        var desc = element.FindPropertyRelative("description");

                        var row = new VisualElement();
                        row.style.flexDirection = FlexDirection.Row;
                        row.style.marginBottom = 5;

                        var unityTextField = new TextField();
                        unityTextField.value = unityField?.stringValue ?? "";
                        unityTextField.style.flexGrow = 1;
                        unityTextField.style.marginRight = 5;
                        unityTextField.RegisterValueChangedCallback(evt => {
                            if (unityField != null) {
                                unityField.stringValue = evt.newValue;
                                serializedConfig.ApplyModifiedProperties();
                            }
                        });
                        row.Add(unityTextField);

                        var arrowLabel = new Label("→");
                        arrowLabel.style.marginRight = 5;
                        arrowLabel.style.unityTextAlign = TextAnchor.MiddleCenter;
                        row.Add(arrowLabel);

                        var pythonTextField = new TextField();
                        pythonTextField.value = pythonField?.stringValue ?? "";
                        pythonTextField.style.flexGrow = 1;
                        pythonTextField.style.marginRight = 5;
                        pythonTextField.RegisterValueChangedCallback(evt => {
                            if (pythonField != null) {
                                pythonField.stringValue = evt.newValue;
                                serializedConfig.ApplyModifiedProperties();
                            }
                        });
                        row.Add(pythonTextField);

                        var descTextField = new TextField();
                        descTextField.value = desc?.stringValue ?? "";
                        descTextField.style.flexGrow = 1.5f;
                        descTextField.RegisterValueChangedCallback(evt => {
                            if (desc != null) {
                                desc.stringValue = evt.newValue;
                                serializedConfig.ApplyModifiedProperties();
                            }
                        });
                        row.Add(descTextField);

                        mappingSection.Add(row);
                    }
                }
            }

            container.Add(mappingSection);

            // 操作按钮区域
            var actionSection = new VisualElement();
            actionSection.style.marginTop = 20;
            actionSection.style.flexDirection = FlexDirection.Row;

            var exportBtn = new Button(() => ExportSkillSystemConfig());
            exportBtn.text = "导出配置到 Python 端";
            exportBtn.style.height = 30;
            exportBtn.style.backgroundColor = new Color(0.2f, 0.5f, 0.3f);
            exportBtn.style.marginRight = 10;
            actionSection.Add(exportBtn);

            var validateBtn = new Button(() => ValidateSkillSystemConfig());
            validateBtn.text = "验证类型配置";
            validateBtn.style.height = 30;
            validateBtn.style.marginRight = 10;
            actionSection.Add(validateBtn);

            var clearCacheBtn = new Button(() => ClearTypeCache());
            clearCacheBtn.text = "清除类型缓存";
            clearCacheBtn.style.height = 30;
            actionSection.Add(clearCacheBtn);

            container.Add(actionSection);

            parent.Add(container);
        }

        /// <summary>
        /// 创建Buff系统配置Tab
        /// </summary>
        private void CreateBuffSystemTab(VisualElement parent)
        {
            var container = CreateSectionContainer("Buff系统类型配置", "配置用于适配不同项目Buff架构的类型信息");

            var config = RAGConfig.Instance;
            if (config == null)
            {
                container.Add(new Label("无法加载配置"));
                parent.Add(container);
                return;
            }

            // 基类配置区域
            var baseSection = CreateSubSection("基类与程序集配置");
            AddNestedConfigField(baseSection, "Buff模板类型名", "buffSystemConfig.buffTemplateTypeName",
                "Buff模板类的完整类型名");
            AddNestedConfigField(baseSection, "Buff效果接口类型名", "buffSystemConfig.buffEffectTypeName",
                "Buff效果接口的完整类型名");
            AddNestedConfigField(baseSection, "Buff触发器接口类型名", "buffSystemConfig.buffTriggerTypeName",
                "Buff触发器接口的完整类型名");
            AddNestedConfigField(baseSection, "程序集名称", "buffSystemConfig.assemblyName",
                "目标程序集名称（如：Assembly-CSharp）");
            container.Add(baseSection);

            // 导出配置区域
            var exportSection = CreateSubSection("导出配置");
            AddNestedConfigField(exportSection, "导出目录", "buffSystemConfig.exportDirectory",
                "JSON 文件导出目录");
            container.Add(exportSection);

            // 操作按钮区域
            var actionSection = new VisualElement();
            actionSection.style.marginTop = 20;
            actionSection.style.flexDirection = FlexDirection.Row;

            var exportBtn = new Button(() => ExportBuffSystemConfig());
            exportBtn.text = "导出Buff配置到Python端";
            exportBtn.style.height = 30;
            exportBtn.style.backgroundColor = new Color(0.2f, 0.5f, 0.3f);
            exportBtn.style.marginRight = 10;
            actionSection.Add(exportBtn);

            var validateBtn = new Button(() => ValidateBuffSystemConfig());
            validateBtn.text = "验证类型配置";
            validateBtn.style.height = 30;
            validateBtn.style.marginRight = 10;
            actionSection.Add(validateBtn);

            var clearCacheBtn = new Button(() => ClearBuffTypeCache());
            clearCacheBtn.text = "清除类型缓存";
            clearCacheBtn.style.height = 30;
            actionSection.Add(clearCacheBtn);

            container.Add(actionSection);

            parent.Add(container);
        }

        private void CreateDeepSeekTab(VisualElement parent)
        {
            var container = CreateSectionContainer("DeepSeek API 配置", "配置用于生成 Action 描述的 AI 服务");
            
            // API Key (stored in EditorPrefs)
            var apiKeySection = new VisualElement();
            apiKeySection.style.marginBottom = 15;
            
            var apiKeyLabel = new Label("[Key] API Key (安全存储于 EditorPrefs，不进入版本控制)");
            apiKeyLabel.style.marginBottom = 5;
            apiKeyLabel.style.color = new Color(0.9f, 0.7f, 0.3f);
            apiKeySection.Add(apiKeyLabel);
            
            var apiKeyField = new TextField();
            apiKeyField.value = RAGConfig.DeepSeekApiKey;
            apiKeyField.isPasswordField = true;
            apiKeyField.style.height = 25;
            apiKeyField.RegisterValueChangedCallback(evt => RAGConfig.DeepSeekApiKey = evt.newValue);
            apiKeySection.Add(apiKeyField);
            
            var apiKeyHint = new Label("提示: API Key 仅存储在本地 EditorPrefs 中，不会提交到版本控制");
            apiKeyHint.style.fontSize = 10;
            apiKeyHint.style.color = new Color(0.5f, 0.5f, 0.5f);
            apiKeyHint.style.marginTop = 3;
            apiKeySection.Add(apiKeyHint);
            
            container.Add(apiKeySection);
            
            // API URL
            AddConfigField(container, "API 地址", "deepSeekApiUrl", "DeepSeek API 的完整 URL");
            
            // Model
            AddConfigField(container, "模型名称", "deepSeekModel", "使用的模型，如 deepseek-chat");
            
            // Temperature
            AddSliderField(container, "温度 (Temperature)", "deepSeekTemperature", 0f, 2f, 
                "越低越稳定确定，越高越有创造性");
            
            // Max Tokens
            AddIntField(container, "最大 Token 数", "deepSeekMaxTokens", "生成内容的最大长度");
            
            // Request Interval
            AddIntField(container, "请求间隔 (毫秒)", "aiRequestInterval", "批量生成时的请求间隔，用于限流");
            
            parent.Add(container);
        }

        private void CreateServerTab(VisualElement parent)
        {
            var container = CreateSectionContainer("SkillAgent 服务器配置", "配置 Python 后端服务器连接参数");
            
            AddConfigField(container, "服务器地址", "serverHost", "服务器 IP 或域名");
            AddIntField(container, "服务器端口", "serverPort", "服务器监听端口");
            AddConfigField(container, "WebUI URL", "webUIUrl", "Web 管理界面地址");
            AddIntField(container, "启动超时 (秒)", "serverStartTimeout", "等待服务器启动的最长时间");
            
            // Server status section
            var statusSection = new VisualElement();
            statusSection.style.marginTop = 20;
            statusSection.style.paddingTop = 15;
            statusSection.style.paddingBottom = 15;
            statusSection.style.paddingLeft = 15;
            statusSection.style.paddingRight = 15;
            statusSection.style.backgroundColor = new Color(0.15f, 0.15f, 0.15f);
            statusSection.style.borderTopLeftRadius = 6;
            statusSection.style.borderTopRightRadius = 6;
            statusSection.style.borderBottomLeftRadius = 6;
            statusSection.style.borderBottomRightRadius = 6;
            
            var statusTitle = new Label("[Links] 快捷链接");
            statusTitle.style.unityFontStyleAndWeight = FontStyle.Bold;
            statusTitle.style.marginBottom = 10;
            statusSection.Add(statusTitle);
            
            var linksContainer = new VisualElement();
            linksContainer.style.flexDirection = FlexDirection.Row;
            
            AddLinkButton(linksContainer, "打开 WebUI", () => Application.OpenURL(config.webUIUrl));
            AddLinkButton(linksContainer, "打开 RAG 查询", () => Application.OpenURL($"{config.webUIUrl}/rag"));
            AddLinkButton(linksContainer, "API 文档", () => Application.OpenURL($"http://{config.serverHost}:{config.serverPort}/docs"));
            
            statusSection.Add(linksContainer);
            container.Add(statusSection);
            
            parent.Add(container);
        }

        private void CreatePathsTab(VisualElement parent)
        {
            var container = CreateSectionContainer("路径配置", "配置数据库和导出文件的路径");
            
            AddConfigField(container, "数据库路径", "actionDatabasePath", "Action 描述数据库的 Unity 资产路径");
            AddConfigField(container, "导出目录", "exportDirectory", "JSON 文件导出目录（相对于 Unity 项目）");
            AddConfigField(container, "服务器脚本", "serverScriptName", "Python 服务器入口脚本名");
            AddConfigField(container, "依赖安装脚本", "installDepsScriptName", "依赖安装批处理脚本名");
            
            // Auto notify toggle
            AddToggleField(container, "导出后自动通知重建索引", "autoNotifyRebuild", 
                "导出 JSON 后自动通知服务器重新构建搜索索引");
            
            // Path preview section
            var pathPreview = new VisualElement();
            pathPreview.style.marginTop = 20;
            pathPreview.style.paddingTop = 15;
            pathPreview.style.paddingBottom = 15;
            pathPreview.style.paddingLeft = 15;
            pathPreview.style.paddingRight = 15;
            pathPreview.style.backgroundColor = new Color(0.15f, 0.15f, 0.15f);
            pathPreview.style.borderTopLeftRadius = 6;
            pathPreview.style.borderTopRightRadius = 6;
            pathPreview.style.borderBottomLeftRadius = 6;
            pathPreview.style.borderBottomRightRadius = 6;
            
            var previewTitle = new Label("[Path] 完整路径预览");
            previewTitle.style.unityFontStyleAndWeight = FontStyle.Bold;
            previewTitle.style.marginBottom = 10;
            pathPreview.Add(previewTitle);
            
            try
            {
                var fullPath = Path.GetFullPath(config.exportDirectory);
                var pathLabel = new Label($"导出目录: {fullPath}");
                pathLabel.style.fontSize = 11;
                pathLabel.style.color = new Color(0.6f, 0.8f, 0.6f);
                pathPreview.Add(pathLabel);
                
                var existsLabel = new Label(Directory.Exists(fullPath) ? "[OK] 目录存在" : "[X] 目录不存在");
                existsLabel.style.fontSize = 11;
                existsLabel.style.color = Directory.Exists(fullPath) ? Color.green : Color.yellow;
                existsLabel.style.marginTop = 5;
                pathPreview.Add(existsLabel);
            }
            catch (Exception e)
            {
                var errorLabel = new Label($"路径解析错误: {e.Message}");
                errorLabel.style.color = Color.red;
                pathPreview.Add(errorLabel);
            }
            
            container.Add(pathPreview);
            parent.Add(container);
        }

        private void CreatePromptTab(VisualElement parent)
        {
            var container = CreateSectionContainer("Prompt 模板配置", "配置 AI 生成 Action 描述时使用的提示词模板");
            
            // System Role
            AddTextAreaField(container, "系统角色描述", "promptSystemRole", 3, 
                "定义 AI 的角色和任务");
            
            // Output Format
            AddTextAreaField(container, "输出格式要求", "promptOutputFormat", 6, 
                "指定 JSON 输出格式");
            
            // Description Spec
            AddTextAreaField(container, "Description 编写规范", "promptDescriptionSpec", 8, 
                "指导 AI 如何编写高质量的描述");
            
            // Keywords Spec
            AddTextAreaField(container, "SearchKeywords 编写规范", "promptKeywordsSpec", 5, 
                "指导 AI 如何选择关键词");
            
            // Notes
            AddTextAreaField(container, "注意事项", "promptNotes", 5, 
                "其他重要提醒");
            
            parent.Add(container);
        }

        private void CreatePreviewTab(VisualElement parent)
        {
            var container = CreateSectionContainer("Prompt 预览 & 测试", "预览完整的 Prompt 并测试 API 连接");
            
            // Test connection button
            var testSection = new VisualElement();
            testSection.style.flexDirection = FlexDirection.Row;
            testSection.style.marginBottom = 15;
            
            var testBtn = new Button(() => TestApiConnection());
            testBtn.text = "测试 API 连接";
            testBtn.style.height = 30;
            testBtn.style.width = 150;
            testSection.Add(testBtn);
            
            var refreshBtn = new Button(() => RefreshPromptPreview());
            refreshBtn.text = "刷新预览";
            refreshBtn.style.height = 30;
            refreshBtn.style.width = 120;
            refreshBtn.style.marginLeft = 10;
            testSection.Add(refreshBtn);
            
            container.Add(testSection);
            
            // Prompt preview
            var previewLabel = new Label("[Preview] 完整 Prompt 预览 (示例: MoveAction)");
            previewLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            previewLabel.style.marginBottom = 10;
            container.Add(previewLabel);
            
            promptPreviewField = new TextField();
            promptPreviewField.multiline = true;
            promptPreviewField.isReadOnly = true;
            promptPreviewField.style.height = 400;
            promptPreviewField.style.whiteSpace = WhiteSpace.Normal;
            promptPreviewField.style.backgroundColor = new Color(0.12f, 0.12f, 0.12f);
            container.Add(promptPreviewField);
            
            // Refresh preview
            RefreshPromptPreview();
            
            // Statistics
            var statsSection = new VisualElement();
            statsSection.style.marginTop = 15;
            statsSection.style.flexDirection = FlexDirection.Row;
            
            var charCount = new Label($"字符数: {promptPreviewField.value.Length}");
            charCount.style.color = new Color(0.6f, 0.6f, 0.6f);
            charCount.style.marginRight = 20;
            statsSection.Add(charCount);
            
            var estimatedTokens = new Label($"预估 Token: ~{promptPreviewField.value.Length / 4}");
            estimatedTokens.style.color = new Color(0.6f, 0.6f, 0.6f);
            statsSection.Add(estimatedTokens);
            
            container.Add(statsSection);
            
            parent.Add(container);
        }

        #endregion

        #region UI Helpers

        private VisualElement CreateSectionContainer(string title, string description)
        {
            var container = new VisualElement();
            container.style.backgroundColor = SectionColor;
            container.style.paddingTop = 15;
            container.style.paddingBottom = 15;
            container.style.paddingLeft = 15;
            container.style.paddingRight = 15;
            container.style.borderTopLeftRadius = 8;
            container.style.borderTopRightRadius = 8;
            container.style.borderBottomLeftRadius = 8;
            container.style.borderBottomRightRadius = 8;
            container.style.marginBottom = 10;
            
            var titleLabel = new Label(title);
            titleLabel.style.fontSize = 14;
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            titleLabel.style.color = Color.white;
            titleLabel.style.marginBottom = 5;
            container.Add(titleLabel);
            
            var descLabel = new Label(description);
            descLabel.style.fontSize = 11;
            descLabel.style.color = new Color(0.6f, 0.6f, 0.6f);
            descLabel.style.marginBottom = 15;
            container.Add(descLabel);
            
            return container;
        }

        private void AddConfigField(VisualElement parent, string label, string propertyName, string tooltip)
        {
            if (serializedConfig == null) return;
            
            var prop = serializedConfig.FindProperty(propertyName);
            if (prop == null) return;
            
            var field = new VisualElement();
            field.style.marginBottom = 10;
            
            var labelElement = new Label(label);
            labelElement.style.marginBottom = 3;
            labelElement.tooltip = tooltip;
            field.Add(labelElement);
            
            var textField = new TextField();
            textField.value = prop.stringValue;
            textField.style.height = 22;
            textField.RegisterValueChangedCallback(evt =>
            {
                prop.stringValue = evt.newValue;
                serializedConfig.ApplyModifiedProperties();
            });
            field.Add(textField);
            
            parent.Add(field);
        }

        private void AddIntField(VisualElement parent, string label, string propertyName, string tooltip)
        {
            if (serializedConfig == null) return;
            
            var prop = serializedConfig.FindProperty(propertyName);
            if (prop == null) return;
            
            var field = new VisualElement();
            field.style.marginBottom = 10;
            
            var labelElement = new Label(label);
            labelElement.style.marginBottom = 3;
            labelElement.tooltip = tooltip;
            field.Add(labelElement);
            
            var intField = new IntegerField();
            intField.value = prop.intValue;
            intField.style.height = 22;
            intField.RegisterValueChangedCallback(evt =>
            {
                prop.intValue = evt.newValue;
                serializedConfig.ApplyModifiedProperties();
            });
            field.Add(intField);
            
            parent.Add(field);
        }

        private void AddSliderField(VisualElement parent, string label, string propertyName, float min, float max, string tooltip)
        {
            if (serializedConfig == null) return;
            
            var prop = serializedConfig.FindProperty(propertyName);
            if (prop == null) return;
            
            var field = new VisualElement();
            field.style.marginBottom = 10;
            
            var labelElement = new Label($"{label}: {prop.floatValue:F2}");
            labelElement.style.marginBottom = 3;
            labelElement.tooltip = tooltip;
            field.Add(labelElement);
            
            var slider = new Slider(min, max);
            slider.value = prop.floatValue;
            slider.style.height = 22;
            slider.RegisterValueChangedCallback(evt =>
            {
                prop.floatValue = evt.newValue;
                labelElement.text = $"{label}: {evt.newValue:F2}";
                serializedConfig.ApplyModifiedProperties();
            });
            field.Add(slider);
            
            parent.Add(field);
        }

        private void AddToggleField(VisualElement parent, string label, string propertyName, string tooltip)
        {
            if (serializedConfig == null) return;
            
            var prop = serializedConfig.FindProperty(propertyName);
            if (prop == null) return;
            
            var toggle = new Toggle(label);
            toggle.value = prop.boolValue;
            toggle.tooltip = tooltip;
            toggle.style.marginBottom = 10;
            toggle.RegisterValueChangedCallback(evt =>
            {
                prop.boolValue = evt.newValue;
                serializedConfig.ApplyModifiedProperties();
            });
            
            parent.Add(toggle);
        }

        private void AddTextAreaField(VisualElement parent, string label, string propertyName, int lines, string tooltip)
        {
            if (serializedConfig == null) return;
            
            var prop = serializedConfig.FindProperty(propertyName);
            if (prop == null) return;
            
            var field = new VisualElement();
            field.style.marginBottom = 15;
            
            var labelElement = new Label(label);
            labelElement.style.marginBottom = 3;
            labelElement.tooltip = tooltip;
            labelElement.style.unityFontStyleAndWeight = FontStyle.Bold;
            field.Add(labelElement);
            
            var textField = new TextField();
            textField.multiline = true;
            textField.value = prop.stringValue;
            textField.style.minHeight = lines * 20;
            textField.style.whiteSpace = WhiteSpace.Normal;
            textField.RegisterValueChangedCallback(evt =>
            {
                prop.stringValue = evt.newValue;
                serializedConfig.ApplyModifiedProperties();
            });
            field.Add(textField);
            
            parent.Add(field);
        }

        private void AddLinkButton(VisualElement parent, string text, Action onClick)
        {
            var btn = new Button(onClick);
            btn.text = text;
            btn.style.height = 25;
            btn.style.marginRight = 10;
            btn.style.backgroundColor = new Color(0.25f, 0.4f, 0.6f);
            parent.Add(btn);
        }

        private VisualElement CreateSubSection(string title)
        {
            var section = new VisualElement();
            section.style.marginTop = 15;
            section.style.marginBottom = 10;
            section.style.paddingTop = 10;
            section.style.paddingBottom = 10;
            section.style.paddingLeft = 10;
            section.style.paddingRight = 10;
            section.style.backgroundColor = new Color(0.15f, 0.15f, 0.15f);
            section.style.borderTopLeftRadius = 6;
            section.style.borderTopRightRadius = 6;
            section.style.borderBottomLeftRadius = 6;
            section.style.borderBottomRightRadius = 6;

            var titleLabel = new Label(title);
            titleLabel.style.fontSize = 12;
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            titleLabel.style.color = new Color(0.9f, 0.7f, 0.3f);
            titleLabel.style.marginBottom = 10;
            section.Add(titleLabel);

            return section;
        }

        private void AddNestedConfigField(VisualElement parent, string label, string propertyPath, string tooltip)
        {
            if (serializedConfig == null) return;

            var prop = serializedConfig.FindProperty(propertyPath);
            if (prop == null)
            {
                var errorLabel = new Label($"[!] 属性未找到: {propertyPath}");
                errorLabel.style.color = Color.red;
                errorLabel.style.fontSize = 10;
                parent.Add(errorLabel);
                return;
            }

            var field = new VisualElement();
            field.style.marginBottom = 8;

            var labelElement = new Label(label);
            labelElement.style.marginBottom = 3;
            labelElement.style.fontSize = 11;
            labelElement.tooltip = tooltip;
            field.Add(labelElement);

            var textField = new TextField();
            textField.value = prop.stringValue;
            textField.style.height = 22;
            textField.RegisterValueChangedCallback(evt =>
            {
                prop.stringValue = evt.newValue;
                serializedConfig.ApplyModifiedProperties();
            });
            field.Add(textField);

            parent.Add(field);
        }

        #endregion

        #region Footer

        private void CreateFooter(VisualElement parent)
        {
            var footer = new VisualElement();
            footer.style.flexDirection = FlexDirection.Row;
            footer.style.justifyContent = Justify.SpaceBetween;
            footer.style.marginTop = 10;
            footer.style.paddingTop = 10;
            footer.style.borderTopWidth = 1;
            footer.style.borderTopColor = new Color(0.3f, 0.3f, 0.3f);
            
            // Left buttons
            var leftButtons = new VisualElement();
            leftButtons.style.flexDirection = FlexDirection.Row;
            
            var resetBtn = new Button(() => ResetToDefaults());
            resetBtn.text = "重置为默认值";
            resetBtn.style.height = 30;
            leftButtons.Add(resetBtn);
            
            var openAssetBtn = new Button(() => 
            {
                Selection.activeObject = config;
                EditorGUIUtility.PingObject(config);
            });
            openAssetBtn.text = "定位配置文件";
            openAssetBtn.style.height = 30;
            openAssetBtn.style.marginLeft = 10;
            leftButtons.Add(openAssetBtn);
            
            footer.Add(leftButtons);
            
            // Right buttons
            var rightButtons = new VisualElement();
            rightButtons.style.flexDirection = FlexDirection.Row;
            
            var saveBtn = new Button(() => SaveConfig());
            saveBtn.text = "保存配置";
            saveBtn.style.height = 30;
            saveBtn.style.backgroundColor = new Color(0.2f, 0.5f, 0.3f);
            rightButtons.Add(saveBtn);
            
            footer.Add(rightButtons);
            parent.Add(footer);
        }

        #endregion

        #region Actions

        private void RefreshPromptPreview()
        {
            if (config == null || promptPreviewField == null) return;
            
            // Generate a sample prompt
            string sampleCode = @"public class MoveAction : ActionBase
{
    public float moveSpeed = 5f;
    public Vector3 direction;
    
    public override void Execute()
    {
        // Move character in direction
        transform.position += direction * moveSpeed * Time.deltaTime;
    }
}";
            
            string prompt = config.BuildPrompt("MoveAction", sampleCode, "移动", "Movement");
            promptPreviewField.value = prompt;
        }

        private async void TestApiConnection()
        {
            if (string.IsNullOrEmpty(RAGConfig.DeepSeekApiKey))
            {
                EditorUtility.DisplayDialog("错误", "请先配置 DeepSeek API Key", "确定");
                return;
            }
            
            EditorUtility.DisplayProgressBar("测试连接", "正在连接 DeepSeek API...", 0.5f);
            
            try
            {
                var client = new DeepSeekClient(RAGConfig.DeepSeekApiKey);
                var result = await client.GenerateActionDescriptionAsync(
                    "TestAction", 
                    "public class TestAction : ActionBase { public override void Execute() { } }");
                
                EditorUtility.ClearProgressBar();
                
                if (result.success)
                {
                    EditorUtility.DisplayDialog("成功", 
                        $"API 连接正常！\n\n生成结果:\n显示名称: {result.displayName}\n分类: {result.category}", 
                        "确定");
                }
                else
                {
                    EditorUtility.DisplayDialog("失败", $"API 调用失败:\n{result.error}", "确定");
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                EditorUtility.DisplayDialog("错误", $"连接失败:\n{e.Message}", "确定");
            }
        }

        private void ResetToDefaults()
        {
            if (EditorUtility.DisplayDialog("确认", "确定要重置所有配置为默认值吗？", "确定", "取消"))
            {
                config.ResetToDefaults();
                serializedConfig.Update();
                SwitchTab(currentTab); // Refresh current tab
                Debug.Log("[RAGConfig] 配置已重置为默认值");
            }
        }

        private void SaveConfig()
        {
            if (config != null)
            {
                config.Save();
                Debug.Log("[RAGConfig] 配置已保存");
                ShowNotification(new GUIContent("配置已保存"));
            }
        }

        private void ExportSkillSystemConfig()
        {
            if (config == null) return;

            try
            {
                config.ExportSkillSystemConfig();
                ShowNotification(new GUIContent("配置已导出到 Python 端"));
            }
            catch (Exception e)
            {
                EditorUtility.DisplayDialog("导出失败", $"导出配置时出错:\n{e.Message}", "确定");
            }
        }

        private void ValidateSkillSystemConfig()
        {
            if (config == null) return;

            var typeConfig = config.skillSystemConfig;
            var errors = new System.Collections.Generic.List<string>();

            // 验证基类类型
            var baseType = typeConfig.GetBaseActionType();
            if (baseType == null)
            {
                errors.Add($"无法找到基类类型: {typeConfig.baseActionTypeName}");
            }

            // 验证技能数据类型
            var skillDataType = typeConfig.GetSkillDataType();
            if (skillDataType == null)
            {
                errors.Add($"无法找到技能数据类型: {typeConfig.skillDataTypeName}");
            }

            // 验证技能轨道类型
            var skillTrackType = typeConfig.GetSkillTrackType();
            if (skillTrackType == null)
            {
                errors.Add($"无法找到技能轨道类型: {typeConfig.skillTrackTypeName}");
            }

            if (errors.Count > 0)
            {
                EditorUtility.DisplayDialog("验证失败",
                    "以下类型配置有误:\n\n" + string.Join("\n", errors), "确定");
            }
            else
            {
                EditorUtility.DisplayDialog("验证通过",
                    $"所有类型配置正确！\n\n" +
                    $"基类类型: {baseType.FullName}\n" +
                    $"技能数据类型: {skillDataType.FullName}\n" +
                    $"技能轨道类型: {skillTrackType.FullName}", "确定");
            }
        }

        private void ClearTypeCache()
        {
            if (config == null) return;

            config.skillSystemConfig.ClearCache();
            ShowNotification(new GUIContent("类型缓存已清除"));
            Debug.Log("[RAGConfig] 技能系统类型缓存已清除");
        }

        /// <summary>
        /// 导出Buff系统配置
        /// </summary>
        private void ExportBuffSystemConfig()
        {
            if (config == null) return;

            try
            {
                // 导出Buff系统配置到JSON
                string outputPath = Path.GetFullPath(Path.Combine(
                    config.buffSystemConfig.exportDirectory,
                    "../buff_system_config.json"));

                // 确保目录存在
                string directory = Path.GetDirectoryName(outputPath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // 使用StringBuilder构建JSON
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("{");
                sb.AppendLine($"  \"project\": {{");
                sb.AppendLine($"    \"name\": \"{Application.productName}\",");
                sb.AppendLine($"    \"assembly\": \"{config.buffSystemConfig.assemblyName}\",");
                sb.AppendLine($"    \"export_time\": \"{DateTime.Now:o}\"");
                sb.AppendLine($"  }},");
                sb.AppendLine($"  \"types\": {{");
                sb.AppendLine($"    \"buff_template\": \"{config.buffSystemConfig.buffTemplateTypeName}\",");
                sb.AppendLine($"    \"buff_effect\": \"{config.buffSystemConfig.buffEffectTypeName}\",");
                sb.AppendLine($"    \"buff_trigger\": \"{config.buffSystemConfig.buffTriggerTypeName}\",");
                sb.AppendLine($"    \"buff_template_full\": \"{config.buffSystemConfig.GetOdinTypeString(config.buffSystemConfig.buffTemplateTypeName)}\",");
                sb.AppendLine($"    \"buff_effect_full\": \"{config.buffSystemConfig.GetOdinTypeString(config.buffSystemConfig.buffEffectTypeName)}\",");
                sb.AppendLine($"    \"buff_trigger_full\": \"{config.buffSystemConfig.GetOdinTypeString(config.buffSystemConfig.buffTriggerTypeName)}\"");
                sb.AppendLine($"  }},");
                sb.AppendLine($"  \"export_directory\": \"{config.buffSystemConfig.exportDirectory.Replace("\\", "\\\\")}\"");
                sb.AppendLine("}");

                File.WriteAllText(outputPath, sb.ToString());

                EditorUtility.DisplayDialog("导出成功", $"Buff系统配置已导出到:\n{outputPath}", "确定");
                Debug.Log($"[RAGConfig] Buff系统配置已导出到: {outputPath}");
            }
            catch (Exception e)
            {
                EditorUtility.DisplayDialog("导出失败", e.Message, "确定");
                Debug.LogError($"[RAGConfig] 导出Buff系统配置失败: {e}");
            }
        }

        /// <summary>
        /// 验证Buff系统类型配置
        /// </summary>
        private void ValidateBuffSystemConfig()
        {
            if (config == null) return;

            var errors = new List<string>();

            var templateType = config.buffSystemConfig.GetBuffTemplateType();
            if (templateType == null)
            {
                errors.Add($"无法找到Buff模板类型: {config.buffSystemConfig.buffTemplateTypeName}");
            }

            var effectType = config.buffSystemConfig.GetBuffEffectType();
            if (effectType == null)
            {
                errors.Add($"无法找到Buff效果接口: {config.buffSystemConfig.buffEffectTypeName}");
            }

            var triggerType = config.buffSystemConfig.GetBuffTriggerType();
            if (triggerType == null)
            {
                errors.Add($"无法找到Buff触发器接口: {config.buffSystemConfig.buffTriggerTypeName}");
            }

            if (errors.Count > 0)
            {
                EditorUtility.DisplayDialog("验证失败", string.Join("\n", errors), "确定");
            }
            else
            {
                EditorUtility.DisplayDialog("验证成功",
                    $"所有类型配置有效:\n" +
                    $"- Buff模板: {templateType.FullName}\n" +
                    $"- Buff效果: {effectType.FullName}\n" +
                    $"- Buff触发器: {triggerType.FullName}",
                    "确定");
            }
        }

        /// <summary>
        /// 清除Buff类型缓存
        /// </summary>
        private void ClearBuffTypeCache()
        {
            if (config == null) return;

            config.buffSystemConfig.ClearCache();
            EditorUtility.DisplayDialog("完成", "Buff类型缓存已清除", "确定");
        }

        #endregion
    }
}
