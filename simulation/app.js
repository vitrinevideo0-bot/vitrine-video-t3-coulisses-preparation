const screen = document.querySelector('#screen');
const meta = document.querySelector('#meta');
const previous = document.querySelector('#previous');
const next = document.querySelector('#next');
let contract = null;
let index = 0;

function render() {
  const item = contract.screens[index];
  const scene = `SCÈNE ${item.scene_index}/4`;
  const labels = {A_GUIDE:'Guide avant prise',B_RECORDING:'Enregistrement caméra + micro',C_REVIEW:'Relecture avec son'};
  screen.innerHTML = `<div><div class="badge">${scene}</div><div class="state">${item.state}</div><div class="title">${labels[item.state]}</div><div class="description">${item.purpose}</div></div>`;
  meta.textContent = `${item.screen_id} · ${item.capture_duration_ms/1000} s · écran ${item.ordinal}/12`;
  previous.disabled = index === 0;
  next.textContent = index === contract.screens.length - 1 ? 'TERMINER' : 'SUIVANT';
}

previous.addEventListener('click', () => { if (index > 0) { index -= 1; render(); } });
next.addEventListener('click', () => { if (index < contract.screens.length - 1) { index += 1; render(); } });

fetch('../config/T3_CAPTURE_FLOW_V1_0_0.json')
  .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
  .then(value => { contract = value; render(); })
  .catch(error => { screen.innerHTML = `<p class="error">Servez le dépôt par HTTP pour charger le contrat : ${error.message}</p>`; });
