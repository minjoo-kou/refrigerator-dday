from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from bson import ObjectId

app = Flask(__name__)

SECRET_KEY = 'SPARTA'

client = MongoClient('localhost', 27017)
db = client.dbsparta




@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    d_today = datetime.today()
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"user_id": payload["id"]})
        foods = list(db.refrigerator.find({'user_id': user_info['user_id']}).sort('date', 1))
        now = d_today.strftime('%Y%m%d')
        for i in range(len(foods)):
            id = str(foods[i]['_id'])
            foods[i]['_id']=id
            now_date = datetime.today()
            date = foods[i]['date']
            end_date = datetime.strptime(date, "%Y%m%d")
            dday = end_date - now_date
            foods[i]['dday'] = abs(dday.days + 1)
        return render_template('index.html', user_info=user_info, foods=foods, now=now)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'user_id': username_receive, 'user_pw': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "user_id": username_receive,
        "user_pw": password_hash,
        "user_name": username_receive

    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"user_id": username_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})


# 재료 등록하기 작업 됨
@app.route('/board', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"user_id": payload["id"]})
        user_id_receive = user_info['user_id']
        name_receive = request.form['name_give']
        count_receive = request.form['count_give']
        msrmt_receive = request.form['msrmt_give']
        date_receive_temp = request.form['date_give'].split('/')
        date_receive = date_receive_temp[2] + date_receive_temp[0] + date_receive_temp[1]
        memo_receive = request.form['memo_give']
        doc = {
            'user_id': user_id_receive,
            'name': name_receive,
            'count': int(count_receive),
            'msrmt': msrmt_receive,
            'date': date_receive,
            'memo': memo_receive
        }
        db.refrigerator.insert_one(doc)
        return jsonify({'msg': '저장이 완료되었습니다!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/board', methods=['DELETE'])
def test_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"user_id": payload["id"]})
        user_id_receive = user_info['user_id']
        name_receive = request.form['name_give']
        date_receive = request.form['date_give']
        msrmt_receive = request.form['msrmt_give']
        db.refrigerator.delete_one(
            {'user_id': user_id_receive, 'name': name_receive, 'date': date_receive, 'msrmt': msrmt_receive})
        return jsonify({'msg': '삭제되었습니다!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



if __name__ == '__main__':
    app.run('0.0.0.0', port=3000, debug=True)