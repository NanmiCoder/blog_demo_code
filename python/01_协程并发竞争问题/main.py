# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/10 15:50
# @Desc    :
import os
import uuid
import asyncio
from typing import List

import uvicorn
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import aiomysql

import models
from db import init_pool

app = FastAPI()


@app.on_event("startup")
async def init_db():
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
        return JSONResponse({"messgae": "注册成功", "code": 0})
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

    # 批量发起注册请求
    async_client = httpx.AsyncClient(base_url="http://localhost:9999")
    task_list = [async_client.post("/register", data=user_item.model_dump(),headers={"Content-Type": "application/json"}) for user_item in user_info_list]
    await asyncio.gather(*task_list)

    return JSONResponse({"messgae": "批量注册成功", "code": 0})

if __name__ == '__main__':
    uvicorn.run(app, port=9999)
