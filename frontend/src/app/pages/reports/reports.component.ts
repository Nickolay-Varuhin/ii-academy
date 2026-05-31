import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { IconComponent } from '../../components/icon/icon.component';

interface Employee {
  id: number;
  full_name: string;
  department: string | null;
}

type ReportFormat = 'pdf' | 'docx';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div style="padding: 28px; max-width: 1000px; margin: 0 auto">

      <!-- ── Page header ───────────────────────────────────────────── -->
      <div style="margin-bottom: 28px">
        <h1 style="font-size: 22px; font-weight: 700; color: #1f2937; margin-bottom: 4px">
          Отчёты о достижениях
        </h1>
        <p style="font-size: 14px; color: #6b7280">
          Выберите сотрудника, формат и скачайте персональный отчёт о прохождении курса
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start">

        <!-- ── Left: employee picker ─────────────────────────────── -->
        <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden">

          <!-- Search bar -->
          <div style="padding: 16px; border-bottom: 1px solid #f3f4f6">
            <div style="position: relative">
              <app-icon name="search" [size]="16" color="#9ca3af"
                style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); pointer-events: none"></app-icon>
              <input
                [(ngModel)]="searchQuery"
                (ngModelChange)="onSearch()"
                placeholder="Поиск по имени, email или отделу..."
                style="width: 100%; padding: 10px 12px 10px 36px; border: 1px solid #e5e7eb;
                       border-radius: 8px; font-size: 14px; color: #1f2937; outline: none;
                       background: #f9fafb; box-sizing: border-box"
              />
            </div>
          </div>

          <!-- Employee list -->
          <div style="max-height: 480px; overflow-y: auto">

            @if (loading()) {
              <div style="padding: 40px; text-align: center; color: #9ca3af">
                <div style="font-size: 24px; margin-bottom: 8px">⏳</div>
                Загрузка сотрудников...
              </div>
            } @else if (filteredEmployees().length === 0) {
              <div style="padding: 40px; text-align: center; color: #9ca3af">
                <div style="font-size: 32px; margin-bottom: 8px">🔍</div>
                Сотрудники не найдены
              </div>
            } @else {
              @for (emp of filteredEmployees(); track emp.id) {
                <div
                  (click)="selectEmployee(emp)"
                  [style.background]="selectedEmployee()?.id === emp.id ? '#eff6ff' : 'transparent'"
                  [style.border-left]="selectedEmployee()?.id === emp.id
                    ? '3px solid #2563eb' : '3px solid transparent'"
                  style="display: flex; align-items: center; gap: 12px; padding: 12px 16px;
                         cursor: pointer; transition: all 0.15s; border-bottom: 1px solid #f9fafb"
                  onmouseenter="if(!this.classList.contains('selected'))this.style.background='#f9fafb'"
                  onmouseleave="if(this.style.borderLeft!=='3px solid rgb(37, 99, 235)')this.style.background='transparent'"
                >
                  <!-- Avatar -->
                  <div [style.background]="selectedEmployee()?.id === emp.id ? '#2563eb' : '#e5e7eb'"
                       style="width: 40px; height: 40px; border-radius: 50%; display: flex;
                              align-items: center; justify-content: center; flex-shrink: 0;
                              font-size: 15px; font-weight: 700; transition: background 0.15s"
                       [style.color]="selectedEmployee()?.id === emp.id ? '#fff' : '#6b7280'">
                    {{ emp.full_name.charAt(0) }}
                  </div>

                  <!-- Info -->
                  <div style="flex: 1; min-width: 0">
                    <div style="font-size: 14px; font-weight: 600; color: #1f2937;
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                      {{ emp.full_name }}
                    </div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 2px">
                      {{ emp.department || 'Отдел не указан' }}
                    </div>
                  </div>

                  <!-- Check icon -->
                  @if (selectedEmployee()?.id === emp.id) {
                    <app-icon name="check" [size]="18" color="#2563eb"></app-icon>
                  }
                </div>
              }
            }
          </div>

          <!-- Footer: count -->
          <div style="padding: 10px 16px; border-top: 1px solid #f3f4f6;
                      font-size: 12px; color: #9ca3af; background: #f9fafb">
            Показано: {{ filteredEmployees().length }} из {{ employees().length }} сотрудников
          </div>
        </div>

        <!-- ── Right: report settings & download ──────────────────── -->
        <div style="display: flex; flex-direction: column; gap: 16px">

          <!-- Selected employee card -->
          @if (selectedEmployee()) {
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 16px">
              <div style="font-size: 11px; font-weight: 600; color: #2563eb;
                          text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px">
                Выбран сотрудник
              </div>
              <div style="display: flex; align-items: center; gap: 12px">
                <div style="width: 44px; height: 44px; border-radius: 50%; background: #2563eb;
                            color: #fff; display: flex; align-items: center; justify-content: center;
                            font-size: 17px; font-weight: 700; flex-shrink: 0">
                  {{ selectedEmployee()!.full_name.charAt(0) }}
                </div>
                <div>
                  <div style="font-size: 15px; font-weight: 700; color: #1e40af">
                    {{ selectedEmployee()!.full_name }}
                  </div>
                  <div style="font-size: 12px; color: #3b82f6; margin-top: 2px">
                    {{ selectedEmployee()!.department || 'Отдел не указан' }}
                  </div>
                </div>
              </div>
            </div>
          } @else {
            <div style="background: #f9fafb; border: 1px dashed #d1d5db; border-radius: 12px;
                        padding: 20px; text-align: center; color: #9ca3af">
              <div style="font-size: 28px; margin-bottom: 6px">👤</div>
              <div style="font-size: 13px">Выберите сотрудника из списка слева</div>
            </div>
          }

          <!-- Format selector -->
          <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px">
            <div style="font-size: 12px; font-weight: 600; color: #374151;
                        text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px">
              Формат отчёта
            </div>

            <div style="display: flex; flex-direction: column; gap: 8px">
              <!-- PDF -->
              <label style="display: flex; align-items: center; gap: 12px; padding: 12px;
                            border: 2px solid; border-radius: 8px; cursor: pointer; transition: all 0.15s"
                     [style.border-color]="selectedFormat() === 'pdf' ? '#2563eb' : '#e5e7eb'"
                     [style.background]="selectedFormat() === 'pdf' ? '#eff6ff' : '#fafafa'">
                <input type="radio" name="format" value="pdf"
                       [checked]="selectedFormat() === 'pdf'"
                       (change)="selectedFormat.set('pdf')"
                       style="accent-color: #2563eb" />
                <div style="font-size: 22px">📄</div>
                <div>
                  <div style="font-size: 13px; font-weight: 600; color: #1f2937">PDF</div>
                  <div style="font-size: 11px; color: #9ca3af">Удобен для просмотра и печати</div>
                </div>
              </label>

              <!-- DOCX -->
              <label style="display: flex; align-items: center; gap: 12px; padding: 12px;
                            border: 2px solid; border-radius: 8px; cursor: pointer; transition: all 0.15s"
                     [style.border-color]="selectedFormat() === 'docx' ? '#2563eb' : '#e5e7eb'"
                     [style.background]="selectedFormat() === 'docx' ? '#eff6ff' : '#fafafa'">
                <input type="radio" name="format" value="docx"
                       [checked]="selectedFormat() === 'docx'"
                       (change)="selectedFormat.set('docx')"
                       style="accent-color: #2563eb" />
                <div style="font-size: 22px">📝</div>
                <div>
                  <div style="font-size: 13px; font-weight: 600; color: #1f2937">Word (DOCX)</div>
                  <div style="font-size: 11px; color: #9ca3af">Редактируемый документ</div>
                </div>
              </label>
            </div>
          </div>

          <!-- Download button -->
          <button
            (click)="downloadReport()"
            [disabled]="!selectedEmployee() || downloading()"
            style="width: 100%; padding: 14px; border-radius: 10px; border: none; cursor: pointer;
                   font-size: 15px; font-weight: 600; display: flex; align-items: center;
                   justify-content: center; gap: 10px; transition: all 0.2s"
            [style.background]="!selectedEmployee() ? '#e5e7eb' : '#2563eb'"
            [style.color]="!selectedEmployee() ? '#9ca3af' : '#fff'"
            [style.cursor]="!selectedEmployee() ? 'not-allowed' : 'pointer'"
          >
            @if (downloading()) {
              <span style="display: inline-block; width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3);
                           border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite"></span>
              Генерируем отчёт...
            } @else {
              <app-icon name="download" [size]="18" [color]="!selectedEmployee() ? '#9ca3af' : '#fff'"></app-icon>
              Скачать отчёт
            }
          </button>

          <!-- Success/error messages -->
          @if (successMsg()) {
            <div style="padding: 12px 14px; background: #f0fdf4; border: 1px solid #bbf7d0;
                        border-radius: 8px; font-size: 13px; color: #15803d; display: flex;
                        align-items: center; gap: 8px">
              ✅ {{ successMsg() }}
            </div>
          }
          @if (errorMsg()) {
            <div style="padding: 12px 14px; background: #fef2f2; border: 1px solid #fecaca;
                        border-radius: 8px; font-size: 13px; color: #dc2626; display: flex;
                        align-items: center; gap: 8px">
              ❌ {{ errorMsg() }}
            </div>
          }

          <!-- Info block -->
          <div style="padding: 14px; background: #fffbeb; border: 1px solid #fde68a;
                      border-radius: 10px; font-size: 12px; color: #92400e; line-height: 1.6">
            <b>Что включает отчёт:</b><br>
            • Профиль и роль сотрудника<br>
            • Статус всех заданий (выполнено / в процессе / просрочено)<br>
            • Статистика AI-сессий и средний балл<br>
            • Уровень освоения навыков
          </div>
        </div>
      </div>
    </div>

    <style>
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      input[type=radio] { width: 16px; height: 16px; flex-shrink: 0; }
    </style>
  `,
})
export class ReportsComponent implements OnInit {
  employees    = signal<Employee[]>([]);
  loading      = signal(true);
  downloading  = signal(false);
  searchQuery  = '';
  successMsg   = signal('');
  errorMsg     = signal('');

  selectedEmployee = signal<Employee | null>(null);
  selectedFormat   = signal<ReportFormat>('pdf');

  filteredEmployees = computed(() => {
    const q = this.searchQuery.toLowerCase().trim();
    if (!q) return this.employees();
    return this.employees().filter(e =>
      e.full_name.toLowerCase().includes(q) ||
      (e.department ?? '').toLowerCase().includes(q)
    );
  });

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<Employee[]>('/api/reports/employees').subscribe({
      next: list => { this.employees.set(list); this.loading.set(false); },
      error: ()  => { this.loading.set(false); this.errorMsg.set('Не удалось загрузить список сотрудников'); },
    });
  }

  onSearch() {
    // filteredEmployees is computed — nothing extra needed
  }

  selectEmployee(emp: Employee) {
    this.selectedEmployee.set(emp);
    this.successMsg.set('');
    this.errorMsg.set('');
  }

  downloadReport() {
    const emp = this.selectedEmployee();
    if (!emp || this.downloading()) return;

    this.downloading.set(true);
    this.successMsg.set('');
    this.errorMsg.set('');

    const fmt = this.selectedFormat();
    const url = `/api/reports/download/${emp.id}?format=${fmt}`;

    this.http.get(url, { responseType: 'blob', observe: 'response' }).subscribe({
      next: resp => {
        this.downloading.set(false);
        const blob = resp.body!;

        // Extract filename from Content-Disposition header
        const cd = resp.headers.get('Content-Disposition') ?? '';
        const match = cd.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : `report_${emp.full_name}.${fmt}`;

        // Trigger download
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);

        this.successMsg.set(`Отчёт для ${emp.full_name} успешно скачан`);
        setTimeout(() => this.successMsg.set(''), 5000);
      },
      error: err => {
        this.downloading.set(false);
        this.errorMsg.set(
          err.status === 403 ? 'Недостаточно прав для генерации отчёта' :
          err.status === 404 ? 'Сотрудник не найден' :
          'Ошибка при генерации отчёта. Попробуйте позже.'
        );
      },
    });
  }
}
