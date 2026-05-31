import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-mentor',
  standalone: true,
  imports: [CommonModule, RouterLink, IconComponent],
  template: `
    <div style="padding:24px">
      <h2 style="font-size:24px;font-weight:700;margin-bottom:8px">AI-Наставник</h2>
      <p style="font-size:14px;color:#6b7280;margin-bottom:24px">
        Персональные рекомендации на основе вашего прогресса.
      </p>

      @if (skills.length) {
        <div class="card" style="max-width:720px;margin-bottom:16px">
          <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px">
            <div style="width:40px;height:40px;background:#f3e8ff;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <app-icon name="sparkle" [size]="20" color="#8b5cf6"></app-icon>
            </div>
            <div style="flex:1">
              <div style="font-weight:600;color:#1f2937">ИИ-Наставник</div>
              <div style="font-size:14px;color:#4b5563;margin-top:8px;line-height:1.6">
                @if (strongest) {
                  <div>
                    Ваша сильнейшая сторона — <strong>{{strongest.skill_name}}</strong>
                    ({{strongest.current_level | number:'1.0-0'}}/100). Используйте это как базу.
                  </div>
                }
                @if (weakest) {
                  <div style="margin-top:12px">
                    Требует внимания — <strong>{{weakest.skill_name}}</strong>
                    ({{weakest.current_level | number:'1.0-0'}}/100). Рекомендуем сосредоточиться на этом навыке.
                  </div>
                }
              </div>
            </div>
          </div>

          <div style="background:#eff6ff;border-radius:8px;padding:16px;margin-top:16px">
            <div style="font-size:14px;font-weight:600;color:#1d4ed8;margin-bottom:8px;display:flex;align-items:center;gap:6px">
              <app-icon name="clipboard" [size]="16" color="#1d4ed8"></app-icon>
              <span>Рекомендованный план на неделю:</span>
            </div>
            <ul style="font-size:14px;color:#2563eb;list-style:none;display:flex;flex-direction:column;gap:6px">
              <li>1. Пройти симуляцию по вашему слабому навыку (20–30 мин)</li>
              <li>2. Изучить модуль «Эмоциональный интеллект» (45 мин)</li>
              <li>3. Повторить оценку навыков через 7 дней</li>
            </ul>
          </div>

          <a routerLink="/simulator" class="btn-primary" style="display:inline-flex;margin-top:16px">
            <span>Перейти к симулятору</span>
            <app-icon name="arrow-right" [size]="16" color="#fff"></app-icon>
          </a>
        </div>
      } @else {
        <div class="card" style="max-width:640px">
          <p style="color:#6b7280">
            Наставник анализирует ваш профиль. Пройдите хотя бы одну симуляцию —
            и здесь появятся персональные рекомендации.
          </p>
          <a routerLink="/simulator" class="btn-primary" style="display:inline-flex;margin-top:16px">
            <span>Начать симуляцию</span>
            <app-icon name="arrow-right" [size]="16" color="#fff"></app-icon>
          </a>
        </div>
      }
    </div>
  `,
})
export class MentorComponent implements OnInit {
  skills: any[] = [];
  strongest: any = null;
  weakest: any = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getSkillMap().subscribe(data => {
      this.skills = data || [];
      if (this.skills.length) {
        const sorted = [...this.skills].sort((a, b) => b.current_level - a.current_level);
        this.strongest = sorted[0];
        this.weakest = sorted[sorted.length - 1];
      }
    });
  }
}
