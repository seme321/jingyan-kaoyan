/**
 * 平台品牌配置（多院校、多专业课通用考研复习站）。
 * 具体院校与科目信息由 `public/data/courses.json` 动态驱动。
 */
export const BRAND = {
  name: '鲸研',
  fullName: '鲸研专业课',
  mascotName: '大肥鱼',
  tagline: '精研历年真题 · 吃透专业课原理',
  contact: 'amassss321@gmail.com',
  qqGroup: '1058675261',
  /** Cloudflare Workers + D1「先审后发」公开留言后端接口 */
  guestbookApiUrl: '/api/guestbook',
  backupPrefix: '鲸研考研_学习记录全量备份',
} as const;
