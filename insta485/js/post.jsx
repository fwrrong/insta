import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import UpperBar from "./upperBar";
import LikeButton from "./likeButton";
import Comments from "./comments";
import PostComment from "./postComment";
import NumLikes from "./numLikes";


// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function Post({ url }) {
  /* Display image and post owner of a single post */

  const [comments, setComments] = useState([])
  // const [commentsUrl, setCommentsUrl] = useState("");
  const [created, setCreated] = useState("");
  const [imgUrl, setImgUrl] = useState("");
  // const [likes, setLikes] = useState();
  const [owner, setOwner] = useState("");
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [ownerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [numLikes, setNumLikes] = useState(0);
  const [lognameLikesThis, setLognameLikesThis] = useState(false);
  const [likesUrl, setLikesUrl] = useState("");
  const [postid, setPostid] = useState(1);
  const [commentText, setCommentText] = React.useState('');

  useEffect(() => {
    let ignoreStaleRequest = false;

    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (!ignoreStaleRequest) {
          setComments(data.comments);
          setCreated(data.created);
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
          setOwnerImgUrl(data.ownerImgUrl);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
          setNumLikes(data.likes.numLikes);
          setLognameLikesThis(data.likes.lognameLikesThis);
          setLikesUrl(data.likes.url);
          setPostid(data.postid);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      ignoreStaleRequest = true;
    };
  }, [url]);

  const handleClickLike = React.useCallback(() => {
    const newLikeStatus = !lognameLikesThis;
    if (newLikeStatus) {
        // Liking the post
        // console.log(newLikeStatus)
        
        fetch(`/api/v1/likes/?postid=${url.split("/").slice(-2)[0]}`, {
            method: 'POST',
            credentials: "same-origin",
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                setLikesUrl(data.url);
                setNumLikes(numLikes+1)
            }
            setLognameLikesThis(true);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else { 
        fetch(likesUrl, {
            method: 'DELETE'
        })
        .then((response) => {
          console.log("Made request");
          if (!response.ok) throw Error(response.statusText);
          return response.text().then((text) => (text ? JSON.parse(text) : {}));
        })
      
        // .then(response => {
        //     if (response.status === 204) {  // No content, successful deletion
        //         setLognameLikesThis(false);
        //         setLikesUrl("");
        //         setNumLikes(numLikes-1)
        //     }
        // })
        .catch(error => {
            console.error('Error:', error);
        });
    }
  }, [lognameLikesThis, likesUrl, numLikes, url]);

  const handleDeleteComment = React.useCallback((commentUrl, commentId) => {
    fetch(commentUrl, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.status === 204) {  // No content, successful deletion
              const updatedComments = comments.filter(comment => comment.commentid !== commentId);
              setComments(updatedComments);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
  }, [comments]);

  const handleSubmitComment = React.useCallback((event) => {
    event.preventDefault();
    console.log('PostID:', postid);
    fetch(`/api/v1/comments/?postid=${url.split("/").slice(-2)[0]}`, {
      method: 'POST',
      credentials: "same-origin",
      body: JSON.stringify({ text: commentText }),
      headers: {
          'Content-Type': 'application/json'
      }
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text) });
        }
        return response.json();
    })
    .then(data => {
      // console.log("Received data:", data);
      setComments([...comments, data]);
      setCommentText('')
    })
    .catch(error => {
            console.error('Error:', error);
    });
  }, [comments, postid, commentText]);

  const handleImageDoubleClick = () => {
    if (lognameLikesThis) return;
    handleClickLike(); 
  };
  
  // Render post image and post owner
  return (
    <div className="post">
      <UpperBar 
        ownerImgUrl = {ownerImgUrl}
        owner = {owner}
        ownerShowUrl = {ownerShowUrl}
        postShowUrl = {postShowUrl}
        created = {created}
      />
      <img 
        src={imgUrl}
        alt="post_image"
        onDoubleClick={handleImageDoubleClick}
      />
      <NumLikes
        numLikes={ numLikes }
      />
      <Comments
        comments={ comments }
        handleDeleteComment={ handleDeleteComment }
      />
      <LikeButton
        lognameLikesThis={ lognameLikesThis }
        handleClickLike={ handleClickLike }
      />
      <PostComment
        handleSubmitComment={ handleSubmitComment }
        commentText={commentText}
        setCommentText={setCommentText}
      />
    </div>
  );
}

Post.propTypes = {
  url: PropTypes.string.isRequired,
};
