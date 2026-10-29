# CORPSE FACTORY 简体中文汉化补丁

非官方粉丝汉化。**使用前你必须拥有正版 CORPSE FACTORY（Steam）。本补丁不包含任何游戏文件，只在你自己的游戏副本上生成汉化。**

## 包含内容
- `apply_patch.py` —— 一键应用器
- `40_build_final.py` —— 文本注入引擎（被 apply_patch 调用）
- `translations_complete.json` —— 约 1.1 万条英→中翻译表
- `occurrences.json` / `occurrences_v2.json` —— 文本在 assets 中的定位索引
- `cjk_subset.ttf` —— 子集化中文字体（已嵌入游戏字体）
- `PATCH_README.md` —— 本说明

## 使用方法
1. 安装依赖（只需一次）：
   ```
   pip install UnityPy fonttools
   ```
2. 运行一键应用器，参数填**游戏根目录**（即包含 `CORPSE FACTORY_Data` 的那一层）：
   ```
   python apply_patch.py "G:/SteamLibrary/steamapps/common/CORPSE FACTORY"
   ```
3. 脚本会：
   - 自动备份原始 `resources.assets` 与 `Elringus.Naninovel.Runtime.dll`
   - 注入中文并嵌入字体
   - 汉化引擎内置的「覆盖存档 / 删除存档 / 返回主菜单」确认提示
   - 做完整性自检
4. 启动游戏，即为简体中文。

## 还原
将 `resources.assets.bak_patch` 与 `Elringus.Naninovel.Runtime.dll.bak_patch` 改回原名覆盖即可。

## 注意事项
- **请勿**改动或重命名 `CORPSE FACTORY_Data/resources.assets.resS`（程序不会动它）。
- 引擎确认框按钮保持英文（Cancel / Delete / Continue）—— 它们是输入动作标识符，翻译会导致按钮失效。
- 本补丁为粉丝作品，与游戏官方无关；仅供已购买者个人使用。
