import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // ─── Пользовательский дашборд / навыки ────────────
  getDashboard(): Observable<any>  { return this.http.get('/api/dashboard'); }
  getSkillMap():  Observable<any>  { return this.http.get('/api/skills/map'); }

  // ─── Диалоги (двухшаговая архитектура) ────────────
  getScenarios():               Observable<any> { return this.http.get('/api/dialog/scenarios'); }
  startDialog(id: number):      Observable<any> { return this.http.post('/api/dialog/start', { scenario_id: id }); }
  sendMessage(sid: number, text: string): Observable<any> {
    return this.http.post(`/api/dialog/${sid}/message`, { message_text: text });
  }
  requestAiReply(sid: number):  Observable<any> { return this.http.post(`/api/dialog/${sid}/ai-reply`, {}); }
  completeDialog(sid: number):  Observable<any> { return this.http.post(`/api/dialog/${sid}/complete`, {}); }
  getSession(sid: number):      Observable<any> { return this.http.get(`/api/dialog/${sid}`); }

  // ─── HR-аналитика ─────────────────────────────────
  getDepartments():    Observable<any> { return this.http.get('/api/hr/analytics/departments'); }
  getTopPerformers():  Observable<any> { return this.http.get('/api/hr/analytics/top-performers'); }
  getHrSummary():      Observable<any> { return this.http.get('/api/hr/analytics/summary'); }
  getMonthlyTrend():   Observable<any> { return this.http.get('/api/hr/analytics/trend'); }

  // ─── Админка ──────────────────────────────────────
  getAdminStats():     Observable<any> { return this.http.get('/api/admin/stats'); }
  getUsers():          Observable<any> { return this.http.get('/api/admin/users'); }
  createUser(data: any):  Observable<any> { return this.http.post('/api/admin/users', data); }
  updateUser(id: number, data: any): Observable<any> { return this.http.patch(`/api/admin/users/${id}`, data); }
  deleteUser(id: number): Observable<any> { return this.http.delete(`/api/admin/users/${id}`); }
  getLogs(eventType?: string): Observable<any> {
    const q = eventType ? `?event_type=${encodeURIComponent(eventType)}` : '';
    return this.http.get(`/api/admin/logs${q}`);
  }

  // ─── Задания (v3) ─────────────────────────────────
  /** Возвращает задания:
   *  - для сотрудника: только свои;
   *  - для HR/admin: все в системе. */
  getAssignments(): Observable<any>     { return this.http.get('/api/assignments'); }

  /** HR/admin: список сотрудников, которым можно выдать задание. */
  getAssignableEmployees(): Observable<any> {
    return this.http.get('/api/assignments/employees');
  }

  /** HR/admin: создать задание. */
  createAssignment(data: any): Observable<any> {
    return this.http.post('/api/assignments', data);
  }

  /** Обновить статус или заметку о выполнении. */
  updateAssignment(id: number, data: any): Observable<any> {
    return this.http.patch(`/api/assignments/${id}`, data);
  }

  /** HR/admin: удалить задание. */
  deleteAssignment(id: number): Observable<any> {
    return this.http.delete(`/api/assignments/${id}`);
  }

  // ─── Отчёты о достижениях (v3.1) ──────────────────
  /** HR/admin: список сотрудников для пикера. */
  getReportEmployees(search = ''): Observable<any> {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.http.get(`/api/reports/employees${q}`);
  }

  /** HR/admin: скачать отчёт по сотруднику (blob). */
  downloadReport(userId: number, format: 'pdf' | 'docx'): Observable<any> {
    return this.http.get(
      `/api/reports/download/${userId}?format=${format}`,
      { responseType: 'blob', observe: 'response' },
    );
  }
}
