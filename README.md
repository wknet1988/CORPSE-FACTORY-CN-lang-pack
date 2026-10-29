# CORPSE FACTORY 简体中文汉化工程 (CN lang pack)

CORPSE FACTORY（《尸体工厂》）的**非官方**简体中文汉化工程源码。

本仓库（源码）包含：英文 → 简体中文的**翻译对照表**、**文本提取 / 注入脚本**、**子集化中文字体**以及工程文档。
**仓库本身不包含**游戏本体或任何第三方专有二进制文件。但本工程在 **Releases** 中提供**已打好的汉化补丁**（由作者自有正版副本生成的衍生文件：`resources.assets` 已注入中文并内嵌字体、`Elringus.Naninovel.Runtime.dll` 已汉化确认提示），供普通玩家直接下载使用。

> ⚠️ **版权与免责声明**
> - 本汉化为粉丝个人作品，**与游戏原作者 / 发行商无任何关联**，不代表其立场。
> - 使用本工程前，你必须**合法拥有** CORPSE FACTORY 的 PC 版（Unity 2020.3.22f1 + Naninovel 引擎）。
> - 本仓库仅提供「在你的**自己**游戏副本上重新生成汉化补丁」所需的翻译数据与工具。
> - **请勿**将游戏原始二进制文件（`resources.assets` / `*.resS` / `*.dll` / 可执行文件）上传或转发给他人；请只分享本仓库（翻译 + 工具）或本工程的 Release 补丁。

---

## 开箱即用（推荐：下载即玩，无需编译）

如果你只是想玩中文版、不会用 Python，直接去 **Releases** 下载 `CORPSE-FACTORY-CN-patch-v1.0.0.7z`
（7z 格式，请用 **7-Zip / WinRAR / Windows 11 资源管理器** 解压）：

- **方式一（推荐，带自动备份）**：把压缩包解压到任意文件夹，进入后双击 **`install.bat`**，
  它会自动定位游戏目录、备份原文件并覆盖汉化文件。
- **方式二（直接覆盖）**：打开游戏根目录（含 `CORPSE FACTORY_Data` 的文件夹），
  把压缩包里的 `CORPSE FACTORY_Data` 文件夹直接解压覆盖进去（提示覆盖时选“全部覆盖”）。

启动游戏即可体验中文。

> 还原方法：把 `CORPSE FACTORY_Data\resources.assets.bak` 和
> `CORPSE FACTORY_Data\Managed\Elringus.Naninovel.Runtime.dll.bak` 去掉 `.bak` 后缀覆盖回去即可；
> 若用方式二且未备份，可在 Steam 对该游戏「验证游戏文件的完整性」恢复。
> 引擎确认框的按钮（Cancel / Delete / Continue）仍为英文——它们是输入动作标识符，改中文会导致按钮失效，故保留英文。

补丁压缩包内含 `source/` 目录（本工程的全部源码与翻译表），仅供有兴趣的玩家自行重建或核对，普通玩家无需使用。

---

## 仓库内容

| 文件 / 目录 | 说明 |
|---|---|
| `translations_complete.json` | **权威翻译表** `{英文原文: 简体中文}`，约 1.1 万条，构建注入时直接使用。 |
| `occurrences.json` / `occurrences_v2.json` | 文本在 `resources.assets` 中的定位索引（长度前缀偏移 + pid）。`40_build_final.py` 读 `occurrences.json`，`77_add_translations.py` 读 `occurrences_v2.json`（两者内容相同）。 |
| `cjk_subset.ttf` | 按译文实际用字从 `simhei.ttf` 子集化得到的中文字体（已嵌入 `resources.assets` 的 `AveriaSerifLibre-Regular`）。 |
| `40_build_final.py` | **权威注入构建脚本**：读取原始 `resources.assets`，注入译文并嵌入中文字体。 |
| `76_extract_v2.py` | 全量提取器：扫描所有 MonoBehaviour 对象，抽取显示文本并生成 `occurrences_v2.json`。 |
| `77_add_translations.py` | 补译脚本：把新增译文合并进 `translations_complete.json`。 |
| `78_patch_dll.py` | 引擎内置提示补丁：原地等长替换 `Elringus.Naninovel.Runtime.dll` 里 3 条确认提示（覆盖 / 删除存档、返回主菜单）。 |
| `80_verify.py` | 结构校验器（部署前硬门槛）：遍历 Naninovel 元素结构，要求精确落到下一标记，`BAD=0` 才算通过。 |
| `55_merge_complete.py` | 合并全部译文批次生成 `translations_complete.json`。 |
| `cn_batch*.txt` / `translations_batch*.json` / `batch_*.json` | 分批翻译的工作记录（可读中文 / 中英对照 / 原始抽取）。 |
| `0*.py` ~ `11*.py` | 探索与诊断脚本（开发过程记录，非必要）。 |
| `HANDOFF.md` / `DISPATCH.md` | 协作交接文档：术语表、工作流、规则、质检与回滚。 |

---

## 环境依赖

- Python 3.10+（已用 3.13 验证）
- [`UnityPy`](https://pypi.org/project/UnityPy/) —— 读写 `resources.assets`
- [`fonttools`](https://pypi.org/project/fonttools/) —— 字体子集化
- Windows 系统字体 `C:/Windows/Fonts/simhei.ttf`（构建时用于生成中文字体子集；非 Windows 可用仓库自带的 `cjk_subset.ttf`）

```
pip install UnityPy fonttools
```

---

## 使用方法（在你自己的游戏副本上生成汉化补丁）

1. **准备原始素材（你自己游戏里的文件，不要从本仓库获取）**
   把你的 `CORPSE FACTORY_Data/resources.assets` 复制一份，放到工作区的
   `backup_original/resources.assets` 作为**未修改的原始注入源**
   （脚本默认从该路径读取；也可用 `--in` 指定）。
   - 同时保留 `CORPSE FACTORY_Data/resources.assets.resS` 原样，**绝对不要改动或重命名它**。

2. **生成汉化后的 `resources.assets`**
   ```
   python 40_build_final.py --out ./build_out
   ```
   脚本会：读取 `translations_complete.json` + `occurrences.json` → 注入译文 →
   嵌入 `cjk_subset.ttf` 中文字体 → 将完整 `resources.assets` 写入 `./build_out/`。

3. **部署文本汉化**
   把 `./build_out/resources.assets` **覆盖**到你的
   `CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets`。
   （务必保留同目录的 `resources.assets.resS` 不动。）

4. **汉化引擎内置确认提示**（覆盖 / 删除存档、返回主菜单）
   需要你自己的 `Elringus.Naninovel.Runtime.dll` 的一份干净备份 `*.dll.bak_patch`，然后：
   ```
   python 78_patch_dll.py
   ```
   它会从 `.bak_patch` 原地等长替换 3 条提示并写回 `Elringus.Naninovel.Runtime.dll`。
   - ⚠️ **切勿**翻译 `Cancel` / `Delete` / `Continue` 按钮标签——它们同时是引擎的输入动作标识符
     （`Submit.Cancel.Delete.Continue`），改中文会导致按钮无响应。

5. **结构校验（部署前建议）**
   ```
   python 80_verify.py
   ```
   输出 `BAD=0` 表示结构完整、可正常加载。

---

## 重要注意事项

- **路径为硬编码**：脚本中的 `DATA` / `DLL` / `BACKUP` 常量指向作者本机
  `G:/SteamLibrary/steamapps/common/CORPSE FACTORY/...`。
  应用到你自己的机器时，请相应修改这些常量（或改用 `--in` / 相对路径）。
- **`.resS` 不可动**：仍有 730+ 对象引用外部 `.resS`，改动/重命名会丢失纹理与音频。
- **按钮标识符陷阱**：见上方第 4 步。
- **回滚**：保留 `backup_original/resources.assets`（原版）与 `*.dll.bak_patch`（原版 DLL），
  出问题直接覆盖回去即可。

---

## 兼容性

- 游戏版本：CORPSE FACTORY PC（Unity 2020.3.22f1，Naninovel 引擎）
- 目标语言：简体中文（UTF-8 注入；显示文本近乎全覆盖，UI / 菜单 / 制作人员 / 引擎提示均已处理）

---

*本工程仅供学习与交流。如权利人提出异议，将配合停止使用。*
