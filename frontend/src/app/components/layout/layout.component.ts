import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../icon/icon.component';

interface NavItem {
  path: string;
  icon: string;
  label: string;
  roles?: string[];
}

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, IconComponent],
  template: `
    <div style="display:flex;min-height:100vh">
      <aside style="width:240px;background:#fff;border-right:1px solid #e5e7eb;padding:16px;display:flex;flex-direction:column">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px;padding:4px">
          <app-icon name="academy" [size]="26" color="#2563eb"></app-icon>
          <span style="font-weight:700;font-size:17px;color:#1f2937">ИИ-Академия</span>
        </div>

        <nav style="display:flex;flex-direction:column;gap:2px">
          @for (item of visibleItems; track item.path) {
            <a [routerLink]="item.path"
               routerLinkActive="active-link"
               [routerLinkActiveOptions]="{exact: item.path === '/'}"
               class="nav-link">
              <app-icon [name]="item.icon" [size]="18"></app-icon>
              <span>{{item.label}}</span>
            </a>
          }
        </nav>

        <div style="margin-top:auto;padding:12px;background:#f9fafb;border-radius:8px">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em">Ваша роль</div>
          <div style="font-size:14px;font-weight:600;color:#1f2937;margin-top:2px">
            {{roleLabel(auth.user?.role)}}
          </div>
        </div>
      </aside>

      <div style="flex:1;display:flex;flex-direction:column;overflow:auto">
        <header style="height:60px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 24px">
          <h1 style="font-size:15px;font-weight:600;color:#6b7280">{{currentTitle}}</h1>
          <div style="display:flex;align-items:center;gap:16px">
            <button class="icon-btn" title="Уведомления">
              <app-icon name="bell" [size]="19" color="#6b7280"></app-icon>
            </button>
            <div style="display:flex;align-items:center;gap:10px">
              <div style="text-align:right">
                <div style="font-size:14px;font-weight:500;color:#1f2937">{{auth.user?.full_name}}</div>
                <div style="font-size:11px;color:#9ca3af">{{roleLabel(auth.user?.role)}}</div>
              </div>
              <div style="width:36px;height:36px;border-radius:50%;background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700">
                {{auth.user?.full_name?.charAt(0)}}
              </div>
              <button (click)="auth.logout()" class="icon-btn" title="Выйти"
                style="color:#9ca3af;display:flex;align-items:center;gap:6px;font-size:13px">
                <app-icon name="logout" [size]="17" color="#9ca3af"></app-icon>
                <span>Выйти</span>
              </button>
            </div>
          </div>
        </header>

        <main style="flex:1;overflow:auto">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .nav-link {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 14px;
      color: #6b7280;
      transition: all 0.15s;
    }
    .nav-link:hover { background: #f9fafb; color: #1f2937; }
    .active-link {
      background: #eff6ff !important;
      color: #2563eb !important;
      font-weight: 600 !important;
    }

    .icon-btn {
      background: none;
      border: none;
      cursor: pointer;
      padding: 6px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      transition: background 0.15s;
    }
    .icon-btn:hover { background: #f3f4f6; }
  `],
})
export class LayoutComponent {
  currentTitle = 'ИИ-Академия';

  private allItems: NavItem[] = [
    { path: '/',                icon: 'dashboard',  label: 'Обзорная панель' },

    // Страницы обучения — только сотрудник
    { path: '/skills',          icon: 'map',        label: 'Карта навыков',      roles: ['employee'] },
    { path: '/simulator',       icon: 'chat',       label: 'AI-Симулятор',       roles: ['employee'] },
    { path: '/mentor',          icon: 'sparkle',    label: 'AI-Наставник',       roles: ['employee'] },

    // Мои задания — только сотрудник
    { path: '/assignments',     icon: 'clipboard',  label: 'Мои задания',        roles: ['employee'] },

    // HR-секция
    { path: '/hr-dashboard',    icon: 'users',      label: 'HR-панель',              roles: ['hr', 'admin'] },
    { path: '/hr-assignments',  icon: 'clipboard',  label: 'Задания для команды',    roles: ['hr', 'admin'] },
    { path: '/analytics',       icon: 'chart',      label: 'Аналитика',              roles: ['hr', 'admin'] },
    { path: '/reports',         icon: 'document',   label: 'Отчёты о достижениях',   roles: ['hr', 'admin'] },

    // Админская секция
    { path: '/admin',           icon: 'shield',     label: 'Администрирование',      roles: ['admin'] },
  ];

  constructor(public auth: AuthService) {}

  get visibleItems(): NavItem[] {
    const role = this.auth.user?.role;
    if (!role) return [];
    return this.allItems.filter(item => !item.roles || item.roles.includes(role));
  }

  roleLabel(role?: string): string {
    switch (role) {
      case 'admin':    return 'Администратор';
      case 'hr':       return 'HR-специалист';
      case 'employee': return 'Сотрудник';
      default:         return '—';
    }
  }
}
