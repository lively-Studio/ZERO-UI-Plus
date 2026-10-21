# ZERO-UI+

面向 Minecraft Java 版的现代化界面材质包，界面语言参考 Microsoft Fluent Design。

![ZERO-UI+ 预览](preview.png)

## 这是什么

ZERO-UI+ 用一套统一的 Fluent 视觉语言重绘了 Minecraft 的全部 GUI：容器界面、HUD、菜单、
提示框、吐司、进度条、成就与配方书。所有几何尺寸与原版逐像素对齐——Minecraft 的 GUI 布局是
硬编码的，任何尺寸偏差都会导致裁切或拉伸，因此本包只改变"表面"，不改变布局。

- **包装格式** 97（`min_format` 63，`max_format` 110），即 1.21.8 及以上客户端通用
- **分辨率** 界面主体（快捷栏、经验条、进度条、弹窗、吐司、成就背景等 104 张）为 4× 高清纹理，
  在 GUI 缩放或高 DPI 屏幕上不再出现锯齿与像素块
- **体积** 约 2.4 MB，511 张纹理
- **覆盖** `textures/gui/` 下 469/469 个精灵、26/26 个容器界面，全部替换；成书界面保持原版
- **零尺寸偏差** 构建时逐张校验尺寸与九宫格切片，不匹配即中止

## 安装

1. 下载本仓库，或直接使用 `pack/` 目录
2. 将 `pack/` 重命名为 `ZERO-UI+.zip`（或将 `pack/` 复制到
   `.minecraft/resourcepacks/ZERO-UI+`）
3. 在「选项 → 资源包」中启用

```
tools/
  fluent.py            调色板、超采样绘制表面、材质配方、语义字形
  textures.py          控件与 HUD 生成器（第一部分）
  textures_ui.py       菜单、提示框、吐司、图标、社交界面
  extras.py            剩余精灵与成就界面
  containers.py        容器面板管线（槽位/内嵌区/预览底板的检测与重绘）
  restyle.py           字形换色策略表与 Fluent 配色阶梯
  build.py             装配、尺寸校验、九宫格继承、轮廓审计
  dump_manifest.py     从客户端 jar 导出原版精灵尺寸清单（维护用）
  vanilla_manifest.json  上一步的产物，textures.py 中硬编码尺寸的来源
```

## 许可

本项目采用 [MIT 许可证](LICENSE)，Copyright (c) 2026 lively-Studio。
