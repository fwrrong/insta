"""REST API for likes."""
import hashlib
import flask
import insta485


def check_auth(password, password_db_string):
    password_db_string_list = password_db_string.split('$')
    algorithm = password_db_string_list[0]
    salt = password_db_string_list[1]
    stored_password_hash = password_db_string_list[2]
    # Hash the provided password with the extracted salt
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    provided_password_hash = hash_obj.hexdigest()
    return provided_password_hash == stored_password_hash


@insta485.app.route('/api/v1/likes/', methods=['POST'])
def like_post():
    """
    Like POST.
    """
    # check auth
    auth = flask.request.authorization
    connection = insta485.model.get_db()
    if auth:
        username = auth.username
        password = auth.password
        password_row = connection.execute(
            '''
            SELECT password FROM users
            WHERE username = ?;
            ''',
            (username, )
        ).fetchone()
        if not password_row or not check_auth(password, password_row['password']):
            return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
        logname = username
    elif 'username' in flask.session:
        # if do not have auth, check session
        logname = flask.session['username']
    else:
        # both do not have, 403 error
        return flask.jsonify({"message": "Missing authorization", "status_code": 403}), 403

    # 
    postid = flask.request.args.get('postid')

    # check if like already exist in db
    find = connection.execute(
            '''
            SELECT owner, postid FROM likes
            WHERE owner = ? AND postid = ?;
            ''',
            (logname, postid)
        ).fetchone()
    
    if not find:
        #if find this postid
        connection.execute(
            '''
            INSERT INTO likes(owner, postid)
            VALUES
            (?, ?);
            ''',
            (logname, postid)
        )
        connection.commit()
        likeid = connection.execute(
            '''
            SELECT likeid FROM likes
            WHERE owner = ? AND postid = ?;
            ''',
            (logname, postid)
        ).fetchone()
        print(likeid)
        context = {"likeid": likeid['likeid'], "url": f"/api/v1/likes/{likeid['likeid']}/"}
        return flask.jsonify(**context), 201
    else:
        likeid = connection.execute(
            '''
            SELECT likeid FROM likes
            WHERE owner = ? AND postid = ?;
            ''',
            (logname, postid)
        ).fetchone()
        context = {"likeid": likeid['likeid'], "url": f"/api/v1/likes/{likeid['likeid']}/"}
        return flask.jsonify(**context), 200


@insta485.app.route('/api/v1/likes/<likeid>/', methods=['DELETE'])
def like_delete(likeid):
    # check auth
    auth = flask.request.authorization
    connection = insta485.model.get_db()
    if auth:
        username = auth.username
        password = auth.password
        password_row = connection.execute(
            '''
            SELECT password FROM users
            WHERE username = ?;
            ''',
            (username, )
        ).fetchone()
        if not password_row or not check_auth(password, password_row['password']):
            return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
        logname = username
    elif 'username' in flask.session:
        # if do not have auth, check session
        logname = flask.session['username']
    else:
        # both do not have, 403 error
        return flask.jsonify({"message": "Missing authorization", "status_code": 403}), 403

    find = connection.execute(
            '''
            SELECT owner, postid FROM likes
            WHERE likeid = ?;
            ''',
            (likeid, )
        ).fetchone()
    if not find:
        return flask.jsonify({"message": f"Like not found{likeid}", "status_code": 404}), 404
    elif find['owner'] != logname:
        return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
    else:
        connection.execute(
            '''
            DELETE FROM likes
            WHERE likeid = ?;
            ''',
            (likeid, )
        )
        connection.commit()
        return '', 204