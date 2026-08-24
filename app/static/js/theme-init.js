(function () {
    try {
        const savedTheme = window.localStorage.getItem('sgpn-theme');
        document.documentElement.dataset.theme = savedTheme === 'dark' ? 'dark' : 'light';
    } catch (_error) {
        document.documentElement.dataset.theme = 'light';
    }
}());
