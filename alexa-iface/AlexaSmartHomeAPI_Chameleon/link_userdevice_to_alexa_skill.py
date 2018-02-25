from nodb import NoDB
import requests
from service import make_af_request
import os

if __name__ == "__main__":
    endpoint = 'dev001'
    bearer = {'token':
              'Atza|IwEBIO6VGVsR_Ceg9P1Serr5QJPbQ6n12LCL2247Xz8eXzj9FS7VP1xbL0XsYQK4u5LUZDWiJIP7JF1Yb-iE2C7iPnD8nmlrzrXgqOUvkKpuCwD8OD0MWIQnD4fuao1ayayfRYVO3Hv3nMBykiEl5hVaMomRwIjbLL7nxAVnBJymIxsgFGteK7E6qoDZLabVlrlPnoRCDyIdvCYSxFg7ztNe9fpG2wsAY0pYZnsqNTr_SXGIiJlBLsA1k9b6tMAFW4V_ZitjoA5mrQThQpAJQuRdv78eZLgrk2qGZlCgekJn9HmfYun9ZH8a-Vw7z2g6DRdwu4kx4WFlEiHeaTLcjB8WW9HKf_WArNjNdwCLEj3eSwRV51Y-GG-pZg2fN2GjuEaZufUYiiNIwwtp3fapD4ZVR9DaUIjraEn8s9nmzI4AuGVRJ0crgE4NwDFV9vbQSQC2T8g0_5shGZXqgjhqfRzuLGRE74HpQArHXMLVlSO0Rw7a5E2nBfvfLZ9YOwxfy2Df7ss'}


    # verify it with amazon
    from urllib.parse import quote_plus

    resp = requests.get("https://api.amazon.com/auth/o2/tokeninfo?access_token=" +
                        quote_plus(bearer['token']))
    print(resp)
    verify = resp.json()['aud']
    if verify != os.environ['CLIENT_ID']:
        print("*********** invalid auth token %s" % verify)
        raise Exception("Invalid Token")

    # get user info
    headers = {'Authorization': 'bearer ' + bearer['token'],
               'Content-Type': 'application/json'}
    user_info = requests.get('https://api.amazon.com/user/profile', headers=headers).json()

    # Save an object!
    store = NoDB()
    store.bucket = "chameleon-moto"
    store.serializer = 'json'
    store.index = "email"
    user = {"endpointid": endpoint, "email": user_info['email'],
            'name': user_info['name'], 'amzn_userid': user_info['user_id']
            }
    print("********** about to store \n" + str(user))
    store.save(user)  # True
    loaded_user = store.load(user_info['email'])
    assert loaded_user['endpointid'] == 'dev001'
    print("users saved successfully")


