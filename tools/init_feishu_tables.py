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
        "name": "惠企政策审计数据库test"
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



if __name__ == "__main__":
    token = node_get_token()
    print("✅ token获取成功：",token)

    app = node_create_base()
    print("✅ 多维表格已创建成功! 默认表名已更新为: 企业财务审计表")
    print("    app_token: ",app["app_token"])
    print("    Base_url: ",app["url"])
    print("    企业财务审计表id: ",app["default_table_id"])

    app_token = app["app_token"]
    node_update_permission(app_token)
    print("✅ 公共链接权限已设置")

    fin_id = node_create_table(app_token,"企业研发纳税信息表")
    base_id = node_create_table(app_token,"企业基础信息表")
    print("新增表: 企业研发纳税信息表",fin_id)
    print("新增表: 企业基础信息表",base_id)

    audit_id = app["default_table_id"]
    # 列出字段
    fields = node_list_fields(app_token, audit_id)
    print("默认表现有字段：")
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
    print("开始新增字段...")
    for table_name,table_id in table_map.items():
        print(f"针对-{table_name}-新增字段中...")
        for field in TABLE_FIELDS[table_name]:
            node_add_field(app_token,table_id,field)
    print("✅ 新增字段已完毕")