import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import requests
from tools.feishu_tool import get_feishu_token

API_BASE = "https://open.feishu.cn/open-apis"
# 三张表各自需要新增的字段
TABLE_FIELDS = {
    "企业基础信息表": [
        {
            "field_name": "企业名称",
            "type": 1
        },
        {
            "field_name": "统一社会信用代码(Key)",
            "type": 1
        },
        {
            "field_name": "行业分类",
            "type": 1
         },
        {
            "field_name": "注册资本(万元)",
            "type": 2,
            "property": {
                "formatter": "0.0"
            }
        },
        {
            "field_name": "经营状态",
            "type": 3,
            "property": {
                "options": [
                    {"name": "在营"},
                    {"name": "注销"}
                ]
            }
         },
    ],

    "企业研发纳税信息表": [
        {
            "field_name": "统一社会信用代码(Key)",
            "type": 1
        },
        {
            "field_name": "年度纳税总额(万元)",
            "type": 2,
            "property": {
                "formatter": "0.0"
            }
        },
        {
            "field_name": "研发投入金额(万元)",
            "type": 2,
            "property": {
                "formatter": "0.0"
            }
        },
        {
            "field_name": "研发投入比例",
            "type": 1
        },
        {
            "field_name": "专利数量",
            "type": 2,
            "property": {
                "formatter": "0.0"
            }
        },
    ],

    "企业财务审计表": [
        {
            "field_name": "企业名称",
            "type": 1
        },
        {
            "field_name": "依据政策版本",
            "type": 3,
            "property": {
                "options": [
                    {"name": "原办法版"},
                    {"name": "补充通知版"}
                ]
            }
        },
        {
            "field_name": "审计结果",
            "type": 3,
            "property": {
                "options": [
                    {"name": "审核通过"},
                    {"name": "条件不符"}
                ]
            }
        },
        {
            "field_name": "不符合条款说明",
            "type": 1
        },
        {
            "field_name": "预估补贴金额（万元）",
            "type": 2,
            "property": {
                "formatter": "0.0"
            }
        },
        {
            "field_name": "最后核验时间",
            "type": 1
        },
    ],
}

# 基础信息表
DEMO_BASE_INFO = [
    {"企业名称": "极光创新科技有限公司", "统一社会信用代码(Key)": "91310115MA1H888A", "行业分类": "信息技术", "注册资本(万元)": 500, "经营状态": "在营"},
    {"企业名称": "数字科技有限公司", "统一社会信用代码(Key)": "91310115MA1H222F", "行业分类": "信息技术", "注册资本(万元)": 1000, "经营状态": "注销"},
    {"企业名称": "金地地产开发有限公司", "统一社会信用代码(Key)": "91310115MA1H555E", "行业分类": "房地产", "注册资本(万元)": 5000, "经营状态": "在营"},
    {"企业名称": "宏图重工有限公司", "统一社会信用代码(Key)": "91310115MA1H999B", "行业分类": "先进制造", "注册资本(万元)": 2500, "经营状态": "在营"},
    {"企业名称": "蓝天生物科技有限公司", "统一社会信用代码(Key)": "91310115MA1H777C", "行业分类": "生物医药", "注册资本(万元)": 1200, "经营状态": "在营"},
    {"企业名称": "晨曦新材料有限公司", "统一社会信用代码(Key)": "91310115MA1H666D", "行业分类": "新材料", "注册资本(万元)": 5000, "经营状态": "在营"},
    {"企业名称": "蓝山重工有限公司", "统一社会信用代码(Key)": "91310115MA1H333G", "行业分类": "先进制造", "注册资本(万元)": 3000, "经营状态": "在营"},
]

# 研发纳税表
DEMO_FIN_INFO = [
    {"统一社会信用代码(Key)": "91310115MA1H888A", "研发投入金额(万元)": 60, "年度纳税总额(万元)": 18, "研发投入比例": "8.50%", "专利数量": 12},
    {"统一社会信用代码(Key)": "91310115MA1H222F", "研发投入金额(万元)": 0, "年度纳税总额(万元)": 0, "研发投入比例": "0.00%", "专利数量": 0},
    {"统一社会信用代码(Key)": "91310115MA1H555E", "研发投入金额(万元)": 0, "年度纳税总额(万元)": 500, "研发投入比例": "0.00%", "专利数量": 0},
    {"统一社会信用代码(Key)": "91310115MA1H999B", "研发投入金额(万元)": 300, "年度纳税总额(万元)": 45, "研发投入比例": "4.20%", "专利数量": 45},
    {"统一社会信用代码(Key)": "91310115MA1H777C", "研发投入金额(万元)": 50, "年度纳税总额(万元)": 12, "研发投入比例": "3.50%", "专利数量": 5},
    {"统一社会信用代码(Key)": "91310115MA1H666D", "研发投入金额(万元)": 150, "年度纳税总额(万元)": 22, "研发投入比例": "7.50%", "专利数量": 20},
    {"统一社会信用代码(Key)": "91310115MA1H333G", "研发投入金额(万元)": 380, "年度纳税总额(万元)": 50, "研发投入比例": "5.50%", "专利数量": 40},
]



def node_get_token() -> str:
    """获取飞书访问凭证"""
    return get_feishu_token()

def _headers() -> dict:
    """拼请求头：带token"""
    return {
        "Authorization": f"Bearer {node_get_token()}",
        "Content-Type": "application/json"
    }

def _check(resp_data:dict, action:str):
    """检查飞书返回内容，code!=0 就抛异常"""
    if resp_data.get("code") != 0:
        raise Exception(f"{action}失败: {resp_data.get('msg')}")


def node_create_base() -> dict:
    """创建多维表格，拿app_token"""
    url = f"{API_BASE}/bitable/v1/apps"
    body = {
        "name": "惠企政策审计数据库"
    }

    resp = requests.post(url, headers=_headers(), json=body, timeout = 15)
    resp_data = resp.json()

    _check(resp_data, "创建多维表格")
    app = resp_data["data"]["app"]

    # 修改默认数据表名称
    rename_url = f"{API_BASE}/bitable/v1/apps/{app['app_token']}/tables/{app['default_table_id']}"
    rename_body = {
        "name": "企业财务审计表"
    }

    rename_resp = requests.patch(rename_url, headers=_headers(), json=rename_body, timeout = 15)
    _check(rename_resp.json(),"重命名默认表")

    return app # 包含"app_token"、"url"、"default_table_id"

def node_update_permission(app_token: str):
    """更新云文档权限"""
    url = f"{API_BASE}/drive/v2/permissions/{app_token}/public"
    params = {
        "type": "bitable"
    }
    body = {
        "external_access_entity": "open",
        "security_entity": "anyone_can_view",
        "comment_entity": "anyone_can_view",
        "share_entity": "anyone",
        "manage_collaborator_entity": "collaborator_can_view",
        "link_share_entity": "tenant_editable",
        "copy_entity": "anyone_can_view"
    }

    resp = requests.patch(url, params=params, headers=_headers(), json=body, timeout = 15)
    resp_data = resp.json()

    _check(resp_data,"更新云文档权限")

def node_create_table(app_token: str, table_name: str) -> str:
    """新增数据表"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables"
    body = {
        "table": {
            "name": f"{table_name}",
            "default_view_name": "表格视图",
            "fields": [
                {
                    "field_name": "序号",
                    "type": 1005,
                    "property": {
                        "auto_serial": {
                            "type": "auto_increment_number"
                        }
                    }
                }
            ]
        }
    }

    resp = requests.post(url, headers=_headers(), json=body, timeout = 15)
    resp_data = resp.json()

    _check(resp_data,"新增数据表")

    return resp_data["data"]["table_id"]

def node_list_fields(app_token: str, table_id: str) -> list[dict]:
    """列出字段"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"

    resp = requests.get(url, headers=_headers(), timeout = 15)
    resp_data = resp.json()
    _check(resp_data,"列出字段")

    return resp_data["data"]["items"]  # 包含多个"field_id"

def node_rename_field(app_token: str, table_id: str, field_id: str):
    """修改索引字段"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}"
    body = {
        "field_name": "序号",
        "type": 1005,
        "property": {
            "auto_serial": {
                "type": "auto_increment_number"
            }
        }
    }

    resp = requests.put(url, headers=_headers(), json=body, timeout = 15)
    resp_data = resp.json()

    _check(resp_data,"修改索引字段")

def node_delete_field(app_token: str, table_id: str, field_id: str):
    """删除默认生成的无关字段"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}"

    resp = requests.delete(url, headers=_headers(), timeout = 15)
    _check(resp.json(),"删除默认字段")

def node_add_field(app_token: str, table_id: str, field: dict):
    """新增字段"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    body = field

    resp = requests.post(url, headers=_headers(), json=body, timeout = 15)
    _check(resp.json(),f"新增字段{field["field_name"]}")
    print(f"    已新增字段: {field["field_name"]}")


def node_add_records(app_token: str, table_id: str, records: list):
    """新增记录"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    for r in records:
        body = {"fields": r}

        resp = requests.post(url, headers=_headers(), json=body, timeout = 15)
        _check(resp.json(),"新增记录")
        print(f"    已写入：{r.get('企业名称',r.get('统一社会信用代码(Key)'))}")


def node_list_views(app_token:str, table_id: str):
    """列出视图，拿view_id"""
    url = f"{API_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/views"

    resp = requests.get(url, headers=_headers(), timeout = 15)
    resp_data = resp.json()
    _check(resp_data,"列出视图")

    return resp_data["data"]["items"]


def node_update_env(app_token: str, base_table_id: str, fin_table_id: str, audit_table_id: str):
    """更新 .env：只替换4个表格ID字段，其他行保留"""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    new_values = {
        "FEISHU_APP_TOKEN": app_token,
        "BASE_INFO_TABLE_ID": base_table_id,
        "FINANCIAL_TABLE_ID": fin_table_id,
        "AUDIT_TABLE_ID": audit_table_id,
    }

    # 读全部行
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 逐行处理：命中要替换的key → 整行换掉
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 跳过空行和注释行（#开头）
        if not stripped or stripped.startswith("#"):
            continue
        key = stripped.split("=", 1)[0].strip()   # 取"="左边的key
        if key in new_values:
            lines[i] = f"{key}={new_values[key]}\n"

    # 写回（utf-8 保持原编码）
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def node_save_links(links: dict):
    """把三张表链接保存到 table_links.txt（覆盖）"""
    file_path = os.path.join(PROJECT_ROOT, "table_links.txt")
    lines = [
        "========================================",
        "惠企政策审计智能体 - 飞书三表链接",
        "========================================",
        f"企业基础信息表：{links['企业基础信息表']}",
        f"企业研发纳税信息表：{links['企业研发纳税信息表']}",
        f"企业财务审计表：{links['企业财务审计表']}",
        "（提示：从飞书客户端「多维表格」首页也能找到这三张表）",
        "",
        "==== 测试用例（跑 main.py 时复制下面代码）====",
        "极光创新：91310115MA1H888A",
        "数字科技：91310115MA1H222F",
        "金地地产：91310115MA1H555E",
        "宏图重工：91310115MA1H999B",
        "蓝天生物：91310115MA1H777C",
        "晨曦新材料：91310115MA1H666D",
        "蓝山重工：91310115MA1H333G",
    ]
    with open(file_path, "w", encoding="utf-8") as f:   # "w" = 覆盖
        f.write("\n".join(lines))
    print("✅ 三张表链接已保存到 table_links.txt（覆盖最新）")



if __name__ == "__main__":
    token = node_get_token()
    print("✅ token获取成功：",token)

    # 创建多维表格
    app = node_create_base()
    print("✅ 多维表格已创建成功! 默认表名已更新为: 企业财务审计表")
    print("    app_token: ",app["app_token"])
    print("    Base_url: ",app["url"])
    print("    企业财务审计表id: ",app["default_table_id"])

    # 获取更新权限
    app_token = app["app_token"]
    node_update_permission(app_token)
    print("✅ 公共链接权限已设置")

    # 新增数据表
    print("\n新建数据表中...")
    fin_id = node_create_table(app_token,"企业研发纳税信息表")
    base_id = node_create_table(app_token,"企业基础信息表")
    print("新增表: 企业研发纳税信息表",fin_id)
    print("新增表: 企业基础信息表",base_id)

    audit_id = app["default_table_id"]

    # 列出字段
    fields = node_list_fields(app_token, audit_id)
    print("表中存在默认字段：")
    for f in fields:
        print(f"   {f['field_name']} | type={f['type']} | id={f['field_id']}")

    # 修改索引字段
    node_rename_field(app_token, audit_id, fields[0]["field_id"])
    print("✅ 索引字段已修改为：序号")

    # 删除默认字段
    field_ids = [f["field_id"] for f in fields[1:]]
    for field_id in field_ids:
        node_delete_field(app_token, audit_id, field_id)
    print("🗑️ 已删除无关字段")
    if not field_ids:
        print("✅ 没有可删的默认字段（只有主字段）")

    # 新增字段
    table_map = {
        "企业基础信息表": base_id,
        "企业研发纳税信息表": fin_id,
        "企业财务审计表": audit_id,
    }
    print("\n==开始新增字段==")
    for table_name,table_id in table_map.items():
        print(f"针对-{table_name}-新增字段中...")
        for field in TABLE_FIELDS[table_name]:
            node_add_field(app_token,table_id,field)
    print("✅ 新增字段已完毕")

    # 新增记录
    print("\n==开始新增演示数据==")
    print("新增基础信息中...")
    node_add_records(app_token, base_id, DEMO_BASE_INFO)
    print("新增研发纳税信息中...")
    node_add_records(app_token, fin_id, DEMO_FIN_INFO)
    print("✅ 数据已添加完毕")

    # 列出视图，拿view_id 返回完整链接, 再把表链接保存到 table_links.txt
    print("\n正在为您打印数据表链接...")
    links = {}
    for table_name, table_id in table_map.items():
        views = node_list_views(app_token, table_id)
        view_id = views[0]["view_id"]
        link = f"{app['url']}?table={table_id}&view={view_id}"
        # 存进字典
        links[table_name] = link
        print(f"✅ {table_name}：{link}")

    # 更新 .env
    node_update_env(app_token, base_id, fin_id, audit_id)
    print("✅ 已更新 .env（app_token + 三个 table_id）")

    node_save_links(links)   # 一次性写入文件
    print("✅ 为防止终端刷屏丢失链接，已将链接写入：table_links.txt")
