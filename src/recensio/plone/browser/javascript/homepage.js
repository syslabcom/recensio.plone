jQuery(document).ready(function () {
    jQuery(
        "#latest_reviewparts_box .ellipsis_container, \
        #latest_monographies_box .ellipsis_container, \
        #latest_internet_resources_box .ellipsis_container, \
        #latest_reviews_box .ellipsis_container"
    ).ThreeDots({ max_rows: 3 });
    jQuery("#latest_reviews_box .ellipsis_container").ThreeDots({ max_rows: 2 });
    /* The ticker items need to be displayed so that the size can be
       calculated by ThreeDots. They can then be hidden. Using
       visibility in css to avoid seeing an ugly flash of text before
       the page is loaded and the JavaScript kicks in. */
    jQuery("div#latest_reviews_box ul li.not_first").css("display", "none");
    jQuery("div#latest_reviews_box ul li.not_first").css("visibility", "visible");

    jQuery(".list_reviews").easyticker();
});
