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





if __name__ == '__main__':
    uvicorn.run(app, port=9999)
