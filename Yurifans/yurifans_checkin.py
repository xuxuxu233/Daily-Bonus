# -*- coding: utf-8 -*-
# @File     : yurifans_checkin.py
# @Time     : 2023/04/25 12:17
# @Author   : Cloudac7

import os
import requests
from time import sleep

# session
SESSION = requests.session()

# info
USERNAME = os.environ.get('YURIFANS_EMAIL')
PASSWORD = os.environ.get('YURIFANS_PASSWORD')

# message
msg = []

# 登录 - 添加详细错误处理
def login():
    print(f"尝试登录账号: {USERNAME}")
    url = "https://yuri.website/wp-json/jwt-auth/v1/token"
    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://yuri.website/",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    form_data = {
        "username": USERNAME,
        "password": PASSWORD,
    }

    try:
        req = SESSION.post(
            url, 
            headers=headers,
            data=form_data,
            timeout=10  # 添加超时防止卡死
        )
        
        # 添加详细的响应检查
        print(f"登录响应状态码: {req.status_code}")
        print(f"登录响应内容: {req.text[:200]}...")  # 打印部分响应内容
        
        if req.status_code != 200:
            print(f"登录失败，状态码: {req.status_code}")
            return ""
            
        # 尝试从cookie获取token
        b2_token = req.cookies.get("b2_token")
        
        # 如果cookie中没有，尝试从JSON响应中获取
        if not b2_token:
            try:
                response_data = req.json()
                if "token" in response_data:
                    b2_token = response_data["token"]
                    print(f"从JSON响应获取token: {b2_token}")
            except:
                pass
        
        if not b2_token:
            print("登录成功但未获取到 b2_token")
            return ""
            
        print(f"登录成功，获取的token: {b2_token[:15]}...")  # 打印部分token
        return b2_token
        
    except Exception as e:
        print(f"登录异常: {str(e)}")
        return ""

# 获取用户信息
def check_user_info(b2_token):
    if not b2_token:
        print('未提供有效token，跳过获取用户信息')
        return False
        
    url = "https://yuri.website/wp-json/b2/v1/getUserInfo"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f'Bearer {b2_token}',
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    
    try:
        req = SESSION.post(url, headers=headers, timeout=10)
        print(f"用户信息响应状态码: {req.status_code}")
        
        if req.status_code != 200:
            print('获取用户信息失败')
            return False
            
        try:
            user_data = req.json()["user_data"]
            global msg
            msg += [
                {"name": "账户信息", "value": user_data.get("name")},
            ]
            return True
        except Exception as e:
            print(f'解析用户信息失败: {str(e)}')
            print(f'完整响应: {req.text}')
            return False
    except Exception as e:
        print(f'请求用户信息异常: {str(e)}')
        return False

# 查询积分
def query_credit(b2_token):
    if not b2_token:
        print('未提供有效token，跳过积分查询')
        return True
        
    url = "https://yuri.website/wp-json/b2/v1/getUserMission"
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    
    global msg

    try:
        req = SESSION.post(url, headers=headers, timeout=10)
        print(f"积分查询响应状态码: {req.status_code}")
        
        if req.status_code != 200:
            print(f"积分查询失败，状态码: {req.status_code}")
            return True
            
        response_data = req.json()
        mission = response_data.get("mission", {})
        date = mission.get("date")
        my_credit = mission.get("my_credit", 0)
        
        msg += [{"name": "当前积分", "value": my_credit}]
        
        if not date:
            return True
            
        credit = mission.get("credit", 0) 
        msg += [
            {"name": "签到信息", "value": "今日已经签到"},
            {"name": "今日获取积分", "value": credit}
        ]
        return False
    except Exception as e:
        print(f"积分查询异常: {str(e)}")
        return True

# 签到
def check_in(b2_token):
    if not b2_token:
        print('未提供有效token，跳过签到')
        global msg
        msg += [{"name": "签到信息", "value": "未登录，签到失败"}]
        return False
        
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    url = "https://yuri.website/wp-json/b2/v1/userMission"

    try:
        req = SESSION.post(url, headers=headers, timeout=10)
        print(f"签到响应状态码: {req.status_code}")
        print(f"签到响应内容: {req.text[:200]}...")
        
        global msg
        
        if req.status_code != 200:
            msg += [{"name": "签到信息", "value": f"签到失败，状态码: {req.status_code}"}]
            return False
            
        try:
            data = req.json()
            if "mission" in data:
                mission_data = data["mission"]
                credit = mission_data.get("credit", "未知")
                msg += [
                    {"name": "签到信息", "value": "签到成功"},
                    {"name": "今日获取积分", "value": credit},
                ]
                return True
            else:
                # 处理已签到的情况
                msg += [
                    {"name": "签到信息", "value": "今日已签到"},
                    {"name": "今日获取积分", "value": req.text}
                ]
                return True
        except Exception as e:
            print(f"解析签到响应失败: {str(e)}")
            msg += [{"name": "签到信息", "value": "签到响应解析失败"}]
            return False
    except Exception as e:
        print(f"签到请求异常: {str(e)}")
        msg += [{"name": "签到信息", "value": "签到请求异常"}]
        return False

# 登出 - 添加空值检查
def logout(b2_token):
    if not b2_token:
        print("⚠️ 无法退出：未获取有效 token")
        return
        
    url = "https://yuri.website/wp-json/b2/v1/loginOut"
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    
    try:
        req = SESSION.get(url, headers=headers, timeout=5)
        if req.status_code != 200:
            print(f"退出登录失败，状态码: {req.status_code}")
        else:
            print("退出登录成功")
    except Exception as e:
        print(f"退出登录异常: {str(e)}")

# 主函数 - 添加全面错误处理
def main():
    global msg
    msg = []  # 重置消息
    
    print("=" * 30 + " Yurifans 签到开始 " + "=" * 30)
    
    try:
        # 登录
        b2_token = login()
        sleep(2)
        
        if not b2_token:
            msg.append({"name": "签到状态", "value": "登录失败，无法签到"})
            return format_message()
        
        # 获取用户信息
        user_info_success = check_user_info(b2_token)
        
        # 查询积分和签到
        if user_info_success:
            need_checkin = query_credit(b2_token)
            if need_checkin:
                check_in(b2_token)
        
        # 登出
        logout(b2_token)
        
        return format_message()
        
    except Exception as e:
        print(f"主流程异常: {str(e)}")
        msg.append({"name": "签到状态", "value": f"程序异常: {str(e)}"})
        return format_message()
    finally:
        print("=" * 30 + " Yurifans 签到结束 " + "=" * 30)

# 格式化消息
def format_message():
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(main())
