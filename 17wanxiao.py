import time
import datetime
import json
import logging
import requests

from login import CampusCard


def initLogging():
    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format="[%(levelname)s]; %(message)s")


def get_token(username, password):
    """
    获取用户令牌，模拟登录获取：https://github.com/zhongbr/wanmei_campus
    :param username: 账号
    :param password: 密码
    :return:
    """
    user_dict = CampusCard(username, password).user_info
    if not user_dict['login']:
        return None
    return user_dict["sessionId"]


def get_post_json(jsons):
    """
    获取打卡数据
    :param jsons: 用来获取打卡数据的json字段
    :return:
    """
    retry = 0
    while retry < 3:
        try:
            res = requests.post(url="https://reportedh5.17wanxiao.com/sass/api/epmpics", json=jsons, timeout=10).json()
            # print(res)
        except:
            retry += 1
            logging.warning('获取完美校园打卡post参数失败，正在重试...')
            time.sleep(1)
            continue

        if res['code'] != '10000':
            # logging.warning(res)
            return None
        data = json.loads(res['data'])
        # print(data)
        try:
            dep = data['deptStr']['deptid']
        except:
            logging.info(data['phonenum']+' 信息没写')
            logs(data['phonenum']+'信息没写')
            return None
        post_dict = {
            "areaStr": data['areaStr'],
            "deptStr": data['deptStr'],
            "deptid": data['deptStr']['deptid'],
            "customerid": data['customerid'],
            "userid": data['userid'],
            "username": data['username'],
            "stuNo": data['stuNo'],
            "phonenum": data['phonenum'],
            "templateid": data['templateid'],
            "updatainfo": [{"propertyname": i["propertyname"], "value": i["value"]} for i in
                           data['cusTemplateRelations']],
            "checkbox": [{"description": i["decription"], "value": i["value"]} for i in
                         data['cusTemplateRelations']],
        }
        # print(json.dumps(post_dict, sort_keys=True, indent=4, ensure_ascii=False))
        logging.info('获取完美校园打卡post参数成功')
        return post_dict
    return None


def receive_check_in(token, custom_id, post_dict):
    """
    第二类健康打卡
    :param token: 用户令牌
    :param custom_id: 健康打卡id
    :param post_dict: 健康打卡数据
    :return:
    """
    check_json = {
        "userId": post_dict['userId'],
        "name": post_dict['name'],
        "stuNo": post_dict['stuNo'],
        "whereabouts": post_dict['whereabouts'],
        "familyWhereabouts": "",
        "beenToWuhan": post_dict['beenToWuhan'],
        "contactWithPatients": post_dict['contactWithPatients'],
        "symptom": post_dict['symptom'],
        "fever": post_dict['fever'],
        "cough": post_dict['cough'],
        "soreThroat": post_dict['soreThroat'],
        "debilitation": post_dict['debilitation'],
        "diarrhea": post_dict['diarrhea'],
        "cold": post_dict['cold'],
        "staySchool": post_dict['staySchool'],
        "contacts": post_dict['contacts'],
        "emergencyPhone": post_dict['emergencyPhone'],
        "address": post_dict['address'],
        "familyForAddress": "",
        "collegeId": post_dict['collegeId'],
        "majorId": post_dict['majorId'],
        "classId": post_dict['classId'],
        "classDescribe": post_dict['classDescribe'],
        "temperature": post_dict['temperature'],
        "confirmed": post_dict['confirmed'],
        "isolated": post_dict['isolated'],
        "passingWuhan": post_dict['passingWuhan'],
        "passingHubei": post_dict['passingHubei'],
        "patientSide": post_dict['patientSide'],
        "patientContact": post_dict['patientContact'],
        "mentalHealth": post_dict['mentalHealth'],
        "wayToSchool": post_dict['wayToSchool'],
        "backToSchool": post_dict['backToSchool'],
        "haveBroadband": post_dict['haveBroadband'],
        "emergencyContactName": post_dict['emergencyContactName'],
        "helpInfo": "",
        "passingCity": "",
        "longitude": "",  # 请在此处填写需要打卡位置的longitude
        "latitude": "",  # 请在此处填写需要打卡位置的latitude
        "token": token,
    }
    headers = {
        'referer': f'https://reportedh5.17wanxiao.com/nCovReport/index.html?token={token}&customerId={custom_id}',
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/api/reported/receive", headers=headers, data=check_json).json()
        # 以json格式打印json字符串
        # print(res)
        if res['code'] == 0:
            logging.info(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type='healthy')
        else:
            logging.warning(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type='healthy')
    except:
        errmsg = f"```打卡请求出错```"
        logging.warning('打卡请求出错，网络不稳定')
        return dict(status=0, errmsg=errmsg)


def get_recall_data(token):
    """
    获取第二类健康打卡的打卡数据
    :param token: 用户令牌
    :return: 返回dict数据
    """
    retry = 0
    while retry < 3:
        try:
            res = requests.post(url="https://reportedh5.17wanxiao.com/api/reported/recall", data={"token": token}, timeout=10).json()
        except:
            retry += 1
            logging.warning('获取完美校园打卡post参数失败，正在重试...')
            time.sleep(1)
            continue
        if res['code'] == 0:
            logging.info('获取完美校园打卡post参数成功')
            return res['data']
        return None
    return None


def healthy_check_in(token, post_dict):
    """
    第一类健康打卡
    :param token: 用户令牌
    :param post_dict: 打卡数据
    :return:
    """
    check_json = {"businessType": "epmpics", "method": "submitUpInfo",
                  "jsonData": {"deptStr": post_dict['deptStr'], "areaStr": post_dict['areaStr'],
                               "reportdate": round(time.time() * 1000), "customerid": post_dict['customerid'],
                               "deptid": post_dict['deptid'], "source": "app",
                               "templateid": post_dict['templateid'], "stuNo": post_dict['stuNo'],
                               "username": post_dict['username'], "phonenum": post_dict['phonenum'],
                               "userid": post_dict['userid'], "updatainfo": post_dict['updatainfo'],
                               "gpsType": 1, "token": token},
                  }
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/sass/api/epmpics", json=check_json).json()
        # 以json格式打印json字符串
        if res['code'] != '10000':
            logging.warning(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type='healthy')
        else:
            logging.info(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type='healthy')
    except:
        errmsg = f"```打卡请求出错```"
        logging.warning('校内打卡请求出错')
        return dict(status=0, errmsg=errmsg)


def campus_check_in(username, token, post_dict, id):
    """
    校内打卡
    :param username: 电话号
    :param token: 用户令牌
    :param post_dict: 校内打卡数据
    :param id: 校内打卡id
    :return:
    """
    check_json = {"businessType": "epmpics", "method": "submitUpInfoSchool",
                  "jsonData": {"deptStr": post_dict['deptStr'],
                               "areaStr": post_dict['areaStr'],
                               "reportdate": round(time.time() * 1000), "customerid": post_dict['customerid'],
                               "deptid": post_dict['deptid'], "source": "app",
                               "templateid": post_dict['templateid'], "stuNo": post_dict['stuNo'],
                               "username": post_dict['username'], "phonenum": username,
                               "userid": post_dict['userid'], "updatainfo": post_dict['updatainfo'],
                               "customerAppTypeRuleId": id, "clockState": 0, "token": token},
                  "token": token
                  }
    # print(check_json)
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/sass/api/epmpics", json=check_json).json()

        # 以json格式打印json字符串
        if res['code'] != '10000':
            logging.warning(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type=post_dict['templateid'])
        else:
            logging.info(res)
            return dict(status=1, res=res, post_dict=post_dict, check_json=check_json, type=post_dict['templateid'])
    except BaseException:
        errmsg = f"```校内打卡请求出错```"
        logging.warning('校内打卡请求出错')
        return dict(status=0, errmsg=errmsg)

def logs(phone):
    with open('./log.txt', 'a+') as f:
      f.write(phone+"\n")
      f.close()
def check_in(username, password):
    # 登录获取token用于打卡
    token = get_token(username, password)
    # print(token)
    check_dict_list = []
    # 获取现在是上午，还是下午，还是晚上
    ape_list = get_ap()

    # 获取学校使用打卡模板Id
    custom_id_dict = get_custom_id(token)

    if not token:
        errmsg = f"{username[:4]}，获取token失败，打卡失败"
        logging.warning(username+errmsg)
        logs(username+'密码错了')
        return False

    # 获取第一类健康打卡的参数
    json1 = {"businessType": "epmpics",
             "jsonData": {"templateid": "pneumonia", "token": token},
             "method": "userComeApp"}
    post_dict = get_post_json(json1)

    if post_dict:
        # 第一类健康打卡
        # print(post_dict)

        # 修改温度等参数
        # for j in post_dict['updatainfo']:  # 这里获取打卡json字段的打卡信息，微信推送的json字段
        #     if j['propertyname'] == 'temperature':  # 找到propertyname为temperature的字段
        #         j['value'] = '36.2'  # 由于原先为null，这里直接设置36.2（根据自己学校打卡选项来）
        #     if j['propertyname'] == '举一反三即可':
        #         j['value'] = '举一反三即可'

        # 修改地址，依照自己完美校园，查一下地址即可
        # post_dict['areaStr'] = '{"streetNumber":"89号","street":"建设东路","district":"","city":"新乡市","province":"河南省",' \
        #                        '"town":"","pois":"河南师范大学(东区)","lng":113.91572178314209,' \
        #                        '"lat":35.327695868943984,"address":"牧野区建设东路89号河南师范大学(东区)","text":"河南省-新乡市",' \
        #                        '"code":""} '
        healthy_check_dict = healthy_check_in(token, post_dict)
        check_dict_list.append(healthy_check_dict)
    else:
        # 获取第二类健康打卡参数
        post_dict = get_recall_data(token)
        # 第二类健康打卡
        if post_dict == None:
            return False
        if custom_id_dict == None:
            return False
        healthy_check_dict = receive_check_in(token, custom_id_dict['customerId'], post_dict)
        if healthy_check_dict == None:
            return False
        check_dict_list.append(healthy_check_dict)

    # 获取校内打卡ID
    id_list = get_id_list(token, custom_id_dict['customerAppTypeId'])
    # print(id_list)
    if not id_list:
        return check_dict_list

    # 校内打卡
    for index, i in enumerate(id_list):
        if ape_list[index]:
            # print(i)
            logging.info(f"-------------------------------{i['templateid']}-------------------------------")
            json2 = {"businessType": "epmpics",
                     "jsonData": {"templateid": i['templateid'], "customerAppTypeRuleId": i['id'],
                                  "stuNo": post_dict['stuNo'],
                                  "token": token}, "method": "userComeAppSchool",
                     "token": token}
            campus_dict = get_post_json(json2)
            campus_dict['areaStr'] = post_dict['areaStr']
            for j in campus_dict['updatainfo']:
                if j['propertyname'] == 'temperature':
                    j['value'] = '36.4'
                if j['propertyname'] == 'symptom':
                    j['value'] = '无症状'
            campus_check_dict = campus_check_in(username, token, campus_dict, i['id'])
            check_dict_list.append(campus_check_dict)
            logging.info("--------------------------------------------------------------")
    return check_dict_list


def server_push(sckey, desp):
    """
    Server酱推送：https://sc.ftqq.com/3.version
    :param sckey: 通过官网注册获取，获取教程：https://github.com/ReaJason/17wanxiaoCheckin-Actions/blob/master/README_LAST.md#%E4%BA%8Cserver%E9%85%B1%E6%9C%8D%E5%8A%A1%E7%9A%84%E7%94%B3%E8%AF%B7
    :param desp: 需要推送的内容
    :return:
    """
    send_url = f"https://sc.ftqq.com/{sckey}.send"
    params = {
        "text": "健康打卡推送通知",
        "desp": desp
    }
    # 发送消息
    res = requests.post(send_url, data=params)
    # {"errno":0,"errmsg":"success","dataset":"done"}
    # logging.info(res.text)
    try:
        if not res.json()['errno']:
            logging.info('Server酱推送服务成功')
        else:
            logging.warning('Server酱推送服务失败')
    except:
        logging.warning("Server酱不起作用了，可能是你的sckey出现了问题")


def get_custom_id(token):
    """
    用来获取custom_id，即类似与打卡模板id
    :param token: 用户令牌
    :return: return {
            'customerId': res.json()['userInfo'].get('customerId'),  # 健康打卡模板id
            'customerAppTypeId': res.json()['userInfo'].get('customerAppTypeId') # 校内打卡模板id
        }
    """
    data = {
        "appClassify": "DK",
        "token": token
    }
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/api/clock/school/getUserInfo", data=data)
        # print(res.text)
        return {
            'customerId': res.json()['userInfo'].get('customerId'),
            'customerAppTypeId': res.json()['userInfo'].get('customerAppTypeId')
        }
    except:
        return None


def get_id_list(token, custom_id):
    """
    通过校内模板id获取校内打卡具体的每个时间段id
    :param token: 用户令牌
    :param custom_id: 校内打卡模板id
    :return: 返回校内打卡id列表
    """
    post_data = {
        "customerAppTypeId": custom_id,
        "longitude": "",
        "latitude": "",
        "token": token
    }
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/api/clock/school/rules", data=post_data)
        # print(res.text)
        return res.json()['customerAppTypeDto']['ruleList']
    except:
        return None


def get_id_list_v1(token):
    """
    通过校内模板id获取校内打卡具体的每个时间段id（初版,暂留）
    :param token: 用户令牌
    :return: 返回校内打卡id列表
    """
    post_data = {
        "appClassify": "DK",
        "token": token
    }
    try:
        res = requests.post("https://reportedh5.17wanxiao.com/api/clock/school/childApps", data=post_data)
        if res.json()['appList']:
            id_list = sorted(res.json()['appList'][-1]['customerAppTypeRuleList'], key=lambda x: x['id'])
            res_dict = [{'id': j['id'], "templateid": f"clockSign{i + 1}"} for i, j in enumerate(id_list)]
            return res_dict
        return None
    except:
        return None


def get_ap():
    """
    获取当前时间，用于校内打卡
    :return: 返回布尔列表：[am, pm, ev]
    """
    now_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    am = 0 <= now_time.hour < 12
    pm = 12 <= now_time.hour < 17
    ev = 17 <= now_time.hour <= 23
    return [am, pm, ev]


def run():
    initLogging()
    now_time = datetime.datetime.now()
    bj_time = now_time + datetime.timedelta(hours=8)
    log_info = [f"""
------
#### 现在时间：
```
{bj_time.strftime("%Y-%m-%d %H:%M:%S %p")}
```"""]
    ua = '15072775373,15527906189,18040512514,18627861728,17671677417,17671118149,15623714350,16602772631,17771491749,13071245220,15827997046,13597650397,18571472753,13016447007,13264680201,13027100198,13027102996,15549646441,13098855597,17671017655,13597919381,13016442373,13886278214,18571811736,15662455715,13037109956,15071336026,15826743755,13037106187,18971375850,13308639936,18910069372,18827472886,17371702756,19971080025,17683835531,15072770769,13037102996,13037103197,17754415571,13037103135,13163219853,13100658459,13617277135,13487037113,17683828153,17683966285,13886798500,17683916403,17607101308,13986225805,18327628148,13545146099,18571364720,15897915750,13037100906,18272283798,13037107915,15072482479,13037107876,18872512949,13047150110,18872547994,13037102995,13407180193,18507139722,13581256080,17671874070,13098858727,17607115821,15870171550,15571726217,13207275311,13071246372,17683893252,15827169522,15272526496,13297061587,13037156956,13657247478,17671442287,18186610691,15392764677,13071254828,18971958125,13237146026,13135892005,18272409876,13016448081,18627944876,15071214664,17607106052,15549462725,18717190007,17683769301,13016431639,13018021577,17683985691,17671348210,18672432334,15072877765,18372677621,13545621021,13027101658,13027101708,13027101878,13027127565,13018055976,13397177412,16607239810,17671385957,15717103675,13016427182,18671358065,17683743609,13212733392,13071240692,18371235038,13016437510,13026384181,17671704652,13071254591,15196005458,15182843690,18507153449,17362384531,17762665630,15377647953,13071242005,13018050710,17605870815,19110502041,13018028296,18571636113,18572926771,13296600147,13329972960,13098857677,18507192403,18007219891,13027120365,13016421029,13260551661,13016428339,13163290967,13277957201,17607169332,15527906641,15186421325,13018018896,15971609073,13027125276,15272190828,13016433982,17607148563,15527551846,18627164050,15527108479,15527659927,15907243097,13164105069,13018032556,13018019228,13018057527,13018058307,13027103386,13027100907,17683765685,18571147680,18502701035,13027127008,13871172524,13297083278,13437220622,13277327182,17362415293,13886717538,13164605708,13071241701,18571541250,15392713521,13071240965,15623622992,13071240397,13016448136,17671887416,18582542401,13476462139,13027122875,13027126977,13223525994,13036168357,13037138517,13884488381,18671454897,13037130535,13037150696,13037113596,13018021598,15607182196,13797921615,15972802814,15826814813,13027131587,18727065403,13071214220,13797172776,13016438137,13779563267,15527116848,17730375092,15390880124,15972145961,13026384965,13016409211,18066022068,13018035537,18062049051,13098832026,13098850186,17354429202,15527099946,15387045325,18831012077,15271608372,13037103975,18007023396,18871317409,13016435197,13016451033,13036110367,17692679528,15997387736,13409751952,15102783986,15010737128,15672305545,15571303961,13027101018,13016422622,13007181162,13071264377,15527887411,15527116748,17607210517,18571650516,13972852346,13016436122,13871986164,18171084681,15631651235,13777486361,15623504350,13732320906,13018025237,18627871625,15327075983,15392954253,13476624279,17671740291,13027102906,13027102127,13027117997,13016421023,17607149963,18007195022,13071249337,17740692970,13071247620,18171656053,17769637026,15572507338,15827494062,13016417937,18062413042,17363326447,18627828781,13638634684,18049361828,13407119188,13476624279'
    pw = 'wangli1231230,asdf123123,wsgt336699,ky123456,123456yzd,17671118149zjh,136665374a,xml123456,17771491749@qq.com,DAI932266027,lk983554873,qwer123456789,whp549673269,19990221hjh,123456zzw. ,zm123456,ck117120,991026xjl,abc12345,xuwenjing812,sjj19990909,15926201367xha,love0223,funny1123,xiaoQIAO521,,dfqhxd123.,MUSAGIsang0802,czl10212817103,WHQ19990204V,741852963wjy,1234567q,Ys19990117,wsxftgbji66,cheng123,wjk1761012443,183883xc..,zx991229.,j13037102996,PwGbk25866,fengrunfeng16,zzq123456,caca310232050,153624...,689757qq,yy123456789,qwer1234,jcm123456,ttkxtjh123,mk7415369,nimasile123,qlj275798194,liu123456,hu303298020,hwqhwq123,123456hh,102030zxc,xxs963258,20000209wx.,459459..,yaoling0607@@@,123456wh,zhoujinlin0,tjx111111,wyx13037102995,,wj10212817215,zm1259761947,cl123456789,czw10212817213,yxc10212817214,xc10212817208,wyr042099,zyz17204,zzw10212817206,yuyiwei233,lg10212817221,zsc10212817209,ljw10212817222,sxh10212817225,80723pengliu,sss123456,hyf10212817220,llc10212817212,zxh12345,gw10212817231,hm10212817234,123456phq,keliheng19970424,33ttt...,fjl123456,zst110110,xyt10212817227,Wmxy1234,dy10212817211,Tzzzj20200906,lzgsm123,sr10212817226,,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,hxrj1174,,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx 1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,hxdx1171,,psting123,hgx123456,jmh123456,zyy123456,zq123456789,zqh123456,lzq991018,cq123456,hzf1297873205,chenpan666,ylyl1128,huaxiaruanjian1173,sx123456,12345678zrj,123789zzk,cc12345678,czy123456,a10212817318,10212817319ldc,12345678,an300008,nmsllaofive123,lj@123456,yl123456,qaz123456..,scc12345,yuxuan1999,libiao19981124,zqx123456,lx0415@...,4962kaodian,oq10212817334,123456789,,123456liu,fjh12345,sjc123456,wodejia303,mjm123456,@13676848866ljq,lmw979200,229yanxiwen,zjj123456,xqf123456,2580502lang.,a15826814813,ghh123456,csj123456,hct123456,wyh123456789,wk123456,aaa88888888,mxx123456,123456ht,jcylkh6125,ym12345678,lxy0909@,rfy199967,yang3681908,qazwsx123,hk123456,srz13098832026,ljzlhy108,wmxy123456,,hx123456,@10212417213,12345678zdh,lk123456,wcbx123456,w1234567,qwer1234,zh12345678.,daixiao.,k12345678,ydp123456789,yy123456,wmxy12345678,zp666666,z1111111,asd123456,159357..,rabbit1221,123456wyq,dwt@@123,qwe12345679,Caorongyan0017,zhr993200,1013007130asd,hkl962464,Jsl654321,12345678qwertyui,qwer6164,z1234567890,LPlp@314159,,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456,dx123456'
    sk = 'SCU78325T36718c82406e69c1ddf7ea98d31d97505e252231052cb'
    username_list = ua.split(',')
    password_list = pw.split(',')
    sckey = sk
    for username, password in zip([i.strip() for i in username_list if i != ''],
                                  [i.strip() for i in password_list if i != '']):
        check_dict = check_in(username, password)
        if not check_dict:
            pass
        else:
            for check in check_dict:
                if check['post_dict'].get('checkbox'):
                    post_msg = "\n".join(
                        [f"| {i['description']} | {i['value']} |" for i in check['post_dict'].get('checkbox')])
                else:
                    post_msg = "暂无详情"
                name = check['post_dict'].get('username')
                if not name:
                    name = check['post_dict']['name']
                log_info.append(f"""#### {name}{check['type']}打卡信息：
```
{json.dumps(check['check_json'], sort_keys=True, indent=4, ensure_ascii=False)}
```
------
| Text                           | Message |
| :----------------------------------- | :--- |
{post_msg}
------
```
{check['res']}
```""")
    log_info.append(f"""
>
> [GitHub项目地址](https://github.com/ReaJason/17wanxiaoCheckin-Actions)
>
>期待你给项目的star✨
""")
    server_push(sckey, "\n".join(log_info))


if __name__ == '__main__':
    run()
