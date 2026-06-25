-- ============================================================
-- DeepTalk — Supabase Schema
-- 在 Supabase 控制台 → SQL Editor 中运行此文件
-- ============================================================

-- 用户表
create table if not exists users (
  username      text primary key,
  display_name  text not null,
  password_hash text not null,
  created_at    timestamptz default now()
);

-- 联系人表（每行一个人物，归属某个用户）
create table if not exists persons (
  id            text primary key,
  owner         text not null references users(username) on delete cascade,
  name          text not null,
  color         text default '#3d6bff',
  chat_records  text default '',
  analysis      jsonb default '{}',
  chat_history  jsonb default '[]',
  created_at    timestamptz default now()
);

create index if not exists idx_persons_owner on persons(owner);

-- 全局 Agent 对话历史（每个用户一条记录）
create table if not exists global_history (
  username  text primary key references users(username) on delete cascade,
  messages  jsonb default '[]'
);
