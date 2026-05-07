function getToken() {
  return localStorage.getItem("access_token");
}

async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = options.headers || {};
  headers["Content-Type"] = headers["Content-Type"] || "application/json";
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
}

async function login(emailOrUsername, password) {
  const payload = emailOrUsername.includes("@")
    ? { email: emailOrUsername, password }
    : { username: emailOrUsername, password };

  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Login failed");
  }

  localStorage.setItem("access_token", data.access_token);
  window.location.href = "/dashboard";
}

function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "/";
}

function renderBracket(matches) {
  const container = document.getElementById("bracket");
  if (!container) return;

  container.innerHTML = "";
  const grouped = {};

  matches.forEach((match) => {
    if (!grouped[match.round]) grouped[match.round] = [];
    grouped[match.round].push(match);
  });

  Object.keys(grouped)
    .sort((a, b) => Number(a) - Number(b))
    .forEach((round) => {
      const roundEl = document.createElement("div");
      roundEl.className = "round";

      const title = document.createElement("h5");
      title.textContent = `Round ${round}`;
      roundEl.appendChild(title);

      grouped[round].forEach((match) => {
        const card = document.createElement("div");
        card.className = "match-card";
        card.innerHTML = `
          <div><strong>${match.team1_name || "TBD"}</strong> vs <strong>${match.team2_name || "TBD"}</strong></div>
          <div class="small">Status: ${match.status}</div>
          <div class="small">Winner: ${match.winner_name || "TBD"}</div>
        `;
        roundEl.appendChild(card);
      });

      container.appendChild(roundEl);
    });
}

async function reportMatch(matchId, score1, score2) {
  const res = await authFetch(`/matches/${matchId}/report`, {
    method: "POST",
    body: JSON.stringify({ score1, score2 }),
  });
  return res.json();
}

async function confirmMatch(matchId) {
  const res = await authFetch(`/matches/${matchId}/confirm`, {
    method: "POST",
  });
  return res.json();
}

document.addEventListener("DOMContentLoaded", async () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const loginInput = document.getElementById("login-input").value;
        const password = document.getElementById("password").value;
        await login(loginInput, password);
      } catch (err) {
        alert(err.message);
      }
    });
  }

  const tournamentsList = document.getElementById("tournaments-list");
  if (tournamentsList && tournamentsList.dataset.autoload === "true") {
    const res = await fetch("/tournaments");
    const tournaments = await res.json();
    tournamentsList.innerHTML = tournaments
      .map(
        (t) => `
          <div class="col-md-4">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">${t.title}</h5>
                <p class="card-text">${t.game} | ${t.format} | ${t.status}</p>
                <a class="btn btn-primary" href="/tournament/${t.id}">Подробнее</a>
              </div>
            </div>
          </div>
        `
      )
      .join("");
  }

  const bracket = document.getElementById("bracket");
  if (bracket && bracket.dataset.tournamentId) {
    const tid = bracket.dataset.tournamentId;
    const res = await fetch(`/tournaments/${tid}/bracket`);
    const matches = await res.json();
    renderBracket(matches);
  }
});