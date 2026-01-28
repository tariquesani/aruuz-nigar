(function () {
    'use strict';

    var GITHUB_API = 'https://api.github.com/repos/tariquesani/aruuz-nigar/releases/latest';

    var modal = document.getElementById('updatesModal');
    var body = document.getElementById('updatesModalBody');
    if (!modal || !body) return;

    modal.addEventListener('show.bs.modal', function () {
        body.textContent = 'Checking for updates…';
    });

    modal.addEventListener('shown.bs.modal', function () {
        body.textContent = 'Checking for updates…';

        fetch(GITHUB_API)
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                var tag = data.tag_name;
                var releaseUrl = data.html_url || 'https://github.com/tariquesani/aruuz-nigar/releases/';

                if (typeof APP_VERSION === 'undefined') {
                    body.innerHTML = 'Unable to determine current version. You can <a href="https://github.com/tariquesani/aruuz-nigar/releases/" target="_blank" rel="noopener noreferrer">visit the releases page</a> to check manually.';
                    return;
                }

                if (tag === APP_VERSION) {
                    body.textContent = 'You have the latest version (v' + APP_VERSION + ').';
                } else {
                    body.innerHTML = 'You have version "' + APP_VERSION + '". The latest released version is "' + tag + '". <a href="' + releaseUrl + '" target="_blank" rel="noopener noreferrer">Get the latest release</a>';
                }
            })
            .catch(function () {
                body.innerHTML = 'Unable to check for updates. You can <a href="https://github.com/tariquesani/aruuz-nigar/releases/" target="_blank" rel="noopener noreferrer">visit the releases page</a> to check manually.';
            });
    });
})();
