<template>
  <div class="saas-shell">
    <SidebarNav
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />
    <div class="saas-main">
      <FilterBar />
      <main class="saas-content">
        <router-view />
      </main>
    </div>
    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import SidebarNav from './components/SidebarNav.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileDetailsModal,
    TasksModal,
    SidebarNav
    // LanguageSwitcher and ProfileMenu moved into SidebarNav
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ============================================================
   Reset
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* ============================================================
   Shell layout — flex row: sidebar + scrollable main column
   ============================================================ */
.saas-shell {
  display: flex;
  min-height: 100vh;
  background: var(--c-bg);
}

/* Main column takes remaining width; min-width:0 prevents flex blowout */
.saas-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.saas-content {
  flex: 1;
  padding: var(--sp-6) var(--sp-8);
  max-width: var(--content-max-w);
  width: 100%;
}

@media (max-width: 960px) {
  .saas-content {
    padding: var(--sp-5);
  }
}

/* ============================================================
   Page header — used at the top of each view
   ============================================================ */
.page-header {
  margin-bottom: var(--sp-6);
}

/* Views use h2 inside .page-header (not h1) */
.page-header h2 {
  font-size: var(--fs-2xl);
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0 0 var(--sp-1) 0;
  color: var(--c-text);
}

.page-header p,
.page-header .page-description {
  color: var(--c-text-muted);
  font-size: var(--fs-md);
  margin: 0;
}

/* ============================================================
   Stats grid + stat cards
   ============================================================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--sp-5);
  margin-bottom: var(--sp-5);
}

.stat-card {
  background: var(--c-surface);
  padding: var(--sp-5);
  border-radius: var(--r-lg);
  border: 1px solid var(--c-border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.12s ease, box-shadow 0.12s ease;
}

.stat-card:hover {
  border-color: var(--c-border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--c-text-muted);
  font-size: var(--fs-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--sp-2);
}

.stat-value {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: -0.02em;
}

/* Status-tinted stat values */
.stat-card.warning .stat-value { color: var(--c-warning); }
.stat-card.success .stat-value { color: var(--c-success); }
.stat-card.danger  .stat-value { color: var(--c-danger); }
/* Info uses accent (indigo) since tokens don't define a separate --c-info */
.stat-card.info    .stat-value { color: var(--c-accent); }

/* ============================================================
   Card — general content container
   ============================================================ */
.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--sp-5);
  margin-bottom: var(--sp-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-4);
  border-bottom: 1px solid var(--c-border);
}

/* Card title uses small-caps style (uppercase, muted) from component-styles.md */
.card-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-muted);
  margin: 0;
}

/* ============================================================
   Tables — bare element selectors so all view tables pick these up
   ============================================================ */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-md);
}

thead {
  background: var(--c-bg);
}

th {
  text-align: left;
  font-size: var(--fs-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-muted);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--c-border);
}

td {
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--c-border);
  color: var(--c-text);
  font-size: var(--fs-md);
}

tbody tr {
  transition: background 0.12s ease;
}

tbody tr:hover {
  background: var(--c-bg);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* ============================================================
   Buttons
   ============================================================ */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  font-size: var(--fs-md);
  font-weight: 500;
  border-radius: var(--r-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
}

.btn-primary {
  background: var(--c-accent);
  color: white;
}

.btn-primary:hover {
  background: var(--c-accent-hover);
}

.btn-secondary {
  background: var(--c-surface);
  color: var(--c-text);
  border-color: var(--c-border);
}

.btn-secondary:hover {
  background: var(--c-bg);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ============================================================
   Badges — status pills. Hex colours kept here because the token
   set doesn't enumerate all badge-specific background/text shades.
   ============================================================ */
.badge {
  display: inline-block;
  padding: var(--sp-1) var(--sp-3);
  border-radius: var(--r-sm);
  font-size: var(--fs-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success    { background: #d1fae5; color: #065f46; }
.badge.warning    { background: #fed7aa; color: #92400e; }
.badge.danger     { background: #fecaca; color: #991b1b; }
.badge.info       { background: #dbeafe; color: #1e40af; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fecaca; color: #991b1b; }
.badge.stable     { background: #e0e7ff; color: #3730a3; }
.badge.high       { background: #fecaca; color: #991b1b; }
.badge.medium     { background: #fed7aa; color: #92400e; }
.badge.low        { background: #dbeafe; color: #1e40af; }

/* ============================================================
   Loading & error states
   ============================================================ */
.loading {
  text-align: center;
  padding: var(--sp-12);
  color: var(--c-text-muted);
  font-size: var(--fs-md);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--sp-4);
  border-radius: var(--r-md);
  margin: var(--sp-4) 0;
  font-size: var(--fs-md);
}

/* ============================================================
   Typography
   ============================================================ */
h1 { font-size: var(--fs-2xl); font-weight: 600; letter-spacing: -0.02em; color: var(--c-text); }
h2 { font-size: var(--fs-xl);  font-weight: 600; letter-spacing: -0.01em; color: var(--c-text); }
h3 { font-size: var(--fs-lg);  font-weight: 600; color: var(--c-text); }

small,
.text-muted { color: var(--c-text-muted); }

code,
.mono { font-family: var(--font-mono); font-size: 0.95em; }
</style>
