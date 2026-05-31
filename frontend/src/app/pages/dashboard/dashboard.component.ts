import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="margin-bottom:24px">
        <h2 style="font-size:24px;font-weight:700;color:#1f2937">
          С возвращением, {{firstName}}!
        </h2>
        <p style="font-size:14px;color:#6b7280;margin-top:4px">
          @if (role === 'admin') {
            <span>Вы вошли как администратор. Переходите в
            <a routerLink="/admin" style="color:#2563eb">панель администрирования</a>
            для управления системой.</span>
          } @else if (role === 'hr') {
            <span>Вы вошли как HR-специалист. Посмотрите
            <a routerLink="/hr-dashboard" style="color:#2563eb">HR-панель</a>,
            <a routerLink="/hr-assignments" style="color:#2563eb">задания для команды</a>
            или <a routerLink="/analytics" style="color:#2563eb">аналитику</a>.</span>
          } @else {
            <span>Ваш профиль компетенций совпадает с целевым на
            <strong>{{stats?.skill_match_percent}}%</strong>. Отличная работа!</span>
          }
        </p>
      </div>

      <!-- Для сотрудника: метрики + рекомендации + задачи -->
      @if (role === 'employee' || !role) {
        <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
          <a routerLink="/mentor" class="btn-primary">
            <span>Спросить ИИ-наставника</span>
            <app-icon name="arrow-right" [size]="16" color="#fff"></app-icon>
          </a>
        </div>

        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
          @for (c of cards; track c.label) {
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div style="width:40px;height:40px;background:#eff6ff;border-radius:10px;display:flex;align-items:center;justify-content:center">
                  <app-icon [name]="c.icon" [size]="20" color="#2563eb"></app-icon>
                </div>
              </div>
              <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em">
                {{c.label}}
              </div>
              <div style="font-size:28px;font-weight:700;color:#1f2937;margin-top:4px">
                {{c.value}}<span style="font-size:16px;color:#9ca3af">{{c.sub}}</span>
              </div>
            </div>
          }
        </div>

        <div style="display:grid;grid-template-columns:2fr 1fr;gap:16px">
          <div>
            <h3 style="font-size:18px;font-weight:600;margin-bottom:12px">Рекомендовано для вас</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              @for (c of stats?.recommended_courses || []; track c.title) {
                <div class="card">
                  <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
                    <span class="badge badge-blue">{{c.tags?.[0] || 'КУРС'}}</span>
                    <span style="font-size:12px;color:#9ca3af">{{c.duration}}</span>
                  </div>
                  <div style="font-weight:600;font-size:15px;color:#1f2937;margin-bottom:6px">{{c.title}}</div>
                  @if (c.description) {
                    <p style="font-size:13px;color:#6b7280;line-height:1.45;margin-bottom:12px">
                      {{c.description}}
                    </p>
                  }
                  <div style="height:6px;background:#f3f4f6;border-radius:9999px;overflow:hidden">
                    <div [style.width.%]="c.progress || 0"
                         style="height:100%;background:linear-gradient(90deg,#3b82f6,#2563eb);border-radius:9999px;transition:width 0.3s"></div>
                  </div>
                  <button class="btn-ghost"
                    style="margin-top:12px;width:100%;justify-content:center">
                    <app-icon name="play" [size]="13"></app-icon>
                    <span>{{c.progress > 0 ? 'Продолжить' : 'Начать модуль'}}</span>
                  </button>
                </div>
              }
            </div>
          </div>

          <div>
            <h3 style="font-size:18px;font-weight:600;margin-bottom:12px">Ближайшие задачи</h3>
            <div class="card" style="padding:0">
              @for (t of stats?.upcoming_tasks || []; track t.title) {
                <div style="padding:16px;display:flex;align-items:flex-start;gap:12px;border-bottom:1px solid #f9fafb">
                  <div style="width:40px;height:40px;background:#eff6ff;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
                    <app-icon [name]="iconForTask(t)" [size]="18" color="#2563eb"></app-icon>
                  </div>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:14px;font-weight:500;color:#1f2937">{{t.title}}</div>
                    <div style="font-size:12px;color:#9ca3af;margin-top:2px">
                      {{t.time}} <span style="margin:0 4px">·</span>
                      <span [style.color]="colorForPriority(t.priority)" style="font-weight:600">
                        {{t.type}}
                      </span>
                    </div>
                  </div>
                </div>
              }
              @if (!stats?.upcoming_tasks?.length) {
                <div style="padding:24px;text-align:center;color:#9ca3af;font-size:14px">
                  Нет задач на ближайшее время
                </div>
              }
            </div>

            @if (role === 'employee') {
              <a routerLink="/assignments" class="btn-ghost" style="margin-top:12px;width:100%;justify-content:center">
                <span>Все мои задания</span>
                <app-icon name="arrow-right" [size]="14"></app-icon>
              </a>
            }
          </div>
        </div>
      }

      <!-- Для HR/admin: быстрые ссылки -->
      @if (role === 'hr' || role === 'admin') {
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">
          <a routerLink="/hr-dashboard" class="card quick-link">
            <div class="quick-icon"><app-icon name="users" [size]="24" color="#2563eb"></app-icon></div>
            <div style="font-weight:700;font-size:18px;margin-top:12px">HR-панель</div>
            <div style="font-size:13px;color:#6b7280;margin-top:4px">
              Сотрудники, отделы, ключевые метрики.
            </div>
          </a>

          <a routerLink="/hr-assignments" class="card quick-link">
            <div class="quick-icon"><app-icon name="clipboard" [size]="24" color="#16a34a"></app-icon></div>
            <div style="font-weight:700;font-size:18px;margin-top:12px">Задания для команды</div>
            <div style="font-size:13px;color:#6b7280;margin-top:4px">
              Создать и контролировать задания сотрудников.
            </div>
          </a>

          <a routerLink="/analytics" class="card quick-link">
            <div class="quick-icon"><app-icon name="chart" [size]="24" color="#8b5cf6"></app-icon></div>
            <div style="font-weight:700;font-size:18px;margin-top:12px">Аналитика</div>
            <div style="font-size:13px;color:#6b7280;margin-top:4px">
              Тренды, графики, топ-исполнители.
            </div>
          </a>

          @if (role === 'admin') {
            <a routerLink="/admin" class="card quick-link">
              <div class="quick-icon"><app-icon name="shield" [size]="24" color="#ef4444"></app-icon></div>
              <div style="font-weight:700;font-size:18px;margin-top:12px">Администрирование</div>
              <div style="font-size:13px;color:#6b7280;margin-top:4px">
                Пользователи, роли, системные логи.
              </div>
            </a>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .quick-link { display:block; cursor:pointer; transition: all 0.2s; }
    .quick-link:hover { border-color:#93c5fd; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .quick-icon { width:44px;height:44px;background:#f3f4f6;border-radius:12px;display:flex;align-items:center;justify-content:center; }
  `],
})
export class DashboardComponent implements OnInit {
  stats: any = null;
  cards: any[] = [];
  firstName = '';
  role = '';

  constructor(private api: ApiService, private auth: AuthService) {}

  ngOnInit() {
    this.firstName = this.auth.user?.full_name?.split(' ')[0] || '';
    this.role = this.auth.user?.role || '';

    this.api.getDashboard().subscribe(data => {
      this.stats = data;
      this.cards = [
        { icon: 'target',   label: 'ОБЩИЙ РЕЙТИНГ',    value: data.overall_rating,    sub: '/100' },
        { icon: 'book',     label: 'ПРОЙДЕНО МОДУЛЕЙ', value: data.completed_modules, sub: '' },
        { icon: 'fire',     label: 'СЕРИЯ ОБУЧЕНИЯ',   value: data.streak_days,       sub: ' дн.' },
        { icon: 'clock',    label: 'ЧАСЫ ПРАКТИКИ',    value: data.practice_hours,    sub: ' ч.' },
      ];
    });
  }

  iconForTask(t: any): string {
    if (t?.priority === 'high')   return 'flag';
    if (t?.type === 'ПРАКТИКА')   return 'play';
    if (t?.type === 'ТЕСТИРОВАНИЕ') return 'clipboard';
    if (t?.type === 'ВСТРЕЧА')    return 'users';
    return 'clipboard';
  }

  colorForPriority(p?: string): string {
    if (p === 'high')   return '#ef4444';
    if (p === 'low')    return '#9ca3af';
    return '#2563eb';
  }
}
