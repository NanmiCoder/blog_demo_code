# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/10 15:50
# @Desc    : 模拟 API 业务请求代码
import asyncio
import os
import uuid
from typing import List

import aiomysql
import httpx
import models
import uvicorn
from db import init_pool
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
    注册用户
    :param user_info:
    :return:
    """
    if not await models.check_user_exist_by_openid(user_info.openid):
        await models.add_new_user(user_info.model_dump())
        return JSONResponse({"message": "注册成功", "code": 0})
    return JSONResponse({"message": "注册失败，Openid已存在", "code": -1})


@app.post("/batch/mock_register_user/{count}")
async def mock_batch_register_user(count: int):
    """
    模拟批量创建指定用户数量
    :return:
    """
    # 构建指定数量的用户信息
    m_user = models.UserRegistrationRequest
    user_info_list: List[m_user] = []
    for index in range(1, count + 1):
        user_info_list.append(
            m_user(openid=str(uuid.uuid4()), username=f"mock_name_{index}", password=f"mock_pwd_{index}")
        )

    # 内部发起注册调用
    async def internal_register(user_item: models.UserRegistrationRequest):
        async with httpx.AsyncClient(base_url="http://localhost:9999") as async_client:
            response = await async_client.post("/register", json=user_item.model_dump())
            res = response.json()
            if res.get("code") == 0:
                print(f"openid:{user_item.openid} ---------> ", res.get("message"))

    # 批量发起注册请求
    task_list = []
    for _user_item in user_info_list:
        # 重放请求，模拟同样请求参数，多次调用注册接口
        task = asyncio.create_task(internal_register(_user_item),name=f"{_user_item.openid}_1")
        duplicate_one_task = asyncio.create_task(internal_register(_user_item), name=f"{_user_item.openid}_2")
        duplicate_two_task = asyncio.create_task(internal_register(_user_item), name=f"{_user_item.openid}_3")
        task_list.append(task)
        task_list.append(duplicate_one_task)
        task_list.append(duplicate_two_task)
    await asyncio.gather(*task_list)

    return JSONResponse({"message": "批量注册成功", "code": 0})


if __name__ == '__main__':
    uvicorn.run(app, port=9999)
