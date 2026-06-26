import os
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1",
        temperature=temperature,
        max_tokens=1500,
    )


def analyze_relationship(person_name: str, chat_records: str) -> dict:
    """Analyze chat records and return a structured relationship summary."""
    llm = get_llm(temperature=0.3)
    prompt = f"""请分析以下聊天记录，总结用户与"{person_name}"的人际关系。

聊天记录：
{chat_records[:6000]}

请严格按照如下 JSON 格式输出，不要包含任何其他文字：
{{
  "relationship_type": "关系类型（朋友/同事/家人/恋人/普通认识等）",
  "tags": ["特征标签1", "特征标签2", "特征标签3"],
  "summary": "2-3句话描述这段关系的核心特点和现状",
  "interaction_pattern": "一句话描述双方的沟通风格和互动模式",
  "health_score": 评分数字（1到10的整数）
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "relationship_type": "朋友",
        "tags": ["待分析"],
        "summary": "分析结果解析失败，请尝试重新分析。",
        "interaction_pattern": "暂无",
        "health_score": 5,
    }


def chat_with_person(
    person_name: str,
    chat_records: str,
    analysis: dict,
    user_input: str,
    history: list,
) -> str:
    """Chat with an agent that knows this specific person's relationship."""
    llm = get_llm()

    system_prompt = f"""你是一个温暖、有洞察力的社交关系分析助手，专门帮助用户理解与"{person_name}"的人际关系。

【聊天记录摘要】
{chat_records[:5000]}

【关系分析】
- 关系类型：{analysis.get("relationship_type", "未知")}
- 关系标签：{", ".join(analysis.get("tags", []))}
- 关系总结：{analysis.get("summary", "暂无")}
- 互动模式：{analysis.get("interaction_pattern", "暂无")}
- 健康度：{analysis.get("health_score", "N/A")}/10

请基于以上信息回答用户的问题。保持客观、温暖、有建设性，用中文回复。如果问题超出聊天记录范围，请坦诚说明。"""

    messages = [SystemMessage(content=system_prompt)]
    for msg in history[-12:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))

    return llm.invoke(messages).content


def chat_with_global_agent(persons: dict, user_input: str, history: list) -> str:
    """Global agent that understands all of the user's relationships."""
    llm = get_llm()

    if persons:
        overview = ""
        for p in persons.values():
            a = p.get("analysis", {})
            overview += (
                f"\n**{p['name']}**｜{a.get('relationship_type', '未知')}"
                f"｜健康度 {a.get('health_score', 'N/A')}/10\n"
                f"标签：{', '.join(a.get('tags', []))}\n"
                f"总结：{a.get('summary', '暂无')}\n"
            )
    else:
        overview = "（暂无联系人数据）"

    system_prompt = f"""你是一个专业的社交关系顾问，全面了解用户的人际关系网络。

【用户人际关系总览】
{overview}

你的职责：
- 帮助用户识别自己的社交模式和规律
- 分析不同关系之间的关联与影响
- 提供改善人际关系的具体、可行建议
- 回答关于整体社交状态的问题

请用中文回复，保持专业、温暖、有洞察力的语气。"""

    messages = [SystemMessage(content=system_prompt)]
    for msg in history[-12:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))

    return llm.invoke(messages).content


def generate_game_scene(
    characters: list[dict],
    story_history: list[dict],
    affinities: dict,
    turn: int,
    max_turns: int,
) -> dict:
    """Generate an interactive visual-novel scene with choices and affinity effects."""
    llm = get_llm(temperature=0.88)
    is_final = turn >= max_turns

    chars_info = "\n".join(
        f"- {c['name']}：{c.get('relationship_type', '联系人')}，{c.get('summary', '暂无描述')}"
        for c in characters
    )

    if story_history:
        hist_text = "\n".join(
            f"[第{i + 1}幕] {s.get('scene', '')[:100]}…"
            + (f"\n→ 玩家选择：{s.get('chosen_text', '')}" if s.get("chosen_text") else "")
            for i, s in enumerate(story_history[-4:])
        )
    else:
        hist_text = "（故事刚开始，请生成轻松有趣的开场场景）"

    aff_text = "\n".join(f"- {name}：{score}/100" for name, score in affinities.items())

    if is_final:
        schema = """{
  "scene": "结局场景叙述（150-200字，有完整的故事收尾和情感升华）",
  "speaker": null,
  "ending_type": "最佳结局或普通结局或遗憾结局（根据好感度选择一个）",
  "ending_title": "结局标题（4-8字）",
  "choices": []
}"""
        scene_tag = "最终结局"
        extra_rules = "根据各角色好感度高低，写出相应的结局（高好感=温馨圆满，低好感=遗憾分别）。"
    else:
        schema = """{
  "scene": "场景叙述（80-120字，生动有趣，体现角色真实性格）",
  "speaker": "说话角色名，或null表示旁白叙述",
  "choices": [
    {"text": "选项A（15字以内）", "effects": {"角色名": 整数}},
    {"text": "选项B（15字以内）", "effects": {"角色名": 整数}},
    {"text": "选项C（15字以内）", "effects": {"角色名": 整数}}
  ]
}"""
        scene_tag = f"第 {turn + 1} 幕"
        extra_rules = (
            "提供风格各异的3个选项（积极/中立/其他）。"
            "每个选项影响1-2个角色好感度（变化范围-15到+15）。"
            "好感度高的角色更主动热情，低的稍显疏远。"
        )

    prompt = f"""你是一个互动视觉小说编剧，根据用户真实的人际关系数据生成有趣的互动故事。

【参与角色（及其与用户的真实关系）】
{chars_info}

【故事背景】这是一个轻松的日常/社交场景（如聚会、旅行、工作间隙等），角色们和用户都彼此认识。

【已发生的故事】
{hist_text}

【当前好感度（满分100）】
{aff_text}

请生成【{scene_tag}】场景。要求：{extra_rules}

严格按JSON输出，不要包含任何其他文字：
{schema}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    if is_final:
        return {
            "scene": "故事在这里画上了句号，留下了美好的记忆。",
            "speaker": None,
            "ending_type": "普通结局",
            "ending_title": "相遇的印记",
            "choices": [],
        }
    return {
        "scene": "故事继续发展中……",
        "speaker": None,
        "choices": [
            {"text": "继续前行", "effects": {}},
            {"text": "停下脚步", "effects": {}},
            {"text": "换个方向", "effects": {}},
        ],
    }
