/* Author search letter tabs with cached infinite scrolling per letter. */
(function () {
    'use strict';

    const ROOT_SELECTOR = '[data-authorsearch-root]';
    const TAB_SELECTOR = '[data-authorsearch-tab]';
    const PANEL_SELECTOR = '[data-authorsearch-panel]';
    const RESULTS_SELECTOR = '[data-authorsearch-results]';
    const LOADER_SELECTOR = '[data-authorsearch-loader]';
    const BATCH_SELECTOR = '#authorsearch-batch';

    function cssEscape(value) {
        if (window.CSS && typeof window.CSS.escape === 'function') {
            return window.CSS.escape(value);
        }
        return value.replace(/([^a-zA-Z0-9_-])/g, '\\$1');
    }

    function parseBatch(html) {
        const template = document.createElement('template');
        template.innerHTML = html.trim();
        return template.content.querySelector(BATCH_SELECTOR);
    }

    function getPanel(root, letter) {
        return root.querySelector(
            `${PANEL_SELECTOR}[data-authorsearch-letter="${cssEscape(letter)}"]`
        );
    }

    function getTab(root, letter) {
        return root.querySelector(
            `${TAB_SELECTOR}[data-authorsearch-letter="${cssEscape(letter)}"]`
        );
    }

    function setLoaderText(loader, text) {
        if (!loader) {
            return;
        }
        loader.textContent = text;
    }

    function updateLoader(panel, labels) {
        const loader = panel.querySelector(LOADER_SELECTOR);
        if (!loader) {
            return;
        }

        const nextUrl = panel.dataset.authorsearchNextUrl || '';
        loader.classList.remove('is-error');
        setLoaderText(loader, labels.loading);

        if (nextUrl) {
            loader.hidden = false;
            loader.dataset.authorsearchUrl = nextUrl;
            return;
        }

        loader.hidden = true;
        loader.removeAttribute('data-authorsearch-url');
    }

    function setPanelLoading(panel, loading, labels) {
        const loader = panel.querySelector(LOADER_SELECTOR);
        panel.classList.toggle('is-loading', loading);
        panel.setAttribute('aria-busy', loading ? 'true' : 'false');
        panel.dataset.authorsearchLoading = loading ? 'true' : 'false';

        if (!loader) {
            return;
        }

        loader.disabled = loading;
        if (loading) {
            loader.classList.remove('is-error');
            setLoaderText(loader, labels.loading);
        }
    }

    function setupAuthorsearch(root) {
        const labels = {
            error: root.dataset.errorLabel || 'Could not load contents.',
            loading: root.dataset.loadingLabel || 'Loading contents…',
        };
        const pendingLoads = new WeakMap();
        let observer = null;

        function disconnectObserver() {
            if (observer) {
                observer.disconnect();
                observer = null;
            }
        }

        function activePanel() {
            return root.querySelector(`${PANEL_SELECTOR}:not([hidden])`);
        }

        function markCurrentTab(letter) {
            root.querySelectorAll(TAB_SELECTOR).forEach((tab) => {
                const current = tab.dataset.authorsearchLetter === letter;
                const item = tab.closest('.authorsearch-jumpnav__item');

                tab.setAttribute('aria-selected', current ? 'true' : 'false');
                tab.setAttribute('tabindex', current ? '0' : '-1');
                if (item) {
                    item.classList.toggle('is-current', current);
                    item.classList.toggle('is-active', !current);
                }
            });
        }

        function showPanel(letter) {
            root.querySelectorAll(PANEL_SELECTOR).forEach((panel) => {
                if (panel.dataset.authorsearchLetter === letter) {
                    panel.removeAttribute('hidden');
                    return;
                }
                panel.setAttribute('hidden', 'hidden');
            });
            root.dataset.authorsearchSelectedLetter = letter;
            markCurrentTab(letter);
        }

        function updateHistory(letter) {
            const tab = getTab(root, letter);
            if (!tab || !tab.href || !window.history || !window.history.replaceState) {
                return;
            }
            window.history.replaceState(null, '', tab.href);
        }

        function appendBatch(panel, batch) {
            const results = panel.querySelector(RESULTS_SELECTOR);
            if (!results) {
                return;
            }

            Array.from(batch.children).forEach((child) => {
                results.appendChild(child);
            });
        }

        function observeActiveLoader() {
            disconnectObserver();

            const panel = activePanel();
            if (!panel || panel.dataset.authorsearchLoading === 'true') {
                return;
            }

            const loader = panel.querySelector(LOADER_SELECTOR);
            if (!loader || loader.hidden || !loader.dataset.authorsearchUrl) {
                return;
            }

            if (!('IntersectionObserver' in window)) {
                return;
            }

            observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    disconnectObserver();
                    loadBatch(panel, loader.dataset.authorsearchUrl);
                });
            }, { rootMargin: '300px 0px' });

            observer.observe(loader);
        }

        async function loadBatch(panel, url) {
            if (!panel || !url) {
                return Promise.resolve();
            }

            if (pendingLoads.has(panel)) {
                return pendingLoads.get(panel);
            }

            const promise = (async function () {
                setPanelLoading(panel, true, labels);

                try {
                    const response = await fetch(url, {
                        credentials: 'same-origin',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    const batch = parseBatch(await response.text());
                    if (!batch) {
                        throw new Error('Missing authorsearch batch payload');
                    }

                    appendBatch(panel, batch);
                    panel.dataset.authorsearchLoaded = 'true';
                    panel.dataset.authorsearchNextUrl = batch.dataset.nextUrl || '';
                    updateLoader(panel, labels);
                } catch (error) {
                    const loader = panel.querySelector(LOADER_SELECTOR);
                    if (loader) {
                        loader.hidden = false;
                        loader.classList.add('is-error');
                        loader.dataset.authorsearchUrl = url;
                        setLoaderText(loader, labels.error);
                    }
                    // eslint-disable-next-line no-console
                    console.error('Failed to load authorsearch batch', error);
                } finally {
                    pendingLoads.delete(panel);
                    setPanelLoading(panel, false, labels);
                    observeActiveLoader();
                }
            })();

            pendingLoads.set(panel, promise);
            return promise;
        }

        function ensurePanelLoaded(panel) {
            if (!panel) {
                return Promise.resolve();
            }

            if (panel.dataset.authorsearchLoaded === 'true') {
                updateLoader(panel, labels);
                observeActiveLoader();
                return Promise.resolve();
            }

            return loadBatch(panel, panel.dataset.authorsearchInitialUrl || '');
        }

        function activateLetter(letter, options) {
            const settings = options || {};
            const panel = getPanel(root, letter);

            if (!panel) {
                return;
            }

            showPanel(letter);
            if (settings.updateHistory !== false) {
                updateHistory(letter);
            }
            ensurePanelLoaded(panel);
        }

        root.addEventListener('click', (event) => {
            const tab = event.target.closest(TAB_SELECTOR);
            if (tab) {
                event.preventDefault();
                activateLetter(tab.dataset.authorsearchLetter);
                return;
            }

            const loader = event.target.closest(LOADER_SELECTOR);
            if (!loader) {
                return;
            }

            event.preventDefault();
            const panel = loader.closest(PANEL_SELECTOR);
            if (!panel || !loader.dataset.authorsearchUrl) {
                return;
            }

            loadBatch(panel, loader.dataset.authorsearchUrl);
        });

        const initialPanel = activePanel() || root.querySelector(PANEL_SELECTOR);
        if (initialPanel) {
            activateLetter(initialPanel.dataset.authorsearchLetter, {
                updateHistory: false,
            });
        }
    }

    function initializeAuthorsearch() {
        document.querySelectorAll(ROOT_SELECTOR).forEach(setupAuthorsearch);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAuthorsearch);
    } else {
        initializeAuthorsearch();
    }
})();
