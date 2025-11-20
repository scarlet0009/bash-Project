// dashboard.js
document.addEventListener("DOMContentLoaded", function() {
  const liveLog = document.getElementById("liveLog");
  const blockedTbody = document.querySelector("#blockedTable tbody");
  const topChartCtx = document.getElementById("topChart").getContext('2d');
  const refreshBtn = document.getElementById("refresh");
  const genReportBtn = document.getElementById("genReport");

  // SSE connection
  const evtSource = new EventSource("/stream");
  evtSource.onmessage = function(e) {
    const line = e.data;
    const div = document.createElement("div");
    div.textContent = line;
    liveLog.appendChild(div);
    // keep scroll bottom
    liveLog.scrollTop = liveLog.scrollHeight;
  };

  async function fetchBlocked() {
    const res = await fetch("/api/blocked");
    const data = await res.json();
    blockedTbody.innerHTML = "";
    data.forEach(row => {
      const tr = document.createElement("tr");
      const blockedAt = row.blocked_at ? new Date(row.blocked_at * 1000).toLocaleString() : "-";
      const until = row.unblock_at ? new Date(row.unblock_at * 1000).toLocaleString() : "-";
      tr.innerHTML = `<td>${row.ip}</td><td>${blockedAt}</td><td>${until}</td><td>${row.reason}</td>
        <td><button class="small" data-ip="${row.ip}">Unblock</button></td>`;
      blockedTbody.appendChild(tr);
    });
    blockedTbody.querySelectorAll("button.small").forEach(btn => {
      btn.addEventListener("click", async (ev) => {
        const ip = ev.target.dataset.ip;
        if (!confirm("Unblock " + ip + "?")) return;
        await fetch("/api/unblock", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ip})});
        await refreshAll();
      });
    });
  }

  let topChart;
  async function fetchTopOffenders() {
    const res = await fetch("/api/top_offenders");
    const data = await res.json();
    const labels = data.map(d => d.ip);
    const counts = data.map(d => d.count);
    if (topChart) {
      topChart.data.labels = labels;
      topChart.data.datasets[0].data = counts;
      topChart.update();
    } else {
      topChart = new Chart(topChartCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{ label: 'Attempts', data: counts }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });
    }
  }

  async function refreshAll() {
    await fetchBlocked();
    await fetchTopOffenders();
  }

  refreshBtn.addEventListener("click", refreshAll);
  genReportBtn.addEventListener("click", async () => {
    genReportBtn.disabled = true;
    try {
      const res = await fetch("/api/generate_report", {method:"POST"});
      const json = await res.json();
      alert("Report generation: " + (json.ok ? "saved" : JSON.stringify(json)));
      await refreshAll();
    } finally {
      genReportBtn.disabled = false;
    }
  });

  // initial
  refreshAll();
});
