import React from "react";
import PropTypes from "prop-types";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";

dayjs.extend(relativeTime);
dayjs.extend(utc);

function PostTime({ postShowUrl, created }) {
    const formattedTime = dayjs.utc(created).local().fromNow();

    return(
        <div>
            <a href={ postShowUrl }>{ formattedTime }</a>
        </div>
    )
}

PostTime.propTypes = {
    postShowUrl: PropTypes.string.isRequired,
    created: PropTypes.string.isRequired
}

export default PostTime;