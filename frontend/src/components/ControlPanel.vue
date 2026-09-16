<template>
  <div class="bg-white rounded-lg shadow p-4 space-y-4">
    <div v-if="blocked" class="bg-warning text-white text-xs font-bold text-center rounded py-1">
      🚧 Pont bloqué (accident)
    </div>

    <div>
      <label class="text-xs text-gray-500 block mb-1">Stratégie de routage</label>
      <div class="flex gap-2">
        <button
          class="flex-1 py-1.5 rounded border text-sm"
          :class="scenario === 'static' ? 'bg-primary text-white border-primary' : 'border-primary text-primary'"
          @click="$emit('update:scenario', 'static')"
        >Statique</button>
        <button
          class="flex-1 py-1.5 rounded border text-sm"
          :class="scenario === 'adaptive' ? 'bg-primary text-white border-primary' : 'border-primary text-primary'"
          @click="$emit('update:scenario', 'adaptive')"
        >Adaptatif</button>
      </div>
    </div>

    <div>
      <label class="text-xs text-gray-500 block mb-1">
        Round : <span class="font-semibold">{{ round }}</span> / {{ maxRound }}
      </label>
      <input
        type="range" min="1" :max="maxRound" :value="round"
        class="w-full accent-primary"
        @input="$emit('update:round', Number($event.target.value))"
      />
    </div>

    <button
      class="w-full py-2 rounded bg-secondary text-white text-sm"
      @click="$emit('toggle-play')"
    >{{ playing ? "⏸ Pause" : "▶ Lecture automatique" }}</button>

    <div class="border-t pt-3 space-y-2">
      <p class="text-xs font-semibold text-gray-600">Paramètres de la simulation</p>

      <label class="text-xs text-gray-500 block">
        Taux d'adoption (part des trajets qui réagissent au trafic) : {{ (params.adoptionRate * 100).toFixed(0) }}%
        <input
          type="range" min="0" max="1" step="0.05" :value="params.adoptionRate"
          class="w-full accent-secondary"
          @input="update('adoptionRate', Number($event.target.value))"
        />
      </label>

      <label class="text-xs text-gray-500 block">
        Début du blocage (round)
        <input
          type="number" min="1" :value="params.blockageStart"
          class="w-full border rounded px-2 py-1 text-sm"
          @change="update('blockageStart', Number($event.target.value))"
        />
      </label>

      <label class="text-xs text-gray-500 block">
        Fin du blocage (round)
        <input
          type="number" min="1" :value="params.blockageEnd"
          class="w-full border rounded px-2 py-1 text-sm"
          @change="update('blockageEnd', Number($event.target.value))"
        />
      </label>

      <button
        class="w-full py-1.5 rounded border border-secondary text-secondary text-sm"
        @click="$emit('rerun')"
        :disabled="loading"
      >{{ loading ? "Simulation en cours…" : "🔄 Relancer la simulation" }}</button>
    </div>

    <div class="border-t pt-3 text-xs text-gray-600 space-y-1">
      <p>Temps de trajet moyen : <span class="font-semibold">{{ avgTime.toFixed(1) }} min</span></p>
      <p>Trajets affichés ce round : {{ pathsCount }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  scenario: String,
  round: Number,
  maxRound: Number,
  playing: Boolean,
  blocked: Boolean,
  avgTime: Number,
  pathsCount: Number,
  params: Object,
  loading: Boolean,
});

const emit = defineEmits(["update:scenario", "update:round", "toggle-play", "rerun", "update:params"]);

function update(key, value) {
  emit("update:params", { key, value });
}
</script>
