/**
 * Единая библиотека иконок проекта.
 *
 * Использование:
 *   <app-icon name="dashboard" />
 *   <app-icon name="target" [size]="20" color="#2563eb" />
 *   <app-icon [name]="dynamicName" [size]="16" />
 *
 * Все иконки — outline-стиль в единой системе (stroke-based),
 * 24x24 viewBox, stroke-width=1.75. Стиль нарочно собственный, чтобы
 * не выглядел как ChatGPT/Claude-интерфейс: без эмодзи, без Lucide,
 * без Material Icons — просто аккуратные геометричные линии.
 */
import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

// Экспортируем тип — на случай если где-то надо проверить на уровне типов.
// В шаблонах же используем просто string (см. @Input ниже), чтобы можно
// было передавать вычисляемые значения без кастов.
export type IconName =
  | 'dashboard' | 'map' | 'chat' | 'sparkle' | 'users' | 'chart'
  | 'settings' | 'bell' | 'trophy' | 'target' | 'clock' | 'book'
  | 'fire' | 'check' | 'plus' | 'edit' | 'trash' | 'close'
  | 'arrow-right' | 'arrow-left' | 'arrow-up' | 'arrow-down'
  | 'logout' | 'academy' | 'send' | 'robot' | 'user' | 'shield'
  | 'warning' | 'info' | 'lightbulb' | 'calendar' | 'briefcase'
  | 'trend-up' | 'trend-down' | 'play' | 'stop' | 'menu'
  | 'clipboard' | 'flag' | 'star' | 'lock' | 'search';

const ICONS: Record<string, string> = {
  // Дашборд — сетка 2x2
  dashboard: `
    <rect x="3" y="3" width="7" height="7" rx="1.5"/>
    <rect x="14" y="3" width="7" height="7" rx="1.5"/>
    <rect x="3" y="14" width="7" height="7" rx="1.5"/>
    <rect x="14" y="14" width="7" height="7" rx="1.5"/>`,

  // Карта навыков — компас
  map: `
    <circle cx="12" cy="12" r="9"/>
    <path d="m15.5 8.5-3.5 7.5-3.5-3.5z"/>`,

  // Диалог/чат
  chat: `
    <path d="M4 7c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2v6c0 1.1-.9 2-2 2h-3l-3 3v-3H6c-1.1 0-2-.9-2-2z"/>`,

  // AI-наставник — искра
  sparkle: `
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>
    <circle cx="12" cy="12" r="2.5"/>`,

  // Люди/команда
  users: `
    <circle cx="9" cy="8" r="3"/>
    <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/>
    <circle cx="17" cy="9" r="2.5"/>
    <path d="M15 20c0-2.5 1.5-4.5 4-5"/>`,

  // График-аналитика
  chart: `
    <path d="M3 3v18h18"/>
    <path d="M7 14l3-3 3 3 5-6"/>`,

  // Настройки
  settings: `
    <circle cx="12" cy="12" r="3"/>
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>`,

  // Колокольчик-уведомления
  bell: `
    <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9"/>
    <path d="M10 21a2 2 0 0 0 4 0"/>`,

  // Трофей
  trophy: `
    <path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0z"/>
    <path d="M17 5h3a2 2 0 0 1-2 4M7 5H4a2 2 0 0 0 2 4"/>`,

  // Мишень
  target: `
    <circle cx="12" cy="12" r="9"/>
    <circle cx="12" cy="12" r="5"/>
    <circle cx="12" cy="12" r="1.5" fill="currentColor"/>`,

  // Часы
  clock: `
    <circle cx="12" cy="12" r="9"/>
    <path d="M12 7v5l3 2"/>`,

  // Книга
  book: `
    <path d="M4 4.5A1.5 1.5 0 0 1 5.5 3h13A1.5 1.5 0 0 1 20 4.5V19a1 1 0 0 1-1 1H6a2 2 0 0 0-2 2z"/>
    <path d="M4 20a2 2 0 0 1 2-2h14"/>`,

  // Огонь/серия
  fire: `
    <path d="M12 2c1.5 3 4 4.5 4 8a4 4 0 0 1-8 0c0-1.5.5-2.5 1.5-3.5C9 9 10 7.5 10 6c0-1 .5-2 2-4z"/>
    <path d="M10 14.5c0 1.4 1 2.5 2 2.5s2-1.1 2-2.5"/>`,

  // Галочка
  check: `<path d="M4 12l5 5L20 6"/>`,

  // Плюс
  plus: `<path d="M12 5v14M5 12h14"/>`,

  // Карандаш-редактировать
  edit: `
    <path d="M4 20h4L19 9l-4-4L4 16z"/>
    <path d="M13 7l4 4"/>`,

  // Корзина
  trash: `
    <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>
    <path d="M10 11v6M14 11v6"/>`,

  // Крестик
  close: `<path d="M6 6l12 12M6 18L18 6"/>`,

  // Стрелки
  'arrow-right': `<path d="M5 12h14M13 6l6 6-6 6"/>`,
  'arrow-left':  `<path d="M19 12H5M11 6l-6 6 6 6"/>`,
  'arrow-up':    `<path d="M12 19V5M6 11l6-6 6 6"/>`,
  'arrow-down':  `<path d="M12 5v14M6 13l6 6 6-6"/>`,

  // Выход
  logout: `
    <path d="M10 17l5-5-5-5"/>
    <path d="M15 12H3"/>
    <path d="M19 4h-8c-1.1 0-2 .9-2 2v3M9 15v3c0 1.1.9 2 2 2h8"/>`,

  // Академия/шапочка
  academy: `
    <path d="M2 10l10-5 10 5-10 5z"/>
    <path d="M6 12v4c0 1.5 3 3 6 3s6-1.5 6-3v-4"/>
    <path d="M22 10v5"/>`,

  // Отправить
  send: `<path d="M4 12l16-8-6 18-2-8z"/>`,

  // Робот
  robot: `
    <rect x="5" y="7" width="14" height="12" rx="2"/>
    <circle cx="9" cy="13" r="1.5" fill="currentColor"/>
    <circle cx="15" cy="13" r="1.5" fill="currentColor"/>
    <path d="M12 7V4M10 4h4"/>
    <path d="M3 13v3M21 13v3"/>`,

  // Одиночный пользователь
  user: `
    <circle cx="12" cy="8" r="4"/>
    <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>`,

  // Щит (admin)
  shield: `
    <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6z"/>
    <path d="M9 12l2 2 4-4"/>`,

  // Предупреждение
  warning: `
    <path d="M12 3l10 18H2z"/>
    <path d="M12 10v5M12 18.5v.5"/>`,

  // Инфо
  info: `
    <circle cx="12" cy="12" r="9"/>
    <path d="M12 16v-5"/>
    <circle cx="12" cy="8.5" r="0.8" fill="currentColor"/>`,

  // Лампочка
  lightbulb: `
    <path d="M9 18h6M10 21h4"/>
    <path d="M7 9a5 5 0 0 1 10 0c0 3-2 4-2 7H9c0-3-2-4-2-7z"/>`,

  // Календарь
  calendar: `
    <rect x="3" y="5" width="18" height="16" rx="2"/>
    <path d="M3 10h18M8 3v4M16 3v4"/>`,

  // Портфель
  briefcase: `
    <rect x="3" y="7" width="18" height="14" rx="2"/>
    <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>`,

  'trend-up':   `<path d="M3 17l6-6 4 4 8-8M14 7h7v7"/>`,
  'trend-down': `<path d="M3 7l6 6 4-4 8 8M14 17h7v-7"/>`,

  // Воспроизведение
  play: `<path d="M6 4v16l14-8z"/>`,
  stop: `<rect x="5" y="5" width="14" height="14" rx="2"/>`,

  // Меню (бургер)
  menu: `<path d="M4 6h16M4 12h16M4 18h16"/>`,

  // Планшет/задание
  clipboard: `
    <rect x="5" y="4" width="14" height="17" rx="2"/>
    <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1"/>
    <path d="M9 12h6M9 16h4"/>`,

  // Флаг (приоритет)
  flag: `
    <path d="M5 3v18"/>
    <path d="M5 4h13l-2 4 2 4H5"/>`,

  // Звезда
  star: `
    <path d="M12 3l2.7 5.7 6.3.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2-4.5-4.4 6.3-.9z"/>`,

  // Замок
  lock: `
    <rect x="5" y="11" width="14" height="10" rx="2"/>
    <path d="M8 11V7a4 4 0 0 1 8 0v4"/>`,

  // Поиск
  search: `
    <circle cx="11" cy="11" r="7"/>
    <path d="M20 20l-4.3-4.3"/>`,
};


@Component({
  selector: 'app-icon',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg xmlns="http://www.w3.org/2000/svg"
         [attr.width]="size" [attr.height]="size"
         viewBox="0 0 24 24" fill="none"
         [attr.stroke]="color" stroke-width="1.75"
         stroke-linecap="round" stroke-linejoin="round"
         style="display:inline-block;vertical-align:middle;flex-shrink:0"
         [innerHTML]="svgBody"></svg>
  `,
})
export class IconComponent {
  // Принимаем обычную строку, чтобы можно было передавать значения
  // вычисленные в compile-time (например, из nav-меню или списка задач).
  // Если строка не найдена в ICONS — покажем fallback-иконку 'dashboard'.
  @Input() name: string = 'dashboard';
  @Input() size: number = 20;
  @Input() color: string = 'currentColor';

  constructor(private sanitizer: DomSanitizer) {}

  get svgBody(): SafeHtml {
    const body = ICONS[this.name] || ICONS['dashboard'];
    return this.sanitizer.bypassSecurityTrustHtml(body);
  }
}
