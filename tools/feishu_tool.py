"""
飞书多维表格工具封装
"""
import time
from wsgiref import headers
import requests
from aiohttp import payload
from config.settings import settings

# 全局变量：缓存飞书token
# 缓存的token、token过期时间戳
_feishu_token = None
_feishu_token_expire = 0


def get_feishu_token() -> str:
    """获取飞书访问凭证，带缓存"""
    global _feishu_token, _feishu_token_expire

    # 已有token没过期，返回缓存
    if _feishu_token and time.time() < _feishu_token_expire:
        return _feishu_token

    # 发请求拿新token
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        # 请求体，两个变量
        "app_id" : settings.FEISHU_APP_ID,
        "app_secret" : settings.FEISHU_APP_SECRET
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp_data = resp.json()

    if resp_data.get("code") != 0:
        raise Exception(f"飞书token获取失败：{resp_data.get('msg')}")

    # 更新缓存和过期时间
    _feishu_token = resp_data["tenant_access_token"]
    _feishu_token_expire = time.time() + resp_data["expire"] - 300
    return _feishu_token



def query_base_info(credit_code: str) -> dict | None:
    """按信用代码查企业基础信息表，查不到返回None"""
    # 查询API地址
    app_token = settings.FEISHU_APP_TOKEN
    table_id = settings.BASE_INFO_TABLE_ID

    # 查询记录url
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    token = get_feishu_token()

    # 请求头
    headers = {
        "Authorization" : f"Bearer {token}",
        "Content-Type" : "application/json"
    }

    # 请求体
    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "统一社会信用代码(Key)",
                    "operator": "is",
                    "value": [credit_code]
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp_data = resp.json()

    if resp_data.get("code") != 0:
        raise Exception(f"查询企业信息失败：{resp_data.get('msg')}")

    items = resp_data["data"]["items"]
    if not items:
        return None
    return items[0]["fields"]


def query_fin_info(credit_code:str) -> dict | None:
    """ 按信用代码查研发纳税表 """
    app_token = settings.FEISHU_APP_TOKEN
    table_id =  settings.FINANCIAL_TABLE_ID

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    token = get_feishu_token()

    headers = {
        "Authorization" : f"Bearer {token}",
        "Content-Type" : "application/json"
    }

    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "统一社会信用代码 (Key)",
                    "operator": "is",
                    "value": [credit_code]
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp_data = resp.json()

    if resp_data.get("code") != 0:
        raise Exception(f"查询财务信息失败：{resp_data.get('msg')}")

    items = resp_data["data"]["items"]
    if not items:
        return None
    return items[0]["fields"]



def add_audit_record(audit_data: dict) -> dict:
    """把结果写入审计表"""
    app_token = settings.FEISHU_APP_TOKEN
    table_id = settings.AUDIT_TABLE_ID

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    token = get_feishu_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": audit_data
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp_data = resp.json()

    if resp_data.get("code") != 0:
        raise Exception(f"写入审计记录失败：{resp_data.get('msg')}")

    return resp_data["data"]["record"]