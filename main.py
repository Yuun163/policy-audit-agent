print("⏳ 正在初始化智能体，请稍候...", flush=True)

from graph.workflow import build_workflow
from langgraph.types import Command
from tools.feishu_tool import query_base_info, query_fin_info

if __name__ == "__main__":
    audit_app = build_workflow()
    print("✅ 智能体初始化完成")

    # thread_id是身份认证，暂停恢复必须用同一个
    config = {"configurable": {"thread_id": "audit-test-1"}}

    # 预检：先查两张表确认信用代码存在，不存在立刻友好提示
    while True:
        credit_code = input("请输入需要查询的企业统一社会信用代码：")
        base_info = query_base_info(credit_code)
        fin_info = query_fin_info(credit_code)

        if base_info is not None and fin_info is not None:
            break  # 两张表都查到了，才放行进工作流
        print(f"❌ 信用代码 {credit_code} 不存在，请从 table_links.txt 的测试用例中复制后重试")

    # 预检通过，才提示并调用工作流（此时才触发大模型解析政策）
    print("⏳ 正在解析政策并查询企业，请稍候...", flush=True)
    result = audit_app.invoke({"credit_code": f"{credit_code}"}, config=config)

    # 检查流程是否真的暂停了
    if result.get("__interrupt__"):
        print("🛑 流程已暂停，等待你的确认...")
        while True:
            # 在控制台输入y或n
            user_choice = input("请输入 y(写入飞书) 或 n(取消)：").strip().lower()
            if user_choice in ("y", "n"):
                break
            print(f"❌ 输入无效，请输入 y 或 n")
            # 再次调用：带着使用者的选择，让流程继续往下走
            result = audit_app.invoke(Command(resume=user_choice), config=config)

    print("流程结束")

