import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
 
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const COUNTRIES = [
  '中国', '美国', '日本', '韩国', '俄罗斯', '英国', '法国', '德国', '印度', 
  '加拿大', '澳大利亚', '巴西', '朝鲜', '伊朗', '以色列', '乌克兰', '欧盟', 
  '东盟', '意大利', '西班牙', '荷兰', '瑞士', '瑞典', '新加坡', '越南'
];

export function isCountry(label: string): boolean {
  return COUNTRIES.some(country => label.includes(country));
}
