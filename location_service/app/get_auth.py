import requests as req 
url = "http://172.30.80.11:31006/auth/"
def get_auth_token()->(str,str):
    data = {
        "email":"admin@test.com",
        "password":"password"
    }

    url = "http://172.30.80.11:31006/auth/"
    url = url+"login"
    resp = req.post(url,json=data)
    if resp.ok:
        return resp.json()["accessToken"],None
    return "",str(resp.text)

def check_user_exists(id:int,role:str):
    token = get_auth_token()
    url = "http://172.30.80.11:31006/auth/"
    data = {
        "email":"admin@test.com",
        "password":"password"
    }
    headers = {
        "Authorization":"Bearer "+token[0]
    }
    url = url+f"user/{id}"
    resp = req.get(url,headers=headers)
    if resp.ok:
        data = resp.json()
        data_role = data["role"].lower()
        if data_role == role.lower() or (role.lower()=="bus" and data_role.lower()=="chauffeur"):
            return True,None
        print(resp.json())
        return False,f"User {id} is of type {data_role}"
    return None,"User Doesn't Exist"
# print(get_auth_token())
print(check_user_exists(2,"admin"))