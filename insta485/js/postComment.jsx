import React from "react";
import PropTypes from "prop-types";

function PostComment({ handleSubmitComment, commentText, setCommentText  }){
    return(
        <form onSubmit={ handleSubmitComment } data-testid="comment-form">
            <input 
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
            />
        </form>
    )
}

PostComment.propTypes = {
    handleSubmitComment: PropTypes.func.isRequired,
    commentText: PropTypes.string.isRequired,
    setCommentText: PropTypes.func.isRequired
};

export default PostComment
