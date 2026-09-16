<template>
  <div class="h-full flex flex-col bg-gray-100">
    <header class="bg-primary text-white px-4 py-3 shadow">
      <h1 class="text-lg font-semibold">🏍️ Zemidjan Routing — Cotonou</h1>
      <p class="text-xs opacity-90">Routage adaptatif face aux embouteillages — démo interactive</p>
    </header>

    <div v-if="error" class="m-4 p-3 bg-red-100 text-red-700 rounded text-sm">
      Impossible de contacter le backend ({{ error }}). Vérifiez qu'il tourne
      bien sur <code>/api</code> (voir README, section Docker).
    </div>

    <div v-else-if="!network || !scenarioData" class="flex-1 flex items-center justify-center text-gray-500">
      Chargement de la simulation…
    </div>

    <div v-else class="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 p-4 min-h-0">
      <div class="lg:col-span-1 overflow-y-auto">
        <ControlPanel
          :scenario="scenario"
          :round="round"
          :max-round="scenarioData.history.static.avg_time.length"
          :playing="playing"
          :blocked="blocked"
          :avg-time="currentRoundData.avg_time"
          :paths-count="currentRoundData.paths.length"
          :params="params"
          :loading="loading"
          @update:scenario="scenario = $event"
          @update:round="round = $event"
          @toggle-play="togglePlay"
          @rerun="rerun"
          @update:params="onParamChange"
        />
      </div>

      <div class="lg:col-span-2 min-h-[420px]">
        <MapView :network="network" :flows="currentRoundData.flows" :paths="currentRoundData.paths" />
      </div>

      <div class="lg:col-span-1 overflow-y-auto">
        <ChartsPanel
          :history="scenarioData.history"
          :blockage-start="scenarioData.blockage_start"
          :blockage-end="scenarioData.blockage_end"
          :current-round="round"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import MapView from "./components/MapView.vue";
import ChartsPanel from "./components/ChartsPanel.vue";
import ControlPanel from "./components/ControlPanel.vue";
import { fetchNetwork, fetchBlockageScenario, edgeKey } from "./api.js";

const network = ref(null);
const scenarioData = ref(null);
const error = ref(null);
const loading = ref(false);

const scenario = ref("adaptive");
const round = ref(1);
const playing = ref(false);
let playTimer = null;

const params = reactive({
  adoptionRate: 0.3,
  blockageStart: 15,
  blockageEnd: 25,
});

const blocked = computed(() => {
  if (!scenarioData.value) return false;
  return round.value >= scenarioData.value.blockage_start && round.value <= scenarioData.value.blockage_end;
});

const currentRoundData = computed(() => {
  const empty = { flows: {}, avg_time: 0, paths: [] };
  if (!scenarioData.value) return empty;
  const idx = round.value - 1;
  const flowsList = scenarioData.value[`${scenario.value}_flows_by_round`];
  const pathsList = scenarioData.value[`${scenario.value}_paths_by_round`];
  const avgTimes = scenarioData.value.history[scenario.value].avg_time;
  if (!flowsList || idx < 0 || idx >= flowsList.length) return empty;
  return { flows: flowsList[idx], avg_time: avgTimes[idx], paths: pathsList[idx] };
});

async function loadAll() {
  loading.value = true;
  error.value = null;
  try {
    const [net, scenario_] = await Promise.all([
      network.value ? Promise.resolve(network.value) : fetchNetwork(),
      fetchBlockageScenario({
        adoptionRate: params.adoptionRate,
        blockageStart: params.blockageStart,
        blockageEnd: params.blockageEnd,
      }),
    ]);
    network.value = net;
    scenarioData.value = scenario_;
    round.value = 1;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function rerun() {
  loadAll();
}

function onParamChange({ key, value }) {
  params[key] = value;
}

function togglePlay() {
  playing.value = !playing.value;
  if (playing.value) {
    const max = scenarioData.value.history.static.avg_time.length;
    playTimer = setInterval(() => {
      round.value = round.value >= max ? 1 : round.value + 1;
    }, 1400);
  } else {
    clearInterval(playTimer);
  }
}

onBeforeUnmount(() => clearInterval(playTimer));

loadAll();
</script>
