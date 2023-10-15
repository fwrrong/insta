"""REST API for comments."""
import hashlib
import flask
import insta485
import logging
logging.basicConfig(level=logging.DEBUG)



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


@insta485.app.route('/api/v1/comments/', methods = ['POST'])
def post_comment():
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

    postid = flask.request.args.get('postid')
    text = flask.request.json.get('text')
    if not postid or not text:
        return flask.jsonify({"message": "Missing postid or text", "status_code": 400}), 400
    logging.debug("Received postid: %s, text: %s", postid, text)

    connection.execute(
            '''
            INSERT INTO comments(owner, postid, text)
            VALUES
            (?, ?, ?);
            ''',
            (logname, postid, text)
        )
    connection.commit()
    commentid = connection.execute('SELECT last_insert_rowid()').fetchone()['last_insert_rowid()']

    context = {"commentid": commentid,
                "lognameOwnsThis": True,
                "owner": logname,
                "ownerShowUrl": f"/users/{logname}/",
                "text": text,
                "url": f"/api/v1/comments/{commentid}/"
                }
    return flask.jsonify(**context), 201


@insta485.app.route('/api/v1/comments/<commentid>/', methods = ['DELETE'])
def delete_comment(commentid):
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
            SELECT owner, postid FROM comments
            WHERE commentid = ?;
            ''',
            (commentid, )
        ).fetchone()
    if not find:
        return flask.jsonify({"message": f"Comment not found{commentid}", "status_code": 404}), 404
    elif find['owner'] != logname:
        return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
    else:
        connection.execute(
            '''
            DELETE FROM comments
            WHERE commentid = ?;
            ''',
            (commentid, )
        )
        connection.commit()
        return '', 204