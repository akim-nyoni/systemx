// Sidebar 
function openSidebar() {
 document.getElementById('sidebar').classList.add('open');
 document.getElementById('overlay').classList.add('active');
 document.body.style.overflow = 'hidden';
}
function closeSidebar() {
 document.getElementById('sidebar').classList.remove('open');
 document.getElementById('overlay').classList.remove('active');
 document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });

// Auto-logout: 10 minutes of inactivity 
(function() {
 const TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes total
 const WARN_SECS = 60; // warn 60s before logout


 let idleTimer, warnTimer, countInterval, countVal;
 const toast = document.getElementById('logoutToast');
 const countEl = document.getElementById('logoutCount');

 function resetIdle() {
 clearTimeout(idleTimer);
 clearTimeout(warnTimer);
 clearInterval(countInterval);
 if (toast) toast.classList.remove('visible');

 // Show warning 60s before timeout
 warnTimer = setTimeout(() => {
 countVal = WARN_SECS;
 if (countEl) countEl.textContent = countVal;
 if (toast) toast.classList.add('visible');
 countInterval = setInterval(() => {
 countVal--;
 if (countEl) countEl.textContent = countVal;
 if (countVal <= 0) {
 clearInterval(countInterval);
 window.location.href = LOGOUT_URL;
 }
 }, 1000);
 }, TIMEOUT_MS - WARN_SECS * 1000);

 // Hard logout at timeout
 idleTimer = setTimeout(() => {
 window.location.href = LOGOUT_URL;
 }, TIMEOUT_MS);
 }

 // Reset timer on any user interaction
 ['mousemove','mousedown','keydown','scroll','touchstart','click'].forEach(ev => {
 document.addEventListener(ev, resetIdle, { passive: true });
 });

 resetIdle(); // start on page load
})();