from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from tools.feishu_tool import query_base_info, query_fin_info, add_audit_record
from datetime import datetime
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from config.settings import settings
from langchain_core.tools import tool
from langchain.agents import create_agent
from pydantic import BaseModel, Field

# 政策规则模型：按结构输出，字段名和类型焊死
class PolicyRules(BaseModel):
    """大模型解析政策后输出的规则结构"""
    latest_version: str = Field(description="最新生效的政策版本名称，如：2024年补充通知")
    tax_threshold: float = Field(description="最新纳税门槛，单位万元，必须是数字，保留1位小数点")
    support_industries: list[str] = Field(description="政策支持的行业列表")
    blacklist_industries: list[str] = Field(description="政策负面清单行业列表")
    min_rd_ratio: float = Field(description="最低研发投入占比，单位%，必须是数字，保留1位小数点")


# 初始化大模型
llm = init_chat_model(
    model="deepseek-flash",
    model_provider="deepseek",
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    extra_body={"thinking": {"type": "disabled"}} # 关闭思考模式
)


@tool
def read_policy_2023() -> str:
    """读取2023年惠企支持办法，返回政策文本内容"""
    with open("assets/policies/2023-management.md", "r", encoding="utf-8") as f:
        return f.read()

@tool
def read_policy_2024() -> str:
    """读取2024年惠企支持补充通知，返回政策文本内容"""
    with open("assets/policies/2024-notice.md", "r", encoding="utf-8") as f:
        return f.read()


# 初始化Agent
policy_agent = create_agent(
    model=llm,
    tools=[read_policy_2023, read_policy_2024]
)


# 整个审计流程全程要传递的数据，存在State里
class AuditState(TypedDict):
    # 企业统一社会信用代码
    credit_code: str
    # 企业基础信息
    company_info: Optional[dict]
    # 企业研发纳税财务数据
    fin_info: Optional[dict]
    # 审计是否通过：True通过，False不通过
    audit_pass: Optional[bool]
    # 不通过的原因，通过就写"无"
    fail_reason: Optional[str]
    # 算出来的补贴金额，单位万元
    subsidy_amount: Optional[float]
    # 命中的政策版本（比如"补充通知"）
    policy_version: Optional[str]
    # 大模型解析政策提取的规则
    policy_rules: Optional[dict]



def node_parse_policy(state: AuditState) -> dict:
    """政策解析节点：大模型自主调工具读政策，再把结果整理成结构化规则"""
    msg = policy_agent.invoke({"messages": [
        ("user", "请调用工具读取2023年原办法和2024年补充通知两份政策文件，"
                 "对比分析：1、哪份是当前最新生效版本；2、2024年相比2023年"
                 "修改了哪些关键规则（纳税门槛、支持行业、负面清单、研发占比）。"
                 "请分条清晰回答。")
    ]})
    final_answer = msg["messages"][-1].content
    print("🤖 政策解析Agent分析：")
    print(final_answer[:200])  # 只打印前200个字，防止大模型输出太长刷屏
    print("-" * 40)

    # 强制按照PolicyRules的固定结构输出
    structured_llm = llm.with_structured_output(PolicyRules)
    rules = structured_llm.invoke(
        "请根据以下政策分析结果，提取出结构化规则：\n" + final_answer +
        "\n行业名称输出要求：支持行业和负面清单，必须统一输出为以下标准词，"
        "政策原文里含义相同的词（如'信息技术服务业'→'信息技术'）一律替换成标准词：\n"
        "支持行业标准词：信息技术、先进制造、生物医药、新材料\n"
        "负面清单标准词：房地产、高污染、落后产能"
    )


    print("✅ 大模型提取的规则：")
    print(rules.model_dump())  # 把规则对象转成普通字典，
    print("-" * 40)

    # 规则存进State；政策版本由check_status节点决定
    return {
        "policy_rules": rules.model_dump()
    }


def node_fetch_company(state: AuditState) -> dict:
    """节点：根据用户输入的信用代码，去飞书查企业基础信息"""
    credit_code = state["credit_code"]
    company_info = query_base_info(credit_code)

    if not company_info:
        return {
            "company_info": None,
            "audit_pass": False,
            "fail_reason": f"未查询到【{credit_code}】企业的相关信息，请重新输入企业的信用代码！"
        }

    return {
        "company_info": company_info
    }



def node_fetch_fin(state: AuditState) -> dict:
    """节点：根据信用代码，去飞书查企业的研发纳税财务数据"""
    credit_code = state["credit_code"]
    fin_info = query_fin_info(credit_code)

    if not fin_info:
        return {
            "fin_info": None,
            "audit_pass": False,
            "fail_reason": "未查询到该企业的完整底账信息，请检查企业信用代码是否与底账数据完全一致！"
        }

    return {
        "fin_info": fin_info
    }



def node_check_status(state: AuditState) -> dict:
    """节点：检查企业经营状态
    企业经营状态是「注销」，默认依据政策版本="原办法版"、审计结果=条件不符
    """
    # 从企业基础信息里拿经营状态
    status = state["company_info"]["经营状态"]

    if status == "注销":
        return {
            "audit_pass": False,
            "fail_reason": "审计不通过：企业经营状态为注销，不予扶持。",
            "policy_version": "原办法版"  # 注销企业命中原办法版
        }

    # 非注销企业：按2024现行政策审计，版本统一为"补充通知版"
    return {
        "policy_version": "补充通知版"
    }



def node_check_industry(state: AuditState) -> dict:
    """节点：行业合规校验
    支持行业和负面清单，从大模型提取的规则里读，不写死
    """
    # 从企业信息里拿行业分类
    industry = state["company_info"]["行业分类"][0]["text"]
    # 从State里读大模型解析政策提取的规则
    rules = state["policy_rules"]

    # 第一关：判断是不是在支持目录里
    support_industries = rules["support_industries"]
    if industry not in support_industries:
        return {
            "audit_pass": False,
            "fail_reason": f"审计不通过：所属行业（{industry}）不在政策支持目录内。",
        }

    # 第二关：判断是不是在负面清单里
    blacklist = rules["blacklist_industries"]
    if industry in blacklist:
        return {
            "audit_pass": False,
            "fail_reason": f"审计不通过：所属行业（{industry}）属于政策负面清单，不予扶持。",
        }

    return {}




def node_check_tax(state: AuditState) -> dict:
    """节点：纳税门槛校验
    2024年补充通知规则：年度纳税总额≥15万元，不满足就熔断
    """
    # 从飞书返回的财务数据里，把纳税额拿出来，转成数字
    # 飞书返回的数字是字符串结构
    tax_str = state["fin_info"]["年度纳税总额(万元)"]
    tax_amount = float(tax_str)

    # 2024年最新门槛是15万，比2023年的20万降了
    rules = state["policy_rules"]
    tax_threshold = rules["tax_threshold"]

    if tax_amount < tax_threshold:
        return {
            "audit_pass": False,
            "fail_reason": "审计不通过：纳税总额未达到最新政策门槛。",
        }

    return {}



def node_check_rd_ratio(state: AuditState) -> dict:
    """节点：研发投入占比校验
    2024年政策要求：研发投入占营收比例≥5%
    """
    # 从财务数据里拿研发占比，字段里带%号，先转成纯数字
    rd_ratio_str = state["fin_info"]["研发投入比例"][0]["text"]
    # 把%去掉，转成float数字
    rd_ratio = float(rd_ratio_str.replace("%", ""))

    rules = state["policy_rules"]
    min_rd_ratio = rules["min_rd_ratio"]

    if rd_ratio < min_rd_ratio:
        return {
            "audit_pass": False,
            "fail_reason": "审计不通过：研发投入占营业收入比例未达到政策要求。",
        }

    return {}



def node_calc_subsidy(state: AuditState) -> dict:
    """节点：硬代码计算补贴金额，禁止大模型算钱
    赛题公式：
    - 大型企业（注册资本>1000万）：补贴 = 研发投入*0.2 + 纳税额*0.1
    - 中小微企业（注册资本≤1000万）：补贴 = 研发投入*0.3 + 纳税额*0.15
    """
    # 从企业信息里拿注册资本，判断企业规模
    reg_capital = float(state["company_info"]["注册资本(万元)"])
    # 从财务数据里拿研发投入和纳税额
    rd_expense = float(state["fin_info"]["研发投入金额(万元)"])
    tax_amount = float(state["fin_info"]["年度纳税总额(万元)"])

    # 按赛题公式计算补贴
    if reg_capital > 1000:
        # 大型企业
        subsidy = rd_expense * 0.2 + tax_amount * 0.1
    else:
        # 中小微企业
        subsidy = rd_expense * 0.3 + tax_amount * 0.15

    return {
        "audit_pass": True,
        "fail_reason": "无",
        "subsidy_amount": round(subsidy, 1),  # 保留1位小数，单位万元
    }



def node_show_result(state: AuditState) -> dict:
    """节点：把审计结果展示给用户"""
    company_name = state["company_info"]["企业名称"][0]["text"]
    print("=" * 40)
    print(f"审计完成！\n企业：{company_name}")
    print(f"审计结果：{'审核通过' if state['audit_pass'] else '条件不符'}")
    print(f"补贴金额：{state['subsidy_amount'] if state['audit_pass'] else 0} 万元")
    if not state["audit_pass"]:
        print(f"失败原因：{state['fail_reason']}")
    print("=" * 40)
    return {}


def node_confirm_write(state: AuditState) -> dict:
    """节点：暂停流程，等用户确认是否写入飞书"""
    # 流程在这里暂停，重放时这行之前没有print，所以不会重复显示
    choice = interrupt("审计完成，是否需要将结果添加到飞书多维表格？(y=添加 / n=取消)")

    if choice == "y":
        company_name = state["company_info"]["企业名称"][0]["text"]
        audit_data = {
            "企业名称": company_name,
            "依据政策版本": state["policy_version"],
            "审计结果": "审核通过" if state["audit_pass"] else "条件不符",
            "不符合条款说明": state["fail_reason"],
            "预估补贴金额（万元）": state["subsidy_amount"] if state["audit_pass"] else 0,
            "最后核验时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        add_audit_record(audit_data)
        print("✅ 已成功写入飞书审计表")
    else:
        print("已取消写入，审计结束")

    return {}


def route_after_check(state:AuditState) -> dict:
    """
    条件路由：判断流程要不要熔断
    如果前面节点已经判定audit_pass=False，直接跳end
    否则继续走下一个校验节点
    """
    if state.get("audit_pass") is False:
        return "end"
    return "next"





# 把所有节点串成状态机
def build_workflow():
    # 1. 初始化状态图，传入AuditState结构
    workflow = StateGraph(AuditState)

    # 2. 注册所有节点
    workflow.add_node("parse_policy", node_parse_policy)
    workflow.add_node("fetch_company", node_fetch_company)
    workflow.add_node("fetch_fin", node_fetch_fin)
    workflow.add_node("check_status", node_check_status)
    workflow.add_node("check_industry", node_check_industry)
    workflow.add_node("check_tax", node_check_tax)
    workflow.add_node("check_rd", node_check_rd_ratio)
    workflow.add_node("calc_subsidy", node_calc_subsidy)
    workflow.add_node("show_result", node_show_result)
    workflow.add_node("confirm_write", node_confirm_write)

    # 3. 定义流程顺序：从START开始，END结束
    workflow.add_edge(START, "parse_policy")
    workflow.add_edge("parse_policy", "fetch_company")
    workflow.add_edge("fetch_company", "fetch_fin")

    # 开始校验
    workflow.add_edge("fetch_fin", "check_status")
    workflow.add_conditional_edges(
        "check_status",
        route_after_check,
        {
            "next": "check_industry",
            "end": "show_result"
        }
    )

    workflow.add_conditional_edges(
        "check_industry",
        route_after_check,
        {
            "next": "check_tax",
            "end": "show_result"
        }
    )

    workflow.add_conditional_edges(
        "check_tax",
        route_after_check,
        {
            "next": "check_rd",
            "end": "show_result"
        }
    )

    workflow.add_conditional_edges(
        "check_rd",
        route_after_check,
        {
            "next": "calc_subsidy",
            "end": "show_result"
        }
    )

    workflow.add_edge("calc_subsidy", "show_result")
    workflow.add_edge("show_result", "confirm_write")
    workflow.add_edge("confirm_write", END)

    # 编译成可执行的状态机
    checkpointer = InMemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app
