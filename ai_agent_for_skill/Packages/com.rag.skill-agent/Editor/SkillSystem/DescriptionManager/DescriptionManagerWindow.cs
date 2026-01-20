using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor.UIElements;
using Cysharp.Threading.Tasks;

namespace RAG
{
    /// <summary>
    /// Action JSON export tool - UIElement based implementation
    /// Export Action data to JSON for skill_agent to use
    /// Supports AI-powered description generation using DeepSeek
    /// Optimized for handling large datasets using virtualized ListView
    /// </summary>
    public class DescriptionManagerWindow : EditorWindow
    {
        // Configuration from RAGConfig
        private RAGConfig Config => RAGConfig.Instance;

        // Action data
        private List<ActionEntry> actionEntries = new List<ActionEntry>();
        private List<ActionEntry> filteredEntries = new List<ActionEntry>();

        // Managers and utilities
        private ActionDatabaseManager databaseManager;
        private AIDescriptionGenerator aiGenerator;
        private ActionJSONExporter jsonExporter;
        private SkillAgentServerClient serverClient;

        // UI Elements (bound from UXML)
        private ListView actionListView;
        private Label totalActionsLabel;
        private Label withDescriptionLabel;
        private Label selectedCountLabel;
        private Label withParamDescLabel;
        private TextField operationLogsField;
        private ProgressBar progressBar;
        private TextField searchField;
        private DropdownField categoryFilter;
        private DropdownField descriptionFilter;
        private Label exportDirLabel;
        private TextField apiKeyField;
        
        // Templates
        private VisualTreeAsset actionItemTemplate;
        
        // Expanded items tracking
        private HashSet<string> expandedItems = new HashSet<string>();

        // Filter options
        private List<string> allCategories = new List<string> { "全部" };

        // Root element - can be set externally for embedding
        private VisualElement _root;
        private VisualElement Root => _root ?? rootVisualElement;

        /// <summary>
        /// Initialize panel content into an external container (for embedding in unified window)
        /// </summary>
        public void InitializeIntoContainer(VisualElement container)
        {
            _root = container;
            InitializeManagers();
            databaseManager.LoadDatabase();
            ScanActions();
            if (!LoadUIContent())
            {
                container.Add(new Label("无法加载 Action 面板 UI") { style = { color = Color.red } });
                return;
            }
            BindUIElements();
            SetupEventHandlers();
            SetupListView();
            UpdateStatistics();
            UpdateCategoryFilter();
            Log("准备就绪，等待操作...");
        }

        // MenuItem removed - use UnifiedRAGExportWindow instead
        // [MenuItem("技能系统/Action导出工具", priority = 100)]
        public static void ShowWindow()
        {
            var window = GetWindow<DescriptionManagerWindow>("Action导出工具");
            window.minSize = new Vector2(1000, 750);
            window.Show();
        }

        private void CreateGUI()
        {
            _root = rootVisualElement;
            InitializeManagers();
            databaseManager.LoadDatabase();
            ScanActions();
            if (!LoadUIContent())
            {
                CreateFallbackUI();
                return;
            }
            BindUIElements();
            SetupEventHandlers();
            SetupListView();
            UpdateStatistics();
            UpdateCategoryFilter();
            Log("准备就绪，等待操作...");
        }

        private bool LoadUIContent()
        {
            string uxmlPath = "Packages/com.rag.skill-agent/Editor/SkillSystem/DescriptionManager/DescriptionManagerWindow.uxml";
            var visualTree = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(uxmlPath);

            if (visualTree == null)
            {
                Debug.LogError($"[DescriptionManager] Failed to load UXML from: {uxmlPath}");
                return false;
            }

            visualTree.CloneTree(Root);

            string ussPath = "Packages/com.rag.skill-agent/Editor/SkillSystem/DescriptionManager/DescriptionManagerWindow.uss";
            var styleSheet = AssetDatabase.LoadAssetAtPath<StyleSheet>(ussPath);
            if (styleSheet != null)
            {
                Root.styleSheets.Add(styleSheet);
            }

            string templatePath = "Packages/com.rag.skill-agent/Editor/SkillSystem/DescriptionManager/ActionItemTemplate.uxml";
            actionItemTemplate = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(templatePath);

            Root.style.paddingTop = 4;
            Root.style.paddingBottom = 4;
            Root.style.paddingLeft = 6;
            Root.style.paddingRight = 6;
            Root.style.flexGrow = 1;

            return true;
        }

        private void CreateFallbackUI()
        {
            var errorLabel = new Label("无法加载UI文件，请确保以下文件存在：\n" +
                "- DescriptionManagerWindow.uxml\n" +
                "- DescriptionManagerWindow.uss\n" +
                "- ActionItemTemplate.uxml\n\n" +
                "路径：Packages/com.rag.skill-agent/Editor/SkillSystem/DescriptionManager/");
            errorLabel.style.color = Color.red;
            errorLabel.style.whiteSpace = WhiteSpace.Normal;
            errorLabel.style.marginTop = 20;
            errorLabel.style.marginLeft = 20;
            Root.Add(errorLabel);

            var refreshBtn = new Button(() => {
                Root.Clear();
                CreateGUI();
            }) { text = "重新加载" };
            refreshBtn.style.width = 100;
            refreshBtn.style.marginTop = 10;
            refreshBtn.style.marginLeft = 20;
            Root.Add(refreshBtn);
        }

        private void InitializeManagers()
        {
            databaseManager = new ActionDatabaseManager(Config.actionDatabasePath, Log);
            aiGenerator = new AIDescriptionGenerator(Config, Log, UpdateProgress);
            jsonExporter = new ActionJSONExporter(Config.exportDirectory, Log);
            serverClient = new SkillAgentServerClient(Config.serverHost, Config.serverPort, Log);
        }

        #region UI Binding

        private void BindUIElements()
        {
            // Statistics labels
            totalActionsLabel = Root.Q<Label>("totalActionsLabel");
            withDescriptionLabel = Root.Q<Label>("withDescriptionLabel");
            withParamDescLabel = Root.Q<Label>("withParamDescLabel");
            selectedCountLabel = Root.Q<Label>("selectedCountLabel");

            // Progress bar
            progressBar = Root.Q<ProgressBar>("progressBar");

            // Search and filters
            searchField = Root.Q<TextField>("searchField");
            categoryFilter = Root.Q<DropdownField>("categoryFilter");
            descriptionFilter = Root.Q<DropdownField>("descriptionFilter");

            // Setup description filter choices
            if (descriptionFilter != null)
            {
                descriptionFilter.choices = new List<string> { "全部", "有描述", "无描述", "有参数描述", "无参数描述" };
                descriptionFilter.value = "全部";
            }

            // Logs field
            operationLogsField = Root.Q<TextField>("operationLogsField");

            // Export directory label
            exportDirLabel = Root.Q<Label>("exportDirLabel");
            if (exportDirLabel != null)
            {
                exportDirLabel.text = $"目录: {Config.exportDirectory}";
            }

            // API Key field
            apiKeyField = Root.Q<TextField>("apiKeyField");
            if (apiKeyField != null)
            {
                apiKeyField.value = RAGConfig.DeepSeekApiKey;
            }

            // List view
            actionListView = Root.Q<ListView>("actionListView");
        }

        private void SetupEventHandlers()
        {
            // Config button
            var openConfigBtn = Root.Q<Button>("openConfigBtn");
            openConfigBtn?.RegisterCallback<ClickEvent>(evt => RAGConfig.SelectConfig());

            // API Key field
            apiKeyField?.RegisterValueChangedCallback(evt =>
            {
                RAGConfig.DeepSeekApiKey = evt.newValue;
                aiGenerator.ResetClient();
            });

            // AI buttons
            var generateSelectedBtn = Root.Q<Button>("generateSelectedBtn");
            generateSelectedBtn?.RegisterCallback<ClickEvent>(evt => GenerateDescriptionsForSelectedAsync().Forget());

            var generateMissingBtn = Root.Q<Button>("generateMissingBtn");
            generateMissingBtn?.RegisterCallback<ClickEvent>(evt => GenerateDescriptionsForMissingAsync().Forget());

            var saveDbBtn = Root.Q<Button>("saveDbBtn");
            saveDbBtn?.RegisterCallback<ClickEvent>(evt => SaveAllToDatabase());

            var selectAllBtn = Root.Q<Button>("selectAllBtn");
            selectAllBtn?.RegisterCallback<ClickEvent>(evt => SelectAll());

            var deselectAllBtn = Root.Q<Button>("deselectAllBtn");
            deselectAllBtn?.RegisterCallback<ClickEvent>(evt => DeselectAll());

            // Export buttons
            var exportJsonBtn = Root.Q<Button>("exportJsonBtn");
            exportJsonBtn?.RegisterCallback<ClickEvent>(evt => ExportActionsToJSON());

            var openFolderBtn = Root.Q<Button>("openFolderBtn");
            openFolderBtn?.RegisterCallback<ClickEvent>(evt => OpenExportFolder());

            // Server buttons
            var rebuildIndexBtn = Root.Q<Button>("rebuildIndexBtn");
            rebuildIndexBtn?.RegisterCallback<ClickEvent>(evt => serverClient.NotifyRebuildIndexAsync().Forget());

            var checkStatusBtn = Root.Q<Button>("checkStatusBtn");
            checkStatusBtn?.RegisterCallback<ClickEvent>(evt => serverClient.CheckServerStatusAsync().Forget());

            // Quick action buttons
            var oneClickExportBtn = Root.Q<Button>("oneClickExportBtn");
            oneClickExportBtn?.RegisterCallback<ClickEvent>(evt => OneClickExportAndNotifyAsync().Forget());

            var refreshBtn = Root.Q<Button>("refreshBtn");
            refreshBtn?.RegisterCallback<ClickEvent>(evt => RefreshActions());

            var clearLogsBtn = Root.Q<Button>("clearLogsBtn");
            clearLogsBtn?.RegisterCallback<ClickEvent>(evt => ClearLogs());

            var expandAllBtn = Root.Q<Button>("expandAllBtn");
            expandAllBtn?.RegisterCallback<ClickEvent>(evt => ExpandAllParameters());

            var collapseAllBtn = Root.Q<Button>("collapseAllBtn");
            collapseAllBtn?.RegisterCallback<ClickEvent>(evt => CollapseAllParameters());

            // Search and filter
            searchField?.RegisterValueChangedCallback(evt => ApplyFilters());

            var clearSearchBtn = Root.Q<Button>("clearSearchBtn");
            clearSearchBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                if (searchField != null) searchField.value = "";
                ApplyFilters();
            });

            categoryFilter?.RegisterValueChangedCallback(evt => ApplyFilters());
            descriptionFilter?.RegisterValueChangedCallback(evt => ApplyFilters());
        }

        private void SetupListView()
        {
            if (actionListView == null) return;
            
            filteredEntries = new List<ActionEntry>(actionEntries);
            actionListView.itemsSource = filteredEntries;
            actionListView.makeItem = MakeActionItem;
            actionListView.bindItem = BindActionItem;
            actionListView.selectionType = SelectionType.None;
            actionListView.virtualizationMethod = CollectionVirtualizationMethod.DynamicHeight;
        }

        #endregion

        #region ListView Item Creation and Binding

        private VisualElement MakeActionItem()
        {
            // Try to use template if available
            if (actionItemTemplate != null)
            {
                var item = actionItemTemplate.CloneTree();
                return item;
            }
            
            // Fallback: create programmatically
            return CreateActionItemProgrammatically();
        }

        private VisualElement CreateActionItemProgrammatically()
        {
            var container = new VisualElement();
            container.AddToClassList("action-item");

            // Main row
            var mainRow = new VisualElement();
            mainRow.AddToClassList("action-item-row");
            mainRow.name = "mainRow";

            // Selection toggle
            var toggle = new Toggle();
            toggle.AddToClassList("select-toggle");
            toggle.name = "selectToggle";
            mainRow.Add(toggle);

            // Expand button
            var expandBtn = new Button();
            expandBtn.text = "▶";
            expandBtn.AddToClassList("expand-button");
            expandBtn.name = "expandBtn";
            mainRow.Add(expandBtn);

            // Type name
            var typeLabel = new Label();
            typeLabel.AddToClassList("type-label");
            typeLabel.name = "typeLabel";
            mainRow.Add(typeLabel);

            // Display name (editable)
            var displayNameField = new TextField();
            displayNameField.AddToClassList("displayname-field");
            displayNameField.name = "displayNameField";
            mainRow.Add(displayNameField);

            // Category (editable)
            var categoryField = new TextField();
            categoryField.AddToClassList("category-field");
            categoryField.name = "categoryField";
            mainRow.Add(categoryField);

            // Parameter count
            var paramCountLabel = new Label();
            paramCountLabel.AddToClassList("param-count-label");
            paramCountLabel.name = "paramCountLabel";
            mainRow.Add(paramCountLabel);

            // Description (editable)
            var descriptionField = new TextField();
            descriptionField.AddToClassList("description-field");
            descriptionField.multiline = true;
            descriptionField.name = "descriptionField";
            mainRow.Add(descriptionField);

            // AI generated indicator
            var aiLabel = new Label();
            aiLabel.AddToClassList("ai-label");
            aiLabel.name = "aiLabel";
            mainRow.Add(aiLabel);

            container.Add(mainRow);

            // Parameter details panel (hidden by default)
            var paramPanel = new VisualElement();
            paramPanel.name = "paramPanel";
            paramPanel.AddToClassList("param-panel");
            paramPanel.style.display = DisplayStyle.None;
            container.Add(paramPanel);

            return container;
        }

        private void BindActionItem(VisualElement element, int index)
        {
            if (index < 0 || index >= filteredEntries.Count) return;

            var entry = filteredEntries[index];

            var toggle = element.Q<Toggle>("selectToggle");
            var expandBtn = element.Q<Button>("expandBtn");
            var typeLabel = element.Q<Label>("typeLabel");
            var displayNameField = element.Q<TextField>("displayNameField");
            var categoryField = element.Q<TextField>("categoryField");
            var paramCountLabel = element.Q<Label>("paramCountLabel");
            var descriptionField = element.Q<TextField>("descriptionField");
            var aiLabel = element.Q<Label>("aiLabel");
            var paramPanel = element.Q("paramPanel");

            // Unregister previous callbacks to prevent accumulation
            toggle?.UnregisterValueChangedCallback(toggle.userData as EventCallback<ChangeEvent<bool>>);
            displayNameField?.UnregisterValueChangedCallback(displayNameField.userData as EventCallback<ChangeEvent<string>>);
            categoryField?.UnregisterValueChangedCallback(categoryField.userData as EventCallback<ChangeEvent<string>>);
            descriptionField?.UnregisterValueChangedCallback(descriptionField.userData as EventCallback<ChangeEvent<string>>);

            // Bind data with new callbacks
            if (toggle != null)
            {
                EventCallback<ChangeEvent<bool>> toggleCallback = evt =>
                {
                    entry.isSelected = evt.newValue;
                    UpdateStatistics();
                };
                toggle.userData = toggleCallback;
                toggle.SetValueWithoutNotify(entry.isSelected);
                toggle.RegisterValueChangedCallback(toggleCallback);
            }

            // Expand button
            if (expandBtn != null)
            {
                bool isExpanded = expandedItems.Contains(entry.typeName);
                expandBtn.text = isExpanded ? "▼" : "▶";
                expandBtn.clickable = new Clickable(() =>
                {
                    int currentIndex = filteredEntries.IndexOf(entry);
                    
                    if (expandedItems.Contains(entry.typeName))
                    {
                        expandedItems.Remove(entry.typeName);
                        expandBtn.text = "▶";
                        if (paramPanel != null) paramPanel.style.display = DisplayStyle.None;
                    }
                    else
                    {
                        expandedItems.Add(entry.typeName);
                        expandBtn.text = "▼";
                        if (paramPanel != null)
                        {
                            paramPanel.style.display = DisplayStyle.Flex;
                            BuildParameterPanel(paramPanel, entry);
                        }
                    }
                    
                    if (currentIndex >= 0)
                    {
                        actionListView.RefreshItem(currentIndex);
                    }
                });
            }

            if (typeLabel != null)
            {
                typeLabel.text = entry.typeName;
                typeLabel.tooltip = entry.fullTypeName;
            }

            if (displayNameField != null)
            {
                EventCallback<ChangeEvent<string>> displayNameCallback = evt => entry.displayName = evt.newValue;
                displayNameField.userData = displayNameCallback;
                displayNameField.SetValueWithoutNotify(entry.displayName ?? "");
                displayNameField.RegisterValueChangedCallback(displayNameCallback);
            }

            if (categoryField != null)
            {
                EventCallback<ChangeEvent<string>> categoryCallback = evt => entry.category = evt.newValue;
                categoryField.userData = categoryCallback;
                categoryField.SetValueWithoutNotify(entry.category ?? "");
                categoryField.RegisterValueChangedCallback(categoryCallback);
            }

            // Parameter count with color coding
            if (paramCountLabel != null)
            {
                int paramCount = entry.parameters?.Count ?? 0;
                int paramWithDesc = entry.parameters?.Count(p => !string.IsNullOrEmpty(p.description)) ?? 0;
                paramCountLabel.text = $"{paramWithDesc}/{paramCount}";
                
                paramCountLabel.RemoveFromClassList("param-count-none");
                paramCountLabel.RemoveFromClassList("param-count-full");
                paramCountLabel.RemoveFromClassList("param-count-partial");
                paramCountLabel.RemoveFromClassList("param-count-empty");
                
                if (paramCount == 0)
                    paramCountLabel.AddToClassList("param-count-none");
                else if (paramWithDesc == paramCount)
                    paramCountLabel.AddToClassList("param-count-full");
                else if (paramWithDesc > 0)
                    paramCountLabel.AddToClassList("param-count-partial");
                else
                    paramCountLabel.AddToClassList("param-count-empty");
                    
                paramCountLabel.tooltip = $"有描述的参数: {paramWithDesc} / 总参数: {paramCount}";
            }

            if (descriptionField != null)
            {
                EventCallback<ChangeEvent<string>> descriptionCallback = evt => entry.description = evt.newValue;
                descriptionField.userData = descriptionCallback;
                descriptionField.SetValueWithoutNotify(entry.description ?? "");
                descriptionField.RegisterValueChangedCallback(descriptionCallback);
            }

            if (aiLabel != null)
            {
                aiLabel.text = entry.isAIGenerated ? "Y" : "";
                aiLabel.tooltip = entry.isAIGenerated ? $"AI生成于: {entry.aiGeneratedTime}" : "";
                
                aiLabel.RemoveFromClassList("ai-label-yes");
                aiLabel.RemoveFromClassList("ai-label-no");
                aiLabel.AddToClassList(entry.isAIGenerated ? "ai-label-yes" : "ai-label-no");
            }

            // Alternate row colors
            element.RemoveFromClassList("action-item-even");
            element.RemoveFromClassList("action-item-odd");
            element.AddToClassList(index % 2 == 0 ? "action-item-even" : "action-item-odd");

            // Handle expanded state
            if (paramPanel != null)
            {
                bool isExpanded = expandedItems.Contains(entry.typeName);
                if (isExpanded)
                {
                    paramPanel.style.display = DisplayStyle.Flex;
                    BuildParameterPanel(paramPanel, entry);
                }
                else
                {
                    paramPanel.style.display = DisplayStyle.None;
                }
            }
        }

        private void BuildParameterPanel(VisualElement paramPanel, ActionEntry entry)
        {
            paramPanel.Clear();

            if (entry.parameters == null || entry.parameters.Count == 0)
            {
                var noParamLabel = new Label("无参数");
                noParamLabel.AddToClassList("no-param-label");
                paramPanel.Add(noParamLabel);
                return;
            }

            // Parameter header
            var headerRow = new VisualElement();
            headerRow.AddToClassList("param-header-row");

            headerRow.Add(CreateParamHeaderLabel("参数名", "param-header-name"));
            headerRow.Add(CreateParamHeaderLabel("类型", "param-header-type"));
            headerRow.Add(CreateParamHeaderLabel("默认值", "param-header-default"));
            headerRow.Add(CreateParamHeaderLabel("标签", "param-header-label-col"));
            headerRow.Add(CreateParamHeaderLabel("描述", "param-header-desc"));
            paramPanel.Add(headerRow);

            // Parameter rows
            foreach (var param in entry.parameters)
            {
                var paramRow = new VisualElement();
                paramRow.AddToClassList("param-row");

                // Parameter name
                var nameLabel = new Label(param.name);
                nameLabel.AddToClassList("param-name");
                nameLabel.tooltip = param.name;
                paramRow.Add(nameLabel);

                // Type
                var typeLabel = new Label(param.type);
                typeLabel.AddToClassList("param-type");
                typeLabel.tooltip = GetTypeTooltip(param);
                paramRow.Add(typeLabel);

                // Default value
                var defaultLabel = new Label(param.defaultValue ?? "-");
                defaultLabel.AddToClassList("param-default");
                defaultLabel.tooltip = param.defaultValue;
                paramRow.Add(defaultLabel);

                // Label (from Odin attribute)
                var labelLabel = new Label(param.label ?? "-");
                labelLabel.AddToClassList("param-label-value");
                labelLabel.tooltip = param.label;
                paramRow.Add(labelLabel);

                // Description (editable)
                var descField = new TextField();
                descField.AddToClassList("param-desc-field");
                if (!string.IsNullOrEmpty(param.description))
                {
                    descField.AddToClassList("param-desc-field-filled");
                }
                descField.SetValueWithoutNotify(param.description ?? "");
                descField.RegisterValueChangedCallback(evt =>
                {
                    param.description = evt.newValue;
                    entry.parameterDescriptions[param.name] = evt.newValue;
                });
                paramRow.Add(descField);

                paramPanel.Add(paramRow);

                // Show additional info if available
                if (!string.IsNullOrEmpty(param.infoBox) || param.isEnum || HasConstraints(param))
                {
                    var infoRow = new VisualElement();
                    infoRow.AddToClassList("param-info-row");

                    var infoText = new List<string>();
                    
                    if (!string.IsNullOrEmpty(param.infoBox))
                        infoText.Add($"[Info] {param.infoBox}");
                    
                    if (param.isEnum && param.enumValues != null && param.enumValues.Count > 0)
                        infoText.Add($"[Enum] {string.Join(", ", param.enumValues)}");
                    
                    if (HasConstraints(param))
                        infoText.Add($"[Range] {GetConstraintText(param)}");

                    if (infoText.Count > 0)
                    {
                        var infoLabel = new Label(string.Join(" | ", infoText));
                        infoLabel.AddToClassList("param-info-label");
                        infoRow.Add(infoLabel);
                        paramPanel.Add(infoRow);
                    }
                }
            }
        }

        private Label CreateParamHeaderLabel(string text, string className)
        {
            var label = new Label(text);
            label.AddToClassList("param-header-label");
            label.AddToClassList(className);
            return label;
        }

        private string GetTypeTooltip(ActionParameterInfo param)
        {
            var parts = new List<string> { $"类型: {param.type}" };
            if (param.isArray) parts.Add("数组类型");
            if (param.isEnum) parts.Add("枚举类型");
            if (!string.IsNullOrEmpty(param.elementType)) parts.Add($"元素类型: {param.elementType}");
            return string.Join("\n", parts);
        }

        private bool HasConstraints(ActionParameterInfo param)
        {
            if (param.constraints == null) return false;
            return !string.IsNullOrEmpty(param.constraints.min) ||
                   !string.IsNullOrEmpty(param.constraints.max) ||
                   !string.IsNullOrEmpty(param.constraints.minValue) ||
                   !string.IsNullOrEmpty(param.constraints.maxValue);
        }

        private string GetConstraintText(ActionParameterInfo param)
        {
            var parts = new List<string>();
            if (!string.IsNullOrEmpty(param.constraints.min))
                parts.Add($"Min: {param.constraints.min}");
            if (!string.IsNullOrEmpty(param.constraints.max))
                parts.Add($"Max: {param.constraints.max}");
            if (!string.IsNullOrEmpty(param.constraints.minValue))
                parts.Add($"MinValue: {param.constraints.minValue}");
            if (!string.IsNullOrEmpty(param.constraints.maxValue))
                parts.Add($"MaxValue: {param.constraints.maxValue}");
            return string.Join(", ", parts);
        }

        #endregion

        #region UI Actions

        private void SelectAll()
        {
            foreach (var entry in filteredEntries)
                entry.isSelected = true;
            actionListView?.Rebuild();
            UpdateStatistics();
        }

        private void DeselectAll()
        {
            foreach (var entry in filteredEntries)
                entry.isSelected = false;
            actionListView?.Rebuild();
            UpdateStatistics();
        }

        private void ExpandAllParameters()
        {
            foreach (var entry in filteredEntries)
            {
                if (entry.parameters != null && entry.parameters.Count > 0)
                {
                    expandedItems.Add(entry.typeName);
                }
            }
            actionListView?.Rebuild();
            Log("[展开] 已展开所有参数面板");
        }

        private void CollapseAllParameters()
        {
            expandedItems.Clear();
            actionListView?.Rebuild();
            Log("[收起] 已收起所有参数面板");
        }

        private void RefreshActions()
        {
            ScanActions();
            ApplyFilters();
            UpdateStatistics();
            UpdateCategoryFilter();
            Log("[刷新] Action列表已刷新");
        }

        private void ClearLogs()
        {
            if (operationLogsField != null)
            {
                operationLogsField.value = "";
            }
            Log("日志已清空");
        }

        private void UpdateStatistics()
        {
            if (totalActionsLabel != null)
                totalActionsLabel.text = $"总数: {actionEntries.Count}";
            if (withDescriptionLabel != null)
                withDescriptionLabel.text = $"有描述: {actionEntries.Count(e => !string.IsNullOrEmpty(e.description))}";
            if (withParamDescLabel != null)
            {
                int withParamDesc = actionEntries.Count(e => 
                    e.parameters != null && e.parameters.Any(p => !string.IsNullOrEmpty(p.description)));
                withParamDescLabel.text = $"参数描述: {withParamDesc}";
            }
            if (selectedCountLabel != null)
                selectedCountLabel.text = $"已选: {actionEntries.Count(e => e.isSelected)}";
        }

        private void UpdateCategoryFilter()
        {
            allCategories = new List<string> { "全部" };
            var categories = actionEntries
                .Where(e => !string.IsNullOrEmpty(e.category))
                .Select(e => e.category)
                .Distinct()
                .OrderBy(c => c);
            allCategories.AddRange(categories);
            
            if (categoryFilter != null)
            {
                categoryFilter.choices = allCategories;
                if (!allCategories.Contains(categoryFilter.value))
                {
                    categoryFilter.value = "全部";
                }
            }
        }

        private void UpdateProgress(float progress)
        {
            if (progressBar != null)
            {
                progressBar.value = progress;
                progressBar.title = $"{progress:F0}%";
            }
        }

        private void ApplyFilters()
        {
            filteredEntries.Clear();

            string searchText = searchField?.value?.ToLower() ?? "";
            string categoryValue = categoryFilter?.value ?? "全部";
            string descFilterValue = descriptionFilter?.value ?? "全部";

            foreach (var entry in actionEntries)
            {
                // Apply category filter
                if (categoryValue != "全部" && entry.category != categoryValue)
                    continue;

                // Apply description filter
                switch (descFilterValue)
                {
                    case "有描述":
                        if (string.IsNullOrEmpty(entry.description)) continue;
                        break;
                    case "无描述":
                        if (!string.IsNullOrEmpty(entry.description)) continue;
                        break;
                    case "有参数描述":
                        if (entry.parameters == null || !entry.parameters.Any(p => !string.IsNullOrEmpty(p.description)))
                            continue;
                        break;
                    case "无参数描述":
                        if (entry.parameters != null && entry.parameters.Any(p => !string.IsNullOrEmpty(p.description)))
                            continue;
                        break;
                }

                // Apply text search
                if (!string.IsNullOrWhiteSpace(searchText))
                {
                    bool matchFound = 
                        (entry.typeName?.ToLower().Contains(searchText) ?? false) ||
                        (entry.displayName?.ToLower().Contains(searchText) ?? false) ||
                        (entry.category?.ToLower().Contains(searchText) ?? false) ||
                        (entry.description?.ToLower().Contains(searchText) ?? false);

                    // Also search in parameters
                    if (!matchFound && entry.parameters != null)
                    {
                        matchFound = entry.parameters.Any(p =>
                            (p.name?.ToLower().Contains(searchText) ?? false) ||
                            (p.label?.ToLower().Contains(searchText) ?? false) ||
                            (p.description?.ToLower().Contains(searchText) ?? false));
                    }

                    if (!matchFound) continue;
                }

                filteredEntries.Add(entry);
            }

            if (actionListView != null)
            {
                actionListView.itemsSource = filteredEntries;
                actionListView.Rebuild();
            }
            
            Log($"[筛选] 显示 {filteredEntries.Count}/{actionEntries.Count} 个Action");
        }

        private void OpenExportFolder()
        {
            string fullPath = Path.GetFullPath(Config.exportDirectory);
            if (Directory.Exists(fullPath))
            {
                System.Diagnostics.Process.Start(fullPath);
            }
            else
            {
                EditorUtility.DisplayDialog("目录不存在", $"导出目录不存在:\n{fullPath}", "确定");
            }
        }

        #endregion

        #region Data Operations

        private void ScanActions()
        {
            actionEntries = ActionScanner.ScanActions(databaseManager.Database);
            Log($"[扫描] 完成，找到 {actionEntries.Count} 个Action");
        }

        private void SaveAllToDatabase()
        {
            // Sync parameter descriptions back to entry
            foreach (var entry in actionEntries)
            {
                if (entry.parameters != null)
                {
                    foreach (var param in entry.parameters)
                    {
                        if (!string.IsNullOrEmpty(param.description))
                        {
                            entry.parameterDescriptions[param.name] = param.description;
                        }
                    }
                }
            }
            
            int savedCount = databaseManager.SaveAllToDatabase(actionEntries);
            EditorUtility.DisplayDialog("保存成功", $"已保存 {savedCount} 个Action描述到数据库", "确定");
        }

        #endregion

        #region AI Description Generation

        private async UniTaskVoid GenerateDescriptionsForSelectedAsync()
        {
            var (successCount, failCount) = await aiGenerator.GenerateDescriptionsForSelectedAsync(actionEntries);
            if (successCount > 0 || failCount > 0)
            {
                actionListView?.Rebuild();
                string message = $"生成完成!\n\n成功: {successCount}\n失败: {failCount}";
                if (successCount > 0)
                {
                    message += "\n\n请点击\"保存到数据库\"保存结果";
                }
                EditorUtility.DisplayDialog("AI生成完成", message, "确定");
            }
        }

        private async UniTaskVoid GenerateDescriptionsForMissingAsync()
        {
            var (successCount, failCount) = await aiGenerator.GenerateDescriptionsForMissingAsync(actionEntries);
            if (successCount > 0 || failCount > 0)
            {
                actionListView?.Rebuild();
                string message = $"生成完成!\n\n成功: {successCount}\n失败: {failCount}";
                if (successCount > 0)
                {
                    message += "\n\n请点击\"保存到数据库\"保存结果";
                }
                EditorUtility.DisplayDialog("AI生成完成", message, "确定");
            }
        }

        #endregion

        #region JSON Export

        private void ExportActionsToJSON()
        {
            var (successCount, failCount) = jsonExporter.ExportActionsToJSON(actionEntries);
            EditorUtility.DisplayDialog(
                "导出完成",
                $"成功导出 {successCount} 个JSON文件\n失败 {failCount}\n\n导出目录: {Path.GetFullPath(Config.exportDirectory)}",
                "确定"
            );
        }

        #endregion

        #region One-Click Export and Notify

        private async UniTaskVoid OneClickExportAndNotifyAsync()
        {
            bool autoNotifyRebuild = Config.autoNotifyRebuild;
            string stepInfo = autoNotifyRebuild
                ? "1. 扫描所有Action\n2. 导出JSON文件\n3. 启动skill_agent服务器（如未运行）\n4. 通知服务器重建索引"
                : "1. 扫描所有Action\n2. 导出JSON文件";

            if (!EditorUtility.DisplayDialog(
                "确认导出",
                $"将依次执行以下操作:\n\n{stepInfo}\n\n是否继续?",
                "继续",
                "取消"))
            {
                return;
            }

            int totalSteps = autoNotifyRebuild ? 4 : 2;
            Log($"\n{new string('=', 60)}\n[一键导出] 开始自动化流程...\n{new string('=', 60)}");

            // Step 1: Scan
            Log($"\n[步骤1/{totalSteps}] 扫描Actions...");
            ScanActions();
            ApplyFilters();
            await UniTask.Delay(500);

            // Step 2: Export JSON
            Log($"\n[步骤2/{totalSteps}] 导出JSON文件...");
            jsonExporter.ExportActionsToJSONSilent(actionEntries);
            await UniTask.Delay(500);

            // Step 3-4: Start server and notify rebuild
            bool notifySuccess = false;
            string notifyMessage = "";

            if (autoNotifyRebuild)
            {
                Log($"\n[步骤3/{totalSteps}] 检查skill_agent服务器状态...");
                bool serverReady = await serverClient.EnsureServerRunningAsync();

                if (serverReady)
                {
                    Log($"\n[步骤4/{totalSteps}] 通知服务器重建索引...");
                    (notifySuccess, notifyMessage) = await serverClient.SendRebuildNotificationAsync();
                }
                else
                {
                    notifyMessage = "服务器启动失败或超时";
                    Log($"  ❌ {notifyMessage}");
                }
            }

            Log($"\n{new string('=', 60)}\n[一键导出] 流程完成!\n{new string('=', 60)}");

            // Show completion dialog
            if (autoNotifyRebuild && notifySuccess)
            {
                EditorUtility.DisplayDialog(
                    "导出完成",
                    $"所有操作已完成!\n\n" +
                    $"✅ Action总数: {actionEntries.Count}\n" +
                    $"✅ JSON已导出\n" +
                    $"✅ 已通知服务器重建索引\n\n" +
                    $"{notifyMessage}",
                    "确定"
                );
            }
            else if (autoNotifyRebuild && !notifySuccess)
            {
                EditorUtility.DisplayDialog(
                    "导出完成（通知失败）",
                    $"导出操作已完成，但通知服务器失败!\n\n" +
                    $"✅ Action总数: {actionEntries.Count}\n" +
                    $"✅ JSON已导出\n" +
                    $"❌ 通知服务器失败: {notifyMessage}\n\n" +
                    $"请确保skill_agent服务器已启动 (http://{Config.serverHost}:{Config.serverPort})",
                    "确定"
                );
            }
            else
            {
                EditorUtility.DisplayDialog(
                    "导出完成",
                    $"导出操作已完成!\n\n" +
                    $"✅ Action总数: {actionEntries.Count}\n" +
                    $"✅ JSON已导出",
                    "确定"
                );
            }
        }

        #endregion

        #region Logging

        private void Log(string message)
        {
            string logEntry = $"[{DateTime.Now:HH:mm:ss}] {message}\n";

            if (operationLogsField != null)
            {
                operationLogsField.value += logEntry;

                if (operationLogsField.value.Length > 10000)
                {
                    operationLogsField.value = operationLogsField.value.Substring(operationLogsField.value.Length - 8000);
                }
            }
        }

        #endregion
    }
}
