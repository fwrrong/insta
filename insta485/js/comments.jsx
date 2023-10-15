import React from "react";
import PropTypes from "prop-types";


function Comments({ comments, handleDeleteComment }){
    const listItems = comments.map(comment =>
        <li key={ comment.commentid }>
            <a href={comment.ownerShowUrl}>
                <span> {comment.owner} </span>
            </a>
            <span data-testid="comment-text">{comment.text}</span>
            {comment.lognameOwnsThis ? (
                <button type="button" onClick={() => handleDeleteComment(comment.url, comment.commentid)} data-testid="delete-comment-button">
                    delete
                </button>
            ) : null}
        </li>
    );
    
    return (
        <ul>{listItems}</ul>
    )
}

Comments.propTypes = {
    comments: PropTypes.arrayOf(
        PropTypes.shape({
            commentid: PropTypes.number,
            lognameOwnsThis: PropTypes.bool,
            owner: PropTypes.string.isRequired,
            ownerShowUrl: PropTypes.string.isRequired,
            text: PropTypes.string.isRequired,
            url: PropTypes.string
        })
    ).isRequired,
    handleDeleteComment: PropTypes.func.isRequired
};

export default Comments;