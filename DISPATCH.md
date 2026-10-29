# 分工调度表（并行工作）

总原则：**翻译并行，集成串行**。
- `translations_batch0NN.json` 按批号命名，两人各写各的 → **天然无冲突，可并行**。
- 合并（`translations_full.json`）、构建（`40_build.py`）、部署（cp）**只由调度者（主 agent）执行**，
  帮手**不要**做这三件事，否则会互相覆盖。

## 批次分配

剩余 27 批：`batch_010.json` ~ `batch_036.json`

| 负责人 | 批次 | 数量 |
|---|---|---|
| **调度者（主 agent）** | 010, 012, 014, 016, 018, 020, 022, 024, 026, 028, 030, 032, 034, 036 | 14 批 |
| **帮手 agent** | 011, 013, 015, 017, 019, 021, 023, 025, 027, 029, 031, 033, 035 | 13 批 |

## 帮手 agent 的工作契约（务必遵守）

1. 先读 `_cnwork/HANDOFF.md`（术语表、规则、坑都在里面）。
2. 对每个分配到的 `batch_0NN.json`：Read → 翻译全部 300 条 → Write `translations_batch0NN.json`。
3. 输出格式：`{"英文原文": "中文译文"}`，**key 必须与源文件逐字符一致**。
4. **禁止**：运行 `40_build.py`、写 `translations_full.json`、复制部署 `resources.assets`、
   修改 `HANDOFF.md` 以外的任何共享文件。
5. 每批写完可自检（只检自己这个文件，不影响他人）：
   ```
   C:/Users/wknet/.workbuddy/binaries/python/envs/default/Scripts/python.exe -c "
   import json,re
   d=json.load(open('translations_batch0NN.json',encoding='utf-8'))
   bad=[(k[:40],v[:50]) for k,v in d.items() if re.search(r'[A-Za-z]{3,}( [A-Za-z]{3,}){3,}', re.sub(r'<[^>]+>','',v))]
   print('entries:',len(d),'| residue:',len(bad))
   for b in bad[:3]: print(' ',b)
   "
   ```
   目标 `residue: 0`。
6. 全部 13 批完成后，在回复里报告"已完成 011~035 奇数批"即可，调度者会来集成。

## 调度者的职责
- 翻译自己 14 批。
- 定期把帮手产出的批次文件并入 `translations_full.json`，跑构建 + 部署 + 校验。
- 更新 `HANDOFF.md` 的进度数字。
