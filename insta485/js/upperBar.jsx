import React from "react";
import PropTypes from "prop-types";
import PostOwner from "./postOwner";
import PostTime from "./postTime";

function UpperBar({ ownerImgUrl, owner, ownerShowUrl, postShowUrl, created}){
    return(
        <div>
        <PostOwner 
            ownerImgUrl = {ownerImgUrl}
            owner = {owner}
            ownerShowUrl = {ownerShowUrl}/>
        <PostTime 
            postShowUrl = {postShowUrl}
            created = {created}/>
        </div>
    )
}

UpperBar.propTypes = {
    ownerImgUrl: PropTypes.string.isRequired,
    owner: PropTypes.string.isRequired,
    ownerShowUrl: PropTypes.string.isRequired,
    postShowUrl: PropTypes.string.isRequired,
    created: PropTypes.string.isRequired
}

export default UpperBar;