# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/15 00:36
# @Desc    : 模拟批量发起注册请求
import asyncio
import uuid
from typing import List

import httpx
import models
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(debug=True)


class BatchRegisterReq(BaseModel):
    count: int = Field(default="50", title="并发注册用户数量")
    register_url: str = Field(default=r"register", title="请求注册的URL")


@app.post("/batch/mock_register_user")
async def mock_batch_register_user(req: BatchRegisterReq):
    """
    模拟批量创建指定用户数量
    :return:
    """
    # 构建指定数量的用户信息
    m_user = models.UserRegistrationRequest
    user_info_list: List[m_user] = []
    for index in range(1, req.count + 1):
        user_info_list.append(
            m_user(openid=str(uuid.uuid4()), username=f"mock_name_{index}", password=f"mock_pwd_{index}")
        )

    # 内部发起注册调用
    async def internal_register(user_item: models.UserRegistrationRequest):
        async with httpx.AsyncClient(base_url="http://localhost:9999") as async_client:
            response = await async_client.post("/" + req.register_url, json=user_item.model_dump())
            if response.status_code == 200:
                res = response.json()
                print(f"openid:{user_item.openid} ---------> ", res.get("message"))

    # 批量发起注册请求
    task_list = []
    for _user_item in user_info_list:
        # 重放请求，模拟同样请求参数，多次调用注册接口
        task = asyncio.create_task(internal_register(_user_item),name=f"{_user_item.openid}_1")
        duplicate_one_task = asyncio.create_task(internal_register(_user_item), name=f"{_user_item.openid}_2")
        task_list.append(task)
        task_list.append(duplicate_one_task)
    await asyncio.gather(*task_list)

    return JSONResponse({"message": "批量注册成功", "code": 0})


if __name__ == '__main__':
    uvicorn.run(app, port=9998)