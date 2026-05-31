import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, tap } from 'rxjs';

export interface AuthUser {
  user_id: number;
  full_name: string;
  role: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private userSubject = new BehaviorSubject<AuthUser | null>(this.loadUser());
  user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient, private router: Router) {}

  get user(): AuthUser | null { return this.userSubject.value; }
  get isLoggedIn(): boolean { return !!this.user; }
  get token(): string | null { return localStorage.getItem('token'); }

  login(email: string, password: string) {
    return this.http.post<any>('/api/auth/login', { email, password }).pipe(
      tap(data => {
        localStorage.setItem('token', data.access_token);
        const u: AuthUser = {
          user_id: data.user_id,
          full_name: data.full_name,
          role: data.role,
        };
        localStorage.setItem('user', JSON.stringify(u));
        this.userSubject.next(u);
      })
    );
  }

  logout() {
    localStorage.clear();
    this.userSubject.next(null);
    this.router.navigate(['/login']);
  }

  private loadUser(): AuthUser | null {
    const s = localStorage.getItem('user');
    return s ? JSON.parse(s) : null;
  }
}
