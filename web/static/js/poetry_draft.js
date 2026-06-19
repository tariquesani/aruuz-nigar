(function () {
    'use strict';

    var STORAGE_KEY = 'aruuznigar.poetryDraft';
    var DEBOUNCE_MS = 300;
    var debounceTimer = null;

    function readState() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (raw === null) return null;
            if (raw.charAt(0) === '{') {
                var parsed = JSON.parse(raw);
                return {
                    text: parsed.text == null ? '' : String(parsed.text),
                    hasMatla: !!parsed.hasMatla
                };
            }
            return { text: raw, hasMatla: false };
        } catch (e) {
            return null;
        }
    }

    function writeState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                text: state.text == null ? '' : String(state.text),
                hasMatla: !!state.hasMatla
            }));
        } catch (e) {
            // quota exceeded or private browsing
        }
    }

    function load() {
        var state = readState();
        return state ? state.text : null;
    }

    function loadHasMatla() {
        var state = readState();
        return state ? state.hasMatla : false;
    }

    function save(text) {
        var state = readState() || { text: '', hasMatla: false };
        state.text = text == null ? '' : String(text);
        writeState(state);
    }

    function saveHasMatla(hasMatla) {
        var state = readState() || { text: '', hasMatla: false };
        state.hasMatla = !!hasMatla;
        writeState(state);
    }

    function bindTextarea(el) {
        if (!el) return;

        var state = readState();
        var restoredFromStorage = false;
        if (state !== null) {
            el.value = state.text;
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
        loadHasMatla: loadHasMatla,
        save: save,
        saveHasMatla: saveHasMatla,
        bindTextarea: bindTextarea
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoBind);
    } else {
        autoBind();
    }
})();
