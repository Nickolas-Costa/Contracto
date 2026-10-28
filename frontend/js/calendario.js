/* Calendário pop-up da data de assinatura. `aoEscolher(valor)` recebe DD/MM/AAAA. */
(function () {
  "use strict";
  function abrir(input, aoEscolher) {
    const today = new Date();
    const year = today.getFullYear(), month = today.getMonth(), day = today.getDate();
    const months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const diasSemana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
    const overlay = document.createElement("div");
    overlay.className = "calendario-overlay";
    overlay.innerHTML = `
      <div class="calendario-card">
        <div class="calendario-header">
          <button type="button" class="cal-btn" data-acao="prev" aria-label="Mês anterior">◄</button>
          <strong id="cal-mes-ano">${months[month]} ${year}</strong>
          <button type="button" class="cal-btn" data-acao="next" aria-label="Próximo mês">►</button>
          <button type="button" class="cal-btn cal-fechar" data-acao="fechar">✕</button>
        </div>
        <div class="cal-dias-semana">
          ${diasSemana.map(d=>`<span>${d}</span>`).join("")}
        </div>
        <div class="cal-grid" id="cal-grid" tabindex="0"></div>
      </div>
    `;
    document.body.append(overlay);
    function renderCal(y, m) {
      const firstDay = new Date(y, m, 1).getDay();
      const lastDate = new Date(y, m + 1, 0).getDate();
      const grid = overlay.querySelector("#cal-grid");
      grid.dataset.ano = y; grid.dataset.mes = m;
      overlay.querySelector("#cal-mes-ano").textContent = `${months[m]} ${y}`;
      grid.innerHTML = "";
      for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement("span"); grid.append(empty);
      }
      for (let d = 1; d <= lastDate; d++) {
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "cal-dia";
        if (d === day && m === month && y === year) btn.classList.add("hoje");
        btn.textContent = d; btn.dataset.dia = d;
        grid.append(btn);
      }
    }
    renderCal(year, month);
    overlay.addEventListener("click", e => {
      const btn = e.target.closest("button");
      if (!btn) return;
      if (btn.dataset.acao === "fechar") { overlay.remove(); input.focus(); return; }
      const grid = overlay.querySelector("#cal-grid");
      if (btn.dataset.acao === "prev") { let m = Number(grid.dataset.mes) - 1, y = Number(grid.dataset.ano); if (m < 0) { m = 11; y--; } renderCal(y, m); return; }
      if (btn.dataset.acao === "next") { let m = Number(grid.dataset.mes) + 1, y = Number(grid.dataset.ano); if (m > 11) { m = 0; y++; } renderCal(y, m); return; }
      if (btn.classList.contains("cal-dia")) {
        const d = Number(btn.dataset.dia), m = Number(grid.dataset.mes), y = Number(grid.dataset.ano);
        const val = `${String(d).padStart(2,"0")}/${String(m+1).padStart(2,"0")}/${y}`;
        input.value = val;
        aoEscolher(val);
        overlay.remove();
        input.focus();
      }
    });
    overlay.addEventListener("keydown", e => { if (e.key === "Escape") { overlay.remove(); input.focus(); } });
    overlay.querySelector(".cal-grid").focus();
  }

  window.ContractoCalendario = { abrir };
})();
