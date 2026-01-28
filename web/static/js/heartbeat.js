(function () {
    'use strict';

    var INTERVAL_MS = 5000;
    var el = document.getElementById('heartbeat-status');
    if (!el) return;

    var CLASS_OK = 'heartbeat-ok';
    var CLASS_FAIL = 'heartbeat-fail';

    function setState(ok) {
        el.classList.remove(CLASS_OK, CLASS_FAIL);
        el.classList.add(ok ? CLASS_OK : CLASS_FAIL);
        el.title = ok ? 'Server status: online' : 'Server status: offline';
        el.setAttribute('aria-label', ok ? 'Server status: online' : 'Server status: offline');
    }

    function check() {
        fetch('/heartbeat')
            .then(function (r) {
                setState(r.ok);
            })
            .catch(function () {
                setState(false);
            });
    }

    check();
    setInterval(check, INTERVAL_MS);
})();
