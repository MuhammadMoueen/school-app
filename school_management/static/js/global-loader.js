(function () {
    var loader = document.getElementById('globalPageLoader');

    if (!loader) {
        return;
    }

    function showLoader() {
        loader.classList.remove('is-hidden');
        loader.setAttribute('aria-hidden', 'false');
    }

    function hideLoader() {
        loader.classList.add('is-hidden');
        loader.setAttribute('aria-hidden', 'true');
    }

    showLoader();

    window.addEventListener('load', function () {
        hideLoader();
    });

    // Show loader when user navigates to another page via links.
    document.addEventListener('click', function (event) {
        var anchor = event.target.closest('a[href]');

        if (!anchor) {
            return;
        }

        var href = anchor.getAttribute('href');
        var target = anchor.getAttribute('target');

        if (!href || href.startsWith('#')) {
            return;
        }

        if (target === '_blank' || anchor.hasAttribute('download')) {
            return;
        }

        var isJsLink = href.toLowerCase().startsWith('javascript:');
        if (isJsLink) {
            return;
        }

        var url;
        try {
            url = new URL(anchor.href, window.location.href);
        } catch (e) {
            return;
        }

        if (url.origin !== window.location.origin) {
            return;
        }

        if (url.pathname === window.location.pathname && url.search === window.location.search) {
            return;
        }

        showLoader();
    });

    // Show loader on regular form submit navigation.
    document.addEventListener('submit', function (event) {
        var form = event.target;

        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        var method = (form.getAttribute('method') || 'get').toLowerCase();
        if (method === 'dialog') {
            return;
        }

        showLoader();
    });

    // If browser restores page from cache, ensure loader stays hidden.
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            hideLoader();
        }
    });
})();
