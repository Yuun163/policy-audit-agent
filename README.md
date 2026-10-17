# 惠企政策精准匹配与申报审计智能体

基于 **LangChain 1.2 + LangGraph** 实现的政务智能体，从蓝桥杯国赛 FastGPT 低代码方案**迁移为纯代码工程**，完成 "政策解析 → 企业画像聚合 → 合规审计 → 补贴测算 → 人工确认 → 飞书留痕" 的完整闭环。

## 赛题背景

本项目源自第十七届蓝桥杯大赛人工智能赛（智能体开发）国赛赛题《智慧政务：惠企政策精准匹配与申报审计智能体》。

业务场景：政府对科技型企业申报的惠企补贴进行自动化审计 —— 依据 2023 版《管理办法》与 2024 版《补充通知》

两版政策，对企业依次执行行业准入、负面清单、纳税门槛、研发占比四项审计，按规定公式测算补贴金额，

并将审计结论（版本 / 结果 / 金额 / 原因）留痕至飞书多维表格。

政策要点：2024 补充通知仅修改两项（纳税门槛 20 万→15 万、新增 "先进制造" 行业），其余条款沿用 2023 原办法；

审计以最新政策为准；经营状态为 "注销" 的企业按原办法直接否决（依据政策版本 = 原办法版）。

## 技术栈



* **Python 3.12** / Conda 环境管理

* **LangChain 1.2**（`init_chat_model` 统一模型接入、`create_agent` 构建工具调用型 Agent、`with_structured_output` 结构化输出）

* **LangGraph 1.1**（StateGraph 状态机、条件路由熔断、interrupt 人工确认、InMemorySaver 断点续跑）

* **Pydantic 2.x**（结构化输出模型 `PolicyRules`）+ **pydantic-settings**（.env 统一配置）

* **DeepSeek API**（大模型） + **飞书开放平台 API**（多维表格数据存取）

## 项目结构



```
policy-audit-agent/
├── main.py                # 测试入口（invoke + interrupt 确认 + Command 续跑）
├── config/settings.py     # pydantic-settings 配置类（全部敏感配置走 .env）
├── tools/feishu_tool.py   # 飞书工具层：token缓存 / 查企业 / 查财务 / 写审计
├── graph/workflow.py      # 核心状态机：10节点 + 4处熔断 + 政策解析Agent
└── assets/policies/       # 政策知识库（赛题政策 URL 本地化固化）
```

## 核心流程（LangGraph 状态机）



```
parse_policy → fetch_company → fetch_fin → check_status → check_industry
   → check_tax → check_rd → calc_subsidy → show_result → confirm_write → END
```



* `parse_policy`：**Agent 自主调用工具**读取两份政策原文，`with_structured_output` 强制输出结构化规则（纳税门槛 / 支持行业 / 负面清单 / 研发占比），替换掉写死的规则值；

* `check_status`：注销企业直接熔断（依据政策版本 = **原办法版**）；

* `check_industry / check_tax / check_rd`：从 `state["policy_rules"]` 读取大模型提取的规则逐项校验，任一不通过即**熔断**（跳过补贴测算）；

* `calc_subsidy`：**代码硬算**补贴金额（赛题红线：大模型禁止生成金额）；

* `confirm_write`：interrupt 人工确认后写入飞书审计表。

## 关键设计决策



1. **混合架构**：状态机钉死刚性流程（顺序、熔断、金额计算），Agent 只负责语义理解（政策解析）。LLM 擅长语义、不擅长保证流程确定性 —— 关键业务逻辑交给代码，是 "确定性优先" 的工程判断。

2. **结构化输出防幻觉**：`with_structured_output(PolicyRules)` 强制模型按固定结构返回规则，配合 Pydantic 校验，防止自由发挥。

3. **单一数据来源**：政策版本只由 `check_status` 节点设置（注销 = 原办法版，其他 = 补充通知版），规则只由 `parse_policy` 写入，避免节点间覆盖冲突。

4. **Human-in-the-loop**：写入飞书前必须人工确认，保证审计留痕可追溯。

5. **配置安全**：App ID/Secret/ 表 ID/API Key 全部抽离到 `.env`，`.env.example` 提供模板，密钥不入库。

## 赛题红线遵守



* ✅ 补贴金额由代码节点按公式硬算：大型企业（注册资本 > 1000 万）= 研发 ×0.2 + 纳税 ×0.1；中小微 = 研发 ×0.3 + 纳税 ×0.15

* ✅ 审计顺序固定：行业 → 负面清单 → 纳税门槛 → 研发占比，前置不通过立即熔断

* ✅ "依据政策版本" 仅两个合法值：**原办法版 / 补充通知版**（注销→原办法版，其他→补充通知版）

* ✅ 统一提示语规范，异常场景（企业不存在 / 权限不足等）友好返回

## 快速开始



```
# 1. 创建 Conda 环境并安装依赖
conda create -n langchain1.2 python=3.12 -y
conda activate langchain1.2
pip install -r requirements-prod.txt

# 2. 配置 .env（参考 .env.example）
#    填入飞书 App ID/Secret、多维表格三张表 ID、DeepSeek API Key

# 3. 运行
python main.py
# 输入企业统一社会信用代码 → 观察政策解析 → 输入 y/n 确认写入飞书
```

> 注：需自行创建飞书自建应用（开通 bitable 权限）与多维表格（字段名见赛题附件 2/3/4），并将应用添加为表格 "可编辑" 协作者；DeepSeek Key 需为本人账号且有余量。

## 测试成果展示（飞书多维表格・只读链接）



```
输入：企业基础信息表（行业/注册资本/经营状态）+ 企业研发纳税表（纳税/研发/占比）
输出：企业财务审计表（智能体写入：版本/结果/金额/原因）
```



* 企业基础信息表：[https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tble3EWdIRbaDubm\&view=vewesuoZhq](https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tble3EWdIRbaDubm\&view=vewesuoZhq)

* 企业研发与纳税信息表：[https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tbllC2FSiaMv0E5I\&view=vewerLurxM](https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tbllC2FSiaMv0E5I\&view=vewerLurxM)

* 企业财务审计表：[https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tblItpVjQtrmauXJ\&view=vewNv7FTIR](https://ocnil3bpxcun.feishu.cn/base/I0IKbqEdTaZO51sLbIic4dLKnIh?table=tblItpVjQtrmauXJ\&view=vewNv7FTIR)

## 测试结果（赛题 7 个用例全通过）



| 企业    | 版本    | 结果        | 验证点            |
| ----- | ----- | --------- | -------------- |
| 极光创新  | 补充通知版 | 通过 20.7 万 | 中小微公式          |
| 数字科技  | 原办法版  | 条件不符      | 注销熔断           |
| 金地地产  | 补充通知版 | 条件不符      | 负面清单           |
| 宏图重工  | 补充通知版 | 条件不符      | 研发 4.2%<5%     |
| 蓝天生物  | 补充通知版 | 条件不符      | 纳税 12 万 < 15 万 |
| 晨曦新材料 | 补充通知版 | 通过 32.2 万 | 大型公式           |
| 蓝山重工  | 补充通知版 | 通过 81.0 万 | 先进制造 + 大型      |

## 未来扩展



* **Milvus 向量库 RAG**：政策文件多版本管理、企业画像语义检索。