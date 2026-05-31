import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Chart, RadarController, RadialLinearScale, PointElement,
         LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

Chart.register(RadarController, RadialLinearScale, PointElement,
               LineElement, Filler, Tooltip, Legend);

@Component({
  selector: 'app-skill-map',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <div style="padding:24px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
        <div>
          <h2 style="font-size:24px;font-weight:700">Профиль компетенций</h2>
          <p style="font-size:14px;color:#6b7280;margin-top:4px">
            Визуализация ваших текущих навыков относительно ожиданий должности.
          </p>
        </div>
        <a routerLink="/simulator" class="btn-primary" style="background:#16a34a">
          <app-icon name="target" [size]="16" color="#fff"></app-icon>
          <span>Начать тренировку</span>
        </a>
      </div>

      @if (!skills.length) {
        <div class="card" style="text-align:center;padding:48px;color:#9ca3af">
          Данные о навыках ещё не собраны. Пройдите несколько симуляций,
          и здесь появится ваша карта компетенций.
        </div>
      } @else {
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:24px">
          <div class="card">
            <h3 style="font-weight:600;margin-bottom:4px">Радар навыков (Soft-Skills)</h3>
            <div style="font-size:12px;color:#9ca3af;margin-bottom:16px;display:flex;gap:16px">
              <span style="display:inline-flex;align-items:center;gap:4px">
                <span style="width:8px;height:8px;background:#3b82f6;border-radius:50%"></span>
                Текущий уровень
              </span>
              <span style="display:inline-flex;align-items:center;gap:4px">
                <span style="width:8px;height:8px;border:1.5px dashed #9ca3af;border-radius:50%"></span>
                Цель должности
              </span>
            </div>
            <div style="max-width:480px;margin:0 auto;position:relative;height:400px">
              <canvas #radarCanvas></canvas>
            </div>
          </div>

          <div style="display:flex;flex-direction:column;gap:16px">
            <div class="card">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                <app-icon name="target" [size]="18" color="#2563eb"></app-icon>
                <h3 style="font-weight:600">Зоны для роста</h3>
              </div>
              <p style="font-size:12px;color:#9ca3af;margin-bottom:16px">
                Рекомендуем сфокусироваться на следующих областях.
              </p>
              @for (s of growthZones; track s.skill_id) {
                <div style="margin-bottom:16px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:14px;font-weight:500">{{s.skill_name}}</span>
                    <span style="font-size:14px;font-weight:700">
                      {{s.current_level | number:'1.0-0'}}<span style="color:#9ca3af;font-weight:400">/{{s.target_level}}</span>
                    </span>
                  </div>
                  <div style="height:8px;background:#f3f4f6;border-radius:9999px">
                    <div [style.width.%]="(s.current_level / s.target_level) * 100"
                         [style.background]="s.current_level < 65 ? '#8b5cf6' : '#3b82f6'"
                         style="height:100%;border-radius:9999px;transition:width 0.3s"></div>
                  </div>
                  <div style="display:flex;justify-content:space-between;margin-top:4px">
                    <span style="font-size:11px;color:#9ca3af">
                      Осталось {{s.target_level - s.current_level | number:'1.0-0'}} баллов
                    </span>
                    <a routerLink="/simulator" style="font-size:12px;color:#2563eb;font-weight:600">Тренировка →</a>
                  </div>
                </div>
              }
              @if (!growthZones.length) {
                <div style="color:#16a34a;font-size:14px;display:flex;align-items:center;gap:6px">
                  <app-icon name="check" [size]="16" color="#16a34a"></app-icon>
                  <span>Все навыки на целевом уровне!</span>
                </div>
              }
            </div>

            <div class="card" style="border:1.5px solid #dcfce7;background:#fafffc">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
                <app-icon name="trophy" [size]="18" color="#16a34a"></app-icon>
                <h3 style="font-weight:600">Ключевые сильные стороны</h3>
              </div>
              @for (s of strengths; track s.skill_id) {
                <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0">
                  <div style="display:flex;align-items:center;gap:8px">
                    <app-icon name="trend-up" [size]="16" color="#16a34a"></app-icon>
                    <span style="font-size:14px;font-weight:500">{{s.skill_name}}</span>
                  </div>
                  <span class="badge badge-green">{{s.current_level | number:'1.0-0'}}/100</span>
                </div>
              }
              @if (!strengths.length) {
                <div style="color:#9ca3af;font-size:14px">
                  Продолжайте обучение — сильные стороны появятся здесь.
                </div>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class SkillMapComponent implements OnInit, OnDestroy {
  skills: any[] = [];
  growthZones: any[] = [];
  strengths: any[] = [];

  private _canvasRef?: ElementRef<HTMLCanvasElement>;
  private chart: Chart | null = null;

  // Setter вместо простого @ViewChild — срабатывает при каждом появлении
  // canvas в DOM. Это устраняет гонку условий: старая версия пыталась
  // отрисовать до того как canvas был добавлен (он был внутри @else).
  @ViewChild('radarCanvas')
  set canvasRef(ref: ElementRef<HTMLCanvasElement> | undefined) {
    this._canvasRef = ref;
    if (ref) setTimeout(() => this.tryRender(), 0);
  }

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getSkillMap().subscribe(data => {
      this.skills = data || [];
      this.growthZones = this.skills
        .filter(s => s.current_level < s.target_level)
        .sort((a, b) => a.current_level - b.current_level)
        .slice(0, 3);
      this.strengths = this.skills
        .filter(s => s.current_level >= 80)
        .sort((a, b) => b.current_level - a.current_level)
        .slice(0, 3);
      setTimeout(() => this.tryRender(), 0);
    });
  }

  ngOnDestroy() {
    if (this.chart) { this.chart.destroy(); this.chart = null; }
  }

  private tryRender() {
    if (!this._canvasRef || !this.skills.length) return;
    if (this.chart) { this.chart.destroy(); this.chart = null; }

    this.chart = new Chart(this._canvasRef.nativeElement, {
      type: 'radar',
      data: {
        labels: this.skills.map(s => s.skill_name),
        datasets: [
          {
            label: 'Текущий уровень',
            data: this.skills.map(s => s.current_level),
            backgroundColor: 'rgba(59,130,246,0.15)',
            borderColor: 'rgba(59,130,246,0.7)',
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: 'rgba(59,130,246,1)',
          },
          {
            label: 'Цель должности',
            data: this.skills.map(s => s.target_level),
            backgroundColor: 'rgba(156,163,175,0.08)',
            borderColor: 'rgba(156,163,175,0.5)',
            borderWidth: 1,
            borderDash: [4, 4],
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: { stepSize: 25, backdropColor: 'transparent' },
            pointLabels: { font: { size: 12, weight: 'bold' } },
          },
        },
        plugins: { legend: { display: false } },
      },
    });
  }
}
