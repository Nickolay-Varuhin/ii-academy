import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="margin-bottom:24px">
        <h2 style="font-size:24px;font-weight:700">Панель администратора</h2>
        <p style="font-size:14px;color:#6b7280;margin-top:4px">
          Управление пользователями и мониторинг системы.
        </p>
      </div>

      <!-- Статистика -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
        <div class="card">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Всего юзеров</div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">{{stats?.total_users || 0}}</div>
          <div style="font-size:12px;color:#16a34a;margin-top:4px">
            Активных: {{stats?.active_users || 0}}
          </div>
        </div>
        <div class="card">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Всего диалогов</div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">{{stats?.total_dialogs || 0}}</div>
          <div style="font-size:12px;color:#2563eb;margin-top:4px">
            Сегодня: {{stats?.total_sessions_today || 0}}
          </div>
        </div>
        <div class="card">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Админов</div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{stats?.users_by_role?.admin || 0}}
          </div>
        </div>
        <div class="card">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">HR-специалистов</div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{stats?.users_by_role?.hr || 0}}
          </div>
        </div>
      </div>

      <!-- Переключатель таба -->
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <button (click)="activeTab='users'"
                [style.background]="activeTab==='users' ? '#2563eb' : '#f9fafb'"
                [style.color]="activeTab==='users' ? '#fff' : '#6b7280'"
                style="padding:8px 16px;border:none;border-radius:8px;font-weight:500;cursor:pointer">
          Пользователи
        </button>
        <button (click)="activeTab='logs'"
                [style.background]="activeTab==='logs' ? '#2563eb' : '#f9fafb'"
                [style.color]="activeTab==='logs' ? '#fff' : '#6b7280'"
                style="padding:8px 16px;border:none;border-radius:8px;font-weight:500;cursor:pointer">
          Системные логи
        </button>
      </div>

      <!-- Пользователи -->
      @if (activeTab === 'users') {
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h3 style="font-weight:600">Список пользователей</h3>
            <button class="btn-primary" (click)="openCreateForm()">
              <app-icon name="plus" [size]="14" color="#fff"></app-icon>
              <span>Добавить</span>
            </button>
          </div>

          @if (formUser) {
            <div style="background:#f9fafb;padding:16px;border-radius:8px;margin-bottom:16px">
              <h4 style="font-weight:600;margin-bottom:12px">
                {{formUser.id ? 'Редактировать' : 'Создать'}} пользователя
              </h4>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <input [(ngModel)]="formUser.email" placeholder="Email"
                       [disabled]="!!formUser.id">
                @if (!formUser.id) {
                  <input [(ngModel)]="formUser.password" placeholder="Пароль" type="password">
                }
                <input [(ngModel)]="formUser.first_name" placeholder="Имя">
                <input [(ngModel)]="formUser.last_name" placeholder="Фамилия">
                <select [(ngModel)]="formUser.role">
                  <option value="employee">Сотрудник</option>
                  <option value="hr">HR-специалист</option>
                  <option value="admin">Администратор</option>
                </select>
                <input [(ngModel)]="formUser.department" placeholder="Отдел">
                <input [(ngModel)]="formUser.position" placeholder="Должность"
                       style="grid-column:span 2">
              </div>
              @if (formError) {
                <div style="color:#ef4444;font-size:13px;margin-top:8px">{{formError}}</div>
              }
              <div style="margin-top:12px;display:flex;gap:8px">
                <button (click)="saveUser()" class="btn-primary">
                  <app-icon name="check" [size]="14" color="#fff"></app-icon>
                  <span>Сохранить</span>
                </button>
                <button (click)="formUser = null" class="btn-ghost">Отмена</button>
              </div>
            </div>
          }

          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <thead>
              <tr style="text-align:left;color:#9ca3af;border-bottom:1px solid #f3f4f6">
                <th style="padding:10px 8px;font-weight:500">ID</th>
                <th style="padding:10px 8px;font-weight:500">Email</th>
                <th style="padding:10px 8px;font-weight:500">ФИО</th>
                <th style="padding:10px 8px;font-weight:500">Роль</th>
                <th style="padding:10px 8px;font-weight:500">Отдел</th>
                <th style="padding:10px 8px;font-weight:500">Статус</th>
                <th style="padding:10px 8px;font-weight:500">Действия</th>
              </tr>
            </thead>
            <tbody>
              @for (u of users; track u.id) {
                <tr style="border-bottom:1px solid #fafafa">
                  <td style="padding:10px 8px;color:#9ca3af">#{{u.id}}</td>
                  <td style="padding:10px 8px">{{u.email}}</td>
                  <td style="padding:10px 8px">{{u.first_name}} {{u.last_name}}</td>
                  <td style="padding:10px 8px">
                    <span [class]="'badge ' + roleBadge(u.role)">{{roleLabel(u.role)}}</span>
                  </td>
                  <td style="padding:10px 8px;color:#6b7280">{{u.department || '—'}}</td>
                  <td style="padding:10px 8px">
                    <span [style.color]="u.is_active ? '#16a34a' : '#9ca3af'"
                          style="font-weight:600;font-size:12px">
                      {{u.is_active ? '● Активен' : '○ Отключён'}}
                    </span>
                  </td>
                  <td style="padding:10px 8px;display:flex;gap:4px">
                    <button class="icon-btn" (click)="editUser(u)" title="Редактировать">
                      <app-icon name="edit" [size]="15" color="#2563eb"></app-icon>
                    </button>
                    @if (u.is_active) {
                      <button class="icon-btn" (click)="deleteUser(u)" title="Отключить">
                        <app-icon name="trash" [size]="15" color="#ef4444"></app-icon>
                      </button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }

      <!-- Логи -->
      @if (activeTab === 'logs') {
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h3 style="font-weight:600">Системные логи</h3>
            <select [(ngModel)]="logFilter" (change)="loadLogs()">
              <option value="">Все события</option>
              <option value="user_login">Входы</option>
              <option value="dialog_completed">Завершения диалогов</option>
              <option value="skill_mastery_changed">Изменения уровня навыков</option>
            </select>
          </div>

          <table style="width:100%;font-size:13px;border-collapse:collapse">
            <thead>
              <tr style="text-align:left;color:#9ca3af;border-bottom:1px solid #f3f4f6">
                <th style="padding:10px 8px;font-weight:500">Время</th>
                <th style="padding:10px 8px;font-weight:500">Событие</th>
                <th style="padding:10px 8px;font-weight:500">Пользователь</th>
                <th style="padding:10px 8px;font-weight:500">Подробности</th>
              </tr>
            </thead>
            <tbody>
              @for (log of logs; track log.id) {
                <tr style="border-bottom:1px solid #fafafa">
                  <td style="padding:10px 8px;color:#6b7280;white-space:nowrap">
                    {{log.created_at | date:'dd.MM HH:mm:ss'}}
                  </td>
                  <td style="padding:10px 8px">
                    <span class="badge badge-blue">{{log.event_type}}</span>
                  </td>
                  <td style="padding:10px 8px">{{log.user_email || '—'}}</td>
                  <td style="padding:10px 8px;color:#6b7280;font-family:monospace;font-size:12px">
                    {{formatDetails(log.details)}}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
  styles: [`
    .icon-btn {
      background: none; border: none; cursor: pointer; padding: 6px;
      border-radius: 6px; display: inline-flex; align-items: center;
    }
    .icon-btn:hover { background: #f3f4f6; }
  `],
})
export class AdminComponent implements OnInit {
  activeTab: 'users' | 'logs' = 'users';
  stats: any = null;
  users: any[] = [];
  logs: any[] = [];
  logFilter = '';

  formUser: any = null;
  formError = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadStats();
    this.loadUsers();
    this.loadLogs();
  }

  loadStats() { this.api.getAdminStats().subscribe(s => this.stats = s); }
  loadUsers() { this.api.getUsers().subscribe(u => this.users = u || []); }
  loadLogs()  { this.api.getLogs(this.logFilter || undefined).subscribe(l => this.logs = l || []); }

  openCreateForm() {
    this.formUser = {
      email: '', password: '', first_name: '', last_name: '',
      role: 'employee', department: '', position: '',
    };
    this.formError = '';
  }

  editUser(u: any) { this.formUser = { ...u }; this.formError = ''; }

  saveUser() {
    this.formError = '';
    if (this.formUser.id) {
      const payload: any = {
        first_name: this.formUser.first_name,
        last_name: this.formUser.last_name,
        role: this.formUser.role,
        department: this.formUser.department,
        position: this.formUser.position,
        is_active: this.formUser.is_active,
      };
      this.api.updateUser(this.formUser.id, payload).subscribe({
        next: () => { this.formUser = null; this.loadUsers(); this.loadStats(); },
        error: (e) => this.formError = e?.error?.detail || 'Ошибка сохранения',
      });
    } else {
      this.api.createUser(this.formUser).subscribe({
        next: () => { this.formUser = null; this.loadUsers(); this.loadStats(); },
        error: (e) => this.formError = e?.error?.detail || 'Ошибка создания',
      });
    }
  }

  deleteUser(u: any) {
    if (!confirm(`Отключить пользователя ${u.email}?`)) return;
    this.api.deleteUser(u.id).subscribe(() => { this.loadUsers(); this.loadStats(); });
  }

  roleLabel(r: string): string {
    return ({ admin: 'Администратор', hr: 'HR', employee: 'Сотрудник' } as any)[r] || r;
  }

  roleBadge(r: string): string {
    return ({ admin: 'badge-red', hr: 'badge-yellow', employee: 'badge-blue' } as any)[r] || 'badge-blue';
  }

  formatDetails(d: any): string {
    if (!d || !Object.keys(d).length) return '—';
    try { return JSON.stringify(d); } catch { return String(d); }
  }
}
