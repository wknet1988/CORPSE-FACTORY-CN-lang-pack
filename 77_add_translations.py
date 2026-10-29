#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build translations_add.json for the 267 previously-missed display strings.
Only genuine DISPLAY text is translated; type-qualifiers, asset paths, lorem
ipsum, logic expressions, and name lists are intentionally omitted (the build
simply skips strings not present in the translation map, so omitting them is safe).
Date variable displays (Text_Month="...";...) are transformed keeping the
variable KEYS and translating only the VALUES.
"""
import json, re

HERE = "G:/SteamLibrary/steamapps/common/CORPSE FACTORY/_cnwork"
occ = json.load(open(f"{HERE}/occurrences_v2.json", encoding="utf-8"))
tr = json.load(open(f"{HERE}/translations_complete.json", encoding="utf-8"))

# unique new strings (display strings not already translated)
seen = {}
for o in occ:
    seen.setdefault(o["text"], True)
new = [t for t in seen if t not in tr]
print("new unique display strings:", len(new))

MONTHS = {"January":"1月","February":"2月","March":"3月","April":"4月","May":"5月",
          "June":"6月","July":"7月","August":"8月","September":"9月","October":"10月",
          "November":"11月","December":"12月"}
DAYS = {"MONDAY":"星期一","TUESDAY":"星期二","WEDNESDAY":"星期三","THURSDAY":"星期四",
        "FRIDAY":"星期五","SATURDAY":"星期六","SUNDAY":"星期日"}
TIMES = {"Morning":"早晨","Afternoon":"下午","Evening":"傍晚","Night":"夜晚"}

def transform_date(s):
    out = []
    for part in s.split(";"):
        if "=" not in part:
            out.append(part); continue
        k, v = part.split("=", 1)
        v = v.strip('"')
        if k == "Text_Month":
            m = re.match(r"(\w+)\s+(\d+)", v)
            if m:
                v = MONTHS.get(m.group(1), m.group(1)) + m.group(2) + "日"
        elif k == "Text_Day":
            v = DAYS.get(v, v)
        elif k == "Text_Time":
            v = TIMES.get(v, v)
        out.append(f'{k}="{v}"')
    return ";".join(out)

# ---- manual display-text translations (keys MUST exactly match occurrence text) ----
MANUAL = {
    'JUNE 2 TUESDAY MIDNIGHT / EARLY MORNING': '6月2日 星期二 午夜／清晨',
    'Forge a bond with Tomoe.': '与智惠建立羁绊。',
    'NORIKO: “Sex can be wonderful. But it can be scary as well.”': '纪子：「性爱有时很美妙，但也可能很可怕。」',
    'The type of <color=#7e67b8><b>girl</b></color> that always has the best grades, but never really has any friends.':
        '那种<color=#7e67b8><b>女生</b></color>——成绩总是最好，却从没什么朋友。',
    'She seems to have a new sugar daddy every few weeks, some poor old fool that she strings along and milks dry.':
        '她似乎每隔几周就换一个干爹，都是些被她玩弄、榨干的可怜老蠢货。',
    'She must be nearing thirty, but all her friends are still in senior high school. It’s more than a little weird.':
        '她肯定快三十了，可她的朋友还都在念高中。这实在有点诡异。',
    'Platform = {G_Platform}.': '平台 = {G_Platform}。',
    '--- END PLATFORM BUTTONS': '--- 平台按钮结束',
    'Change title screen to version 0': '将标题画面切换为版本 0',
    'Change title screen to version 2': '将标题画面切换为版本 2',
    'Change title screen to version 3': '将标题画面切换为版本 3',
    'Change title screen to version 4': '将标题画面切换为版本 4',
    'Start rain over 2 seconds': '在 2 秒内开始下雨',
    'REQUIREMENTS: AOI (ANY), TOMOE 1, SHINYA 1': '解锁条件：葵（任意）、智惠 1、真也 1',
    'ENDING D - BONUS (can be unlocked alongside A, B or C)': '结局 D - 追加结局（可与 A、B 或 C 同时解锁）',
    'REQUIREMENTS: TOMOE 1, SHINYA 1': '解锁条件：智惠 1、真也 1',
    '(THIS SCENE IS INSERTED BEFORE THE OTHER UNLOCKED ENDING)': '（此场景插入在其他已解锁结局之前）',
    'REQUIREMENTS: AOI 1, TOMOE 1, SHINYA 1': '解锁条件：葵 1、智惠 1、真也 1',
    'Need to view all CGs in game by following above routes': '需按上述路线通关，以查看游戏内全部 CG',
    'REQUIREMENTS: AOI 0, TOMOE 1': '解锁条件：葵 0、智惠 1',
    'REQUIREMENTS: AOI 0, TOMOE 0': '解锁条件：葵 0、智惠 0',
    '"\\>> Downloading image attachment <<\\"    wait:true waitInput:false':
        '"\\>> 正在下载图片附件 <<\\"    wait:true waitInput:false',
    'Tomoe = {TomoeRoute} & Shinya = {ShinyaRoute}.': '智惠 = {TomoeRoute} 且 真也 = {ShinyaRoute}。',
    'Aoi = {AoiRoute} & Tomoe = {TomoeRoute} & Shinya = {ShinyaRoute}.':
        '葵 = {AoiRoute} 且 智惠 = {TomoeRoute} 且 真也 = {ShinyaRoute}。',
    'I can be critical about other parts of my body, but I’ll never complain about my wings, caw.':
        '我可以对身体其他部位挑挑拣拣，但翅膀我绝不会抱怨，嘎。',
    'With or without feathers, I think they look great, caw caww.': '无论有没有羽毛，我都觉得它们很好看，嘎嘎。',
    'Mother used to tell me I inherited her wings, and my big sister inherited Father’s wings.':
        '母亲曾告诉我，我继承了她的翅膀，而姐姐继承了父亲的翅膀。',
    'Mother doesn’t fly too well anymore, and that might be something I have to also worry about in the future.':
        '母亲现在飞得不太好，而这可能也是我将来要担心的。',
    'But for now, my wings are perfect, caw, and I couldn’t be happier with them.':
        '但至少现在，我的翅膀完美无瑕，嘎，我再也满意不过了。',
    'My alarm goes off at 6:00am. The early bird catches the worm, after all, caw.':
        '我的闹钟在早上6点响起。毕竟早起的鸟儿有虫吃，嘎。',
    'I skip breakfast because I don’t want to get my beak dirty by digging in the dirt.':
        '我不吃早饭，因为不想在刨土时把喙弄脏。',
    'The static drone of workspace <color=#b96890><b>noise</b></color> fills my ear holes.':
        '工作室里<color=#b96890><b>噪音</b></color>的静电嗡鸣灌满了我的耳孔。',
    'Unlock the bonus ending.': '解锁追加结局。',
    'Unlock the false ending.': '解锁虚假结局。',
    'Scroll Down': '向下滚动',
    'Scroll Up': '向上滚动',
    'Master Volume': '主音量',
    'BGM Volume': '背景音乐音量',
    'SFX Volume': '音效音量',
    'Voice Volume': '语音音量',
    'LAZY STUDENT': '懒散的学生',
    'TIRED STUDENT': '疲惫的学生',
    'SECURITY GUARD': '保安',
    'NEWS ANCHOR': '新闻主播',
    'UNKNOWN CALLER': '未知来电者',
    'Mouse Scrollwheel': '鼠标滚轮',
    'Mouse X': '鼠标 X',
    'Mouse Y': '鼠标 Y',
    'Smiling face with smiling eyes': '微笑眯眼脸',
    'Grinning face': '咧嘴笑脸',
    'Face with tears of joy': '笑出眼泪的脸',
    'Skip mode:': '跳过模式：',
    'Option A': '选项 A',
    'Option B': '选项 B',
    'Option C': '选项 C',
    'Memory usage text': '内存占用文本',
    'Screen mode:': '画面模式：',
    'Author Name': '作者名',
    'Select a script to play': '选择要播放的脚本',
    'QUICK LOAD': '快速读取',
    'EXTERNAL SCRIPTS': '外部脚本',
    'SCRIPT NAVIGATOR': '脚本导航器',
    'File {N} - {D}': '文件 {N} - {D}',
    'Music volume:': '音乐音量：',
    'Effects volume:': '音效音量：',
    'Choice text': '选项文本',
    'Master volume:': '主音量：',
    'Voice volume:': '语音音量：',
    'Message speed:': '文字速度：',
    'CG GALLERY': 'CG 鉴赏',
    'Crow Factory Illustration': '乌鸦工厂 插画',
    'Actor Name': '演员名',
    'November 21': '11月21日',
    'Composed by Alec Shea\nLyrics/Vocals - Emi Evans\nPiano - Rob Kovacs\nCello - Mason Lieberman\nMix Engineer - Masahiro Aoki\nScore Engraving Assistance - Thomas Misson':
        '作曲：Alec Shea\n作词／演唱：Emi Evans\n钢琴：Rob Kovacs\n大提琴：Mason Lieberman\n混音工程：Masahiro Aoki\n总谱刻版协助：Thomas Misson',
    'RIVER CROW STUDIO': '河流乌鸦工作室',
    'Font size:': '字体大小：',
    'Voice language:': '语音语言：',
    'Kickstarter Backers': 'Kickstarter 支持者',
    'BUY SOUNDTRACK': '购买原声碟',
    'Sound effects used under license from Fusehive\nDeveloped using Unity\nDeveloped with Naninovel':
        '音效经 Fusehive 授权使用\n使用 Unity 开发\n使用 Naninovel 开发',
    'Discard your sense of morality and enter the world of Corpse Factory.':
        '抛下你的道德感，进入尸体工厂的世界。',
    'Character Art\nEvent Illustration': '角色立绘\n事件插画',
    'Original Soundtrack': '原声音乐',
    'CROW FACTORY': '乌鸦工厂',
    'NEW GAME': '新游戏',
    'QUICK SAVE': '快速保存',
    'Confirmation message.': '确认信息。',
    'Tip category': '提示分类',
    'Background Illustration': '背景插画',
    "Theme Song 'Strange Flower' Credits": "主题曲《异样之花》制作人员",
    'Developed by': '开发',
    'Play Script Button Prototype': '播放脚本按钮原型',
    'Tip Title': '提示标题',
    'Lead Developer\nStory': '主程序\n剧本',
    'Auto delay:': '自动延迟：',
    'Detective Fujikawa': '藤川侦探',
    'SKIP MOVIE': '跳过影片',
    'Enter text...': '输入文本……',
    'Additional Resources': '附加资源',
    'KenjiName="SECURITY GUARD"': 'KenjiName="保安"',
}

DATE_RE = re.compile(r'^Text_(?:Month|Day|Time)=')

add = {}
warn = []
for t in new:
    if DATE_RE.match(t):
        add[t] = transform_date(t)
    elif t in MANUAL:
        add[t] = MANUAL[t]
    else:
        # skipped (non-display / keep-original)
        continue

# sanity: ensure every MANUAL key actually exists in `new` (catch typos)
for k in MANUAL:
    if k not in new:
        warn.append(k)

print(f"translated this batch: {len(add)}")
print(f"MANUAL keys NOT found in occurrences (typo?): {len(warn)}")
for w in warn:
    print("   WARN MISSING KEY:", repr(w)[:80])

# merge
merged = dict(tr)
merged.update(add)
json.dump(merged, open(f"{HERE}/translations_complete.json", "w", encoding="utf-8"),
           ensure_ascii=False)
json.dump(add, open(f"{HERE}/translations_add.json", "w", encoding="utf-8"),
          ensure_ascii=False)

skipped = [t for t in new if t not in add]
print(f"\nSKIPPED (not translated, {len(skipped)}):")
for s in skipped:
    print("   SKIP", repr(s)[:90])
