/* Uang Kas v1.0 — main.js */

// ─── Sidebar toggle (owner mobile) ───────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (sidebar && toggle && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

// ─── Auto-dismiss alerts after 4 seconds ─────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 4000);
  });

  // Format input number rupiah (visual only, strip dots on submit)
  const rupiahInputs = document.querySelectorAll('input[data-rupiah]');
  rupiahInputs.forEach(function (input) {
    input.addEventListener('input', function () {
      const raw = this.value.replace(/\D/g, '');
      this.value = raw;
    });
  });

  // txn-choice visual selection sync
  document.querySelectorAll('.txn-choice input[type=radio]').forEach(function (radio) {
    if (radio.checked) {
      radio.closest('.txn-choice').classList.add('selected');
    }
    radio.addEventListener('change', function () {
      document.querySelectorAll('.txn-choice').forEach(function (el) {
        el.classList.remove('selected');
      });
      this.closest('.txn-choice').classList.add('selected');
    });
  });
});
