"""REST API for posts."""
import pathlib
import uuid
import hashlib
import flask
import insta485
import arrow


@insta485.app.route('/api/v1/posts/<int:postid>/')
def get_post(postid):
    """Return post on postid."""
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

    # check postid
    exist = connection.execute(
        '''
        SELECT postid FROM posts
        WHERE postid = ?;
        ''',
        (postid,)
    ).fetchone()
    if not exist:
        return flask.jsonify({"message": "Not Found", "status_code": 404}), 404

    # comments
    comments = connection.execute(
        '''
        SELECT commentid, owner, text FROM comments
        WHERE comments.postid = ?;
        ''',
        (postid, )
    ).fetchall()
    for comment in comments:
        if comment["owner"] == logname:
            comment["lognameOwnsThis"] = True
        else:
            comment["lognameOwnsThis"] = False
        comment["ownerShowUrl"] = f"/users/{comment['owner']}/"
        comment["url"] = f"/api/v1/comments/{comment['commentid']}/"

    # comments_url
    comments_url = f"/api/v1/comments/?postid={postid}"

    # created
    created = connection.execute(
        '''
        SELECT created AS timestamp FROM posts
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    created = created['timestamp']

    # imgUrl
    imgUrl= connection.execute(
        '''
        SELECT filename AS img_url FROM posts
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    imgUrl = "/uploads/" + imgUrl['img_url']

    # likes
    likes = {}
    numLikes = connection.execute(
        '''
        SELECT COUNT(DISTINCT likeid) AS likes FROM likes
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    likes["numLikes"] = numLikes['likes']
    likeid = connection.execute(
        '''
        SELECT likeid FROM likes
        WHERE postid = ? AND owner = ?;
        ''',
        (postid, logname)
    ).fetchone()
    if likeid is not None:
        likes["lognameLikesThis"] = True
        likes['url'] = f"/api/v1/likes/{likeid['likeid']}/"
    else:
        likes["lognameLikesThis"] = False
        likes['url'] = None

    # owner
    owner = connection.execute(
        '''
        SELECT owner FROM posts
        WHERE posts.postid = ?;
        ''',
        (postid, )
    ).fetchone()
    if owner is None:
        return flask.redirect(flask.url_for('get_login'))
    owner = owner['owner']

    # owner_img_url
    ownerImgUrl = connection.execute(
        '''
        SELECT filename AS owner_img_url FROM users
        WHERE username = ?;
        ''',
        (owner, )
    ).fetchone()
    ownerImgUrl = "/uploads/" + ownerImgUrl['owner_img_url']

    # ownerShowUrl
    ownerShowUrl = f"/users/{logname}/"
    # postShowUrl
    postShowUrl = f"/posts/{postid}/"
    # url
    url = flask.url_for('get_post', postid=postid)

    context = {"comments": comments,
                "comments_url": comments_url,
                "created": created,
                "imgUrl": imgUrl,
                "likes": likes,
                "owner": owner,
                "ownerImgUrl": ownerImgUrl,
                "ownerShowUrl": ownerShowUrl,
                "postShowUrl": postShowUrl,
                "postid": postid,
                "url": url
                }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/')
def get_index():
    auth = flask.request.authorization
    connection = insta485.model.get_db()
    # check auth
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
    
    size = flask.request.args.get("size", default=10, type=int)
    page = flask.request.args.get("page", default=0,type=int)
    # if (size and size < 1) or (page and page < 0):
    if size < 1 or page < 0: 
        return flask.jsonify({"message": "Bad Request","status_code": 400}), 400
    offset = page * size
    # get postid_lte
    postid_lte = flask.request.args.get("postid_lte", type=int)
    if postid_lte is None:
        most_recent_post = connection.execute(
            '''
            SELECT postid 
            FROM posts 
            ORDER BY postid DESC
            LIMIT 1;
            '''
        ).fetchone()
        if most_recent_post:
            postid_lte = most_recent_post['postid']
        else:
            postid_lte = 0
    
    # Query database
    posts = connection.execute(
        '''
        SELECT postid
        FROM posts
        WHERE (owner IN (
            SELECT username2
            FROM following
            WHERE username1 = ?
        ) OR owner = ?)
        AND postid <= ?
        ORDER BY postid DESC
        LIMIT ? OFFSET ?;
        ''',
        (logname, logname, postid_lte, size, offset)
    ).fetchall()
        
    results = [{"postid": post["postid"], "url": f"/api/v1/posts/{post['postid']}/"} for post in posts]
    # results = []
    # for post in posts:
    #     if post["postid"] <= postid_lte:
    #         results.append({"postid": post["postid"], "url": f"/api/v1/posts/{post['postid']}/"})
    
    # get next
    if len(results) < size:
        next = ""
    else:
        next = f"/api/v1/posts/?size={size}&page={page+1}"
        # if size:
        #     next += f"?size={size}"
        # if page >= 0:
        #     next += f"&page={page+1}"
        next += f"&postid_lte={postid_lte}"
    url = flask.url_for('get_index', **flask.request.args)
    context = {"next": next, "results" : results, "url": url}
    #"page": page, "size": size, "postid_lte": postid_lte
    return flask.jsonify(**context)

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

