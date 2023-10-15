import React from "react";
import PropTypes from "prop-types";

function PostOwner({ ownerImgUrl, owner, ownerShowUrl }) {
    return (
        <div>
            <a href={ownerShowUrl}>
                <img src={ownerImgUrl} alt="insta" className = "profilePic" />
            </a>
            <a href={ownerShowUrl}>{owner}</a>
        </div>
    )
}

PostOwner.propTypes = {
    ownerImgUrl: PropTypes.string.isRequired,
    owner: PropTypes.string.isRequired,
    ownerShowUrl: PropTypes.string.isRequired
};

export default PostOwner;