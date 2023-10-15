"""
Insta485 index (main) view.

URLs include:
/
"""
import pathlib
import uuid
import hashlib
import os
import flask
import arrow
from flask import abort, Response, request
import insta485


@insta485.app.route('/')
def show_index():
    """Show main page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))

    #     return flask.redirect("login.html")
    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    logname = flask.session['username']
    posts = connection.execute(
        """
        SELECT
            posts.postid,
            posts.owner,
            users.filename AS owner_img_url,
            posts.filename AS img_url,
            posts.created AS timestamp,
            COUNT(DISTINCT likes.likeid) AS number_of_likes,
            GROUP_CONCAT(likes.owner) AS like_owners
        FROM posts
        LEFT JOIN likes ON posts.postid = likes.postid
        LEFT JOIN users ON posts.owner = users.username
        INNER JOIN following ON following.username2 = posts.owner
        OR posts.owner = ?
        WHERE following.username1 = ?
        GROUP BY posts.postid, posts.filename, posts.owner, users.filename
        ORDER BY posts.postid DESC;
        """,
        (logname, logname)
    ).fetchall()
    for post in posts:
        if post["like_owners"]:
            post["like_owners"] = post["like_owners"].split(",")
        else:
            post["like_owners"] = []
        post['timestamp'] = arrow.get(post['timestamp']).humanize()
        comments = connection.execute(
            '''
            SELECT owner, text FROM comments
            WHERE comments.postid = ?
            ORDER BY commentid ASC;
            ''',
            (post['postid'], )
        )
        comments = comments.fetchall()
        post['comments'] = comments
    # Add database info to context
    context = {"logname": logname, "posts": posts}
    return flask.render_template("index.html", **context)


@insta485.app.route('/uploads/<filename>')
def download_file(filename):
    """Download <filename> from UPLOAD_FOLDER."""
    if 'username' not in flask.session:
        abort(403)
    path = insta485.app.config["UPLOAD_FOLDER"]/filename
    # path = os.path.join('/var/uploads/', filename)
    if not os.path.exists(path):
        abort(404)
    return flask.send_from_directory(
        insta485.app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
        )


@insta485.app.route('/users/<username>/')
def show_user(username):
    """Show user page."""
    connection = insta485.model.get_db()
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']

    # logname_follows_username
    logname_follows_username = connection.execute(
        "SELECT username1, username2 FROM following "
        "WHERE username1 = ? AND username2 = ?;",
        (logname, username)
    ).fetchall()
    logname_follows_username = bool(logname_follows_username)

    # fullname
    fullname_data = connection.execute(
        "SELECT fullname From users WHERE username = ?;",
        (username, )
    )
    fullname = fullname_data.fetchone()
    if fullname is None:
        abort(404)
    else:
        fullname = fullname["fullname"]

    # following
    following_data = connection.execute(
        "SELECT COUNT(username1) FROM following "
        "WHERE username1 = ?;",
        (username, )
    )
    following = following_data.fetchone()
    following = following["COUNT(username1)"] if following else 0

    # follower
    follower_data = connection.execute(
        '''
        SELECT COUNT(username2) FROM following
        WHERE username2 = ?;
        ''',
        (username, )
    )
    followers = follower_data.fetchone()
    followers = followers["COUNT(username2)"] if followers else 0

    # total posts
    total_posts_data = connection.execute(
        '''
        SELECT COUNT(owner)
        FROM posts
        WHERE owner = ?;
        ''',
        (username, )
    )
    total_posts = total_posts_data.fetchone()
    total_posts = total_posts['COUNT(owner)'] if total_posts else 0

    # posts
    posts_data = connection.execute(
        '''
        SELECT
            postid,
            filename AS img_url
        FROM posts
        WHERE owner = ?;
        ''',
        (username, )
    )
    posts = posts_data.fetchall()
    posts = posts if posts else []

    context = {"logname": logname,
               "username": username,
               "logname_follows_username": logname_follows_username,
               'fullname': fullname,
               "following": following,
               "followers": followers,
               "total_posts": total_posts,
               "posts": posts}
    return flask.render_template("user.html", **context)


@insta485.app.route('/users/<username>/followers/')
def show_followers(username):
    """Show follower page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    connection = insta485.model.get_db()
    logname = flask.session['username']

    find = connection.execute(
            '''
            SELECT username
            FROM users
            WHERE username = ?;
            ''',
            (username, )
    ).fetchone()
    if not find:
        abort(404)

    followers = connection.execute(
            '''
            SELECT username1 AS username, users.filename AS user_img_url
            FROM following
            LEFT JOIN users ON users.username = username1
            WHERE username2 = ?;
            ''',
            (username, )
    ).fetchall()
    followers = followers if followers else {}
    for follower in followers:
        logname_follows_username = connection.execute(
            '''
            SELECT username1, username2
            FROM following
            WHERE username1 = ? AND username2 = ?;
            ''',
            (logname, follower['username'])
        ).fetchone()
        if logname_follows_username:
            follower['logname_follows_username'] = True
        else:
            follower['logname_follows_username'] = False

    context = {'logname': logname,
               'username': username,
               'followers': followers
               }
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<username>/following/')
def show_following(username):
    """Show following page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    connection = insta485.model.get_db()
    logname = flask.session['username']

    find = connection.execute(
            '''
            SELECT username
            FROM users
            WHERE username = ?;
            ''',
            (username, )
    ).fetchone()
    if not find:
        abort(404)

    followings = connection.execute(
            '''
            SELECT username2 AS username, users.filename AS user_img_url
            FROM following
            LEFT JOIN users ON users.username = username2
            WHERE username1 = ?;
            ''',
            (username, )
    ).fetchall()
    followings = followings if followings else {}

    for following in followings:
        logname_follows_username = connection.execute(
            '''
            SELECT username1, username2
            FROM following
            WHERE username1 = ? AND username2 = ?;
            ''',
            (logname, following['username'])
        ).fetchone()
        if logname_follows_username:
            following['logname_follows_username'] = True
        else:
            following['logname_follows_username'] = False

    context = {'logname': logname,
               'username': username,
               'following': followings}
    return flask.render_template("following.html", **context)


@insta485.app.route('/posts/<postid>/')
def show_post(postid):
    """Include the same information for this one post as main page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']
    connection = insta485.model.get_db()

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
    owner_img_url = connection.execute(
        '''
        SELECT filename AS owner_img_url FROM users
        WHERE username = ?;
        ''',
        (owner, )
    ).fetchone()
    owner_img_url = owner_img_url['owner_img_url']

    # img_url
    img_url_data = connection.execute(
        '''
        SELECT filename AS img_url FROM posts
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    img_url = img_url_data['img_url']

    # timestamp
    timestamp = connection.execute(
        '''
        SELECT created AS timestamp FROM posts
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    timestamp = timestamp['timestamp']
    timestamp = arrow.get(timestamp).humanize()

    # likes
    likes = connection.execute(
        '''
        SELECT COUNT(DISTINCT likeid) AS likes FROM likes
        WHERE postid = ?;
        ''',
        (postid, )
    ).fetchone()
    likes = likes['likes']

    # comments
    comments = connection.execute(
        '''
        SELECT owner, text, commentid FROM comments
        WHERE comments.postid = ?;
        ''',
        (postid, )
    ).fetchall()

    like_owners = connection.execute(
        """
        SELECT
            GROUP_CONCAT(owner) AS like_owners
        FROM likes
        WHERE postid = ?;
        """,
        (postid, )
    ).fetchone()
    if like_owners['like_owners']:
        like_owners = like_owners['like_owners'].split(",")
    else:
        like_owners = []

    context = {"logname": logname,
               "postid": postid,
               "owner": owner,
               "owner_img_url": owner_img_url,
               "img_url": img_url,
               "timestamp": timestamp,
               "likes": likes,
               "comments": comments,
               "like_owners": like_owners
               }
    return flask.render_template("post.html", **context)


@insta485.app.route('/explore/')
def get_explore():
    """Get explore page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    connection = insta485.model.get_db()
    logname = flask.session['username']
    not_following = connection.execute(
        '''
        SELECT DISTINCT users.username, filename AS user_img_url
        FROM users
        LEFT JOIN following ON following.username1 = ?
        AND users.username = following.username2
        WHERE following.username2 IS NULL AND users.username != ?;

        ''',
        (logname, logname)
    ). fetchall()
    context = {"logname": logname, "not_following": not_following}
    return flask.render_template("explore.html", **context)


@insta485.app.route('/accounts/login/')
def get_login():
    """Get login page."""
    if 'username' in flask.session:
        return flask.redirect("/")
    return flask.render_template("login.html")


@insta485.app.route('/accounts/logout/', methods=['POST'])
def get_logout():
    """Log out user. Immediately redirect to /accounts/login/."""
    flask.session.clear()
    return flask.redirect(flask.url_for('get_login'))


@insta485.app.route('/accounts/create/')
def get_create():
    """Get create page."""
    if 'username' in flask.session:
        return flask.redirect("/accounts/edit/")
    return flask.render_template("create.html")


@insta485.app.route('/accounts/delete/')
def get_delete():
    """Confirm page includes username and delete form."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']
    context = {'logname': logname}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/edit/')
def get_edit():
    """
    Get edit page.

    1, Include user’s current photo and username.
    2, Include a form with photo upload, name and email.
    3, Link to /accounts/password/ and /accounts/delete/.
    """
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    username = flask.session['username']
    connection = insta485.model.get_db()
    user_info = connection.execute(
        '''
        SELECT
        filename as user_img_url,
        fullname,
        email
        FROM users
        WHERE username = ?
        ''',
        (username, )
    ).fetchone()

    context = {"username": username, "user_info": user_info}
    return flask.render_template('edit.html', **context)


@insta485.app.route('/accounts/password/')
def get_password():
    """
    Get password page.

    1, Include password form.
    2, Link to /accounts/edit/.
    """
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    logname = flask.session['username']
    context = {"logname": logname}
    return flask.render_template('password.html', **context)


@insta485.app.route('/accounts/auth/')
def get_auth():
    """
    Account auth.

    Return a 200 status code with no content (i.e. an
    empty response) if the user is logged in.
    abort(403) if the user is not logged in.
    """
    if 'username' not in flask.session:
        abort(403)
    return Response(status=200)


@insta485.app.route('/likes/', methods=['POST'])
def post_likes():
    """
    Like POST.

    1, This endpoint only accepts POST requests.
    2, Create or delete a like and immediately redirect to URL.
    3, If operation is like, create a like for postid.
    4, If operation is unlike, delete a like for postid.
    5, Then, redirect to URL.
    6, If the value of ?target is not set, redirect to /.
    7, If someone tries to like a post they have already
    liked or unlike a post they have not liked, then abort(409)
    """
    if flask.request.method != 'POST':
        return "Method Not Allowed", 405

    postid = flask.request.form.get('postid')
    operation = flask.request.form.get('operation')

    # if not postid:
    #     return "Post ID missing", 400

    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']

    connection = insta485.model.get_db()
    find = connection.execute(
            '''
            SELECT owner, postid FROM likes
            WHERE owner = ? AND postid = ?;
            ''',
            (logname, postid)
        ).fetchone()
    if operation == 'like':
        if find:
            abort(409)
        connection.execute(
            '''
            INSERT INTO likes(owner, postid)
            VALUES
            (?, ?);
            ''',
            (logname, postid)
        )
    elif operation == 'unlike':
        if not find:
            abort(409)
        connection.execute(
            '''
            DELETE FROM likes
            WHERE owner = ? AND postid = ?;
            ''',
            (logname, postid)
        )
    connection.commit()
    target_url = request.args.get('target')
    if target_url:
        return flask.redirect(target_url)
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/comments/', methods=['POST'])
def post_comments():
    """
    Comment POST.

    1, Create or delete a comment on a post and immediately redirect to URL.
    2, If operation is create, then create a new comment on
    postid with the content text.
    3, If operation is delete, then delete comment with ID commentid.
    4, If a user tries to create an empty comment, then abort(400).
    5, If a user tries to delete a comment that they do not own,
    then abort(403).
    6, If the value of ?target is not set, redirect to /.
    """
    # if flask.request.method != 'POST':
    #     return "Method Not Allowed", 405
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']
    operation = flask.request.form.get('operation')
    connection = insta485.model.get_db()
    if operation == 'create':
        postid = flask.request.form.get('postid')
        text = flask.request.form.get('text')
        if not postid:
            return "Post ID missing", 400
        if not text:
            abort(400)

        connection.execute(
            '''
            INSERT INTO comments(owner, postid, text)
            VALUES
            (?, ?, ?);
            ''',
            (logname, postid, text)
        )
    elif operation == 'delete':
        commentid = flask.request.form.get('commentid')
        owner = connection.execute(
            '''
            SELECT owner FROM comments
            WHERE commentid = ?;
            ''',
            (commentid,)
        ).fetchone()
        if owner['owner'] != logname:
            abort(403)
        connection.execute(
            '''
            DELETE FROM comments
            WHERE owner = ? AND commentid = ?;
            ''',
            (logname, commentid)
        )
    connection.commit()

    target_url = request.args.get('target')
    if target_url:
        return flask.redirect(target_url)
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/posts/', methods=['POST'])
def post_posts():
    """
    Post POST.

    1, Create or delete a post and immediately redirect to URL.
    2, If operation is create, save the image file to disk
    and redirect to URL.
    3, If a user tries to create a post with an empty file,
    then abort(400).
    4, If operation is delete, delete the image file for postid
    from the filesystem. Delete everything in the database
    related to this post.
    5, If the value of ?target is not set,
    redirect to /users/<logname>/.
    6, If a user tries to delete a post that they do not own, then abort(403).
    """
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']
    operation = flask.request.form.get('operation')
    connection = insta485.model.get_db()
    if operation == 'create':
        # Unpack flask object
        fileobj = flask.request.files["file"]
        # check if empty
        if fileobj is None or fileobj.filename == "":
            abort(400)
        # save to disk
        filename = fileobj.filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)

        connection.execute(
            '''
            INSERT INTO posts(filename, owner)
            VALUES (?, ?);
            ''',
            (filename, logname)
        )
    elif operation == 'delete':
        postid = flask.request.form.get('postid')
        # get filename fron database
        post = connection.execute(
            '''
            SELECT filename, owner FROM posts
            WHERE postid = ?;
            ''',
            (postid, )
        ).fetchone()
        filename = post['filename']
        # If a user tries to delete a post that they do not own
        owner = post['owner']
        if owner != logname:
            abort(403)
        # delete the image file for postid from the filesystem
        path = insta485.app.config["UPLOAD_FOLDER"]/filename
        os.remove(path)
        # Delete everything in the database related to this post.
        connection.execute(
            '''
            DELETE FROM posts
            WHERE postid = ?;
            ''',
            (postid, )
        )
    # redirect to URL
    connection.commit()
    target_url = request.args.get('target')
    if target_url:
        return flask.redirect(target_url)
    return flask.redirect(flask.url_for('show_user', username=logname))


@insta485.app.route('/following/', methods=['POST'])
def post_following():
    """
    Following post.

    1, If operation is follow, then make user logname follow user username.
    2, If operation is unfollow, then make user logname unfollow user username.
    3, If a user tries to follow a user that they already follow or
    unfollow a user that they do not follow, then abort(409).
    """
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('get_login'))
    logname = flask.session['username']
    operation = flask.request.form.get('operation')
    username = flask.request.form.get('username')
    connection = insta485.model.get_db()
    find = connection.execute(
        '''
        SELECT username1, username2 FROM following
        WHERE username1 = ? AND username2 = ?;
        ''',
        (logname, username)
    ).fetchone()
    if operation == 'follow':
        if find:
            abort(409)
        # make user logname follow user username
        connection.execute(
            '''
            INSERT INTO following(username1, username2)
            VALUES (?, ?);
            ''',
            (logname, username)
        )
    elif operation == 'unfollow':
        if not find:
            abort(409)
        # make user logname unfollow user username.
        print(username)
        connection.execute(
            '''
            DELETE FROM following
            WHERE username1 = ? AND username2 = ?;
            ''',
            (logname, username)
        )
    connection.commit()
    target_url = request.args.get('target')
    if target_url:
        return flask.redirect(target_url)
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """Perform various account operations and immediately redirect to URL."""
    operation = flask.request.form.get('operation')
    if operation == 'login':
        handle_login()
    elif operation == 'create':
        handle_create()
    elif operation == "delete":
        handle_delete()
    elif operation == 'edit_account':
        handle_edit_account()
    elif operation == 'update_password':
        handle_update_password()
    target_url = request.args.get('target')
    print(target_url)
    if target_url:
        return flask.redirect(target_url)
    return flask.redirect(flask.url_for('show_index'))


def handle_login():
    """Handle login."""
    connection = insta485.model.get_db()
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    # If the username or password fields are empty, abort(400).
    if not username or not password:
        abort(400)
    # If username and password authentication fails, abort(403).
    password_db_string = connection.execute(
        '''
        SELECT password FROM users
        WHERE username = ?;
        ''',
        (username, )
    ).fetchone()
    if (not password_db_string or not
            check_password(password, password_db_string['password'])):
        abort(403)
    # Set a session cookie
    flask.session['username'] = flask.request.form['username']


def handle_create():
    """Handle create."""
    connection = insta485.model.get_db()
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    fullname = flask.request.form.get('fullname')
    email = flask.request.form.get('email')
    fileobj = flask.request.files["file"]
    filename = fileobj.filename
    # If any of the above fields are empty, abort(400).
    if (not username or not password or
            not fullname or not email or not filename):
        abort(400)
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    fileobj.save(path)
    # If a user tries to create an account with an
    # existing username in the database, abort(409)
    find = connection.execute(
        '''
        SELECT username FROM users
        WHERE username = ?;
        ''',
        (username, )
    ).fetchone()
    if find:
        abort(409)
    # Log the user
    flask.session['username'] = flask.request.form['username']
    connection.execute(
        '''
        INSERT INTO users
        (username, fullname, email, filename, password)
        VALUES (?, ?, ?, ?, ?);
        ''',
        (username, fullname,
            email, filename,
            get_password_db_string(password))
    )
    connection.commit()


def handle_delete():
    """Handle account delete."""
    connection = insta485.model.get_db()
    # If the user is not logged in, abort(403).
    if 'username' not in flask.session:
        abort(403)
    user = flask.session['username']
    # Delete user icon file.
    filename = connection.execute(
        '''
        SELECT filename FROM users
        WHERE username = ?;
        ''',
        (user, )
    ).fetchone()
    filename = filename['filename']
    path = insta485.app.config["UPLOAD_FOLDER"]/filename
    os.remove(path)
    # Delete all post files created by this user.
    filename = connection.execute(
        '''
        SELECT GROUP_CONCAT(filename) AS filename FROM posts
        WHERE owner = ?;
        ''',
        (user, )
    ).fetchone()
    filename = filename['filename'].split(',')
    for jpg in filename:
        path = insta485.app.config["UPLOAD_FOLDER"]/jpg
        os.remove(path)
    # Delete all related entries in all tables
    connection.execute(
        '''
        DELETE FROM users WHERE username = ?
        ''',
        (user, )
    )
    connection.commit()
    # Clear session
    flask.session.clear()


def handle_edit_account():
    """Handle edit account."""
    connection = insta485.model.get_db()
    # If the user is not logged in, abort(403).
    if 'username' not in flask.session:
        abort(403)
    username = flask.session['username']
    fullname = flask.request.form.get('fullname')
    email = flask.request.form.get('email')
    fileobj = flask.request.files["file"]
    filename = fileobj.filename

    # If the fullname or email fields are empty, abort(400).
    if not fullname or not email:
        abort(400)

    if filename is None:
        # If no photo file is included,
        # update only the user’s name and email.
        connection.execute(
            '''
            UPDATE users
            SET fullname = ?, email = ?
            WHERE username = ?;
            ''',
            (fullname, email, username)
        )
    else:
        # If a photo file is included
        # Delete the old photo
        old_file = connection.execute(
            '''
            SELECT filename FROM users
            WHERE username = ?;
            ''',
            (username, )
        ).fetchone()
        old_file = old_file['filename']
        path = insta485.app.config["UPLOAD_FOLDER"]/old_file
        os.remove(path)

        # Update the user’s photo, name and email
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        connection.execute(
            '''
            UPDATE users
            SET fullname = ?, email = ?, filename = ?
            WHERE username = ?;
            ''',
            (fullname, email, uuid_basename, username)
        )
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
    connection.commit()


def handle_update_password():
    """Handle update password."""
    connection = insta485.model.get_db()
    # If the user is not logged in, abort(403).
    if 'username' not in flask.session:
        abort(403)
    username = flask.session['username']
    # Use password, new_password1 and new_password2
    password = flask.request.form.get('password')
    password1 = flask.request.form.get('new_password1')
    password2 = flask.request.form.get('new_password2')
    # If any of the above fields are empty, abort(400).
    if not password or not password1 or not password2:
        abort(400)
    # Verify password against the user’s password hash in the database.
    password_db_string = connection.execute(
        '''
        SELECT password FROM users
        WHERE username = ?;
        ''',
        (username, )
    ).fetchone()
    password_db_string = password_db_string['password']
    # If verification fails, abort(403).
    if not check_password(password, password_db_string):
        abort(403)
    # Verify both new passwords match.
    # If verification fails, abort(401).
    if password1 != password2:
        abort(401)
    # Update hashed password entry in database.
    connection.execute(
        '''
        UPDATE users
        SET password = ?
        WHERE username = ?;
        ''',
        (get_password_db_string(password1), username)
    )
    connection.commit()


def get_password_db_string(password):
    """Transfer password to database string."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def check_password(password, password_db_string):
    """Check if the provided password matches the hashed version."""
    # Split the stored password string to extract algorithm, salt, and hash
    password_db_string_list = password_db_string.split('$')
    algorithm = password_db_string_list[0]
    salt = password_db_string_list[1]
    stored_password_hash = password_db_string_list[2]
    # Hash the provided password with the extracted salt
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    provided_password_hash = hash_obj.hexdigest()
    # Check if the hash of the provided password matches the stored hash
    return provided_password_hash == stored_password_hash
