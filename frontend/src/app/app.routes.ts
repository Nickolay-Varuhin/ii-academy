import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { roleGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  {
    path: '',
    loadComponent: () => import('./components/layout/layout.component').then(m => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      // Общая — для всех
      { path: '', loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent) },

      // ─── Только для сотрудника (HR/admin сюда не попадают) ───
      {
        path: 'skills',
        loadComponent: () => import('./pages/skill-map/skill-map.component').then(m => m.SkillMapComponent),
        canActivate: [roleGuard(['employee'])],
      },
      {
        path: 'simulator',
        loadComponent: () => import('./pages/simulator/simulator.component').then(m => m.SimulatorComponent),
        canActivate: [roleGuard(['employee'])],
      },
      {
        path: 'mentor',
        loadComponent: () => import('./pages/mentor/mentor.component').then(m => m.MentorComponent),
        canActivate: [roleGuard(['employee'])],
      },
      {
        path: 'assignments',
        loadComponent: () => import('./pages/assignments/assignments.component').then(m => m.AssignmentsComponent),
        canActivate: [roleGuard(['employee'])],
      },

      // ─── Только для HR/admin ───
      {
        path: 'analytics',
        loadComponent: () => import('./pages/analytics/analytics.component').then(m => m.AnalyticsComponent),
        canActivate: [roleGuard(['hr', 'admin'])],
      },
      {
        path: 'hr-dashboard',
        loadComponent: () => import('./pages/hr-dashboard/hr-dashboard.component').then(m => m.HrDashboardComponent),
        canActivate: [roleGuard(['hr', 'admin'])],
      },
      {
        path: 'hr-assignments',
        loadComponent: () => import('./pages/hr-assignments/hr-assignments.component').then(m => m.HrAssignmentsComponent),
        canActivate: [roleGuard(['hr', 'admin'])],
      },
      {
        path: 'reports',
        loadComponent: () => import('./pages/reports/reports.component').then(m => m.ReportsComponent),
        canActivate: [roleGuard(['hr', 'admin'])],
      },

      // ─── Только admin ───
      {
        path: 'admin',
        loadComponent: () => import('./pages/admin/admin.component').then(m => m.AdminComponent),
        canActivate: [roleGuard(['admin'])],
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
