/* Some browsers *ahem* don't implement indexOf. We provide it here for this case */
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function (elt /*, from*/) {
        var len = this.length;

        var from = Number(arguments[1]) || 0;
        from = from < 0 ? Math.ceil(from) : Math.floor(from);
        if (from < 0) from += len;

        for (; from < len; from++) {
            if (from in this && this[from] === elt) return from;
        }
        return -1;
    };
}

var topical = (function () {
    var currentopen = [],
        show_num = 8,
        show_step = 8;

    function toggler(elem, headline) {
        var i = currentopen.indexOf(elem.attr("id"));
        if (i < 0) {
            elem.show();
            headline.addClass("open");
            currentopen.push(elem.attr("id"));
        } else {
            elem.hide();
            headline.removeClass("open");
            currentopen.splice(i);
        }
    }
    return {
        currentopen: currentopen,
        show_num: show_num,
        show_step: show_step,
        toggler: toggler,
    };
})();

jq(document).ready(function () {
    jq(".submenu_content").not(".open").hide("fast");
    jq(".submenu_title")
        .not(".empty")
        .click(function (e) {
            var targ;
            if (!e) var e = window.event;
            if (e.target) targ = e.target;
            else if (e.srcElement) targ = e.srcElement;
            if (targ.nodeType == 3)
                // defeat Safari bug
                targ = targ.parentNode;
            targ = targ.closest(".submenu_title");
            //if (!(targ.tagName = "DIV") {}
            topical.toggler(
                jq(".submenu_content#" + targ.id.replace("title", "content")),
                jq(".submenu_title#" + targ.id)
            );
        });
    jq("#submenu_ddcSubject .submenu_more").click(function () {
        jq("#submenu_ddcSubject .submenu-lvl2")
            .slice(topical.show_num, topical.show_num + topical.show_step)
            .show();
        topical.show_num += topical.show_step;
        if (jq("#submenu_ddcSubject .submenu-lvl2").length <= topical.show_num) {
            jq("#submenu_ddcSubject .submenu_more").addClass("invisible");
        }
    });
    //jq('.collapsible').do_search_collapse()
    if (jq("#submenu_ddcSubject .submenu-lvl2").length > topical.show_num) {
        jq("#submenu_ddcSubject .submenu-lvl2").slice(topical.show_num).hide();
        jq("#submenu_ddcSubject .submenu_more").removeClass("invisible");
    }
    jq(".submenu_title.open").each(function () {
        topical.currentopen.push(this.id);
    });
});
