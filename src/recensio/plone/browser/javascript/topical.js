/* Minimal JavaScript for topical browse interactions */
(function () {
    'use strict';

    const show_num = 8;
    const show_step = 8;
    let visibleCount = show_num;

    function showMoreItems() {
        const submenuItems = document.querySelectorAll('#submenu_ddcSubject .submenu-lvl2');
        const moreContainer = document.querySelector('#submenu_ddcSubject .submenu_more');

        for (let i = visibleCount; i < Math.min(visibleCount + show_step, submenuItems.length); i++) {
            submenuItems[i].style.display = '';
        }

        visibleCount += show_step;

        if (submenuItems.length <= visibleCount && moreContainer) {
            moreContainer.classList.add('invisible');
        }
    }

    function initializeShowMore() {
        // Handle "show more" functionality
        const moreContainer = document.querySelector('#submenu_ddcSubject .submenu_more');
        const moreButton = document.querySelector('#submenu_ddcSubject .submenu-more-link');

        if (moreButton) {
            moreButton.addEventListener('click', function (e) {
                e.preventDefault();
                showMoreItems();
            });
        }

        // Hide extra items initially
        const submenuItems = document.querySelectorAll('#submenu_ddcSubject .submenu-lvl2');
        if (submenuItems.length > show_num) {
            for (let i = show_num; i < submenuItems.length; i++) {
                submenuItems[i].style.display = 'none';
            }
            if (moreContainer) {
                moreContainer.classList.remove('invisible');
            }
        }
    }

    function initializeSortSelector() {
        const sortSelect = document.querySelector('#topical-sort-select');

        if (!sortSelect) {
            return;
        }

        sortSelect.addEventListener('change', function (e) {
            if (e.target.value) {
                window.location.href = e.target.value;
            }
        });
    }

    function initializeTopicalBrowse() {
        initializeShowMore();
        initializeSortSelector();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTopicalBrowse);
    } else {
        initializeTopicalBrowse();
    }
})();
