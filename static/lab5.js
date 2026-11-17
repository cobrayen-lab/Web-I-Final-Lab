// Cobra Tech restricted room controller
(function () {
  const input = document.getElementById('admin-password');
  const unlock = document.getElementById('unlock-btn');
  const status = document.getElementById('room-message');

  function checkAccess() {
    const pass = input.value;
    if (pass !== 'cobra_admin_2026') {
      status.textContent = 'Access Denied!';
      return;
    }
    document.getElementById('secretForm').submit();
  }

  unlock.addEventListener('click', checkAccess);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') checkAccess();
  });
})();
