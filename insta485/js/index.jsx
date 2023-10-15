import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import InfiniteScroll from "react-infinite-scroll-component";
import Post from "./post";

export default function Index({ url }) {
  /* Display image and post owner of a single post */

    const [results, setResults] = useState([])
    const [nextUrl, setNextUrl] = useState("/api/v1/posts/");
    // const [postid, setPostid] = useState();

    useEffect(() => {
        // Declare a boolean flag that we can use to cancel the API request.
        let ignoreStaleRequest = false;

        // Call REST API to get the post's information
        fetch(url, { credentials: "same-origin" })
        .then((response) => {
            if (!response.ok) throw Error(response.statusText);
            return response.json();
        })
        .then((data) => {
            // If ignoreStaleRequest was set to true, we want to ignore the results of the
            // the request. Otherwise, update the state to trigger a new render.
            if (!ignoreStaleRequest) {
                setResults(data.results)
                if (data.next) {
                    setNextUrl(data.next);
                } else {
                    setNextUrl(null);
                }
            }
        })
        .catch((error) => console.log(error));

        return () => {
        // This is a cleanup function that runs whenever the Post component
        // unmounts or re-renders. If a Post is about to unmount or re-render, we
        // should avoid updating state.
        ignoreStaleRequest = true;
        };
    }, [url]);

    const fetchMoreData = () => {
        if (nextUrl) {
            fetch(nextUrl, { credentials: "same-origin" })
            .then(response => response.json())
            .then(data => {
                setResults(prevResults => [...prevResults, ...data.results]);

                if (data.next) {
                setNextUrl(data.next);
                } else {
                setNextUrl(null);  // No more posts to load
                }
            })
            .catch(error => console.log(error));
        }
    };


    const listPosts = results.map(post =>
        <li key={post.postid}>
            <Post url = {post.url}/>
        </li>
    );

    // Render post image and post owner
    return (
        <InfiniteScroll
            dataLength={results.length}
            next={fetchMoreData}
            hasMore={nextUrl !== null}
            loader={<h4>Loading...</h4>}
            endMessage={
            <p style={{textAlign: 'center'}}>
                <b>No more posts to display</b>
            </p>
            }
        >
            <ul>{listPosts}</ul>
        </InfiniteScroll>
    );
}

Index.propTypes = {
    url: PropTypes.string.isRequired,
};