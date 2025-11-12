# 训练场URP商业品质配置指南

本指南帮助你完成训练场系统的最终配置，达到商业级视觉品质�?

## 📋 目录

1. [URP渲染管线配置](#urp渲染管线配置)
2. [相机配置](#相机配置)
3. [场景设置](#场景设置)
4. [性能优化](#性能优化)
5. [故障排除](#故障排除)

---

## 1. URP渲染管线配置

### 1.1 Universal Render Pipeline Asset配置

**位置**: `Assets/Settings/PC_RPAsset.asset`

推荐设置（高质量PC端）�?

```
General:
  - Depth Texture: �?Enabled
  - Opaque Texture: �?Enabled
  - Opaque Downsampling: None
  - Terrain Holes: �?Enabled

Quality:
  - HDR: �?Enabled
  - MSAA: 4x (�?x，根据性能调整)
  - Render Scale: 1.0
  - Upscaling Filter: Automatic

Lighting:
  - Main Light: Per Pixel
  - Main Light Shadow Resolution: 2048
  - Additional Lights: Per Pixel
  - Additional Lights Per Object Limit: 4
  - Additional Light Shadow Resolution: 2048

Shadows:
  - Max Distance: 50
  - Cascade Count: 2 �?4
  - Depth Bias: 1.0
  - Normal Bias: 1.0
  - Soft Shadows: �?Enabled

Post-processing:
  - Grading Mode: High Dynamic Range
  - LUT Size: 32
```

### 1.2 Universal Renderer Data配置

**位置**: `Assets/Settings/PC_Renderer.asset`

推荐设置�?

```
Rendering:
  - Rendering Path: Forward
  - Depth Priming Mode: Auto

Post-processing:
  - �?Post Processing Enabled

Renderer Features:
  - 添加以下Renderer Features（如需要）:
    * Screen Space Ambient Occlusion (SSAO)
    * Screen Space Reflections (SSR) - 可�?
```

---

## 2. 相机配置

### 2.1 主相机设�?

1. **添加必要组件**:
   ```
   - Camera（主相机�?
   - CinemachineBrain（自动添加）
   - Universal Additional Camera Data（自动添加）
   ```

2. **相机参数**:
   ```
   Projection: Perspective
   Field of View: 60
   Clipping Planes:
     - Near: 0.3
     - Far: 1000

   Rendering:
     - Post Processing: �?Enabled
     - Anti-aliasing: None (使用MSAA)
     - Stop NaNs: �?Enabled
     - Dithering: �?Enabled
   ```

3. **Universal Camera设置**:
   ```
   Camera Features:
     - Render Shadows: �?Enabled
     - Require Depth Texture: �?Enabled
     - Require Opaque Texture: �?Disabled (按需)

   Post Processing:
     - Anti-aliasing: None (使用MSAA)
     - Render Post Processing: �?Enabled
   ```

### 2.2 Cinemachine虚拟相机设置

1. **创建虚拟相机** (或使用TrainingGroundCameraController自动创建):
   ```
   - 右键 Hierarchy �?Cinemachine �?Virtual Camera
   - 命名�? CM_TrainingGroundCamera
   ```

2. **配置虚拟相机**:
   ```
   Priority: 10

   Follow: [设置为玩家Transform]
   Look At: [设置为玩家Transform]

   Body:
     - Type: CinemachineFollow (或FramingTransposer)
     - Follow Offset: (0, 3, -6)
     - Damping: (1, 1, 1)

   Aim:
     - Type: CinemachineRotationComposer
     - Tracked Object Offset: (0, 1.5, 0)
     - Damping: (1, 1, 0)

   Lens:
     - Field of View: 60
     - Near Clip: 0.3
     - Far Clip: 1000
   ```

---

## 3. 场景设置

### 3.1 光照配置

1. **主光源（Directional Light�?*:
   ```
   Transform:
     - Rotation: (50, -30, 0)

   Light:
     - Type: Directional
     - Mode: Realtime
     - Color: 浅黄�?(255, 244, 214)
     - Intensity: 1.0
     - Indirect Multiplier: 1.0
     - Shadow Type: Soft Shadows
     - Shadow Resolution: High Resolution
     - Shadow Distance: 50
   ```

2. **环境光照**:
   ```
   Window �?Rendering �?Lighting

   Environment:
     - Skybox Material: Default-Skybox
     - Sun Source: Directional Light
     - Environment Lighting: Sky
     - Ambient Intensity: 1.0
     - Environment Reflections: Skybox
   ```

### 3.2 Post-Processing Volume

1. **创建Global Volume**:
   ```
   - 右键 Hierarchy �?Volume �?Global Volume
   - 命名�? Global Post-Processing
   ```

2. **配置Volume**:
   ```
   Mode: Global
   Priority: 0
   Profile: [创建新Profile或使用PostProcessingManager]
   ```

3. **推荐的后期效果配�?*:
   ```
   Bloom:
     - �?Override
     - Threshold: 0.9
     - Intensity: 0.2
     - Scatter: 0.7

   Color Adjustments:
     - �?Override
     - Post Exposure: 0
     - Contrast: 5
     - Saturation: 5

   Vignette:
     - �?Override
     - Intensity: 0.2
     - Smoothness: 0.4
     - Color: Black

   Tonemapping:
     - �?Override
     - Mode: ACES
   ```

---

## 4. 性能优化

### 4.1 质量等级配置

**路径**: `Edit �?Project Settings �?Quality`

创建多个质量等级�?

**Low (低配PC/移动�?**:
```
- URP Asset: Mobile_RPAsset
- Anti Aliasing: Disabled
- Shadows: Hard Shadows Only
- Shadow Resolution: 256
- Shadow Distance: 20
```

**Medium (中配PC)**:
```
- URP Asset: PC_RPAsset
- Anti Aliasing: 2x MSAA
- Shadows: Soft Shadows
- Shadow Resolution: 1024
- Shadow Distance: 30
```

**High (高配PC)**:
```
- URP Asset: PC_RPAsset
- Anti Aliasing: 4x MSAA
- Shadows: Soft Shadows
- Shadow Resolution: 2048
- Shadow Distance: 50
```

### 4.2 性能优化建议

1. **材质优化**:
   - 使用MaterialLibrary避免重复创建材质
   - 启用GPU Instancing（在材质中勾选）
   - 使用MaterialPropertyBlock减少DrawCall

2. **对象�?*:
   - DamageNumberPool已实�?
   - 考虑为粒子特效添加对象池

3. **LOD系统** (可�?:
   - 对复杂模型添加LOD组件
   - 配置LOD距离阈�?

4. **遮挡剔除** (可�?:
   - `Window �?Rendering �?Occlusion Culling`
   - 烘焙遮挡数据

---

## 5. 故障排除

### 5.1 材质显示粉色

**原因**: Shader未找到或不兼�?

**解决方案**:
1. 确认URP包已正确安装
2. 检查Shader名称拼写是否正确
3. 重新导入URP�? `Window �?Package Manager �?URP �?Reimport`

### 5.2 Post-Processing不生�?

**原因**: 相机或Volume配置错误

**检查清�?*:
- [ ] 相机开启了Post Processing
- [ ] Volume Profile不为�?
- [ ] Volume的Priority设置正确
- [ ] 后期效果已勾选Override

### 5.3 Cinemachine相机不工�?

**原因**: CinemachineBrain未添加或配置错误

**解决方案**:
1. 确认主相机有CinemachineBrain组件
2. 检查虚拟相机的Priority大于0
3. 确认虚拟相机的Follow和Look At目标已设�?

### 5.4 伤害数字不显�?

**原因**: DamageNumberPool或Canvas配置错误

**检查清�?*:
- [ ] 场景中存在DamageNumberPool
- [ ] DamageNumberPool有有效的预制�?
- [ ] Canvas的World Space相机已设�?
- [ ] TextMeshPro已正确导�?

### 5.5 性能问题

**优化步骤**:
1. 打开Profiler: `Window �?Analysis �?Profiler`
2. 检查CPU和GPU占用
3. 降低MSAA等级�?x �?2x �?Off�?
4. 降低阴影分辨率和距离
5. 禁用不必要的后期效果

---

## 6. 快速启动检查清�?

完成以下步骤确保系统正常工作�?

### 基础设置
- [ ] URP包已安装（版�?7.1.0�?
- [ ] Cinemachine包已安装（版�?.0.1�?
- [ ] 项目Graphics设置指向URP Asset

### 场景组件
- [ ] 主相机存在并配置正确
- [ ] CinemachineBrain已添加到主相�?
- [ ] TrainingGroundCameraController已添加到场景
- [ ] Post-Processing Volume已创�?

### 训练场组�?
- [ ] TrainingGroundManager已添加到场景
- [ ] DamageNumberPool已创�?
- [ ] MaterialLibrary自动初始�?
- [ ] PostProcessingManager已添�?

### 测试验证
- [ ] 玩家和木桩材质正常（非粉色）
- [ ] 镜头跟随玩家移动
- [ ] 技能释放时有震屏效�?
- [ ] AOE范围显示正常（红色半透明圆环�?
- [ ] 伤害数字正常弹出并飘�?
- [ ] 后期效果（Bloom、Vignette等）可见

---

## 7. 额外资源

### 官方文档
- [URP官方文档](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest)
- [Cinemachine文档](https://docs.unity3d.com/Packages/com.unity.cinemachine@latest)
- [Post-Processing文档](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/post-processing-ssao.html)

### 训练场脚本参�?
- `TrainingGroundCameraController.cs` - 相机控制
- `PostProcessingManager.cs` - 后期处理管理
- `MaterialLibrary.cs` - 材质�?
- `DamageNumber.cs` - 伤害数字
- `CameraActionVisualizer.cs` - 镜头效果

---

## 8. 联系与支�?

如遇到问题：
1. 查看控制台错误日�?
2. 检查本指南的故障排除章�?
3. 参考Unity官方文档
4. 在项目中搜索相关脚本的注�?

**祝你打造出商业级品质的训练场系统！** 🎮�?
