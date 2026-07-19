// Shared theme bootstrap, loaded by every page (chat, classic, about, terms,
// privacy) so a theme picked in one place applies everywhere via the same
// localStorage key. Runs synchronously in <head>, before first paint, to
// avoid a flash of the wrong theme.
(function () {
    var THEME_KEY = 'aimotional_theme';

    function applyTheme(theme) {
        var root = document.documentElement;
        if (!theme || theme === 'system') {
            root.removeAttribute('data-theme');
        } else {
            root.setAttribute('data-theme', theme);
        }
    }

    applyTheme(localStorage.getItem(THEME_KEY) || 'system');

    window.AIMotionalTheme = {
        KEY: THEME_KEY,
        apply: applyTheme,
        get: function () {
            return localStorage.getItem(THEME_KEY) || 'system';
        },
        set: function (theme) {
            localStorage.setItem(THEME_KEY, theme);
            applyTheme(theme);
        }
    };
})();
