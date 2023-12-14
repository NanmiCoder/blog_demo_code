# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/10 16:56
# @Desc    :
import asyncio
from typing import Dict

import db
from pydantic import BaseModel


class UserRegistrationRequest(BaseModel):
    openid: str
    username: str
    password: str


async def check_user_exist_by_openid(openid: str) -> bool:
    """
    判断 openid 相关的用户是否已存在
    :param openid:
    :return:
    """
    sql: str = "select * from users where openid = %s"
    data = await db.user_db.get_first(sql, openid)
    if data:
        return True
    return False


async def add_new_user(user_item: Dict) -> int:
    """
    新增一条用户信息记录
    :param user_item:
    :return:
    """
    return await db.user_db.item_to_table(table_name="users", item=user_item)


# 在模块级别定义一个锁
registration_lock = asyncio.Lock()

async def check_user_exist_by_openid_use_asyncio_lock(openid: str) -> bool:
    """
    判断 openid 相关的用户是否已存在 - 使用asyncio.Lock()来防止查询并发问题
    :param openid:
    :return:
    """
    async with registration_lock:
        sql: str = "select * from users where openid = %s"
        data = await db.user_db.get_first(sql, openid)
        if data:
            return True
        return False


async def check_user_exist_by_openid_use_redis_lock(openid: str) -> bool:
    """
    判断 openid 相关的用户是否已存在 - 使用asyncio.Lock()来防止查询并发问题
    :param openid:
    :return:
    """
    sql: str = "select * from users where openid = %s"
    data = await db.user_db.get_first(sql, openid)
    if data:
        return True
    return False
