from graph.workflow import build_workflow
from langgraph.types import Command

if __name__ == "__main__":
    audit_app = build_workflow()

    # thread_id是身份认证，暂停恢复必须用同一个
    config = {"configurable": {"thread_id": "audit-test-1"}}

    credit_code = input("请输入需要查询的企业统一社会信用代码：")
    # 调用时：流程跑到"人工确认"节点会暂停
    result = audit_app.invoke({"credit_code": f"{credit_code}"}, config=config)

    # 检查流程是否真的暂停了
    if result.get("__interrupt__"):
        print("🛑 流程已暂停，等待你的确认...")
        # 在控制台输入y或n
        user_choice = input("请输入 y(写入飞书) 或 n(取消)：")
        # 再次调用：带着使用者的选择，让流程继续往下走
        result = audit_app.invoke(Command(resume=user_choice), config=config)

    print("流程结束")

