# CORPSE FACTORY 汉化 —— 交接文档（给接手的 AI Agent）

> 本文件是自包含的：你不需要看之前的对话，按本文件即可独立接手工作。
> 工作目录：`G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork/`

---

## 0. 当前状态（2026-10-29 20:45 最终版，务必先读）

> ### ⚠️ 曾发生过一次严重事故，务必了解
> 旧版构建脚本注入时按 `align4(o["len"])` 消费原区域，但 `o["len"]` 取自提取阶段、
> 与文件真实存储跨度不完全一致，叠加字符串长度变化产生累积位移，吞掉类标记 → Unity 报
> "resources.assets is corrupted"，游戏进正文闪退。
> **修复**：`40_build_final.py` 注入时**直接从文件读取真实长度前缀**算区域大小，
> 并自校验「存储字节 == 英文文本字节」才替换（不一致则跳过，绝不破坏）。
> **权威校验**：每次构建后必须跑 `80_verify.py`（逐对象走 Naninovel 元素结构，要求精确落到
> 下一标记）。**`BAD=0` 才算通过**，这是唯一能证明游戏能加载的测试（UnityPy 宽松加载不算数）。

**进度：翻译 100% 完成（正文 + 菜单/提示 + 单词短句三类全覆盖），已构建并部署。**

- 译文权威表：`translations_complete.json`（**10,902** 条，含正文 act00b + 短句）
- 当前部署版：`build_short3/`（正文 + UI 标签 + 371 条短句，47,527,072 字节，`BAD=0`）
- 游戏内实际替换：**33,516**（正文）+ **336**（UI 标签）+ **2,359**（短句槽位）

**三类文本的来源不同，这是本项目最大的坑：**

| 类别 | 存在哪 | 用什么工具注入 |
|---|---|---|
| 正文对话 | Naninovel Script 的 `GenericTextScriptLine` 元素内 | `40_build_final.py` + `occurrences.json` |
| 菜单/提示标签 | 152 字节的 `UI.Text` 组件 `m_Text` + UnityEvent 的 `set_text` 参数（**同一标签存两份**） | `104_build_with_ui.py` |
| 单词短句 | 同上，但 `occurrences.json` **漏了它们的偏移** | `113_rescan.py` → `111_inject_missing.py` |

### 并行协作分工（历史记录，翻译已结束）

| 谁 | 负责批次 | 方向 |
|---|---|---|
| 原 Agent | 奇数批 `batch_011` / `013` / `015` / `017` / `019` / `021` / `023` | 从前往后 |
| 接手 Agent | 偶数批 `batch_014`–`026`、`028`–`036` | 从后往前 |

**已完成：全部 37 个批次（001–036 + 序章 act00b）+ UI 标签 + 371 条短句。**
**剩余：无。** 保留原文的仅：`{ShinyaRoute}`/`{TomoeRoute}` 路由变量、`@kojikoji` 等用户名、`Ambience-Storm` 音效名。

### 完成后的最终校验结果（2026-10-29 20:44 全量复验）

| 校验项 | 结果 |
|---|---|
| 合并可用条目 | 10,611 / 10,611（100%），含 371 条短句 |
| 英文残留 | **0** |
| 繁体字误用 | **0** |
| 富文本标签不匹配 | 0 |
| 游戏内实际替换 | 正文 33,516 + UI 336 + 短句 2,359 |
| 与原版差异对象 | 473 个（脚本 + UI Text 组件 + UnityEvent 项 + 字体） |
| 字体覆盖 | pid 5209 内嵌 SimHei 子集 **750,824 字节 / 2,784 字形**；缺字 **1 个 = U+2060（不可见连接符，无需字形）**；中文标点 `，。！？；：、“”‘’（）《》…—·` 全部在 cmap 内 |
| 对象数完整性 | 11,600，`OK` |
| **全量落地验证** | **10,598 / 10,598 条中文译文（100.00%）在部署文件里按 UTF-8 字节命中**（`60_verify_final.py`） |
| 短句槽位验证 | 365/369 已消除，剩 4 条为用户名/音效名（有意保留） |

> 复验脚本：`80_verify.py`（结构）、`60_verify_final.py`（全量命中/残留/繁体）、
> `61_verify_font.py`（字体 cmap）、`112_verify_short.py`（短句残留）。都需 UnityPy 解释器。

### 交接时修正的两个错误（重要）

1. **`40_build.py` 不会自动合并翻译表**（原文第 4 节第 2 步的说法有误）。它只读取传入的
   `translations.json` 做注入。**必须先跑合并脚本**，否则新批次不会进入补丁：
   ```
   python 50_merge.py                      # 合并 + 质检，写出 translations_full.json
   python 40_build.py translations_full.json build_progress
   ```
2. 原质检脚本只查「英文残留」，**查不出富文本标签丢失**。已有 4 条译文丢过
   `<color=…><b>…</b></color>` 高亮（关键词变成白字），`50_merge.py` 已加入标签校验并修好。

### 新增脚本（建议沿用）

| 脚本 | 用途 |
|---|---|
| `50_merge.py` | 合并 `translations_act00b.json` + 全部 `translations_batch*.json` → `translations_full.json`；校验标签配对/空译/英文残留；打印覆盖率与未完成批次 |
| `51_apply.py 0NN` | 把 `cn_batch0NN.txt`（每行一条，顺序与 `batch_0NN.json` 一致）自动配对生成 `translations_batch0NN.json`，**免去手写 JSON key 导致的逐字符不一致问题**，并当场报告标签不匹配 |
| `104_build_with_ui.py` | 在已验证构建上打「菜单/提示标签」补丁并重建字体子集；`--skip-text` 只打 UI |
| `110/113_*.py` | 定位 todo 与 occurrences 的差集，`113_rescan.py` 用精确模式重扫出 2,359 个短句槽位 → `missing_locations2.json` |
| `111_inject_missing.py` | 按位置表补注入短句（`--loc missing_locations2.json`），并重建字体子集 |
| `112_verify_short.py` | 校验短句是否仍有残留槽位 |
| `114/115_*.py` | 导出指定文本的前后相邻槽 / 邻近完整对话行，用于判定多义词（`Lie.` `Fire.` `Contact.` 等） |
| `60/61/62_verify*.py` | 全量命中、字体 cmap、流式资源依赖校验 |

推荐流程：导出原文 → 写 `cn_batch0NN.txt` → `51_apply.py 0NN` → `50_merge.py` → 构建 → 部署。

### 解释器注意（2026-10-29 03:25 补记）

`50_merge.py` / `51_apply.py` 是纯标准库，裸 `python` 即可；
但 **`40_build.py` 必须用带 UnityPy 的解释器**，否则报 `ModuleNotFoundError: No module named 'UnityPy'`：

```
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe 40_build.py translations_full.json build_progress
```

### 部署安全措施

部署前已额外保留上一版：`CORPSE FACTORY_Data/resources.assets.prev`。
原版仍在 `CORPSE FACTORY_Data/backup_original/`。

## 0.5 菜单/提示文本汉化（2026-10-29 16:10，build_ui5）

**已解决：菜单、控制面板、制作人员页全部中文。当前部署文件 = `build_ui5/resources.assets`。**

### UI 文本到底存在哪（重要，别再找错地方）

- **不在** TextAsset（全库只有 2 个 TMP 换行字符表）。
- **不在** typetree（`read_typetree()` 对 2,461/2,474 个 MonoBehaviour 直接抛错）。
- **在** 两类小体量 MonoBehaviour 里，且**同一标签存了两份，必须都改**：
  1. **152 字节的 `UnityEngine.UI.Text` 组件**：`0x5C` 处是字体 PPtr `5209`，**末尾**就是 `m_Text`（如 `LOG`/`HIDE`/`SKIP`）。
  2. **约 200 字节的 UnityEvent 项**：`DefaultUI` + `ControlPanel.Hide` 键 + 标签字面量 + `set_text`。

  替换方式：`[i32 len][bytes][padding]` → 新的 `[i32 len][新bytes][padding]`。新旧都对齐到 4 字节，长度差必为 4 的倍数，**后面的字段不会错位**。

### 工具

```
# 在已验证的构建上只打 UI 补丁（推荐；避免 occurrences v2 回退正文覆盖）
<py> 104_build_with_ui.py --in <build_final2/resources.assets> --out <build_ui5> --skip-text
# 从原版全量构建（正文 + UI）
<py> 104_build_with_ui.py --out <build_ui5>
# 校验
<py> 80_verify.py <输出/resources.assets>      # 必须 BAD=0
<py> 107_text_components.py                    # 列出全部 Text 组件文本，确认无英文
```

`UI_LABELS` 字典在 `104_build_with_ui.py` 顶部，想补词直接加。

### 这些**不能**翻译（踩过的坑）

| 字符串 | 真实用途 |
|---|---|
| `Rain` `Thud` `Zipper` `Morgue` `Stairwell` `Office` `Sick` `Award` `Revelation` `Flashback` `Perish` `Violence` `Terminus` `Submitted` `Unlock` | `@playSfx` / `@stopBgm` 的**音效资源名** |
| `Rollback` `Continue` `Cancel` `Submit` `Skip` `Pause` | **Input System 动作名**（pid 9152/9162） |
| `Settings` `Saves` `GlobalSave` `GameSave{0:000}` | **存档目录名**（pid 9170 StateConfiguration） |
| `Title` `H2` `Link` | **TMP 样式名**（pid 9178 StyleSheet） |
| `Fullscreen` `Wide` `Chat` `Bubble` | **Naninovel 渲染模式名**（pid 9171） |
| `NORIKO` `KOJIRO` `CHOICE_*` | 角色 ID / 选项标签 ID |

判断技巧：命令名后面跟 `Naninovel.Commands`；展示文本前面是 `GenericTextScriptLine` + hash；UI 标签所在对象都 <600 字节且含字体 PPtr `5209`。

### 单词短句漏译 —— 已解决（2026-10-29 20:35，build_short3）

**根因不是翻译缺失，而是「待译清单」与「注入位置表」不同源。**

- `todo_list.json` 有 10,611 条（玩家看到的全部英文），其中 371 条是短句（`Bitch.` `OK.` `Wait…` `“Ah…”`）。
- `occurrences.json` 是 `15_final_extract.py` 生成的**注入位置表**，只有 10,649 条。
- **371 条在 todo 里、不在 occurrences 里** → 译文早已存在（100% 已译），但构建时找不到字节偏移，从未写入文件。

为什么 `15_final_extract.py` 会漏：`fast_strings()` 用 `i += 4` 步进，一旦在二进制区把某个 int32
误判为字符串长度就**失步**，该元素内后续字符串整段丢失。`is_display()` 本身没问题
（`Bitch.` 有句点结尾，是能通过的）。

**修复方式**：`113_rescan.py` 不再逐字节扫槽，改为对每个对象直接搜
`struct.pack('<i', len(utf8)) + utf8` 这一精确模式，因此不受步进失步影响，也不受对象体积限制
（关键：`MainScript` 对象有 **11.5 MB**，早先扫描设了 4 MB 上限，把最大的脚本对象整个跳过了）。
结果 371/371 全命中、共 **2,359 个槽位**，`111_inject_missing.py` 注入后 0 跳过。

已确认**不是**漏译来源（无需再查）：`@playSfx` 音效名（`Rain`/`Thud`/`Fire` 等）、
`@choice` 选项（带空格，已译）、日期 HUD 的 `Text_Month=…;Text_Day=…;Text_Time=…`（45 条已译）、
Input System 动作名（`Rollback`/`Continue`/`Cancel`）、存档目录名（`Settings`/`Saves`）。

**下次若还有人报「某句没汉化」**，最快的办法是拿那句英文原文直接跑：

```bash
# 1) 看它在哪、译了没
<python> -c "import json;t=json.load(open('todo_list.json'));print([x for x in t if '原文' in x])"
# 2) 看它在部署文件里还剩几处（带长度前缀的完整槽）
<python> -c "import struct;d=open('../CORPSE FACTORY_Data/resources.assets','rb').read();e='原文'.encode();print(d.count(struct.pack('<i',len(e))+e))"
```

若 >0，用 `115_deep_context.py "原文"` 看上下文确认词义，改 `translations_complete.json` 后重跑
`113_rescan.py` → `111_inject_missing.py` 即可。

## 1. 任务目标

把游戏 **CORPSE FACTORY**（Steam AppID 1414250，Unity 2020.3.22f1 + Naninovel 引擎）
的**全部英文文本翻译成简体中文**，只翻译文本，不改程序逻辑与美术资源。

游戏安装目录：`G:/SteamLibrary/steamapps/common/CORPSE FACTORY/`

## 2. 当前进度（截至本文件生成时）

| 项目 | 状态 |
|---|---|
| 已翻译独立字符串 | **10,611 / 10,611（100%）**，含 371 条短句 |
| 游戏内实际替换处数 | 33,516（正文）+ 336（UI 标签）+ **2,359（短句）** |
| 已嵌入中文字体 | 2,784 字（750,824 字节） |
| 已完成批次 | 全部（序章 Script_Act_00b + batch_001 ~ batch_036 + 短句补注入） |
| 剩余 | **0**（`{ShinyaRoute}`/`{TomoeRoute}` 路由变量、`@kojikoji` 等用户名、`Ambience-Storm` 音效名按规则保留原文） |
| 已部署状态 | 游戏内 `resources.assets` 为**完整汉化版**（47,527,072 字节，来自 `build_short3/`），`80_verify.py` 报 `total=11600 script_objects=23 BAD=0`，`60_verify_final.py` 全量命中 **10,598/10,598（100.00%）** |

## 3. 术语表（**必须严格遵守，保证全书一致**）

### 核心概念
- `Corpse Girl` → **尸体少女**｜`photo` → **照片**｜`corpse` → **尸体**
- `power` → **力量**｜`prey` → **猎物**｜`name` → **姓名**（作动词"点名"时用"点名/称呼"）
- `Herald` → **先驱**｜`copy cat` → **抄袭者**｜`cadaver` → **尸体**
- `The Human Removal Service` → **人体清除服务**
- `Database of the Deceased` / 缩写 `DD` → **死者数据库**
- `Bloody Mary Effect` → **血腥玛丽效应**
- `Number Mask` → **号码伪装**（应用名）

### 人名（音译，已统一）
- Kurosawa→**黑泽**｜Noriko→**纪子**｜Yuriko→**百合子**｜Asuna→**明日奈**｜Shuji→**修二**
- Emi Katsuno→**胜野惠美**｜Kojiro→**小次郎**｜Tomoe Watanabe→**渡边智惠**
- Aoi Satou→**佐藤葵**｜Shinya Fujikawa→**藤川真也**｜Junpei Matsumoto→**松本纯平**
- Kotomi Ida→**井田琴美**｜Akane Tsurumaki→**鹤卷茜**｜Eiichi Hanada→**花田英一**
- Ruri Hatano→**波多野琉璃**｜Amano→**天野**｜Sachiko→**幸子**｜Kenji→**健二**
- Hirota→**广田**｜Shizuko→**静子**｜Momo→**桃子**

### 保留原文不译
- 应用/网站名：`noise`、`noise-channel`、`HRP`
- 店铺/品牌名：`Don Coyote`、`Temujin`、`Château de Cristal`（译作"水晶城堡"）
- 书名：《`Strange Flower`》→**《奇异之花》**

### 乌鸦彩蛋系列（小游戏角色，保留谐音梗）
- `Crowmoe`→**乌鸦智惠**｜`Noricrow Crowsawa`→**黑泽乌鸦子**｜`Crow Girl`→**乌鸦少女**
- 乌鸦叫声 `caw/caww`→**嘎**｜`Crowkyo`→**乌鸦京**

## 4. 完整工作流（三步）

### 第 1 步：翻译下一批
读取 `batch_0NN.json`（每批 300 条英文字符串的 JSON 数组），把每条翻译成简体中文，
结果写入 `translations_batch0NN.json`，格式为：

```json
{
  "英文原文（必须与 batch 文件里的字符串逐字符一致）": "中文译文"
}
```

**关键：key 必须与源文件逐字符完全一致**（含标点、空格、弯引号 ’ “ ”），否则不会匹配。

### 第 2 步：合并 + 构建补丁
```
cd "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork"
# 1) 合并全部译文源（含正文 act00b）为权威表
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe 55_merge_complete.py
# 2) 从原版备份构建（必须用 40_build_final.py，不要用旧 40_build.py）
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe 40_build_final.py --out "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/build_final"
#    （纯文本兜底：追加 --skip-font）
```
`40_build_final.py` 做三件事：
1. 从 `occurrences.json` 定位每处文本；注入时**直接读文件真实长度前缀**算区域跨度，跳过「存储字节≠英文文本」的条目（防损坏）。
2. 按 `translations_complete.json` 替换 `resources.assets` 里 Script 对象中的展示文本。
3. 用 fonttools 把 `simhei.ttf` 按译文实际用字子集化，替换 `AveriaSerifLibre-Regular`(pid 5209) 的 `m_FontData`。

> ⚠️ **永远用 `40_build_final.py`，不要用 `40_build.py`**：旧版按 `o["len"]` 算跨度，会字节错位损坏文件（已实测导致进正文闪退）。`40_build_final.py` 从 `backup_original/` 读取原版，不会在已损坏文件上二次注入。

### 第 3 步：结构校验（**每次构建后必做，最重要**）
```
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe 80_verify.py "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/build_final/resources.assets"
```
输出必须含 `BAD=0`（例如 `script_objects=23 BAD=0`）。**若 `BAD>0` 说明注入产生字节错位，绝对不能部署。**
（`80_verify.py` 逐对象走 Naninovel 元素结构：rid/className/ns/asm/flags/linehash + body，要求精确落到下一标记。
这是唯一能证明游戏能加载的测试；旧的 `60_verify_final.py` 只查中文命中、查不出结构损坏。）

### 第 4 步：部署到游戏
```
cp "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/build_final/resources.assets" \
   "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
```

## 5. 必须遵守的规则（踩过的坑）

1. **不要翻译 Naninovel 命令**。含 `wait:true` / `waitInput:false` 的整行、以及 `# Start` 这类 `#` 标签是脚本指令，翻译会破坏语法。遇到直接**跳过**该条（不写进翻译表）。
2. **必须保留富文本标签原样**：`<i>` `</i>` `<b>` `</b>` `<color=#XXXXXX>` `</color>`，只翻译标签之间的文字。
3. **变量赋值不译**：形如 `object13=false`、`cutIn01=true` 的条目跳过（todo 清单里已过滤大部分）。
4. **译文里不要残留英文单词**。每批翻译后务必跑一次质检（见第 6 节）。历史上出现过漏译混入 `lingering`、`mostly`、`exterior`、`mainly`、`simultaneously` 的情况。
5. **只用简体中文**。曾误用繁体「建築」「同時」，已修正为「建筑」「同时」。
6. **不要手动编辑 `resources.assets`**。所有修改必须通过 `40_build.py`，它采用 `set_raw_data` 写原始字节，能正确处理脚本对象（含 SerializeReference，普通反序列化会损坏文件）。

## 6. 质检方法（每批必做）

```
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe -c "
import json,glob,re
merged={}
for f in ['translations_act00b.json']+sorted(glob.glob('translations_batch*.json')):
    merged.update(json.load(open(f,encoding='utf-8')))
todo=set(json.load(open('todo_list.json')))
print('translated:',len(merged),'/',len(todo),'| remaining:',len(todo-set(merged)))
bad=[(k[:45],v[:55]) for k,v in merged.items()
     if re.search(r'[A-Za-z]{3,}( [A-Za-z]{3,}){3,}', re.sub(r'<[^>]+>','',v))]
print('untranslated residue:',len(bad))
for b in bad[:5]: print('  ',b)
"
```
目标：`untranslated residue: 0`。

## 7. 部署后验证（每次部署后做）

**最权威（必做）：结构校验，确认无字节错位损坏**
```
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe 80_verify.py "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
```
必须 `BAD=0`。此检查能抓出"进正文闪退"类损坏（旧部署文件实测 10/23 脚本对象 BAD）。

辅助检查（中文命中 / 对象数）：
```
C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe -c "
from UnityPy import Environment
env=Environment(r'G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets')
n=sum(1 for _ in env.objects)
cn=sum(1 for o in env.objects if o.type.name=='MonoBehaviour' and '尸体'.encode('utf-8') in o.get_raw_data())
print('objects:',n,'| scripts with Chinese:',cn,'|','OK' if n==11600 else 'FAIL')
"
```
`objects: 11600` 且含中文即正常。（注意：UnityPy 能加载 ≠ 游戏能加载；结构校验 `80_verify.py` 才是真凭证。）

## 8. 备份与回滚

- 原版备份：`CORPSE FACTORY_Data/backup_original/`（`resources.assets` + `resources.assets.resS`）
- 一键回滚：
  ```
  cp "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/backup_original/resources.assets" \
     "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/CORPSE FACTORY_Data/resources.assets"
  ```
- **不要动 `resources.assets.resS`！**（2026-10-29 03:43 实测更正）
  本文件早先写的「补丁已自包含、可把 `.resS` 改名为 `.bak`」是**错误的**。
  `62_check_resS.py` 实测：部署版 `resources.assets` 里仍有 **730 个对象**的
  `m_StreamData.path == 'resources.assets.resS'`，引用外部数据合计 **1,134.5 MB**（纹理/音频）。
  补丁文件只有 46 MB，与原始 47 MB 相当，说明数据**并未内联**。
  **重命名 `.resS` 会导致游戏缺纹理、缺音频甚至加载失败。**

## 9. 关键文件速查

| 文件 | 用途 |
|---|---|
| `todo_list.json` | 全部待翻译 10,611 条英文（去重后） |
| `batch_010.json` … `batch_036.json` | 分批原文，每批 300 条（**已全部翻译完毕**，仅作核对用） |
| `translations_complete.json` | **权威译文表（10,757 条，显示文本 100% 覆盖）**，由 `55_merge_complete.py` 合并所有源（含正文 `act00b`）生成；**构建时读取此文件** |
| `translations_full.json` | 旧累积表（10,608 条，缺正文 act00b），仅供核对 |
| `translations_batch001..036.json`、`translations_act00b.json` | 各批次译文（全部齐备；正文对话在 `act00b`） |
| `50_merge.py` / `51_apply.py` | 合并质检 / 由 txt 生成批次译文 |
| `55_merge_complete.py` | 合并所有译文源 → `translations_complete.json`（新增，权威） |
| `60_verify_final.py` / `61_verify_font.py` | 终局全量命中校验 / 字体 cmap 校验（辅助） |
| `80_verify.py` | **结构校验器（最重要）**：逐对象走 Naninovel 元素结构，要求精确落到下一标记；`BAD=0` 才算通过。每次构建后必跑 |
| `40_build_final.py` | **构建引擎（必须用这个）**：从 `backup_original/` 注入 + 替换字体；注入时读真实长度前缀、跳过字节不符的条目，杜绝错位损坏 |
| `40_build.py` | ⚠️ 旧版，**已废弃**（按 `o["len"]` 算跨度会字节错位 → 进正文闪退），勿用 |
| `build_final/` | 早期已验证的正文版构建（带 CJK 字体，`BAD=0`） |
| `build_ui5/` | 菜单/提示标签汉化版（正文 + UI，2,784 字字体） |
| `build_short3/` | **当前已部署版**（正文 + UI + 371 条短句，47,527,072 字节） |
| `build_final_textonly/` | 兜底纯文本构建（`--skip-font`），字体异常时备用 |
| `occurrences.json` | 34,383 处文本定位数据（pid/偏移/长度/文本）。**注意：缺 371 条短句** |
| `missing_locations2.json` | 371 条短句的 2,359 个槽位（`113_rescan.py` 生成） |
| `unique_texts.txt` | 10,823 条唯一英文原文 |

## 10. 环境

- Python：`C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe`
- 已装依赖：`UnityPy`、`fonttools`（**必须用这个解释器**，系统 python 没有这些包）

## 11. 已知待办（**翻译工作已全部完成**，以下仅剩人工收尾）

1. ~~翻译 `batch_010` ~ `batch_028`~~ —— **已完成，全部 37 个批次齐备**。
2. ~~跑构建 + 部署~~ —— **已完成**。但 2026-10-29 11:40 发现此前部署版**字节错位损坏、进正文闪退**，
   已用 `40_build_final.py` + `translations_complete.json` 从原版重建并修复，**复验 23/23 脚本对象 `BAD=0` 后重新部署**。
3. ~~菜单/提示文本汉化~~ —— **已完成**（`build_ui5`，336 处替换）。
4. ~~单词短句漏译~~ —— **已完成**（`build_short3`，371 条 / 2,359 处）。根因见 0.5 之后的
   「单词短句漏译 —— 已解决」一节：**译文早就有，缺的是注入位置**。
5. **（不要做）** 早先建议把 `resources.assets.resS` 重命名为 `.bak`——**已实测否定**：
   部署文件仍引用其中 730 个流式对象（1,134.5 MB），改名会丢纹理/音频。**保持原样**。
6. **（唯一剩下的人工验证）** 实机启动游戏，确认：
   (a) 进正文不闪退（结构校验 0 BAD）；
   (b) 中文字体显示与排版无缺字/溢出（子集 2,784 字，仅缺 U+2060 不可见连接符）；
   (c) 菜单、控制面板、短句（如 `Bitch.` → 「贱人。」）显示正常。
7. 若后续想追加润色：改 `translations_complete.json` → `113_rescan.py`（如需补短句）→
   `111_inject_missing.py` / `104_build_with_ui.py` → `80_verify.py` → 部署。
   **不要手改 `resources.assets`**。
8. 回滚层级（从近到远）：`resources.assets.prev_short` → `.prev_ui` → `.prev` →
   `backup_original/`。

## 12. 引擎内置 UI 文本在 DLL 里（2026-10-29 21:40 新增，重要！）

存档/标题界面三类**确认提示**与确认框按钮，不在 `resources.assets`，而在
`CORPSE FACTORY_Data/Managed/Elringus.Naninovel.Runtime.dll` 的 **#US 堆（UTF-16LE 字面量）**：

- `Are you sure you want to overwrite save slot?` → `确定要覆盖这个存档吗？`
- `Are you sure you want to delete save slot?` → `确定要删除这个存档吗？`
- `Are you sure you want to quit to the title screen?\nAny unsaved game progress will be lost.`
  → `确定要返回主菜单吗？\n未保存的进度将丢失。`
- 确认框按钮：`Cancel`→`取消`、`Delete`→`删除`、`Continue`→`继续`

**修改方式**：`78_patch_dll.py`（读 `Elringus.Naninovel.Runtime.dll.bak_patch` 干净备份，
**原地等长替换**——UTF-16 下中英文字符都占 2 字节，保持字符数不变、末尾用空格补齐，
长度前缀字节不动，装配体结构零破坏）。改完 DLL 字节数与备份完全一致。
**绝不要**把这些串塞进 `resources.assets` 或翻译表——它们是引擎代码串，注入脚本碰不到。

> 坑：第 3 条确认串是 **2 字节压缩长度前缀、总长 90 字符**（含 `\n` 与后半句
> "Any unsaved..."），之前只替换前 50 字符会残留英文尾巴，必须用**完整 90 字符原文**整体替换。
> 改 DLL 前务必先确认每条串的真实堆长度（`read_compressed_int` 解析前缀），
> 不要想当然按肉眼看到的句子长度替换。

备份：`Elringus.Naninovel.Runtime.dll.bak_patch`（原版未改）。如确认框还有别的英文，
先搜 DLL 的 UTF-16 串定位偏移再补，不要动 `Save`/`Load`/`Back`/`Settings` 等子串
（它们是更大串的一部分，盲目替换会误伤无关引擎文本）。
