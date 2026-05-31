import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-hr-assignments',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
        <div>
          <h2 style="font-size:24px;font-weight:700">Задания для команды</h2>
          <p style="font-size:14px;color:#6b7280;margin-top:4px">
            Создавайте задания сотрудникам и отслеживайте их выполнение.
          </p>
        </div>
        <button class="btn-primary" (click)="openForm()">
          <app-icon name="plus" [size]="16" color="#fff"></app-icon>
          <span>Новое задание</span>
        </button>
      </div>

      <!-- Сводка -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px">
        <div class="stat-card">
          <div class="stat-icon" style="background:#eff6ff">
            <app-icon name="clipboard" [size]="18" color="#2563eb"></app-icon>
          </div>
          <div>
            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Всего заданий</div>
            <div style="font-size:22px;font-weight:700">{{assignments.length}}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:#fefce8">
            <app-icon name="clock" [size]="18" color="#ca8a04"></app-icon>
          </div>
          <div>
            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">В работе</div>
            <div style="font-size:22px;font-weight:700">{{countBy('in_progress')}}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:#f0fdf4">
            <app-icon name="check" [size]="18" color="#16a34a"></app-icon>
          </div>
          <div>
            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Выполнено</div>
            <div style="font-size:22px;font-weight:700">{{countBy('completed')}}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:#fef2f2">
            <app-icon name="warning" [size]="18" color="#ef4444"></app-icon>
          </div>
          <div>
            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase">Просрочено</div>
            <div style="font-size:22px;font-weight:700">{{overdueCount()}}</div>
          </div>
        </div>
      </div>

      <!-- Список -->
      @if (!assignments.length) {
        <div class="card" style="text-align:center;padding:48px;color:#9ca3af">
          Заданий ещё нет. Создайте первое, нажав кнопку вверху.
        </div>
      } @else {
        <div class="card" style="padding:0">
          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <thead>
              <tr style="text-align:left;color:#9ca3af;border-bottom:1px solid #f3f4f6">
                <th style="padding:14px 20px;font-weight:500">Задание</th>
                <th style="padding:14px 20px;font-weight:500">Сотрудник</th>
                <th style="padding:14px 20px;font-weight:500">Срок</th>
                <th style="padding:14px 20px;font-weight:500">Статус</th>
                <th style="padding:14px 20px;font-weight:500"></th>
              </tr>
            </thead>
            <tbody>
              @for (a of assignments; track a.id) {
                <tr style="border-bottom:1px solid #fafafa">
                  <td style="padding:14px 20px">
                    <div style="display:flex;align-items:center;gap:8px">
                      @if (a.priority === 'high') {
                        <app-icon name="flag" [size]="14" color="#ef4444"></app-icon>
                      }
                      <div>
                        <div style="font-weight:500">{{a.title}}</div>
                        @if (a.scenario_title || a.course_title) {
                          <div style="font-size:12px;color:#9ca3af;margin-top:2px">
                            {{a.scenario_title || a.course_title}}
                          </div>
                        }
                      </div>
                    </div>
                  </td>
                  <td style="padding:14px 20px;color:#4b5563">{{a.assignee_name}}</td>
                  <td style="padding:14px 20px;color:#6b7280;font-size:13px">
                    {{formatDate(a.due_date)}}
                  </td>
                  <td style="padding:14px 20px">
                    <span [class]="'badge ' + badgeForStatus(a.status)">{{statusLabel(a.status)}}</span>
                  </td>
                  <td style="padding:14px 20px">
                    <button class="icon-btn" (click)="removeAssignment(a)" title="Удалить">
                      <app-icon name="trash" [size]="16" color="#ef4444"></app-icon>
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }

      <!-- Модалка создания -->
      @if (showForm) {
        <div class="modal-overlay" (click)="closeForm()">
          <div class="modal" (click)="$event.stopPropagation()">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
              <h3 style="font-size:18px;font-weight:700">Новое задание</h3>
              <button class="icon-btn" (click)="closeForm()">
                <app-icon name="close" [size]="18" color="#9ca3af"></app-icon>
              </button>
            </div>

            @if (formError) {
              <div style="background:#fef2f2;color:#dc2626;padding:10px;border-radius:6px;font-size:13px;margin-bottom:12px">
                {{formError}}
              </div>
            }

            <label class="form-label">Сотрудник <span style="color:#ef4444">*</span></label>
            <select [(ngModel)]="form.assigned_to" style="width:100%;margin-bottom:12px">
              <option [ngValue]="null">— Выберите сотрудника —</option>
              @for (e of employees; track e.id) {
                <option [ngValue]="e.id">
                  {{e.full_name}} @if (e.department) { ({{e.department}}) }
                </option>
              }
            </select>

            <label class="form-label">Название задания <span style="color:#ef4444">*</span></label>
            <input [(ngModel)]="form.title" placeholder="Например: Пройти сценарий «Сложные переговоры»"
                   style="width:100%;margin-bottom:12px">

            <label class="form-label">Описание</label>
            <textarea [(ngModel)]="form.description"
                      placeholder="Подробности: что нужно сделать, на что обратить внимание"
                      style="width:100%;margin-bottom:12px"></textarea>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div>
                <label class="form-label">Срок выполнения</label>
                <input type="datetime-local" [(ngModel)]="form.due_date" style="width:100%">
              </div>
              <div>
                <label class="form-label">Приоритет</label>
                <select [(ngModel)]="form.priority" style="width:100%">
                  <option value="low">Низкий</option>
                  <option value="normal">Обычный</option>
                  <option value="high">Высокий / срочно</option>
                </select>
              </div>
            </div>

            <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end">
              <button class="btn-ghost" (click)="closeForm()">Отмена</button>
              <button class="btn-primary" (click)="submit()" [disabled]="saving">
                <app-icon name="check" [size]="14" color="#fff"></app-icon>
                <span>{{saving ? 'Сохранение...' : 'Выдать задание'}}</span>
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .stat-card {
      background: #fff; border: 1px solid #f3f4f6; border-radius: 12px;
      padding: 16px; display: flex; align-items: center; gap: 12px;
    }
    .stat-icon {
      width: 40px; height: 40px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
    }
    .form-label {
      display: block; font-size: 13px; font-weight: 500; color: #374151;
      margin-bottom: 6px;
    }
    .modal-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex; align-items: center; justify-content: center;
      z-index: 100;
    }
    .modal {
      background: #fff; border-radius: 12px; padding: 24px;
      width: 520px; max-width: 90vw; max-height: 90vh; overflow-y: auto;
    }
    .icon-btn {
      background: none; border: none; cursor: pointer; padding: 4px;
      display: inline-flex; align-items: center; border-radius: 4px;
    }
    .icon-btn:hover { background: #f3f4f6; }
  `],
})
export class HrAssignmentsComponent implements OnInit {
  assignments: any[] = [];
  employees: any[] = [];

  showForm = false;
  saving = false;
  formError = '';
  form: any = this.freshForm();

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.load();
    this.api.getAssignableEmployees().subscribe(data => {
      this.employees = data || [];
    });
  }

  load() {
    this.api.getAssignments().subscribe(data => {
      this.assignments = data || [];
    });
  }

  freshForm() {
    return {
      assigned_to: null,
      title: '',
      description: '',
      due_date: '',
      priority: 'normal',
    };
  }

  openForm() {
    this.form = this.freshForm();
    this.formError = '';
    this.showForm = true;
  }

  closeForm() { this.showForm = false; }

  submit() {
    this.formError = '';
    if (!this.form.assigned_to) {
      this.formError = 'Выберите сотрудника';
      return;
    }
    if (!this.form.title || this.form.title.length < 3) {
      this.formError = 'Название должно быть не короче 3 символов';
      return;
    }

    this.saving = true;
    const payload: any = {
      assigned_to: this.form.assigned_to,
      title: this.form.title,
      description: this.form.description || null,
      priority: this.form.priority,
    };
    if (this.form.due_date) {
      // datetime-local → ISO
      payload.due_date = new Date(this.form.due_date).toISOString();
    }

    this.api.createAssignment(payload).subscribe({
      next: () => {
        this.saving = false;
        this.showForm = false;
        this.load();
      },
      error: (err) => {
        this.saving = false;
        this.formError = err?.error?.detail || 'Не удалось создать задание';
      },
    });
  }

  removeAssignment(a: any) {
    if (!confirm(`Удалить задание «${a.title}»?`)) return;
    this.api.deleteAssignment(a.id).subscribe(() => this.load());
  }

  countBy(status: string): number {
    return this.assignments.filter(a => a.status === status).length;
  }

  overdueCount(): number {
    const now = new Date();
    return this.assignments.filter(a =>
      a.due_date && a.status !== 'completed' && new Date(a.due_date) < now
    ).length;
  }

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

  formatDate(d?: string): string {
    if (!d) return '—';
    const date = new Date(d);
    return date.toLocaleDateString('ru') + ', ' +
           date.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
  }
}
