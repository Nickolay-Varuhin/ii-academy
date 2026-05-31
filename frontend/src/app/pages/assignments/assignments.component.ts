import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-assignments',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="margin-bottom:24px">
        <h2 style="font-size:24px;font-weight:700">Мои задания</h2>
        <p style="font-size:14px;color:#6b7280;margin-top:4px">
          Задания от HR-отдела. Выполненные отмечайте вручную — они попадут в вашу статистику.
        </p>
      </div>

      <!-- Фильтры по статусу -->
      <div style="display:flex;gap:8px;margin-bottom:16px">
        @for (f of filters; track f.key) {
          <button (click)="activeFilter = f.key"
                  [style.background]="activeFilter === f.key ? '#2563eb' : '#fff'"
                  [style.color]="activeFilter === f.key ? '#fff' : '#6b7280'"
                  [style.border]="activeFilter === f.key ? 'none' : '1px solid #e5e7eb'"
                  style="padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;display:inline-flex;align-items:center;gap:6px">
            <span>{{f.label}}</span>
            <span style="opacity:0.7">{{countFor(f.key)}}</span>
          </button>
        }
      </div>

      @if (!filteredAssignments.length) {
        <div class="card" style="text-align:center;padding:48px;color:#9ca3af">
          @if (activeFilter === 'all') {
            <app-icon name="clipboard" [size]="36" color="#d1d5db"></app-icon>
            <div style="margin-top:12px">Заданий пока нет. HR их ещё не назначил.</div>
          } @else {
            Нет заданий в этой категории
          }
        </div>
      } @else {
        <div style="display:flex;flex-direction:column;gap:12px">
          @for (a of filteredAssignments; track a.id) {
            <div class="card" [style.border-left]="borderColorForPriority(a.priority)">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px">
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                    <span [class]="'badge ' + badgeForStatus(a.status)">
                      {{statusLabel(a.status)}}
                    </span>
                    <span [class]="'badge ' + badgeForPriority(a.priority)">
                      <app-icon name="flag" [size]="11" [color]="colorForPriority(a.priority)"></app-icon>
                      <span>{{priorityLabel(a.priority)}}</span>
                    </span>
                  </div>

                  <h3 style="font-size:17px;font-weight:600;margin-bottom:6px">{{a.title}}</h3>
                  @if (a.description) {
                    <p style="font-size:14px;color:#6b7280;line-height:1.5;margin-bottom:10px">
                      {{a.description}}
                    </p>
                  }

                  <div style="display:flex;gap:16px;font-size:13px;color:#9ca3af;flex-wrap:wrap">
                    <div style="display:inline-flex;align-items:center;gap:4px">
                      <app-icon name="user" [size]="13" color="#9ca3af"></app-icon>
                      <span>От: {{a.assigner_name}}</span>
                    </div>
                    @if (a.due_date) {
                      <div style="display:inline-flex;align-items:center;gap:4px"
                           [style.color]="isOverdue(a.due_date) && a.status !== 'completed' ? '#ef4444' : '#9ca3af'">
                        <app-icon name="calendar" [size]="13"
                                  [color]="isOverdue(a.due_date) && a.status !== 'completed' ? '#ef4444' : '#9ca3af'"></app-icon>
                        <span>Срок: {{formatDate(a.due_date)}}</span>
                      </div>
                    }
                    @if (a.scenario_title) {
                      <div style="display:inline-flex;align-items:center;gap:4px">
                        <app-icon name="chat" [size]="13" color="#9ca3af"></app-icon>
                        <span>Сценарий: {{a.scenario_title}}</span>
                      </div>
                    }
                    @if (a.course_title) {
                      <div style="display:inline-flex;align-items:center;gap:4px">
                        <app-icon name="book" [size]="13" color="#9ca3af"></app-icon>
                        <span>Курс: {{a.course_title}}</span>
                      </div>
                    }
                  </div>

                  @if (a.completion_note) {
                    <div style="margin-top:10px;padding:10px;background:#f9fafb;border-radius:6px;font-size:13px;color:#4b5563">
                      <strong>Ваша заметка:</strong> {{a.completion_note}}
                    </div>
                  }
                </div>

                <!-- Действия -->
                <div style="display:flex;flex-direction:column;gap:6px;flex-shrink:0">
                  @if (a.status === 'assigned') {
                    <button class="btn-primary" style="padding:8px 14px;font-size:13px"
                            (click)="setStatus(a, 'in_progress')">
                      <app-icon name="play" [size]="13" color="#fff"></app-icon>
                      <span>Начать</span>
                    </button>
                  }
                  @if (a.status === 'in_progress') {
                    <button class="btn-primary" style="padding:8px 14px;font-size:13px;background:#16a34a"
                            (click)="openCompleteDialog(a)">
                      <app-icon name="check" [size]="13" color="#fff"></app-icon>
                      <span>Завершить</span>
                    </button>
                  }
                  @if (a.status === 'completed') {
                    <div style="color:#16a34a;font-size:13px;display:flex;align-items:center;gap:4px;font-weight:600">
                      <app-icon name="check" [size]="14" color="#16a34a"></app-icon>
                      <span>Выполнено</span>
                    </div>
                  }
                  @if (a.scenario_id && a.status !== 'completed') {
                    <button class="btn-ghost" style="padding:6px 12px;font-size:12px"
                            (click)="goToSimulator()">
                      <span>К сценарию</span>
                    </button>
                  }
                </div>
              </div>
            </div>
          }
        </div>
      }

      <!-- Модалка "Завершить задание" -->
      @if (completing) {
        <div class="modal-overlay" (click)="completing = null">
          <div class="modal" (click)="$event.stopPropagation()">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
              <h3 style="font-size:18px;font-weight:700">Отметить выполненным</h3>
              <button class="icon-btn" (click)="completing = null">
                <app-icon name="close" [size]="18" color="#9ca3af"></app-icon>
              </button>
            </div>
            <div style="font-size:14px;color:#6b7280;margin-bottom:12px">{{completing.title}}</div>
            <label style="display:block;font-size:13px;font-weight:500;margin-bottom:6px">
              Заметка (опционально)
            </label>
            <textarea [(ngModel)]="completionNote"
                      placeholder="Что получилось, какой был результат..."
                      style="width:100%;min-height:80px"></textarea>
            <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end">
              <button class="btn-ghost" (click)="completing = null">Отмена</button>
              <button class="btn-primary" style="background:#16a34a" (click)="confirmComplete()">
                <app-icon name="check" [size]="14" color="#fff"></app-icon>
                <span>Подтвердить</span>
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .modal-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex; align-items: center; justify-content: center;
      z-index: 100;
    }
    .modal {
      background: #fff; border-radius: 12px; padding: 20px;
      width: 460px; max-width: 90vw;
    }
    .icon-btn {
      background: none; border: none; cursor: pointer; padding: 4px;
      display: inline-flex; align-items: center; border-radius: 4px;
    }
    .icon-btn:hover { background: #f3f4f6; }
  `],
})
export class AssignmentsComponent implements OnInit {
  assignments: any[] = [];
  activeFilter: 'all' | 'assigned' | 'in_progress' | 'completed' = 'all';
  filters = [
    { key: 'all' as const,         label: 'Все' },
    { key: 'assigned' as const,    label: 'Новые' },
    { key: 'in_progress' as const, label: 'В работе' },
    { key: 'completed' as const,   label: 'Завершённые' },
  ];

  completing: any | null = null;
  completionNote = '';

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() { this.load(); }

  load() {
    this.api.getAssignments().subscribe(data => {
      this.assignments = data || [];
    });
  }

  get filteredAssignments() {
    if (this.activeFilter === 'all') return this.assignments;
    return this.assignments.filter(a => a.status === this.activeFilter);
  }

  countFor(key: string): number {
    if (key === 'all') return this.assignments.length;
    return this.assignments.filter(a => a.status === key).length;
  }

  setStatus(a: any, status: string) {
    this.api.updateAssignment(a.id, { status }).subscribe(updated => {
      const i = this.assignments.findIndex(x => x.id === a.id);
      if (i >= 0) this.assignments[i] = updated;
    });
  }

  openCompleteDialog(a: any) {
    this.completing = a;
    this.completionNote = '';
  }

  confirmComplete() {
    if (!this.completing) return;
    this.api.updateAssignment(this.completing.id, {
      status: 'completed',
      completion_note: this.completionNote || null,
    }).subscribe(updated => {
      const i = this.assignments.findIndex(x => x.id === this.completing.id);
      if (i >= 0) this.assignments[i] = updated;
      this.completing = null;
      this.completionNote = '';
    });
  }

  goToSimulator() { this.router.navigate(['/simulator']); }

  statusLabel(s: string): string {
    return ({
      assigned: 'Назначено',
      in_progress: 'В работе',
      completed: 'Выполнено',
      overdue: 'Просрочено',
    } as any)[s] || s;
  }

  badgeForStatus(s: string): string {
    return ({
      assigned: 'badge-blue',
      in_progress: 'badge-yellow',
      completed: 'badge-green',
      overdue: 'badge-red',
    } as any)[s] || 'badge-gray';
  }

  priorityLabel(p: string): string {
    return ({ high: 'Срочно', normal: 'Обычный', low: 'Низкий' } as any)[p] || p;
  }

  badgeForPriority(p: string): string {
    return ({ high: 'badge-red', normal: 'badge-gray', low: 'badge-gray' } as any)[p] || 'badge-gray';
  }

  colorForPriority(p: string): string {
    return ({ high: '#ef4444', normal: '#6b7280', low: '#9ca3af' } as any)[p] || '#6b7280';
  }

  borderColorForPriority(p: string): string {
    const map: any = { high: '4px solid #ef4444', normal: '4px solid #e5e7eb', low: '4px solid #f3f4f6' };
    return map[p] || '4px solid #e5e7eb';
  }

  formatDate(d: string): string {
    const date = new Date(d);
    const now = new Date();
    const delta = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    const hm = date.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
    if (delta === 0) return `Сегодня, ${hm}`;
    if (delta === 1) return `Завтра, ${hm}`;
    if (delta < 0) return `Просрочено (${date.toLocaleDateString('ru')})`;
    return date.toLocaleDateString('ru') + ', ' + hm;
  }

  isOverdue(d: string): boolean {
    return new Date(d) < new Date();
  }
}
