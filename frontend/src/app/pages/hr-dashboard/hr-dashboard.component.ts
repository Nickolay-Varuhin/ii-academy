import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-hr-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="margin-bottom:24px">
        <h2 style="font-size:24px;font-weight:700">HR-панель</h2>
        <p style="font-size:14px;color:#6b7280;margin-top:4px">
          Обзор по сотрудникам, отделам и развитию навыков.
        </p>
      </div>

      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
        <div class="card">
          <div class="stat-icon" style="background:#eff6ff">
            <app-icon name="users" [size]="20" color="#2563eb"></app-icon>
          </div>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-top:8px">
            Активных сотрудников
          </div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{summary?.active_users || 0}}
          </div>
          <div style="font-size:12px;margin-top:4px"
               [style.color]="(summary?.active_users_change_pct || 0) >= 0 ? '#16a34a' : '#ef4444'">
            {{summary?.active_users_change_pct >= 0 ? '+' : ''}}{{summary?.active_users_change_pct || 0}}% за 30 дней
          </div>
        </div>

        <div class="card">
          <div class="stat-icon" style="background:#f0fdf4">
            <app-icon name="check" [size]="20" color="#16a34a"></app-icon>
          </div>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-top:8px">
            Завершаемость диалогов
          </div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{summary?.course_completion_pct || 0}}%
          </div>
        </div>

        <div class="card">
          <div class="stat-icon" style="background:#fef2f2">
            <app-icon name="fire" [size]="20" color="#ef4444"></app-icon>
          </div>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-top:8px">
            Вовлечённость
          </div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{summary?.engagement_hours_per_week || 0}}
            <span style="font-size:14px;color:#9ca3af">ч/нед</span>
          </div>
        </div>

        <div class="card">
          <div class="stat-icon" style="background:#fefce8">
            <app-icon name="warning" [size]="20" color="#ca8a04"></app-icon>
          </div>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-top:8px">
            Критические пробелы
          </div>
          <div style="font-size:28px;font-weight:700;margin-top:4px">
            {{summary?.critical_gaps || 0}}
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px">
        <h3 style="font-weight:600;margin-bottom:16px">Срез по отделам</h3>
        <table style="width:100%;font-size:14px;border-collapse:collapse">
          <thead>
            <tr style="text-align:left;color:#9ca3af;border-bottom:1px solid #f3f4f6">
              <th style="padding:10px 8px;font-weight:500">Отдел</th>
              <th style="padding:10px 8px;font-weight:500">Сотрудников</th>
              <th style="padding:10px 8px;font-weight:500">Завершение</th>
              <th style="padding:10px 8px;font-weight:500">Вовлечённость</th>
              <th style="padding:10px 8px;font-weight:500">Ср. балл</th>
            </tr>
          </thead>
          <tbody>
            @for (d of depts; track d.department) {
              <tr style="border-bottom:1px solid #fafafa">
                <td style="padding:10px 8px;font-weight:600">{{d.department}}</td>
                <td style="padding:10px 8px">{{d.employee_count}}</td>
                <td style="padding:10px 8px">
                  <div style="display:flex;align-items:center;gap:8px">
                    <div style="flex:1;max-width:120px;height:6px;background:#f3f4f6;border-radius:9999px">
                      <div [style.width.%]="d.completion_rate"
                           style="height:100%;background:#2563eb;border-radius:9999px"></div>
                    </div>
                    <span>{{d.completion_rate}}%</span>
                  </div>
                </td>
                <td style="padding:10px 8px">
                  <span [style.color]="d.engagement_score >= 4 ? '#16a34a' : '#6b7280'"
                        style="display:inline-flex;align-items:center;gap:4px">
                    <app-icon name="star" [size]="12" [color]="d.engagement_score >= 4 ? '#16a34a' : '#6b7280'"></app-icon>
                    <span>{{d.engagement_score}}/5</span>
                  </span>
                </td>
                <td style="padding:10px 8px">
                  <span [style.color]="d.avg_dialog_score >= 80 ? '#16a34a' :
                                          (d.avg_dialog_score >= 60 ? '#2563eb' : '#ef4444')"
                        style="font-weight:600">
                    {{d.avg_dialog_score || '—'}}
                  </span>
                </td>
              </tr>
            }
            @if (!depts.length) {
              <tr><td colspan="5" style="padding:24px;text-align:center;color:#9ca3af">
                Данные по отделам ещё не собраны.
              </td></tr>
            }
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3 style="font-weight:600;margin-bottom:16px">Лучшие результаты</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">
          @for (p of topPerformers; track p.name) {
            <div style="padding:12px;background:#f9fafb;border-radius:8px;display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-weight:600">{{p.name}}</div>
                <div style="font-size:12px;color:#6b7280">{{p.department}}</div>
              </div>
              <div style="text-align:right">
                <div style="font-weight:700;font-size:18px"
                     [style.color]="p.score >= 85 ? '#16a34a' : '#2563eb'">
                  {{p.score}}
                </div>
                <div style="font-size:11px;color:#9ca3af">{{p.skill}}</div>
              </div>
            </div>
          }
        </div>

        <a routerLink="/analytics" class="btn-primary"
           style="display:inline-flex;margin-top:16px">
          <span>Подробная аналитика</span>
          <app-icon name="arrow-right" [size]="16" color="#fff"></app-icon>
        </a>
      </div>
    </div>
  `,
  styles: [`
    .stat-icon {
      width: 40px; height: 40px; border-radius: 10px;
      display: inline-flex; align-items: center; justify-content: center;
    }
  `],
})
export class HrDashboardComponent implements OnInit {
  summary: any = null;
  depts: any[] = [];
  topPerformers: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getHrSummary().subscribe(s => this.summary = s);
    this.api.getDepartments().subscribe(d => this.depts = d || []);
    this.api.getTopPerformers().subscribe(t => this.topPerformers = t || []);
  }
}
