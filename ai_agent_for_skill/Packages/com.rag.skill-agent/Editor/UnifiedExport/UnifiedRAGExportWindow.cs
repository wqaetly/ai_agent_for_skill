using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;
using Cysharp.Threading.Tasks;
using RAG.BuffSystem;

namespace RAG
{
    /// <summary>
    /// Unified RAG Export Window - Container for Action and Buff export panels
    /// Provides tab switching between the two export tools by embedding existing windows
    /// </summary>
    public class UnifiedRAGExportWindow : EditorWindow
    {
        private enum ExportTab { Actions, Buffs }
        private ExportTab currentTab = ExportTab.Actions;

        // UI Elements
        private Button actionTabBtn;
        private Button buffTabBtn;
        private VisualElement actionPanelContainer;
        private VisualElement buffPanelContainer;
        private Label statusLabel;
        private Label serverStatusLabel;

        // Embedded window instances (non-visual, just for logic)
        private DescriptionManagerWindow actionWindow;
        private BuffDescriptionManagerWindow buffWindow;

        [MenuItem("技能系统/RAG数据导出中心", priority = 99)]
        public static void ShowWindow()
        {
            var window = GetWindow<UnifiedRAGExportWindow>("RAG数据导出中心");
            window.minSize = new Vector2(1100, 800);
            window.Show();
        }

        private void CreateGUI()
        {
            // Load main UXML - 使用Package路径
            string uxmlPath = "Packages/com.rag.skill-agent/Editor/UnifiedExport/UnifiedRAGExportWindow.uxml";
            var visualTree = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(uxmlPath);

            if (visualTree == null)
            {
                CreateFallbackUI();
                return;
            }

            visualTree.CloneTree(rootVisualElement);

            // Load USS - 使用Package路径
            string ussPath = "Packages/com.rag.skill-agent/Editor/UnifiedExport/UnifiedRAGExportWindow.uss";
            var styleSheet = AssetDatabase.LoadAssetAtPath<StyleSheet>(ussPath);
            if (styleSheet != null)
            {
                rootVisualElement.styleSheets.Add(styleSheet);
            }

            // Bind UI elements
            BindUIElements();

            // Create embedded panels
            CreateEmbeddedPanels();

            // Setup tab switching
            SetupEventHandlers();

            // Default to Actions tab
            SwitchToTab(ExportTab.Actions);

            UpdateStatus("准备就绪");
            CheckServerStatus();
        }

        private void CreateFallbackUI()
        {
            var errorLabel = new Label("无法加载UI文件，请确保以下文件存在：\n" +
                "- UnifiedRAGExportWindow.uxml\n" +
                "- UnifiedRAGExportWindow.uss\n\n" +
                "路径：Assets/Scripts/RAG/Editor/UnifiedExport/");
            errorLabel.style.color = Color.red;
            errorLabel.style.whiteSpace = WhiteSpace.Normal;
            errorLabel.style.marginTop = 20;
            errorLabel.style.marginLeft = 20;
            rootVisualElement.Add(errorLabel);

            var refreshBtn = new Button(() => {
                rootVisualElement.Clear();
                CreateGUI();
            }) { text = "重新加载" };
            refreshBtn.style.width = 100;
            refreshBtn.style.marginTop = 10;
            refreshBtn.style.marginLeft = 20;
            rootVisualElement.Add(refreshBtn);
        }

        private void BindUIElements()
        {
            actionTabBtn = rootVisualElement.Q<Button>("actionTabBtn");
            buffTabBtn = rootVisualElement.Q<Button>("buffTabBtn");
            actionPanelContainer = rootVisualElement.Q<VisualElement>("actionPanelContainer");
            buffPanelContainer = rootVisualElement.Q<VisualElement>("buffPanelContainer");
            statusLabel = rootVisualElement.Q<Label>("statusLabel");
            serverStatusLabel = rootVisualElement.Q<Label>("serverStatusLabel");

            var openConfigBtn = rootVisualElement.Q<Button>("openConfigBtn");
            openConfigBtn?.RegisterCallback<ClickEvent>(evt => RAGConfig.SelectConfig());
        }

        private void CreateEmbeddedPanels()
        {
            // Create Action panel by embedding DescriptionManagerWindow
            if (actionPanelContainer != null)
            {
                actionWindow = CreateInstance<DescriptionManagerWindow>();
                actionWindow.InitializeIntoContainer(actionPanelContainer);
            }

            // Create Buff panel by embedding BuffDescriptionManagerWindow
            if (buffPanelContainer != null)
            {
                buffWindow = CreateInstance<BuffDescriptionManagerWindow>();
                buffWindow.InitializeIntoContainer(buffPanelContainer);
            }
        }

        private void SetupEventHandlers()
        {
            actionTabBtn?.RegisterCallback<ClickEvent>(evt => SwitchToTab(ExportTab.Actions));
            buffTabBtn?.RegisterCallback<ClickEvent>(evt => SwitchToTab(ExportTab.Buffs));
        }

        private void SwitchToTab(ExportTab tab)
        {
            currentTab = tab;
            actionTabBtn?.RemoveFromClassList("tab-active");
            buffTabBtn?.RemoveFromClassList("tab-active");

            if (tab == ExportTab.Actions)
            {
                actionTabBtn?.AddToClassList("tab-active");
                actionPanelContainer.style.display = DisplayStyle.Flex;
                buffPanelContainer.style.display = DisplayStyle.None;
                UpdateStatus("当前: 技能 Actions");
            }
            else
            {
                buffTabBtn?.AddToClassList("tab-active");
                actionPanelContainer.style.display = DisplayStyle.None;
                buffPanelContainer.style.display = DisplayStyle.Flex;
                UpdateStatus("当前: Buff 系统");
            }
        }

        private void UpdateStatus(string message)
        {
            if (statusLabel != null) statusLabel.text = message;
        }

        private void CheckServerStatus()
        {
            var client = new SkillAgentServerClient(
                RAGConfig.Instance.serverHost,
                RAGConfig.Instance.serverPort,
                msg => { });
            bool online = client.IsServerRunning();

            if (serverStatusLabel != null)
            {
                serverStatusLabel.text = online ? "服务器: 在线" : "服务器: 离线";
                serverStatusLabel.RemoveFromClassList("server-online");
                serverStatusLabel.RemoveFromClassList("server-offline");
                serverStatusLabel.AddToClassList(online ? "server-online" : "server-offline");
            }
        }

        private void OnDestroy()
        {
            // Clean up embedded window instances
            if (actionWindow != null)
            {
                DestroyImmediate(actionWindow);
            }
            if (buffWindow != null)
            {
                DestroyImmediate(buffWindow);
            }
        }
    }
}

