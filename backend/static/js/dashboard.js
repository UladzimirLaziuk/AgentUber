function deleteUser(email) {
  if (!confirm('Delete ' + email + '?')) return;
  fetch('/admin/users/' + encodeURIComponent(email), { method: 'DELETE' })
    .then(r => r.json())
    .then(() => location.reload())
    .catch(() => alert('Error'));
}

function loadUsers() {
  fetch('/admin/users')
    .then(r => r.json())
    .then(users => {
      const tbody = document.getElementById('users-tbody');
      if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:#555;padding:1rem;">No users yet</td></tr>';
        return;
      }
      tbody.innerHTML = users.map(u => {
        const roleClass = ['admin','driver','client','dev'].includes(u.role) ? u.role : 'other';
        const date = (u.created_at || '').slice(0, 19).replace('T', ' ');
        return `<tr>
          <td>${u.name || '—'}</td>
          <td class="email-cell">${u.email || '—'}</td>
          <td><span class="user-role ${roleClass}">${u.role || '—'}</span></td>
          <td class="note-cell">${u.note || '—'}</td>
          <td class="date-cell">${date || '—'}</td>
          <td><button class="btn-delete" onclick="deleteUser('${u.email}')">✕</button></td>
        </tr>`;
      }).join('');
    })
    .catch(() => {
      document.getElementById('users-tbody').innerHTML =
        '<tr><td colspan="6" style="color:#f87171;">Failed to load users</td></tr>';
    });
}

loadUsers();