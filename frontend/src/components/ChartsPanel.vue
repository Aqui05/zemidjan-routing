<template>
  <div class="grid grid-cols-1 gap-4">
    <div class="bg-white rounded-lg shadow p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-2">Temps de trajet moyen par round</h3>
      <canvas ref="timeCanvas" class="w-full" height="140"></canvas>
    </div>
    <div class="bg-white rounded-lg shadow p-4">
      <h3 class="text-sm font-semibold text-gray-700 mb-2">Trajets empruntant le pont</h3>
      <canvas ref="bridgeCanvas" class="w-full" height="140"></canvas>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from "vue";
import Chart from "chart.js/auto";

const props = defineProps({
  history: { type: Object, required: true }, // { static: {avg_time, bridge_flow}, adaptive: {...} }
  blockageStart: { type: Number, required: true },
  blockageEnd: { type: Number, required: true },
  currentRound: { type: Number, required: true },
});

const timeCanvas = ref(null);
const bridgeCanvas = ref(null);
let timeChart = null;
let bridgeChart = null;

function blockageAnnotationPlugin() {
  // petit plugin maison (evite d'ajouter chartjs-plugin-annotation en
  // dependance juste pour une bande verticale) : dessine le rectangle du
  // blocage et une ligne verticale pour le round courant.
  return {
    id: "blockageBand",
    beforeDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!chartArea) return;
      const x1 = scales.x.getPixelForValue(props.blockageStart);
      const x2 = scales.x.getPixelForValue(props.blockageEnd);
      ctx.save();
      ctx.fillStyle = "rgba(224, 161, 0, 0.15)";
      ctx.fillRect(x1, chartArea.top, x2 - x1, chartArea.bottom - chartArea.top);

      const xCurrent = scales.x.getPixelForValue(props.currentRound);
      ctx.strokeStyle = "#2E7DD1";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(xCurrent, chartArea.top);
      ctx.lineTo(xCurrent, chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    },
  };
}

function buildChart(canvas, datasets, yLabel) {
  const rounds = props.history.static.avg_time.map((_, i) => i + 1);
  return new Chart(canvas, {
    type: "line",
    data: { labels: rounds, datasets },
    options: {
      responsive: true,
      animation: false,
      interaction: { intersect: false, mode: "index" },
      scales: {
        x: { title: { display: true, text: "Round" } },
        y: { title: { display: true, text: yLabel } },
      },
      plugins: { legend: { position: "bottom" } },
    },
    plugins: [blockageAnnotationPlugin()],
  });
}

function render() {
  if (timeChart) timeChart.destroy();
  if (bridgeChart) bridgeChart.destroy();

  timeChart = buildChart(timeCanvas.value, [
    { label: "Statique", data: props.history.static.avg_time, borderColor: "#D34C4C", backgroundColor: "transparent", tension: 0.25 },
    { label: "Adaptatif", data: props.history.adaptive.avg_time, borderColor: "#1B8A5A", backgroundColor: "transparent", tension: 0.25 },
  ], "Minutes");

  bridgeChart = buildChart(bridgeCanvas.value, [
    { label: "Statique", data: props.history.static.bridge_flow, borderColor: "#D34C4C", backgroundColor: "transparent", tension: 0.25 },
    { label: "Adaptatif", data: props.history.adaptive.bridge_flow, borderColor: "#1B8A5A", backgroundColor: "transparent", tension: 0.25 },
  ], "Trajets");
}

onMounted(render);
onBeforeUnmount(() => { timeChart?.destroy(); bridgeChart?.destroy(); });
watch(() => props.currentRound, () => { timeChart?.update(); bridgeChart?.update(); });
watch(() => props.history, render);
</script>
