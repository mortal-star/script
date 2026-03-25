import json
import os
import time
from datetime import datetime

import requests


class GLaDOSAutoCheckin:
    def __init__(self, cookies_dict, account_idx):
        self.account_idx = account_idx
        self.base_url = "https://glados.rocks"
        self.checkin_url = f"{self.base_url}/api/user/checkin"
        self.console_url = f"{self.base_url}/console"
        self.user_status_url = f"{self.base_url}/api/user/status"
        self.clash_url_template = (
            "https://update.glados-config.com/mihomo/{userId}/{code}/{port}/glados.yaml"
        )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": self.base_url,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            }
        )
        self.session.cookies.update(cookies_dict)

    def log_prefix(self):
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [账号{self.account_idx}]"

    def test_login_status(self):
        try:
            response = self.session.get(self.console_url, allow_redirects=False, timeout=10)
            if response.status_code == 200:
                print(f"{self.log_prefix()} Cookie 有效，登录正常")
                return True
            if response.status_code == 302:
                print(f"{self.log_prefix()} Cookie 过期或无效，需要重新配置")
                return False

            print(f"{self.log_prefix()} 登录状态未知，响应码: {response.status_code}")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"{self.log_prefix()} 登录测试失败: {exc}")
            return False

    def get_user_info(self):
        if not self.test_login_status():
            return False

        try:
            print(f"{self.log_prefix()} 开始获取个人信息")
            response = self.session.get(self.user_status_url, timeout=15)
            response.encoding = "utf-8"
            result = response.json()

            if response.status_code == 200 and result.get("code") == 0:
                user_data = result.get("data", {})
                info = {
                    "email": user_data.get("email", "未知"),
                    "package": (
                        "Free(升级)"
                        if user_data.get("vip", 0) in [0, 10]
                        else f"VIP{user_data.get('vip')}(付费)"
                    ),
                    "left_days": str(user_data.get("leftDays", "0")).split(".")[0],
                    "userId": str(user_data.get("userId", "未知")),
                    "code": user_data.get("code", "未知"),
                    "port": str(user_data.get("port", "未知")),
                }

                print(f"{self.log_prefix()} 账户邮箱: {info['email']}")
                print(f"{self.log_prefix()} 套餐类型: {info['package']}")
                print(f"{self.log_prefix()} 剩余天数: {info['left_days']}")

                if (
                    info["userId"] != "未知"
                    and info["code"] != "未知"
                    and info["port"] != "未知"
                ):
                    clash_url = self.clash_url_template.format(**info)
                    print(f"{self.log_prefix()} Clash 订阅链接: {clash_url}")
                else:
                    print(f"{self.log_prefix()} 无法生成订阅链接，缺少 userId/code/port")

                return True

            print(f"{self.log_prefix()} 个人信息获取失败: {result.get('message', '响应异常')}")
            return False
        except json.JSONDecodeError:
            print(f"{self.log_prefix()} 解析失败，响应不是合法 JSON")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"{self.log_prefix()} 信息请求失败: {exc}")
            return False

    def auto_checkin(self):
        print(f"{self.log_prefix()} ===== 开始签到流程 =====")
        if not self.get_user_info():
            print(f"{self.log_prefix()} 个人信息获取失败，跳过本次签到")
            return False

        try:
            print(f"{self.log_prefix()} 发起签到请求")
            response = self.session.post(
                self.checkin_url,
                data=json.dumps({"token": "glados.one"}),
                timeout=15,
            )
            response.encoding = "utf-8"
            result = response.json()

            if response.status_code != 200:
                print(f"{self.log_prefix()} 签到接口异常，状态码: {response.status_code}")
                return False

            code = result.get("code")
            message = result.get("message", "未知")
            points = result.get("points", 0)
            balance_list = result.get("list") or []
            balance = "未知"
            if isinstance(balance_list, list) and balance_list:
                first_item = balance_list[0]
                if isinstance(first_item, dict):
                    balance = first_item.get("balance", "未知")

            if code == 1 and "Repeats" in message:
                print(f"{self.log_prefix()} 今日已经签到: {message}")
                print(f"{self.log_prefix()} 当前积分: {balance}")
                return True

            if code == 0 or "Success" in message:
                print(f"{self.log_prefix()} 签到成功")
                print(f"{self.log_prefix()} 本次获得积分: {points}")
                print(f"{self.log_prefix()} 当前积分: {balance}")
                return True

            print(f"{self.log_prefix()} 签到失败: {message} (code={code})")
            print(f"{self.log_prefix()} 接口返回: {result}")
            return False
        except json.JSONDecodeError:
            print(f"{self.log_prefix()} 解析签到响应失败，非合法 JSON")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"{self.log_prefix()} 签到请求失败: {exc}")
            return False


def parse_cookies(cookie_str):
    cookies_dict = {}
    for item in cookie_str.strip().split(";"):
        if "=" in item:
            key, val = item.strip().split("=", 1)
            cookies_dict[key] = val
    return cookies_dict


def load_accounts():
    raw_value = os.getenv("GLADOS_ACCOUNTS") or os.getenv("GLaDOS_CK")
    if not raw_value:
        print("未找到环境变量 GLADOS_ACCOUNTS（兼容旧变量 GLaDOS_CK）")
        return []

    return [line.strip() for line in raw_value.replace("\r\n", "\n").split("\n") if line.strip()]


def main():
    accounts = load_accounts()
    if not accounts:
        raise SystemExit(1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检测到 {len(accounts)} 个账号，开始处理")

    success_count = 0
    failure_count = 0

    for idx, account in enumerate(accounts, 1):
        if "=" not in account:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [账号{idx}] Cookie 格式错误")
            failure_count += 1
            continue

        checker = GLaDOSAutoCheckin(parse_cookies(account), idx)
        if checker.auto_checkin():
            success_count += 1
        else:
            failure_count += 1

        if idx < len(accounts):
            time.sleep(3)

    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 处理完成，"
        f"成功 {success_count} 个，失败 {failure_count} 个"
    )

    if failure_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
