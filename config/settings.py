"""
项目全局配置：自动从.env文件读取DeepSeek、飞书的密钥、表格链接
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 从项目根目录的.env文件读配置
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # DeepSeek大模型配置
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str

    # 飞书自建应用配置
    FEISHU_APP_ID: str
    FEISHU_APP_SECRET: str
    # 飞书多维表格配置
    FEISHU_APP_TOKEN: str
    BASE_INFO_TABLE_ID: str
    FINANCIAL_TABLE_ID: str
    AUDIT_TABLE_ID: str


# 实例化一个全局配置对象
settings = Settings()
