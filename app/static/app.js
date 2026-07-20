// Helpers compartilhados pelo front: polling, toasts e modal de confirmação.
// Sem dependência externa — mantém o front simples (server-rendered + JS vanilla).

function poll(url, intervalMs, onData) {
  async function tick() {
    try {
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      onData(data);
    } catch (err) {
      // falha de rede pontual não deve poluir a UI; só loga
      console.warn('poll falhou:', url, err);
    }
  }
  tick();
  return setInterval(tick, intervalMs);
}

function toast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 300);
  }, 4000);
}

function confirmModal(message) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal-box">
        <p>${message}</p>
        <div class="modal-actions">
          <button class="btn-secondary" data-action="cancel">Cancelar</button>
          <button class="btn-danger" data-action="confirm">Confirmar</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));

    function close(result) {
      overlay.classList.remove('show');
      setTimeout(() => overlay.remove(), 200);
      resolve(result);
    }

    overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
    overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close(false);
    });
  });
}
