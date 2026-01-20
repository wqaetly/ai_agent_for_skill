using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace RAG
{
    /// <summary>
    /// Helper class to add resizable column functionality to header rows.
    /// Allows users to drag column separators to resize columns.
    /// </summary>
    public class ResizableColumnHelper
    {
        // Column configuration
        public class ColumnConfig
        {
            public string HeaderCellName;      // Name of the header cell element
            public string ItemCellClass;       // Class name for corresponding item cells
            public float MinWidth = 30f;       // Minimum allowed width
            public float MaxWidth = 500f;      // Maximum allowed width
            public float InitialWidth;         // Initial width from USS
        }

        private readonly VisualElement _headerRow;
        private readonly VisualElement _listContainer;
        private readonly List<ColumnConfig> _columns;
        private readonly Dictionary<string, float> _columnWidths = new Dictionary<string, float>();
        
        // Drag state
        private bool _isDragging;
        private ColumnConfig _dragColumn;
        private float _dragStartX;
        private float _dragStartWidth;

        public event Action OnColumnResized;

        public ResizableColumnHelper(VisualElement headerRow, VisualElement listContainer, List<ColumnConfig> columns)
        {
            _headerRow = headerRow;
            _listContainer = listContainer;
            _columns = columns;
            
            // Initialize column widths
            foreach (var col in _columns)
            {
                _columnWidths[col.ItemCellClass] = col.InitialWidth;
            }
        }

        public void SetupResizeHandles()
        {
            foreach (var col in _columns)
            {
                var headerCell = _headerRow.Q<VisualElement>(col.HeaderCellName);
                if (headerCell == null) continue;

                // Create resize handle
                var handle = new VisualElement();
                handle.AddToClassList("column-resize-handle");
                handle.style.position = Position.Absolute;
                handle.style.right = 0;
                handle.style.top = 0;
                handle.style.bottom = 0;
                handle.style.width = 6;
                handle.pickingMode = PickingMode.Position;
                
                // Setup drag events
                handle.RegisterCallback<PointerDownEvent>(evt => OnPointerDown(evt, col, headerCell));
                handle.RegisterCallback<PointerMoveEvent>(evt => OnPointerMove(evt, headerCell));
                handle.RegisterCallback<PointerUpEvent>(evt => OnPointerUp(evt, handle));
                handle.RegisterCallback<PointerLeaveEvent>(evt => OnPointerLeave(evt, handle));

                headerCell.style.position = Position.Relative;
                headerCell.Add(handle);
            }
        }

        private void OnPointerDown(PointerDownEvent evt, ColumnConfig col, VisualElement headerCell)
        {
            _isDragging = true;
            _dragColumn = col;
            _dragStartX = evt.position.x;
            _dragStartWidth = headerCell.resolvedStyle.width;
            
            (evt.target as VisualElement)?.CapturePointer(evt.pointerId);
            evt.StopPropagation();
        }

        private void OnPointerMove(PointerMoveEvent evt, VisualElement headerCell)
        {
            if (!_isDragging || _dragColumn == null) return;

            float delta = evt.position.x - _dragStartX;
            float newWidth = Mathf.Clamp(_dragStartWidth + delta, _dragColumn.MinWidth, _dragColumn.MaxWidth);
            
            // Update header cell width
            headerCell.style.width = newWidth;
            _columnWidths[_dragColumn.ItemCellClass] = newWidth;

            // Update all visible items
            UpdateListItemWidths(_dragColumn.ItemCellClass, newWidth);
            
            OnColumnResized?.Invoke();
        }

        private void OnPointerUp(PointerUpEvent evt, VisualElement handle)
        {
            if (_isDragging)
            {
                handle.ReleasePointer(evt.pointerId);
                _isDragging = false;
                _dragColumn = null;
            }
        }

        private void OnPointerLeave(PointerLeaveEvent evt, VisualElement handle)
        {
            // Don't release if we're dragging - we want to continue tracking
        }

        private void UpdateListItemWidths(string className, float width)
        {
            _listContainer?.Query<VisualElement>(className: className).ForEach(el => el.style.width = width);
        }

        public float GetColumnWidth(string itemCellClass)
        {
            return _columnWidths.TryGetValue(itemCellClass, out var width) ? width : 100f;
        }

        public void ApplyWidthsToItem(VisualElement item)
        {
            foreach (var col in _columns)
            {
                var cell = item.Q<VisualElement>(className: col.ItemCellClass);
                if (cell != null && _columnWidths.TryGetValue(col.ItemCellClass, out var width))
                {
                    cell.style.width = width;
                }
            }
        }
    }

    /// <summary>
    /// Helper class for managing resizable columns in parameter panels.
    /// Since parameter panels are dynamically created, this class stores column widths
    /// and applies them to new panels as they are created.
    /// </summary>
    public class ParamPanelColumnHelper
    {
        public class ParamColumnConfig
        {
            public string ClassName;
            public float MinWidth = 30f;
            public float MaxWidth = 400f;
            public float CurrentWidth;
        }

        private readonly List<ParamColumnConfig> _columns;
        private readonly VisualElement _listContainer;

        public event Action OnColumnResized;

        public ParamPanelColumnHelper(VisualElement listContainer, List<ParamColumnConfig> columns)
        {
            _listContainer = listContainer;
            _columns = columns;
        }

        /// <summary>
        /// Setup resize handles on a parameter panel header row
        /// </summary>
        public void SetupHeaderResizeHandles(VisualElement headerRow)
        {
            foreach (var col in _columns)
            {
                var headerCell = headerRow.Q<VisualElement>(className: col.ClassName);
                if (headerCell == null) continue;

                // Apply current width
                headerCell.style.width = col.CurrentWidth;

                // Skip adding handle to the last column (description which uses flex-grow)
                if (col.ClassName == "param-header-desc") continue;

                // Create resize handle
                var handle = new VisualElement();
                handle.AddToClassList("column-resize-handle");
                handle.style.position = Position.Absolute;
                handle.style.right = 0;
                handle.style.top = 0;
                handle.style.bottom = 0;
                handle.style.width = 6;
                handle.pickingMode = PickingMode.Position;

                // Drag state captured in closure
                bool isDragging = false;
                float startX = 0;
                float startWidth = 0;

                handle.RegisterCallback<PointerDownEvent>(evt =>
                {
                    isDragging = true;
                    startX = evt.position.x;
                    startWidth = headerCell.resolvedStyle.width;
                    handle.CapturePointer(evt.pointerId);
                    evt.StopPropagation();
                });

                handle.RegisterCallback<PointerMoveEvent>(evt =>
                {
                    if (!isDragging) return;

                    float delta = evt.position.x - startX;
                    float newWidth = Mathf.Clamp(startWidth + delta, col.MinWidth, col.MaxWidth);

                    headerCell.style.width = newWidth;
                    col.CurrentWidth = newWidth;

                    // Update all param rows in all visible param panels
                    UpdateAllParamCells(col.ClassName, newWidth);
                    OnColumnResized?.Invoke();
                });

                handle.RegisterCallback<PointerUpEvent>(evt =>
                {
                    if (isDragging)
                    {
                        handle.ReleasePointer(evt.pointerId);
                        isDragging = false;
                    }
                });

                headerCell.style.position = Position.Relative;
                headerCell.Add(handle);
            }
        }

        /// <summary>
        /// Apply current column widths to a parameter row
        /// </summary>
        public void ApplyWidthsToRow(VisualElement paramRow)
        {
            foreach (var col in _columns)
            {
                // Map header class to row class
                string rowClass = col.ClassName.Replace("param-header-", "param-");
                if (rowClass == "param-label-col") rowClass = "param-label-value";

                var cell = paramRow.Q<VisualElement>(className: rowClass);
                if (cell != null)
                {
                    cell.style.width = col.CurrentWidth;
                }
            }
        }

        private void UpdateAllParamCells(string headerClass, float width)
        {
            // Map header class to row class
            string rowClass = headerClass.Replace("param-header-", "param-");
            if (rowClass == "param-label-col") rowClass = "param-label-value";

            _listContainer?.Query<VisualElement>(className: rowClass).ForEach(el => el.style.width = width);
            _listContainer?.Query<VisualElement>(className: headerClass).ForEach(el => el.style.width = width);
        }
    }
}

