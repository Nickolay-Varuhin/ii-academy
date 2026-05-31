import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

/** Фабрика guard'а: принимает список разрешённых ролей.
 *  Пример: canActivate: [roleGuard(['hr', 'admin'])] */
export const roleGuard = (allowedRoles: string[]): CanActivateFn => () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.user) return router.createUrlTree(['/login']);
  if (allowedRoles.includes(auth.user.role)) return true;
  // Роль не подходит → на главную
  return router.createUrlTree(['/']);
};
