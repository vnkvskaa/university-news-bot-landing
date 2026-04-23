const cards = document.querySelectorAll(
  ".tile, .metric-card, .scale-cards article, .decision-card, .insight-card, .mini-chart-panel, .comparison-panel"
    + ", .audience-card, .proof-card, .flow-card, .mvp-clean-grid article, .feature-table, .hero-summary, .metrics-compare"
    + ", .user-journey article"
);

const reveal = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        reveal.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.16 }
);

cards.forEach((card) => {
  card.classList.add("reveal");
  reveal.observe(card);
});

const tooltip = document.createElement("div");
tooltip.className = "chart-tooltip";
tooltip.hidden = true;
document.body.append(tooltip);

const chartItems = document.querySelectorAll("[data-label][data-value]");

function showTooltip(event) {
  const target = event.currentTarget;
  tooltip.innerHTML = `<strong>${target.dataset.label}</strong><span>${target.dataset.value}</span>`;
  tooltip.hidden = false;
  if (event.clientX && event.clientY) {
    moveTooltip(event);
    return;
  }

  const rect = target.getBoundingClientRect();
  tooltip.style.left = `${rect.left + rect.width / 2}px`;
  tooltip.style.top = `${rect.top}px`;
}

function moveTooltip(event) {
  tooltip.style.left = `${event.clientX}px`;
  tooltip.style.top = `${event.clientY}px`;
}

function hideTooltip() {
  tooltip.hidden = true;
}

chartItems.forEach((item) => {
  item.addEventListener("mouseenter", showTooltip);
  item.addEventListener("mousemove", moveTooltip);
  item.addEventListener("mouseleave", hideTooltip);
  item.addEventListener("focus", showTooltip);
  item.addEventListener("blur", hideTooltip);
});
