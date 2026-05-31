import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { IconComponent } from '../../components/icon/icon.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f8f9fb">
      <div class="card" style="width:400px;padding:32px">
        <div style="text-align:center;margin-bottom:28px">
          <div style="width:56px;height:56px;background:#eff6ff;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px">
            <app-icon name="academy" [size]="32" color="#2563eb"></app-icon>
          </div>
          <h1 style="font-size:22px;font-weight:700;color:#1f2937">ИИ-Академия</h1>
          <p style="font-size:14px;color:#9ca3af;margin-top:4px">Платформа развития Soft-Skills</p>
        </div>

        @if (error) {
          <div style="background:#fef2f2;color:#dc2626;padding:12px 14px;border-radius:8px;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px">
            <app-icon name="warning" [size]="16" color="#dc2626"></app-icon>
            <span>{{error}}</span>
          </div>
        }

        <form (ngSubmit)="onLogin()">
          <input [(ngModel)]="email" name="email" type="email" placeholder="Email"
            style="width:100%;margin-bottom:12px">
          <input [(ngModel)]="password" name="password" type="password" placeholder="Пароль"
            style="width:100%;margin-bottom:18px">
          <button type="submit" class="btn-primary" [disabled]="loading"
            style="width:100%;justify-content:center;padding:12px">
            @if (loading) {
              <span>Вход...</span>
            } @else {
              <app-icon name="arrow-right" [size]="16" color="#fff"></app-icon>
              <span>Войти</span>
            }
          </button>
        </form>

        <div style="margin-top:20px;padding-top:16px;border-top:1px solid #f3f4f6;font-size:12px;color:#9ca3af;line-height:1.8">
          <div style="font-weight:600;color:#6b7280;margin-bottom:4px">Демо-аккаунты:</div>
          <div>Сотрудник: employee&#64;company.ru / emp123456</div>
          <div>HR: hr&#64;company.ru / hr123456</div>
          <div>Администратор: admin&#64;company.ru / admin123</div>
        </div>
      </div>
    </div>
  `,
})
export class LoginComponent {
  email = 'employee@company.ru';
  password = 'emp123456';
  error = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onLogin() {
    this.error = '';
    this.loading = true;
    this.auth.login(this.email, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail || 'Неверный email или пароль';
      },
    });
  }
}
