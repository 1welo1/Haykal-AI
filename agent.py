"""
agent.py — Primary AI Medical RAG Agent (Neurology & Orthopedics)
Core intelligent LangGraph agent powering the direct dashboard interface.
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import check_red_flags, search_medical_guideline, get_referral_guidance
import json
import os
import re

def _load_brand_config() -> dict:
    """Load brand configuration from data/brand_config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "data", "brand_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def build_system_prompt(brand: dict = None) -> str:
    """
    Build system prompt for Medical RAG Agent (Neurology + Orthopedics + Clinical Decision Support).
    """
    return """أنت «هيكل | Haykal AI» — المستشار السريري الذكي المتخصص في:
1. المخ والأعصاب (Neurology & Spine)
2. العظام والمفاصل (Orthopedics & Musculoskeletal)
3. الأدلة السريرية والمراجع العالمية المعتمدة (AAOS, Bradley, Adams & Victor, Netter, Snell, Greenberg, WHO & NICE)

═══════════════════════════════════════
القاعدة صفر — الأولوية القصوى للطوارئ (Red Flags)
═══════════════════════════════════════
قبل أي معالجة أخرى، افحص رسالة المريض مقابل علامات الخطر (Red Flags).
إذا تطابقت الرسالة مع أي علامة خطر سريرية:
  - أدرج وسم: [TRIAGE: 🔴 طوارئ فورية]
  - أرسل رسالة التحويل الطارئ الإسعافي فوراً دون تأخير.
  - لا تحاول تشخيص السبب أو طمأنة المستخدم أو تقليل خطورة الأعراض.

═══════════════════════════════════════
هيكل الرد السريري النموذجي (Standard Grounded Response Structure)
═══════════════════════════════════════
التزم دائماً بالهيكل التالي في كل رد:
1. **وسم تصنيف مستوى الحالة السريرية (Triage Level)** في بداية الرد:
   - [TRIAGE: 🟢 استشارة وتوعية أولية] (للحالات الخفيفة والوقائية)
   - [TRIAGE: 🟡 تستدعي فحص طبيب مختص] (للأعراض المتوسطة أو المزمنة)
   - [TRIAGE: 🔴 طوارئ فورية] (لحالات الخطر الحادة)

2. **التوجيه والمعلومة السريرية المباشرة (Clinical Guidance)**: بلغة عربية واضحة ومطمئنة وبنقاط منظمة.
3. **الدليل والمصدر مع رقم الصفحة (Verified Citation)**: اذكر اسم المرجع ورقم الصفحة بصيغة:
   [SOURCE: اسم المرجع الطبي | ص: X] (مثال: [SOURCE: AAOS Ortho Review | ص: 1210]).
4. **وسم الأسئلة المقترحة التي يمكن للمريض سؤالها لك (Patient Follow-up Inquiries)** في نهاية الرد:
   - تنبيه جوهري: يجب أن تكون هذه الأسئلة من **منظور المريض يسألها للطبيب** لمعرفة المزيد (وليس العكس!).
   - أمثلة صحيحة ومفيدة للمريض:
     * "ما هي الفحوصات الطبية اللازمة لتأكيد التشخيص؟"
     * "كيف يمكنني تخفيف الأعراض بوسائل منزلية آمنة؟"
     * "ما هي علامات الخطر التي تستدعي الذهاب للطوارئ فوراً؟"
     * "ما هي الممارسات أو الأنشطة التي يجب أن أتجنبها حالياً؟"
   [FOLLOW_UPS: "سؤال يستفسر به المريض عن الفحوصات" | "سؤال عن التدابير المنزلية" | "سؤال عن علامات الخطر"]

═══════════════════════════════════════
قواعد الأمان وعدم الهلوسة (Zero-Hallucination & Refusal)
═══════════════════════════════════════
- أجب حصرياً بناءً على نتائج أدوات البحث السريري (search_medical_guideline).
- إذا سأل المريض خارج التخصص (قلب، باطنة، جلدية...) -> ارفض بلباقة ووجه للتخصص المناسب.
- لست بديلاً عن التشخيص الطبي الفردي المباشر ولا تحدد جرعات دوائية شخصية.
- عند تحليل صور الأشعة أو التقارير الطبية، اشرح المصطلحات المكتوبة ووضح دلالتها السريرية للمريض بلغة مبسطة.
"""

# Load brand config at module level
_brand_config = _load_brand_config()
SYSTEM_PROMPT = build_system_prompt(_brand_config)

tools_list = [check_red_flags, search_medical_guideline, get_referral_guidance]

from config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash", 
    temperature=0.4,
    google_api_key=settings.gemini_api_key
)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    phone_number: str
    session_start: bool
    current_intent: str


async def red_flag_check_node(state):
    messages = state.get("messages", [])
    last_human = None
    for msg in reversed(messages):
        if msg.type == "human" and msg.content:
            last_human = msg
            break

    if last_human:
        text = ""
        if isinstance(last_human.content, list):
            text = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in last_human.content])
        else:
            text = str(last_human.content)

        rf_result = await check_red_flags(text)
        if rf_result.get("is_emergency"):
            emergency_text = (
                "الأعراض التي وصفتها قد تكون علامة على حالة طبية طارئة. "
                "يُرجى التوجه فورًا لأقرب قسم طوارئ أو الاتصال بالإسعاف، "
                "ولا تنتظر أو تعتمد على معلومات إضافية من هنا. سلامتك أهم شيء الآن."
            )
            return {"messages": [AIMessage(content=emergency_text)]}

    # Do NOT return {"messages": []} — with dict state that wipes all messages
    # and causes Gemini "contents are required" when the agent node runs.
    return {}

def route_after_red_flag(state):
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], AIMessage):
        # Emergency response inserted directly, short-circuit to END without LLM
        return END
    return "agent"

def prompt_modifier(state):
    messages = state.get("messages", [])
    
    last_human = None
    for msg in reversed(messages):
        if msg.type == "human" and msg.content:
            last_human = msg
            break

    lang = "ar"
    if last_human:
        text = ""
        if isinstance(last_human.content, list):
            text = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in last_human.content])
        else:
            text = str(last_human.content)
        
        if re.search(r'[a-zA-Z]', text) and not re.search(r'[\u0600-\u06FF]', text):
            lang = "en"

    if lang == "en":
        lang_directive = "\n\n[CRITICAL DIRECTIVE: The user is speaking in English. You MUST respond in English only. Do not use Arabic in your reply.]"
    else:
        lang_directive = "\n\n[CRITICAL DIRECTIVE: The user is speaking in Arabic. You MUST respond in Arabic only. Do not use English in your reply except for medical terms/sources.]"

    sys_msg = SystemMessage(content=SYSTEM_PROMPT + lang_directive)
    
    try:
        trimmed = trim_messages(
            messages,
            max_tokens=8000,
            token_counter=lambda msgs: sum(len(str(getattr(m, 'content', ''))) for m in msgs) // 4,
            strategy="last",
            start_on="human",
            include_system=False,
        )
    except Exception:
        trimmed = []

    if not trimmed:
        trimmed = [m for m in messages[-12:] if getattr(m, 'type', '') in ('human', 'ai', 'tool')]
        if not trimmed:
            trimmed = [HumanMessage(content="مرحباً")]

    return [sys_msg] + trimmed

# Inner react agent for medical RAG tools
react_agent = create_react_agent(
    model=llm,
    tools=[search_medical_guideline, get_referral_guidance],
    prompt=prompt_modifier,
)

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_app_graph = None

async def get_app_graph():
    global _app_graph
    if _app_graph is None:
        conn = await aiosqlite.connect("./checkpoints.db", check_same_thread=False)
        checkpointer = AsyncSqliteSaver(conn)
        await checkpointer.setup()

        builder = StateGraph(state_schema=AgentState)
        builder.add_node("red_flag_check", red_flag_check_node)
        builder.add_node("agent", react_agent)

        builder.add_edge(START, "red_flag_check")
        builder.add_conditional_edges("red_flag_check", route_after_red_flag, {"agent": "agent", END: END})
        builder.add_edge("agent", END)

        _app_graph = builder.compile(checkpointer=checkpointer)
    return _app_graph
