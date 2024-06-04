from re import match
from time import sleep

from bilibili_api import Credential, sync, data
from bilibili_api.live import LiveDanmaku
from bilibili_api.user import User
from browser_cookie3 import firefox
from flask import Flask, render_template, jsonify

guardName_guardNum_pattern = r'^(.*?)\*(\d+).*?$'

counter = 0
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/counter')
def get_counter():
    return jsonify(counter=counter)


async def handle_guard_buy(event):
    global counter
    if event['data']['data']['gift_name'] == '舰长':
        counter += event['data']['data']['num']
    elif event['data']['data']['gift_name'] == '提督':
        counter += event['data']['data']['num'] * 10
    elif event['data']['data']['gift_name'] == '总督':
        counter += event['data']['data']['num'] * 100


async def handle_common_notice(event):
    global counter
    try:
        if event['data']['data']['content_segments'][2]['text'] == '大航海盲盒':
            guard_name, guard_num = match(guardName_guardNum_pattern,
                                          event['data']['data']['content_segments'][4]['text']).groups()
            if guard_name == '舰长':
                counter += guard_num / 30
            elif guard_name == '提督':
                counter += guard_num * 10 / 30
            elif guard_name == '总督':
                counter += guard_num * 100 / 30
        else:
            return
    except Exception as e:
        return


def bind(live_danmaku: LiveDanmaku):
    __live_danmaku = live_danmaku

    @__live_danmaku.on("ALL")
    async def any_event(event):
        if event['type'] == 'GUARD_BUY':
            await handle_guard_buy(event=event)
        elif event['type'] == 'COMMON_NOTICE_DANMAKU':
            await handle_common_notice(event=event)


if __name__ == '__main__':
    print("正在从火狐浏览器获取bilibili.com的登录身份信息")
    cj = firefox(domain_name="bilibili.com")
    if not cj:
        print("请先在火狐浏览器登录b站")
        sleep(3)
        exit()
    credential = {}
    for cookie in cj:
        name = cookie.name
        if name == 'DedeUserID':
            credential["dedeuserid"] = cookie.value
        elif name == 'bili_jct':
            credential["bili_jct"] = cookie.value
        elif name == 'buvid3':
            credential["buvid3"] = cookie.value
        elif name == 'SESSDATA':
            credential["sessdata"] = cookie.value
    if not credential:
        print("请在火狐浏览器登录b站")
        sleep(3)
        exit()
    my_credential = Credential(**credential)
    print(f"获取登录身份信息成功, uid:{credential['dedeuserid']}")

    user = User(uid=my_credential.dedeuserid, credential=my_credential)
    live_info = sync(user.get_live_info())
    room_id = live_info["live_room"]["roomid"]
    liveDanmaku = LiveDanmaku(room_display_id=room_id, credential=my_credential)
    bind(live_danmaku=liveDanmaku)

    app.run(debug=True, use_reloader=False)
