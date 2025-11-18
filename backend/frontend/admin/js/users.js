/* admin/js/users.js */
class UsersManager {
  constructor() {
    this.users = [];
    // try bind create form if present
    const form = document.getElementById('createUserForm');
    if (form) form.addEventListener('submit', (e)=>{ e.preventDefault(); this.createUser(); });
  }

  async loadUsers(page=1, per_page=25) {
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/users?page=${page}&per_page=${per_page}`);
      if (!resp) return;
      const data = await resp.json();
      if (!resp.ok) {
        auth.showNotification(data.error || 'Failed to load users', 'error');
        return;
      }
      this.users = data.users || [];
      this.render();
    } catch (e) { console.error(e); auth.showNotification('Failed to load users', 'error'); }
  }

  render() {
    const body = document.getElementById('usersTableBody') || document.getElementById('users-table-body');
    if (!body) return;
    if (!this.users.length) {
      body.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-gray-500">No users</td></tr>`;
      return;
    }

    body.innerHTML = this.users.map(u => `
      <tr>
        <td class="p-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded bg-blue-600 text-white flex items-center justify-center">${(u.name||'')[0]||'U'}</div>
            <div>
              <div class="font-medium">${u.name}</div>
              <div class="text-xs text-gray-500">${u.email}</div>
            </div>
          </div>
        </td>
        <td class="p-3">${u.phone||'N/A'}</td>
        <td class="p-3">${u.performance_score ?? 0}%</td>
        <td class="p-3"><span class="${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} px-2 py-1 rounded text-xs">${u.is_active ? 'Active' : 'Inactive'}</span></td>
        <td class="p-3 text-right">
          <button onclick="usersManager.view(${u.id})" class="text-blue-600 mr-2"><i class="fas fa-eye"></i></button>
          <button onclick="usersManager.delete(${u.id})" class="text-red-600"><i class="fas fa-trash"></i></button>
        </td>
      </tr>
    `).join('');
  }

  async view(id) {
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/user-data/${id}`);
      if (!resp) return;
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Load failed', 'error'); return; }
      // show modal or console
      alert(JSON.stringify(data, null, 2));
    } catch (e) { console.error(e); auth.showNotification('User data error','error'); }
  }

  async delete(id) {
    if (!confirm('Delete user?')) return;
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/delete-user/${id}`, { method: 'DELETE' });
      if (!resp) return;
      const data = await resp.json();
      if (resp.ok) { auth.showNotification('User deleted','success'); this.loadUsers(); }
      else auth.showNotification(data.error || 'Delete failed','error');
    } catch (e) { console.error(e); auth.showNotification('Delete error','error'); }
  }

  async createUser() {
    const name = document.getElementById('userName')?.value?.trim();
    const email = document.getElementById('userEmail')?.value?.trim();
    const phone = document.getElementById('userPhone')?.value?.trim();
    const password = document.getElementById('userPassword')?.value;

    if (!name || !email || !password) {
      auth.showNotification('Name, email and password required', 'error');
      return;
    }

    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/create-user', {
        method: 'POST',
        body: JSON.stringify({ name, email, phone, password })
      });
      if (!resp) return;
      const data = await resp.json();
      if (resp.ok) {
        auth.showNotification('User created', 'success');
        document.getElementById('createUserForm')?.reset();
        this.loadUsers();
      } else {
        auth.showNotification(data.error || 'Failed to create user', 'error');
      }
    } catch (e) { console.error(e); auth.showNotification('Failed to create user', 'error'); }
  }
}

const usersManager = new UsersManager();
