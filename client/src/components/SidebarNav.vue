<template>
  <aside class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
    <div class="sidebar-header">
      <span class="brand" v-if="!isCollapsed">{{ t('nav.companyName') }}</span>
      <button
        v-if="!isNarrow"
        class="collapse-btn"
        type="button"
        @click="toggle"
        :aria-label="collapsed ? 'Expand navigation' : 'Collapse navigation'"
      >
        <span class="chevron" :class="{ rot: collapsed }">&#8249;</span>
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.overview') }}</span>
      </router-link>

      <router-link to="/inventory" class="nav-item" :class="{ active: $route.path === '/inventory' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.inventory') }}</span>
      </router-link>

      <router-link to="/orders" class="nav-item" :class="{ active: $route.path === '/orders' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
            <rect x="8" y="2" width="8" height="4" rx="1"/>
            <line x1="9" y1="12" x2="15" y2="12"/>
            <line x1="9" y1="16" x2="15" y2="16"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.orders') }}</span>
      </router-link>

      <router-link to="/spending" class="nav-item" :class="{ active: $route.path === '/spending' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.finance') }}</span>
      </router-link>

      <router-link to="/demand" class="nav-item" :class="{ active: $route.path === '/demand' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
            <polyline points="17 6 23 6 23 12"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.demandForecast') }}</span>
      </router-link>

      <router-link to="/restocking" class="nav-item" :class="{ active: $route.path === '/restocking' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </span>
        <span class="nav-label">{{ t('nav.restocking') }}</span>
      </router-link>

      <router-link to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
        <span class="nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="20" x2="12" y2="10"/>
            <line x1="18" y1="20" x2="18" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="16"/>
          </svg>
        </span>
        <span class="nav-label">Reports</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <!-- LanguageSwitcher is hidden when collapsed to save space -->
      <LanguageSwitcher v-if="!isCollapsed" />
      <!-- ProfileMenu stays visible in both states so user can always access profile/tasks -->
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

// Key for persisting sidebar collapsed state across sessions
const STORAGE_KEY = 'saas.sidebar.collapsed'

export default {
  name: 'SidebarNav',
  components: {
    LanguageSwitcher,
    ProfileMenu
  },
  emits: ['show-profile-details', 'show-tasks'],
  setup() {
    const { t } = useI18n()
    const collapsed = ref(false)

    // Tracks whether viewport is below 960px — auto-collapses sidebar at narrow widths
    const isNarrow = ref(false)

    // Effective collapsed state: narrow viewport overrides manual toggle
    const isCollapsed = computed(() => isNarrow.value || collapsed.value)

    let mqListener = null

    onMounted(() => {
      // Restore manual collapsed state from localStorage on mount
      collapsed.value = localStorage.getItem(STORAGE_KEY) === '1'

      // Set up media query listener to auto-collapse on narrow viewports
      const mq = window.matchMedia('(max-width: 960px)')
      isNarrow.value = mq.matches
      mqListener = (e) => { isNarrow.value = e.matches }
      mq.addEventListener('change', mqListener)
      // Store mq reference for cleanup
      mqListener._mq = mq
    })

    onUnmounted(() => {
      // Clean up media query listener to avoid memory leaks
      if (mqListener && mqListener._mq) {
        mqListener._mq.removeEventListener('change', mqListener)
      }
    })

    const toggle = () => {
      collapsed.value = !collapsed.value
      localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0')
    }

    return { t, collapsed, isNarrow, isCollapsed, toggle }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  /* Light surface with border — matches white bg used across cards */
  background: var(--c-surface);
  border-right: 1px solid var(--c-border);
  transition: width 0.18s ease;
  overflow: hidden;
}

.sidebar.is-collapsed {
  width: var(--sidebar-w-collapsed);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-4);
  border-bottom: 1px solid var(--c-border);
  min-height: 60px;
}

.brand {
  font-weight: 600;
  font-size: var(--fs-lg);
  letter-spacing: -0.01em;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  background: var(--c-surface);
  color: var(--c-text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: background 0.12s ease, color 0.12s ease;
}

.collapse-btn:hover {
  background: var(--c-bg);
  color: var(--c-text);
}

.chevron {
  display: inline-block;
  transition: transform 0.18s ease;
  font-size: 16px;
  line-height: 1;
}

/* Rotate arrow when expanded → collapsed direction reverses */
.chevron.rot {
  transform: rotate(180deg);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--sp-3);
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  color: var(--c-text-muted);
  text-decoration: none;
  font-size: var(--fs-md);
  font-weight: 500;
  transition: background 0.12s ease, color 0.12s ease;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--c-bg);
  color: var(--c-text);
}

.nav-item.active {
  background: var(--c-accent-soft);
  /* Icon and label both inherit this indigo color — no separate icon styling needed */
  color: var(--c-accent);
}

/* SVG icon wrapper — fixed size, centered, inherits current color from nav-item */
.nav-icon {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: inherit;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

/* Collapsed state: hide text labels, center items */
.is-collapsed .nav-label {
  display: none;
}

.is-collapsed .nav-item {
  justify-content: center;
  padding: var(--sp-2);
}

.is-collapsed .sidebar-header {
  justify-content: center;
}

.sidebar-footer {
  padding: var(--sp-3);
  border-top: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.is-collapsed .sidebar-footer {
  align-items: center;
}
</style>
