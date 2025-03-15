// sidebar.js

document.addEventListener('DOMContentLoaded', () => {
    const sidebarContainer = document.querySelector('.sidebar-container');
    const sidebarTrigger = document.querySelector('.sidebar-trigger');

    sidebarTrigger.addEventListener('mouseover', () => {
        sidebarContainer.classList.add('open');
    });

    sidebarContainer.addEventListener('mouseleave', () => {
        sidebarContainer.classList.remove('open');
    });
});