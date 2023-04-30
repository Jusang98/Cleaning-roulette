from flask import Flask, render_template, request,jsonify,redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
import datetime
import jwt

application = Flask(import_name = __name__)

application.config.update(
			DEBUG = True,
			SECRET_KEY = "Sangju"
		)

app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client.cleaner

# 로그인 페이지
@app.route('/')
def loginPage():
    return render_template('login.html')

# 로그인 기능 - 성공시 홈페이지로
@app.route('/login', methods=['POST'])
def login_user():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    
    result = db.user.find_one({'email': email_receive, 'password': pw_hash})
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'email': email_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3000)    #언제까지 유효한지
        }
        #jwt를 암호화
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        token = jwt.encode(payload, "secret", algorithm='HS256')
# .decode('utf8')
        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 회원가입 페이지로    
@app.route('/signUpPage')
def signUpPage():
    return render_template('signUp.html')

#회원가입기능
@app.route('/userRegister', methods = ['POST'])
def register_user():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']
    name_receive = request.form['name_give']
    photo_receive = request.form['photo_give']
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    user = {'email': email_receive, 'password': pw_hash, 'name': name_receive, 'photo': photo_receive}
    db.user.insert_one(user)
    return jsonify({'result': 'success'})

# 홈페이지로 
# todo 서버에서 홈페이지로 추가적으로 넘겨줄 데이터 -> 현재 로그인 상황
@app.route("/home")
def home():
    datas=list(db.feed.find({}))
    winners=list(db.winnerList.find({}))
    for _ in datas:
        db.feed.update_one({"_id":"ObjectId"},{"$set":{"_id":str("_id")}})
    return render_template("home.html", datas=datas, winners = winners)

    
# 어드민제외 유저 리스트 가져오기
@app.route('/userList', methods=['GET'])
def read_users():
    # 어드민 제외 유저 리스트 쿼리문
    # myquery = {"email": { "$not": "admin" }} 
    result = list(db.user.find({},{'_id': False}))
    return jsonify({'result': 'success', 'user': result})

# 당첨자 받아오기 
@app.route("/winnerList", methods=["POST"])
def register_winner():
    receive_winner=request.values["winner_give"]
    winner_info = db.user.find_one({"name": receive_winner})
    winner = {
        "photo":winner_info["photo"],
        "name":receive_winner
    }
    db.winnerList.insert_one(winner)

    return redirect("/")

# 당첨자 DB 전체 삭제
@app.route('/winner/deleteAll', methods=['POST'])
def deleteAll_winnerList():
    db.winnerList.delete_many({})
    return jsonify({'result': 'success'})

#쿠키 이메일 값 가져오기
@app.route('/cookie/get', methods=['POST'])
def getToken():
    token = request.values['mytoken']
    tokenDecode = jwt.decode(token, "secret", algorithms=['HS256'])
    # print(tokenDecode)
    loggedUserEmail = tokenDecode['email'] 
    # print(loggedUserEmail)
    loggedUserInfo = db.user.find_one({"email":loggedUserEmail})
    # print(loggedUserInfo)
    # loggedUserName = 
    # return render_template("home.html", tokenDecode=tokenDecode)

    loggedUser = {
        "name":loggedUserInfo["name"],
        "email":loggedUserInfo["email"],
        "photo":loggedUserInfo["photo"]
    }
    
    # db.loggedUser.insert_one(loggedUser)
    # loggedUserName = 
    
    return jsonify({'result': 'success', 'loggedUser': loggedUser})








@app.route("/uploadPage")
def page_upload():
    return render_template("upload.html")

@app.route("/detail/<string:url_path>")
def page_detail(url_path):
    doc = db.feed.find_one({"_id": ObjectId(url_path)})
    return render_template("detail.html", doc=doc)

@app.route("/api/uploadFile", methods=["POST"])
def upload_file():
    receive_title=request.values["title"]
    receive_content=request.values["content"]
    file = request.files['file']

    doc={
        "title":receive_title,
        "content":receive_content,
        "image":str(file.filename)
    }

    file.save('static/images/' + file.filename)
    db.feed.insert_one(doc)
    return redirect("localhost/home")
 
@app.route('/api/deleteFeed', methods=['POST'])
def delete_feed():
    id_receive = request.form['id_give']
    db.feed.delete_one({"_id": ObjectId(id_receive)})
    return jsonify({'result': 'success'})

# todo 서버에서 홈페이지로 추가적으로 넘겨줄 데이터 -> 현재 로그인 유저 정보(id) 
@app.route('/userlist')
def user_list():
    all_users = list(db.user.find({}))
    return render_template('userlist.html', users = all_users)

@app.route('/api/deleteUser', methods=['POST'])
def delete_user():
    name_receive = request.form['name_give']
    print(name_receive)
    db.user.delete_one({'name': name_receive})
    return jsonify({'result': 'success'})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)

