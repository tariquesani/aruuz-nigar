(function () {
    'use strict';

    var STORAGE_KEY = 'aruuznigar.poetryDraft';
    var DEBOUNCE_MS = 300;
    var debounceTimer = null;

    function load() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            return null;
        }
    }

    function save(text) {
        try {
            localStorage.setItem(STORAGE_KEY, text == null ? '' : String(text));
        } catch (e) {
            // quota exceeded or private browsing
        }
    }

    function bindTextarea(el) {
        if (!el) return;

        var saved = load();
        var restoredFromStorage = false;
        if (saved !== null) {
            el.value = saved;
            restoredFromStorage = true;
        } else {
            save(el.value);
        }

        el.addEventListener('input', function () {
            if (debounceTimer) clearTimeout(debounceTimer);
            var value = el.value;
            debounceTimer = setTimeout(function () {
                debounceTimer = null;
                save(value);
            }, DEBOUNCE_MS);
        });

        var form = el.closest('form');
        if (form) {
            form.addEventListener('submit', function () {
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                    debounceTimer = null;
                }
                save(el.value);
            });

            if (restoredFromStorage && el.value.trim() && form.getAttribute('data-auto-scan') !== 'false') {
                setTimeout(function () {
                    if (typeof form.requestSubmit === 'function') {
                        form.requestSubmit();
                    } else {
                        form.submit();
                    }
                }, 0);
            }
        }
    }

    function autoBind() {
        bindTextarea(document.getElementById('text'));
    }

    window.PoetryDraft = {
        load: load,
        save: save,
        bindTextarea: bindTextarea
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoBind);
    } else {
        autoBind();
    }
})();
