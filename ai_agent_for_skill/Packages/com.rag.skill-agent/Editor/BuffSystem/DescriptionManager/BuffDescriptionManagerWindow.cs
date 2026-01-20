using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor.UIElements;
using Cysharp.Threading.Tasks;
using RAG;

namespace RAG.BuffSystem
{
    /// <summary>
    /// Buff Description Manager Window - UIElement based implementation
    /// Export Buff Effect and Trigger data to JSON for skill_agent to use
    /// Supports AI-powered description generation using DeepSeek
    /// </summary>
    public class BuffDescriptionManagerWindow : EditorWindow
    {
        // Tab enum
        private enum BuffTab { Effects, Triggers }
        private BuffTab currentTab = BuffTab.Effects;

        // Configuration from RAGConfig
        private RAGConfig Config => RAGConfig.Instance;

        // Buff data
        private List<BuffEffectEntry> effectEntries = new List<BuffEffectEntry>();
        private List<BuffTriggerEntry> triggerEntries = new List<BuffTriggerEntry>();
        private List<BuffEffectEntry> filteredEffects = new List<BuffEffectEntry>();
        private List<BuffTriggerEntry> filteredTriggers = new List<BuffTriggerEntry>();

        // Managers and utilities
        private BuffDatabaseManager databaseManager;
        private BuffJSONExporterInstance jsonExporter;
        private SkillAgentServerClient serverClient;

        // UI Elements
        private ListView buffListView;
        private Label totalEffectsLabel;
        private Label totalTriggersLabel;
        private Label withDescriptionLabel;
        private Label selectedCountLabel;
        private TextField operationLogsField;
        private ProgressBar progressBar;
        private TextField searchField;
        private DropdownField categoryFilter;
        private DropdownField descriptionFilter;
        private Label exportDirLabel;
        private TextField apiKeyField;
        private RadioButtonGroup tabGroup;

        // Templates
        private VisualTreeAsset buffItemTemplate;

        // Expanded items tracking
        private HashSet<string> expandedItems = new HashSet<string>();

        // Filter options
        private List<string> allCategories = new List<string> { "全部" };

        // Resizable columns helper for main list
        private ResizableColumnHelper mainColumnHelper;
        // Resizable columns helper for parameter panels
        private ParamPanelColumnHelper paramColumnHelper;

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
            ScanBuffs();
            if (!LoadUIContent())
            {
                container.Add(new Label("无法加载 Buff 面板 UI") { style = { color = Color.red } });
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
        // [MenuItem("技能系统/Buff导出工具", priority = 101)]
        public static void ShowWindow()
        {
            var window = GetWindow<BuffDescriptionManagerWindow>("Buff导出工具");
            window.minSize = new Vector2(1000, 750);
            window.Show();
        }

        private void CreateGUI()
        {
            _root = rootVisualElement;
            InitializeManagers();
            databaseManager.LoadDatabase();
            ScanBuffs();
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
            string uxmlPath = "Packages/com.rag.skill-agent/Editor/BuffSystem/DescriptionManager/BuffDescriptionManagerWindow.uxml";
            var visualTree = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(uxmlPath);

            if (visualTree == null)
            {
                Debug.LogError($"[BuffDescriptionManager] Failed to load UXML from: {uxmlPath}");
                return false;
            }

            visualTree.CloneTree(Root);

            string ussPath = "Packages/com.rag.skill-agent/Editor/BuffSystem/DescriptionManager/BuffDescriptionManagerWindow.uss";
            var styleSheet = AssetDatabase.LoadAssetAtPath<StyleSheet>(ussPath);
            if (styleSheet != null)
            {
                Root.styleSheets.Add(styleSheet);
            }

            string templatePath = "Packages/com.rag.skill-agent/Editor/BuffSystem/DescriptionManager/BuffItemTemplate.uxml";
            buffItemTemplate = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(templatePath);

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
                "- BuffDescriptionManagerWindow.uxml\n" +
                "- BuffDescriptionManagerWindow.uss\n" +
                "- BuffItemTemplate.uxml\n\n" +
                "路径：Packages/com.rag.skill-agent/Editor/BuffSystem/DescriptionManager/");
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
            string dbPath = Config?.buffSystemConfig?.databasePath ?? "Assets/Data/BuffDescriptionDatabase.asset";
            string exportDir = Config?.buffSystemConfig?.exportDirectory ?? "../skill_agent/Data/Buffs";
            
            databaseManager = new BuffDatabaseManager(dbPath, Log);
            jsonExporter = new BuffJSONExporterInstance(exportDir, Log);
            serverClient = new SkillAgentServerClient(Config.serverHost, Config.serverPort, Log);
        }
        
        #region UI Binding

        private void BindUIElements()
        {
            // Statistics labels
            totalEffectsLabel = Root.Q<Label>("totalEffectsLabel");
            totalTriggersLabel = Root.Q<Label>("totalTriggersLabel");
            withDescriptionLabel = Root.Q<Label>("withDescriptionLabel");
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
                descriptionFilter.choices = new List<string> { "全部", "有描述", "无描述" };
                descriptionFilter.value = "全部";
            }

            // Tab group
            tabGroup = Root.Q<RadioButtonGroup>("buffTypeTabGroup");
            if (tabGroup != null)
            {
                tabGroup.value = 0;
            }

            // Logs field
            operationLogsField = Root.Q<TextField>("operationLogsField");

            // Export directory label
            exportDirLabel = Root.Q<Label>("exportDirLabel");
            if (exportDirLabel != null)
            {
                string exportDir = Config?.buffSystemConfig?.exportDirectory ?? "../skill_agent/Data/Buffs";
                exportDirLabel.text = $"目录: {exportDir}";
            }

            // API Key field
            apiKeyField = Root.Q<TextField>("apiKeyField");
            if (apiKeyField != null)
            {
                apiKeyField.value = RAGConfig.DeepSeekApiKey;
            }

            // List view
            buffListView = Root.Q<ListView>("buffListView");

            // Setup resizable columns
            SetupResizableColumns();
        }

        private void SetupResizableColumns()
        {
            var headerRow = Root.Q<VisualElement>("headerRow");
            if (headerRow == null || buffListView == null) return;

            // Define main list columns configuration
            var mainColumns = new List<ResizableColumnHelper.ColumnConfig>
            {
                new ResizableColumnHelper.ColumnConfig { HeaderCellName = "headerCell_2", ItemCellClass = "type-label", MinWidth = 80, MaxWidth = 400, InitialWidth = 140 },
                new ResizableColumnHelper.ColumnConfig { HeaderCellName = "headerCell_3", ItemCellClass = "displayname-field", MinWidth = 50, MaxWidth = 200, InitialWidth = 90 },
                new ResizableColumnHelper.ColumnConfig { HeaderCellName = "headerCell_4", ItemCellClass = "category-field", MinWidth = 40, MaxWidth = 150, InitialWidth = 60 },
                new ResizableColumnHelper.ColumnConfig { HeaderCellName = "headerCell_5", ItemCellClass = "param-count-label", MinWidth = 30, MaxWidth = 80, InitialWidth = 45 },
                new ResizableColumnHelper.ColumnConfig { HeaderCellName = "headerCell_6", ItemCellClass = "description-field", MinWidth = 100, MaxWidth = 600, InitialWidth = 300 },
            };

            mainColumnHelper = new ResizableColumnHelper(headerRow, buffListView, mainColumns);
            mainColumnHelper.SetupResizeHandles();
            mainColumnHelper.OnColumnResized += () => buffListView?.RefreshItems();

            // Setup parameter panel column helper
            var paramColumns = new List<ParamPanelColumnHelper.ParamColumnConfig>
            {
                new ParamPanelColumnHelper.ParamColumnConfig { ClassName = "param-header-name", MinWidth = 60, MaxWidth = 250, CurrentWidth = 100 },
                new ParamPanelColumnHelper.ParamColumnConfig { ClassName = "param-header-type", MinWidth = 50, MaxWidth = 200, CurrentWidth = 80 },
                new ParamPanelColumnHelper.ParamColumnConfig { ClassName = "param-header-default", MinWidth = 50, MaxWidth = 200, CurrentWidth = 80 },
                new ParamPanelColumnHelper.ParamColumnConfig { ClassName = "param-header-label-col", MinWidth = 50, MaxWidth = 200, CurrentWidth = 80 },
                new ParamPanelColumnHelper.ParamColumnConfig { ClassName = "param-header-desc", MinWidth = 100, MaxWidth = 500, CurrentWidth = 200 },
            };
            paramColumnHelper = new ParamPanelColumnHelper(buffListView, paramColumns);
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
            });

            // Tab switching
            tabGroup?.RegisterValueChangedCallback(evt =>
            {
                currentTab = (BuffTab)evt.newValue;
                ApplyFilters();
                UpdateStatistics();
            });

            // Save button
            var saveDbBtn = Root.Q<Button>("saveDbBtn");
            saveDbBtn?.RegisterCallback<ClickEvent>(evt => SaveAllToDatabase());

            var selectAllBtn = Root.Q<Button>("selectAllBtn");
            selectAllBtn?.RegisterCallback<ClickEvent>(evt => SelectAll());

            var deselectAllBtn = Root.Q<Button>("deselectAllBtn");
            deselectAllBtn?.RegisterCallback<ClickEvent>(evt => DeselectAll());

            // Export buttons
            var exportJsonBtn = Root.Q<Button>("exportJsonBtn");
            exportJsonBtn?.RegisterCallback<ClickEvent>(evt => ExportBuffsToJSON());

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
            refreshBtn?.RegisterCallback<ClickEvent>(evt => RefreshBuffs());

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
            if (buffListView == null) return;

            filteredEffects = new List<BuffEffectEntry>(effectEntries);
            filteredTriggers = new List<BuffTriggerEntry>(triggerEntries);

            // Default to effects tab
            buffListView.itemsSource = filteredEffects;
            buffListView.makeItem = MakeBuffItem;
            buffListView.bindItem = BindBuffItem;
            buffListView.selectionType = SelectionType.None;
            buffListView.virtualizationMethod = CollectionVirtualizationMethod.DynamicHeight;
        }

        #endregion

        #region ListView Item Creation and Binding

        private VisualElement MakeBuffItem()
        {
            VisualElement item;
            if (buffItemTemplate != null)
            {
                item = buffItemTemplate.CloneTree();
            }
            else
            {
                item = CreateBuffItemProgrammatically();
            }

            // Apply current column widths
            mainColumnHelper?.ApplyWidthsToItem(item);
            return item;
        }

        private VisualElement CreateBuffItemProgrammatically()
        {
            var container = new VisualElement();
            container.AddToClassList("buff-item");

            var mainRow = new VisualElement();
            mainRow.AddToClassList("buff-item-row");
            mainRow.name = "mainRow";

            var toggle = new Toggle();
            toggle.AddToClassList("select-toggle");
            toggle.name = "selectToggle";
            mainRow.Add(toggle);

            var expandBtn = new Button();
            expandBtn.text = "▶";
            expandBtn.AddToClassList("expand-button");
            expandBtn.name = "expandBtn";
            mainRow.Add(expandBtn);

            var typeLabel = new Label();
            typeLabel.AddToClassList("type-label");
            typeLabel.name = "typeLabel";
            mainRow.Add(typeLabel);

            var displayNameField = new TextField();
            displayNameField.AddToClassList("displayname-field");
            displayNameField.name = "displayNameField";
            mainRow.Add(displayNameField);

            var categoryField = new TextField();
            categoryField.AddToClassList("category-field");
            categoryField.name = "categoryField";
            mainRow.Add(categoryField);

            var paramCountLabel = new Label();
            paramCountLabel.AddToClassList("param-count-label");
            paramCountLabel.name = "paramCountLabel";
            mainRow.Add(paramCountLabel);

            var descriptionField = new TextField();
            descriptionField.AddToClassList("description-field");
            descriptionField.multiline = true;
            descriptionField.name = "descriptionField";
            mainRow.Add(descriptionField);

            var aiLabel = new Label();
            aiLabel.AddToClassList("ai-label");
            aiLabel.name = "aiLabel";
            mainRow.Add(aiLabel);

            container.Add(mainRow);

            var paramPanel = new VisualElement();
            paramPanel.name = "paramPanel";
            paramPanel.AddToClassList("param-panel");
            paramPanel.style.display = DisplayStyle.None;
            container.Add(paramPanel);

            return container;
        }

        private void BindBuffItem(VisualElement element, int index)
        {
            if (currentTab == BuffTab.Effects)
            {
                if (index < 0 || index >= filteredEffects.Count) return;
                BindEffectItem(element, filteredEffects[index], index);
            }
            else
            {
                if (index < 0 || index >= filteredTriggers.Count) return;
                BindTriggerItem(element, filteredTriggers[index], index);
            }
        }

        private void BindEffectItem(VisualElement element, BuffEffectEntry entry, int index)
        {
            var toggle = element.Q<Toggle>("selectToggle");
            var expandBtn = element.Q<Button>("expandBtn");
            var typeLabel = element.Q<Label>("typeLabel");
            var displayNameField = element.Q<TextField>("displayNameField");
            var categoryField = element.Q<TextField>("categoryField");
            var paramCountLabel = element.Q<Label>("paramCountLabel");
            var descriptionField = element.Q<TextField>("descriptionField");
            var aiLabel = element.Q<Label>("aiLabel");
            var paramPanel = element.Q("paramPanel");

            // Unregister previous callbacks
            UnregisterCallbacks(toggle, displayNameField, categoryField, descriptionField);

            if (toggle != null)
            {
                EventCallback<ChangeEvent<bool>> cb = evt => { entry.isSelected = evt.newValue; UpdateStatistics(); };
                toggle.userData = cb;
                toggle.SetValueWithoutNotify(entry.isSelected);
                toggle.RegisterValueChangedCallback(cb);
            }

            if (expandBtn != null)
            {
                bool isExpanded = expandedItems.Contains(entry.typeName);
                expandBtn.text = isExpanded ? "▼" : "▶";
                expandBtn.clickable = new Clickable(() => ToggleExpand(entry.typeName, paramPanel, expandBtn, entry.parameters));
            }

            if (typeLabel != null)
            {
                typeLabel.text = entry.typeName;
                typeLabel.tooltip = entry.fullTypeName;
            }

            if (displayNameField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.displayName = evt.newValue;
                displayNameField.userData = cb;
                displayNameField.SetValueWithoutNotify(entry.displayName ?? "");
                displayNameField.RegisterValueChangedCallback(cb);
            }

            if (categoryField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.category = evt.newValue;
                categoryField.userData = cb;
                categoryField.SetValueWithoutNotify(entry.category ?? "");
                categoryField.RegisterValueChangedCallback(cb);
            }

            BindParamCount(paramCountLabel, entry.parameters);

            if (descriptionField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.description = evt.newValue;
                descriptionField.userData = cb;
                descriptionField.SetValueWithoutNotify(entry.description ?? "");
                descriptionField.RegisterValueChangedCallback(cb);
            }

            BindAILabel(aiLabel, entry.isAIGenerated, entry.aiGeneratedTime);
            BindRowStyle(element, index);
            HandleExpandedState(paramPanel, entry.typeName, entry.parameters);
        }

        private void BindTriggerItem(VisualElement element, BuffTriggerEntry entry, int index)
        {
            var toggle = element.Q<Toggle>("selectToggle");
            var expandBtn = element.Q<Button>("expandBtn");
            var typeLabel = element.Q<Label>("typeLabel");
            var displayNameField = element.Q<TextField>("displayNameField");
            var categoryField = element.Q<TextField>("categoryField");
            var paramCountLabel = element.Q<Label>("paramCountLabel");
            var descriptionField = element.Q<TextField>("descriptionField");
            var aiLabel = element.Q<Label>("aiLabel");
            var paramPanel = element.Q("paramPanel");

            UnregisterCallbacks(toggle, displayNameField, categoryField, descriptionField);

            if (toggle != null)
            {
                EventCallback<ChangeEvent<bool>> cb = evt => { entry.isSelected = evt.newValue; UpdateStatistics(); };
                toggle.userData = cb;
                toggle.SetValueWithoutNotify(entry.isSelected);
                toggle.RegisterValueChangedCallback(cb);
            }

            if (expandBtn != null)
            {
                bool isExpanded = expandedItems.Contains(entry.typeName);
                expandBtn.text = isExpanded ? "▼" : "▶";
                expandBtn.clickable = new Clickable(() => ToggleExpand(entry.typeName, paramPanel, expandBtn, entry.parameters));
            }

            if (typeLabel != null)
            {
                typeLabel.text = entry.typeName;
                typeLabel.tooltip = entry.fullTypeName;
            }

            if (displayNameField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.displayName = evt.newValue;
                displayNameField.userData = cb;
                displayNameField.SetValueWithoutNotify(entry.displayName ?? "");
                displayNameField.RegisterValueChangedCallback(cb);
            }

            if (categoryField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.category = evt.newValue;
                categoryField.userData = cb;
                categoryField.SetValueWithoutNotify(entry.category ?? "");
                categoryField.RegisterValueChangedCallback(cb);
            }

            BindParamCount(paramCountLabel, entry.parameters);

            if (descriptionField != null)
            {
                EventCallback<ChangeEvent<string>> cb = evt => entry.description = evt.newValue;
                descriptionField.userData = cb;
                descriptionField.SetValueWithoutNotify(entry.description ?? "");
                descriptionField.RegisterValueChangedCallback(cb);
            }

            BindAILabel(aiLabel, entry.isAIGenerated, entry.aiGeneratedTime);
            BindRowStyle(element, index);
            HandleExpandedState(paramPanel, entry.typeName, entry.parameters);
        }

        private void UnregisterCallbacks(Toggle toggle, TextField displayName, TextField category, TextField description)
        {
            toggle?.UnregisterValueChangedCallback(toggle.userData as EventCallback<ChangeEvent<bool>>);
            displayName?.UnregisterValueChangedCallback(displayName.userData as EventCallback<ChangeEvent<string>>);
            category?.UnregisterValueChangedCallback(category.userData as EventCallback<ChangeEvent<string>>);
            description?.UnregisterValueChangedCallback(description.userData as EventCallback<ChangeEvent<string>>);
        }

        private void ToggleExpand(string typeName, VisualElement paramPanel, Button expandBtn, List<BuffParameterInfo> parameters)
        {
            if (expandedItems.Contains(typeName))
            {
                expandedItems.Remove(typeName);
                expandBtn.text = "▶";
                if (paramPanel != null) paramPanel.style.display = DisplayStyle.None;
            }
            else
            {
                expandedItems.Add(typeName);
                expandBtn.text = "▼";
                if (paramPanel != null)
                {
                    paramPanel.style.display = DisplayStyle.Flex;
                    BuildParameterPanel(paramPanel, parameters);
                }
            }
            buffListView?.RefreshItems();
        }

        private void BindParamCount(Label label, List<BuffParameterInfo> parameters)
        {
            if (label == null) return;
            int count = parameters?.Count ?? 0;
            int withDesc = parameters?.Count(p => !string.IsNullOrEmpty(p.description)) ?? 0;
            label.text = $"{withDesc}/{count}";

            label.RemoveFromClassList("param-count-none");
            label.RemoveFromClassList("param-count-full");
            label.RemoveFromClassList("param-count-partial");
            label.RemoveFromClassList("param-count-empty");

            if (count == 0) label.AddToClassList("param-count-none");
            else if (withDesc == count) label.AddToClassList("param-count-full");
            else if (withDesc > 0) label.AddToClassList("param-count-partial");
            else label.AddToClassList("param-count-empty");

            label.tooltip = $"有描述的参数: {withDesc} / 总参数: {count}";
        }

        private void BindAILabel(Label label, bool isAIGenerated, string aiGeneratedTime)
        {
            if (label == null) return;
            label.text = isAIGenerated ? "✓ AI" : "手动";
            label.tooltip = isAIGenerated
                ? $"描述由 AI 自动生成\n生成时间: {aiGeneratedTime}"
                : "描述为手动填写或尚未填写";
            label.RemoveFromClassList("ai-label-yes");
            label.RemoveFromClassList("ai-label-no");
            label.AddToClassList(isAIGenerated ? "ai-label-yes" : "ai-label-no");
        }

        private void BindRowStyle(VisualElement element, int index)
        {
            element.RemoveFromClassList("buff-item-even");
            element.RemoveFromClassList("buff-item-odd");
            element.AddToClassList(index % 2 == 0 ? "buff-item-even" : "buff-item-odd");
        }

        private void HandleExpandedState(VisualElement paramPanel, string typeName, List<BuffParameterInfo> parameters)
        {
            if (paramPanel == null) return;
            bool isExpanded = expandedItems.Contains(typeName);
            if (isExpanded)
            {
                paramPanel.style.display = DisplayStyle.Flex;
                BuildParameterPanel(paramPanel, parameters);
            }
            else
            {
                paramPanel.style.display = DisplayStyle.None;
            }
        }

        private void BuildParameterPanel(VisualElement paramPanel, List<BuffParameterInfo> parameters)
        {
            paramPanel.Clear();

            if (parameters == null || parameters.Count == 0)
            {
                var noParamLabel = new Label("无参数");
                noParamLabel.AddToClassList("no-param-label");
                paramPanel.Add(noParamLabel);
                return;
            }

            var headerRow = new VisualElement();
            headerRow.AddToClassList("param-header-row");
            headerRow.Add(CreateParamHeaderLabel("参数名", "param-header-name"));
            headerRow.Add(CreateParamHeaderLabel("类型", "param-header-type"));
            headerRow.Add(CreateParamHeaderLabel("默认值", "param-header-default"));
            headerRow.Add(CreateParamHeaderLabel("标签", "param-header-label-col"));
            headerRow.Add(CreateParamHeaderLabel("描述", "param-header-desc"));
            paramPanel.Add(headerRow);

            // Setup resize handles for parameter header
            paramColumnHelper?.SetupHeaderResizeHandles(headerRow);

            foreach (var param in parameters)
            {
                var paramRow = new VisualElement();
                paramRow.AddToClassList("param-row");

                var nameLabel = new Label(param.name);
                nameLabel.AddToClassList("param-name");
                paramRow.Add(nameLabel);

                var typeLabel = new Label(param.type);
                typeLabel.AddToClassList("param-type");
                paramRow.Add(typeLabel);

                var defaultLabel = new Label(param.defaultValue ?? "-");
                defaultLabel.AddToClassList("param-default");
                paramRow.Add(defaultLabel);

                var labelLabel = new Label(param.label ?? "-");
                labelLabel.AddToClassList("param-label-value");
                paramRow.Add(labelLabel);

                var descField = new TextField();
                descField.AddToClassList("param-desc-field");
                if (!string.IsNullOrEmpty(param.description))
                    descField.AddToClassList("param-desc-field-filled");
                descField.SetValueWithoutNotify(param.description ?? "");
                descField.RegisterValueChangedCallback(evt => param.description = evt.newValue);
                paramRow.Add(descField);

                // Apply current column widths to parameter row
                paramColumnHelper?.ApplyWidthsToRow(paramRow);

                paramPanel.Add(paramRow);
            }
        }

        private Label CreateParamHeaderLabel(string text, string className)
        {
            var label = new Label(text);
            label.AddToClassList("param-header-label");
            label.AddToClassList(className);
            return label;
        }

        #endregion

        #region UI Actions

        private void SelectAll()
        {
            if (currentTab == BuffTab.Effects)
            {
                foreach (var entry in filteredEffects)
                    entry.isSelected = true;
            }
            else
            {
                foreach (var entry in filteredTriggers)
                    entry.isSelected = true;
            }
            buffListView?.Rebuild();
            UpdateStatistics();
        }

        private void DeselectAll()
        {
            if (currentTab == BuffTab.Effects)
            {
                foreach (var entry in filteredEffects)
                    entry.isSelected = false;
            }
            else
            {
                foreach (var entry in filteredTriggers)
                    entry.isSelected = false;
            }
            buffListView?.Rebuild();
            UpdateStatistics();
        }

        private void ExpandAllParameters()
        {
            var entries = currentTab == BuffTab.Effects
                ? filteredEffects.Where(e => e.parameters?.Count > 0).Select(e => e.typeName)
                : filteredTriggers.Where(e => e.parameters?.Count > 0).Select(e => e.typeName);

            foreach (var name in entries)
                expandedItems.Add(name);

            buffListView?.Rebuild();
            Log("[展开] 已展开所有参数面板");
        }

        private void CollapseAllParameters()
        {
            expandedItems.Clear();
            buffListView?.Rebuild();
            Log("[收起] 已收起所有参数面板");
        }

        private void RefreshBuffs()
        {
            ScanBuffs();
            ApplyFilters();
            UpdateStatistics();
            UpdateCategoryFilter();
            Log("[刷新] Buff列表已刷新");
        }

        private void ClearLogs()
        {
            if (operationLogsField != null)
                operationLogsField.value = "";
            Log("日志已清空");
        }

        private void UpdateStatistics()
        {
            if (totalEffectsLabel != null)
                totalEffectsLabel.text = $"效果: {effectEntries.Count}";
            if (totalTriggersLabel != null)
                totalTriggersLabel.text = $"触发器: {triggerEntries.Count}";

            int withDesc = currentTab == BuffTab.Effects
                ? effectEntries.Count(e => !string.IsNullOrEmpty(e.description))
                : triggerEntries.Count(e => !string.IsNullOrEmpty(e.description));
            if (withDescriptionLabel != null)
                withDescriptionLabel.text = $"有描述: {withDesc}";

            int selected = currentTab == BuffTab.Effects
                ? effectEntries.Count(e => e.isSelected)
                : triggerEntries.Count(e => e.isSelected);
            if (selectedCountLabel != null)
                selectedCountLabel.text = $"已选: {selected}";
        }

        private void UpdateCategoryFilter()
        {
            allCategories = new List<string> { "全部" };

            var effectCategories = effectEntries
                .Where(e => !string.IsNullOrEmpty(e.category))
                .Select(e => e.category);
            var triggerCategories = triggerEntries
                .Where(e => !string.IsNullOrEmpty(e.category))
                .Select(e => e.category);

            allCategories.AddRange(effectCategories.Concat(triggerCategories).Distinct().OrderBy(c => c));

            if (categoryFilter != null)
            {
                categoryFilter.choices = allCategories;
                if (!allCategories.Contains(categoryFilter.value))
                    categoryFilter.value = "全部";
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
            string searchText = searchField?.value?.ToLower() ?? "";
            string categoryValue = categoryFilter?.value ?? "全部";
            string descFilterValue = descriptionFilter?.value ?? "全部";

            if (currentTab == BuffTab.Effects)
            {
                filteredEffects.Clear();
                foreach (var entry in effectEntries)
                {
                    if (!MatchesFilters(entry.category, entry.description, entry.typeName, entry.displayName, searchText, categoryValue, descFilterValue))
                        continue;
                    filteredEffects.Add(entry);
                }
                buffListView.itemsSource = filteredEffects;
            }
            else
            {
                filteredTriggers.Clear();
                foreach (var entry in triggerEntries)
                {
                    if (!MatchesFilters(entry.category, entry.description, entry.typeName, entry.displayName, searchText, categoryValue, descFilterValue))
                        continue;
                    filteredTriggers.Add(entry);
                }
                buffListView.itemsSource = filteredTriggers;
            }

            buffListView?.Rebuild();
            int count = currentTab == BuffTab.Effects ? filteredEffects.Count : filteredTriggers.Count;
            int total = currentTab == BuffTab.Effects ? effectEntries.Count : triggerEntries.Count;
            Log($"[筛选] 显示 {count}/{total} 个{(currentTab == BuffTab.Effects ? "效果" : "触发器")}");
        }

        private bool MatchesFilters(string category, string description, string typeName, string displayName,
            string searchText, string categoryValue, string descFilterValue)
        {
            if (categoryValue != "全部" && category != categoryValue)
                return false;

            switch (descFilterValue)
            {
                case "有描述":
                    if (string.IsNullOrEmpty(description)) return false;
                    break;
                case "无描述":
                    if (!string.IsNullOrEmpty(description)) return false;
                    break;
            }

            if (!string.IsNullOrWhiteSpace(searchText))
            {
                bool matchFound =
                    (typeName?.ToLower().Contains(searchText) ?? false) ||
                    (displayName?.ToLower().Contains(searchText) ?? false) ||
                    (category?.ToLower().Contains(searchText) ?? false) ||
                    (description?.ToLower().Contains(searchText) ?? false);
                if (!matchFound) return false;
            }

            return true;
        }

        private void OpenExportFolder()
        {
            string exportDir = Config?.buffSystemConfig?.exportDirectory ?? "../skill_agent/Data/Buffs";
            string fullPath = Path.GetFullPath(exportDir);
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

        private void ScanBuffs()
        {
            effectEntries = BuffScanner.ScanBuffEffects();
            triggerEntries = BuffScanner.ScanBuffTriggers();

            // Load existing descriptions from database
            if (databaseManager.Database != null)
            {
                foreach (var entry in effectEntries)
                {
                    var saved = databaseManager.Database.GetEffectDescriptionByType(entry.typeName);
                    if (saved != null)
                    {
                        entry.displayName = saved.displayName;
                        entry.description = saved.description;
                        entry.category = saved.category;
                        entry.isAIGenerated = saved.isAIGenerated;
                        entry.aiGeneratedTime = saved.aiGeneratedTime;
                    }
                }
                foreach (var entry in triggerEntries)
                {
                    var saved = databaseManager.Database.GetTriggerDescriptionByType(entry.typeName);
                    if (saved != null)
                    {
                        entry.displayName = saved.displayName;
                        entry.description = saved.description;
                        entry.category = saved.category;
                        entry.isAIGenerated = saved.isAIGenerated;
                        entry.aiGeneratedTime = saved.aiGeneratedTime;
                    }
                }
            }

            Log($"[扫描] 完成，找到 {effectEntries.Count} 个效果, {triggerEntries.Count} 个触发器");
        }

        private void SaveAllToDatabase()
        {
            int effectsSaved = databaseManager.SaveEffectsToDatabase(effectEntries);
            int triggersSaved = databaseManager.SaveTriggersToDatabase(triggerEntries);
            EditorUtility.DisplayDialog("保存成功",
                $"已保存 {effectsSaved} 个效果描述和 {triggersSaved} 个触发器描述到数据库", "确定");
        }

        #endregion

        #region JSON Export

        private void ExportBuffsToJSON()
        {
            var (effectSuccess, effectFail) = jsonExporter.ExportEffectsToJSON(effectEntries);
            var (triggerSuccess, triggerFail) = jsonExporter.ExportTriggersToJSON(triggerEntries);

            // Also export enums
            BuffJSONExporter.ExportBuffEnums();

            string exportDir = Config?.buffSystemConfig?.exportDirectory ?? "../skill_agent/Data/Buffs";
            EditorUtility.DisplayDialog(
                "导出完成",
                $"效果: 成功 {effectSuccess}, 失败 {effectFail}\n" +
                $"触发器: 成功 {triggerSuccess}, 失败 {triggerFail}\n\n" +
                $"导出目录: {Path.GetFullPath(exportDir)}",
                "确定"
            );
        }

        #endregion

        #region One-Click Export and Notify

        private async UniTaskVoid OneClickExportAndNotifyAsync()
        {
            bool autoNotifyRebuild = Config.autoNotifyRebuild;
            string stepInfo = autoNotifyRebuild
                ? "1. 扫描所有Buff\n2. 导出JSON文件\n3. 启动skill_agent服务器（如未运行）\n4. 通知服务器重建索引"
                : "1. 扫描所有Buff\n2. 导出JSON文件";

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
            Log($"\n[步骤1/{totalSteps}] 扫描Buffs...");
            ScanBuffs();
            ApplyFilters();
            await UniTask.Delay(500);

            // Step 2: Export JSON
            Log($"\n[步骤2/{totalSteps}] 导出JSON文件...");
            jsonExporter.ExportEffectsToJSONSilent(effectEntries);
            jsonExporter.ExportTriggersToJSONSilent(triggerEntries);
            BuffJSONExporter.ExportBuffEnums();
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
                    $"✅ 效果总数: {effectEntries.Count}\n" +
                    $"✅ 触发器总数: {triggerEntries.Count}\n" +
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
                    $"✅ 效果总数: {effectEntries.Count}\n" +
                    $"✅ 触发器总数: {triggerEntries.Count}\n" +
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
                    $"✅ 效果总数: {effectEntries.Count}\n" +
                    $"✅ 触发器总数: {triggerEntries.Count}\n" +
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

