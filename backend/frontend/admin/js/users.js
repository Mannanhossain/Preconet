/* users manager (admin) */
class UsersManager {
  constructor() {
    this.users = [];
    this.bindCreate();
  }

  async bindCreate() {
    const form = document.getElementById('createUserForm');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('userName').value.trim(),
        email: document.getElementById('userEmail').value.trim(),
        phone: document.getElementById('userPhone').value.trim(),
        password: document.getElementById('userPassword').value.trim()
      };
      try {
        const resp = await auth.makeAuthenticatedRequest('/api/admin/create-user', {
          method: 'POST', body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (resp.ok) {
          auth.showNotification('User created', 'success');
          form.reset();
          this.loadUsers();
        } else {
          auth.showNotification(data.error || 'Create failed', 'error');
        }
      } catch (e) { console.error(e); auth.showNotification('Create error', 'error'); }
    });
  }

  async loadUsers() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/users');
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Load users failed', 'error'); return; }
      this.users = data.users || [];
      this.render();
    } catch (e) { console.error(e); auth.showNotification('Load error', 'error'); }
  }

  render() {
    const body = document.getElementById('usersTableBody');
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
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Load failed', 'error'); return; }
      document.getElementById('modalUserTitle').innerText = data.user?.name || 'User Data';
      document.getElementById('modalUserBody').innerHTML = `<pre class="text-xs bg-gray-50 p-3 rounded">${JSON.stringify(data, null,2)}</pre>`;
      document.getElementById('userDataModal').classList.remove('hidden');
    } catch(e){ console.error(e); auth.showNotification('User data error','error'); }
  }

  async delete(id) {
    if (!confirm('Delete user?')) return;
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/delete-user/${id}`, { method: 'DELETE' });
      const data = await resp.json();
      if (resp.ok) { auth.showNotification('Deleted','success'); this.loadUsers(); }
      else auth.showNotification(data.error || 'Delete failed','error');
    } catch(e){ console.error(e); auth.showNotification('Delete error','error'); }
  }
}

const usersManager = new UsersManager();
