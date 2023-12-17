# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/10 15:50
# @Desc    : 模拟 API 业务请求代码
import os

import aiomysql
import models
import uvicorn
from db import init_pool
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import redis
import time

app = FastAPI(debug=True)

user_db_pool = None


@app.on_event("startup")
async def init_db():
    global user_db_pool
    user_db_pool = await aiomysql.create_pool(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.getenv("RELATION_DB_PWD", "mysql db password"),
        db="blog_demo_code",
        autocommit=True  # 默认为Fasle
    )
    await init_pool(user_db_pool)


# 注册接口
@app.post("/register")
async def register_user(user_info: models.UserRegistrationRequest):
    """
    注册用户 - 普通版本
    :param user_info:
    :return:
    """
    if not await models.check_user_exist_by_openid(user_info.openid):
        await models.add_new_user(user_info.model_dump())
        return JSONResponse({"message": "注册成功", "code": 0})
    return JSONResponse({"message": "注册失败，Openid已存在", "code": -1})


import anyio

# 用于存储每个 openid 对应的锁
openid_locks = {}


@app.post("/register_asyncio_lock")
async def register_user(user_info: models.UserRegistrationRequest):
    """
    注册用户 - 互斥锁Lock()
    :param user_info:
    :return:
    """
    lock = openid_locks.setdefault(user_info.openid, anyio.Lock())
    async with lock:
        if not await models.check_user_exist_by_openid(user_info.openid):
            await models.add_new_user(user_info.model_dump())
            return JSONResponse({"message": "注册成功", "code": 0})
        return JSONResponse({"message": "注册失败，Openid已存在", "code": -1})


def acquire_lock(_redis_conn: redis.Redis, lock_name: str, acquire_timeout=10):
    identifier = str(time.time())  # 生成一个唯一的标识符
    lock_key = f"lock:{lock_name}"

    # 尝试获取锁，设置成功则返回标识符，否则等待一段时间再重试

    if _redis_conn.setnx(lock_key, identifier):
        _redis_conn.expire(lock_key, acquire_timeout)
        return identifier


def release_lock(_redis_conn, lock_name, identifier):
    lock_key = f"lock:{lock_name}"
    current_value = _redis_conn.get(lock_key)

    if current_value and current_value.decode() == identifier:
        _redis_conn.delete(lock_key)
    else:
        raise ValueError("Invalid lock identifier")


@app.post("/register_redis_lock")
async def register_user(user_info: models.UserRegistrationRequest):
    """
    注册用户 - 分布式锁
    :param user_info:
    :return:
    """
    redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0,
                                   password=os.getenv("REDIS_DB_PWD", "you redis db pwd"))

    lock_name = f"register_lock:{user_info.openid}"

    # 尝试获取分布式锁
    identifier = acquire_lock(redis_conn, lock_name)
    if not identifier:
        return JSONResponse({"message": "注册失败，无法获取锁", "code": -1})

    try:
        # 检查用户是否已存在
        if not await models.check_user_exist_by_openid(user_info.openid):
            # 用户不存在，进行注册
            await models.add_new_user(user_info.model_dump())
            return JSONResponse({"message": "注册成功", "code": 0})
        else:
            return JSONResponse({"message": "注册失败，Openid已存在", "code": -1})
    finally:
        # 释放分布式锁
        release_lock(redis_conn, lock_name, identifier)


if __name__ == '__main__':
    uvicorn.run(app, port=9999)
