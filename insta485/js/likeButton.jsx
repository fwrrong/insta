import React from "react";
import PropTypes from "prop-types";

function LikeButton({ lognameLikesThis, handleClickLike }) {
    return (
        <button type="button" onClick={handleClickLike} data-testid="like-unlike-button">
            {lognameLikesThis ? 'unlike' : 'like'}
        </button>
    );
}

LikeButton.propTypes = {
    lognameLikesThis: PropTypes.bool.isRequired,
    handleClickLike: PropTypes.func.isRequired
};

export default LikeButton;