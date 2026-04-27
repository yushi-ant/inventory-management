<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Slider Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-body">
        <div class="budget-display">{{ formatCurrency(budget) }}</div>
        <input
          type="range"
          class="budget-slider"
          min="5000"
          max="100000"
          step="1000"
          v-model.number="budget"
        />
        <div class="slider-labels">
          <span>{{ formatCurrency(5000) }}</span>
          <span>{{ formatCurrency(100000) }}</span>
        </div>
      </div>
    </div>

    <!-- Success Banner -->
    <div v-if="successOrder" class="success-banner">
      {{ t('restocking.orderPlaced', { orderNumber: successOrder.order_number }) }}
      <router-link to="/orders" class="success-link">{{ t('restocking.viewOrders') }}</router-link>
    </div>

    <!-- Recommendation Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="!recommendation || !recommendation.items || recommendation.items.length === 0" class="empty-state">
        {{ t('restocking.noItems') }}
      </div>
      <div v-else>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <!-- Empty header for toggle column -->
                <th class="toggle-col"></th>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.item') }}</th>
                <th>{{ t('restocking.qty') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <!-- Wrap each item's main row + rationale row in a template for correct keying -->
              <template v-for="item in recommendation.items" :key="item.sku">
                <tr>
                  <td class="toggle-cell">
                    <button
                      class="toggle-btn"
                      :class="{ expanded: expandedSkus.has(item.sku) }"
                      @click="toggleExpanded(item.sku)"
                      :aria-label="t('restocking.rationale.why')"
                    >
                      &#8250;
                    </button>
                  </td>
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.quantity }}</td>
                  <td>{{ formatCurrency(item.unit_cost) }}</td>
                  <td><strong>{{ formatCurrency(item.line_total) }}</strong></td>
                </tr>
                <!-- Rationale row, shown only when this SKU is expanded -->
                <tr v-if="expandedSkus.has(item.sku)" class="rationale-row">
                  <td colspan="6" class="rationale-cell">
                    <div class="rationale-metrics">
                      <!-- Inline metric chips separated by · -->
                      <span class="metric">
                        <span class="metric-label">{{ t('restocking.rationale.onHand') }}</span>
                        <span class="metric-value">{{ item.quantity_on_hand }}</span>
                      </span>
                      <span class="separator">·</span>
                      <span class="metric">
                        <span class="metric-label">{{ t('restocking.rationale.forecast') }}</span>
                        <span class="metric-value">{{ item.forecasted_demand }}</span>
                      </span>
                      <span class="separator">·</span>
                      <span class="metric">
                        <span class="metric-label">{{ t('restocking.rationale.shortfall') }}</span>
                        <span class="metric-value">{{ item.shortfall }}</span>
                      </span>
                      <span class="separator">·</span>
                      <span class="metric">
                        <span class="metric-label">{{ t('restocking.rationale.trend') }}</span>
                        <span class="metric-value">
                          {{ item.trend }}
                          <!-- Show trend weight in parentheses -->
                          <span class="metric-weight">(×{{ trendWeight(item.trend) }} {{ t('restocking.rationale.weight') }})</span>
                        </span>
                      </span>
                      <span class="separator">·</span>
                      <span class="metric">
                        <span class="metric-label">{{ t('restocking.rationale.priorityScore') }}</span>
                        <span class="metric-value">{{ item.priority_score }}</span>
                      </span>
                    </div>
                    <!-- Partial fill notice: shown when budget only covers a portion of the shortfall -->
                    <div v-if="item.quantity < item.shortfall" class="rationale-partial">
                      {{ t('restocking.rationale.partialFill', { qty: item.quantity, shortfall: item.shortfall }) }}
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <div class="summary-rows">
          <div class="summary-row">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-value">{{ formatCurrency(recommendation.total_cost) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">{{ t('restocking.remaining') }}</span>
            <span class="summary-value remaining">{{ formatCurrency(recommendation.remaining_budget) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">{{ t('restocking.leadTime') }}</span>
            <span class="summary-value">{{ recommendation.lead_time_days }} {{ t('restocking.days') }}</span>
          </div>
        </div>

        <div class="order-action">
          <button
            class="btn-primary"
            :disabled="submitting || !recommendation?.items?.length"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

// Map trend strings to display weights used in the rationale panel
const TREND_WEIGHTS = {
  increasing: 1.5,
  stable: 1.0,
  decreasing: 0.7
}

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const budget = ref(25000)
    const recommendation = ref(null)
    const loading = ref(false)
    const submitting = ref(false)
    const error = ref(null)
    const successOrder = ref(null)

    // Tracks which SKUs have their rationale rows open
    const expandedSkus = ref(new Set())

    // Toggle a SKU's expanded state; create a new Set so Vue's reactivity detects the change
    const toggleExpanded = (sku) => {
      const next = new Set(expandedSkus.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      expandedSkus.value = next
    }

    // Return the display weight for a trend value; falls back to 1.0 for unknown trends
    const trendWeight = (trend) => {
      return TREND_WEIGHTS[trend] ?? 1.0
    }

    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const loadRecommendation = async () => {
      loading.value = true
      error.value = null
      try {
        recommendation.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      error.value = null
      try {
        const result = await api.createRestockOrder({
          budget: budget.value,
          items: recommendation.value.items
        })
        successOrder.value = result
        // Reload recommendations after placing order
        await loadRecommendation()
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    // Debounce budget changes to avoid spamming the API on slider drag;
    // also reset expanded rows and success banner when budget changes
    let debounceTimer = null
    watch(budget, () => {
      successOrder.value = null
      expandedSkus.value = new Set() // collapse all rationale rows on budget change
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendation()
      }, 250)
    })

    onMounted(loadRecommendation)

    return {
      t,
      budget,
      recommendation,
      loading,
      submitting,
      error,
      successOrder,
      expandedSkus,
      toggleExpanded,
      trendWeight,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-body {
  padding: 0.5rem 0;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1.25rem;
}

.budget-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
  transition: background 0.2s;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #1e293b;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.budget-slider::-moz-range-thumb:hover {
  background: #1e293b;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.success-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.success-link:hover {
  color: #047857;
}

.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Toggle column: narrow fixed width so it doesn't affect other columns */
.toggle-col {
  width: 36px;
}

.toggle-cell {
  padding: 0.5rem 0.5rem;
  text-align: center;
}

/* The chevron toggle button */
.toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 1.125rem;
  line-height: 1;
  padding: 0;
  /* Rotate from pointing right (›) to pointing down when expanded */
  transition: transform 0.15s;
  transform: rotate(0deg);
}

.toggle-btn.expanded {
  transform: rotate(90deg);
}

/* Rationale row styling: subtle inset panel */
.rationale-row {
  background: #f8fafc;
}

.rationale-cell {
  background: #f8fafc;
  font-size: 0.8125rem;
  color: #475569;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border-top: none;
}

/* Inline metric chips row */
.rationale-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
}

.metric {
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
}

.metric-label {
  color: #64748b;
}

/* Metric values rendered in dark semibold */
.metric-value {
  color: #0f172a;
  font-weight: 600;
}

/* Weight annotation next to trend value: lighter, smaller */
.metric-weight {
  color: #64748b;
  font-weight: 400;
  font-size: 0.75rem;
}

.separator {
  color: #94a3b8;
  padding: 0 0.125rem;
}

/* Partial fill notice: muted second line */
.rationale-partial {
  margin-top: 0.375rem;
  color: #64748b;
  font-style: italic;
}

.summary-rows {
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.375rem 0.75rem;
  font-size: 0.938rem;
}

.summary-label {
  color: #64748b;
  font-weight: 500;
}

.summary-value {
  font-weight: 700;
  color: #0f172a;
}

.summary-value.remaining {
  color: #059669;
}

.order-action {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-primary {
  background: #0f172a;
  color: white;
  border: none;
  padding: 0.75rem 1.75rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
