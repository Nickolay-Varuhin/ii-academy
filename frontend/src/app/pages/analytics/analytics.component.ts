import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, CategoryScale, LinearScale, BarController, BarElement,
          LineController, LineElement, PointElement, Tooltip, Legend } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

Chart.register(CategoryScale, LinearScale, BarController, BarElement,
               LineController, LineElement, PointElement, Tooltip, Legend);

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
        <div>
          <h2 style="font-size:24px;font-weight:700">Аналитика по компании</h2>
          <p style="font-size:14px;color:#6b7280;margin-top:4px">
            Мониторинг внедрения платформы и развития навыков по отделам.
          </p>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
        @for (c of summaryCards; track c.label) {
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div [style.background]="c.bg"
                   style="width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center">
                <app-icon [name]="c.icon" [size]="20" [color]="c.iconColor"></app-icon>
              </div>
              <span [style.color]="c.up ? '#16a34a' : (c.down ? '#ef4444' : '#9ca3af')"
                    style="font-size:12px;font-weight:500;display:inline-flex;align-items:center;gap:2px">
                @if (c.up) { <app-icon name="trend-up" [size]="12" color="#16a34a"></app-icon> }
                @if (c.down) { <app-icon name="trend-down" [size]="12" color="#ef4444"></app-icon> }
                <span>{{c.change}}</span>
              </span>
            </div>
            <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em">
              {{c.label}}
            </div>
            <div style="font-size:28px;font-weight:700;margin-top:4px">{{c.value}}</div>
          </div>
        }
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px">
        <div class="card">
          <h3 style="font-weight:600;margin-bottom:16px">Эффективность по отделам</h3>
          <canvas #barCanvas></canvas>
        </div>
        <div class="card">
          <h3 style="font-weight:600;margin-bottom:16px">Тренд среднего балла за 6 месяцев</h3>
          <canvas #trendCanvas></canvas>
        </div>
      </div>

      <div class="card">
        <h3 style="font-weight:600;margin-bottom:16px">Лучшие результаты симуляций этой недели</h3>
        <table style="width:100%;font-size:14px;border-collapse:collapse">
          <thead>
            <tr style="text-align:left;color:#9ca3af;border-bottom:1px solid #f3f4f6">
              <th style="padding-bottom:12px;font-weight:500">Сотрудник</th>
              <th style="padding-bottom:12px;font-weight:500">Отдел</th>
              <th style="padding-bottom:12px;font-weight:500">Балл симуляции</th>
              <th style="padding-bottom:12px;font-weight:500">Ключевой навык</th>
            </tr>
          </thead>
          <tbody>
            @if (!topPerformers.length) {
              <tr><td colspan="4" style="padding:24px;text-align:center;color:#9ca3af">
                Пока нет данных. Завершите несколько диалогов.
              </td></tr>
            }
            @for (p of topPerformers; track p.name) {
              <tr style="border-bottom:1px solid #fafafa">
                <td style="padding:12px 0;font-weight:600">{{p.name}}</td>
                <td style="padding:12px 0;color:#6b7280">{{p.department}}</td>
                <td style="padding:12px 0">
                  <span [style.color]="p.score >= 85 ? '#16a34a' : '#2563eb'"
                        style="font-weight:700">{{p.score}}</span>
                </td>
                <td style="padding:12px 0"><span class="badge badge-blue">{{p.skill}}</span></td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class AnalyticsComponent implements OnInit, AfterViewInit {
  @ViewChild('barCanvas')   barRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('trendCanvas') trendRef!: ElementRef<HTMLCanvasElement>;

  depts: any[] = [];
  topPerformers: any[] = [];
  trend: any[] = [];

  summaryCards: any[] = [
    { icon: 'users',    iconColor: '#2563eb', bg: '#eff6ff', label: 'АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ',  value: '—', change: '', up: false, down: false },
    { icon: 'check',    iconColor: '#16a34a', bg: '#f0fdf4', label: 'ЗАВЕРШАЕМОСТЬ ДИАЛОГОВ', value: '—', change: '', up: false, down: false },
    { icon: 'fire',     iconColor: '#ef4444', bg: '#fef2f2', label: 'ВОВЛЕЧЁННОСТЬ',           value: '—', change: '', up: false, down: false },
    { icon: 'warning',  iconColor: '#ca8a04', bg: '#fefce8', label: 'КРИТИЧЕСКИЕ ПРОБЕЛЫ',     value: '—', change: '', up: false, down: false },
  ];

  private barChart: Chart | null = null;
  private trendChart: Chart | null = null;
  private viewReady = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getHrSummary().subscribe(s => this.applySummary(s));
    this.api.getDepartments().subscribe(d => { this.depts = d || []; this.renderBarChart(); });
    this.api.getTopPerformers().subscribe(d => this.topPerformers = d || []);
    this.api.getMonthlyTrend().subscribe(d => { this.trend = d || []; this.renderTrendChart(); });
  }

  ngAfterViewInit() {
    this.viewReady = true;
    this.renderBarChart();
    this.renderTrendChart();
  }

  private applySummary(s: any) {
    const change = (pct: number) => (pct > 0 ? `+${pct}%` : (pct < 0 ? `${pct}%` : '0%'));
    this.summaryCards = [
      {
        icon: 'users', iconColor: '#2563eb', bg: '#eff6ff',
        label: 'АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ',
        value: s.active_users,
        change: change(s.active_users_change_pct),
        up: s.active_users_change_pct > 0, down: s.active_users_change_pct < 0,
      },
      {
        icon: 'check', iconColor: '#16a34a', bg: '#f0fdf4',
        label: 'ЗАВЕРШАЕМОСТЬ ДИАЛОГОВ',
        value: `${s.course_completion_pct}%`,
        change: change(s.course_completion_change_pct),
        up: s.course_completion_change_pct > 0, down: s.course_completion_change_pct < 0,
      },
      {
        icon: 'fire', iconColor: '#ef4444', bg: '#fef2f2',
        label: 'ВОВЛЕЧЁННОСТЬ',
        value: `${s.engagement_hours_per_week} ч/нед`,
        change: change(s.engagement_change_pct),
        up: s.engagement_change_pct > 0, down: s.engagement_change_pct < 0,
      },
      {
        icon: 'warning', iconColor: '#ca8a04', bg: '#fefce8',
        label: 'КРИТИЧЕСКИЕ ПРОБЕЛЫ',
        value: `${s.critical_gaps}`, change: '',
        up: false, down: false,
      },
    ];
  }

  private renderBarChart() {
    if (!this.viewReady || !this.barRef || !this.depts.length) return;
    if (this.barChart) this.barChart.destroy();
    this.barChart = new Chart(this.barRef.nativeElement, {
      type: 'bar',
      data: {
        labels: this.depts.map(d => d.department),
        datasets: [
          { label: '% Завершения', data: this.depts.map(d => d.completion_rate),
            backgroundColor: 'rgba(59,130,246,0.7)' },
          { label: 'Вовлечённость x 20', data: this.depts.map(d => d.engagement_score * 20),
            backgroundColor: 'rgba(16,185,129,0.7)' },
        ],
      },
      options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } },
    });
  }

  private renderTrendChart() {
    if (!this.viewReady || !this.trendRef || !this.trend.length) return;
    if (this.trendChart) this.trendChart.destroy();
    this.trendChart = new Chart(this.trendRef.nativeElement, {
      type: 'line',
      data: {
        labels: this.trend.map(t => t.month),
        datasets: [{
          label: 'Средний балл',
          data: this.trend.map(t => t.value),
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139,92,246,0.1)',
          tension: 0.3, fill: true, pointRadius: 4,
        }],
      },
      options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } },
    });
  }
}
