import React from "react";
import PropTypes from "prop-types";


export default function NumLikes({ numLikes }){
    return (
        numLikes === 1 ? (
            <h3>1 like</h3>
        ) : (
            <h3>{ numLikes } likes</h3>
        )
    );
}

NumLikes.propTypes = {
    numLikes: PropTypes.number.isRequired
}