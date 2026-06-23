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

    # Extract JSON block robustly
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
